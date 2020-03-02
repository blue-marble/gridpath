#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Projects that can be partly or fully 'energy-only,' i.e. some of the capacity
can have no PRM contribution (and therefore potentially incur a smaller cost),
or partly or fully deliverable
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Var, Set, Param, Constraint, NonNegativeReals, \
    Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import
from gridpath.auxiliary.dynamic_components import prm_cost_group_sets, \
    prm_cost_group_prm_type


# TODO: rename deliverability_group_deliverability_cost_per_mw --> deliverability_group_deliverability_cost_per_mw_yr

def add_module_specific_components(m, d):
    """
    EOA: Energy-Only Allowed
    :param m: 
    :param d: 
    :return: 
    """

    m.EOA_PRM_PROJECTS = Set(
        within=m.PRM_PROJECTS,
        initialize=lambda mod:
        [p for p in mod.PRM_PROJECTS if mod.prm_type[p] == 
         "energy_only_allowed"]
    )

    m.EOA_PRM_PROJECT_OPERATIONAL_PERIODS = Set(
        dimen=2,
        within=m.PRM_PROJECT_OPERATIONAL_PERIODS,
        initialize=lambda mod: [
            (project, period)
            for (project, period) in mod.PRM_PROJECT_OPERATIONAL_PERIODS
            if project in mod.EOA_PRM_PROJECTS
        ]
    )

    # We can allow the 'fully-deliverable' capacity to be different from the
    # total capacity since in some cases full deliverability may require
    # additional costs to be incurred (e.g. for transmission, etc.)
    m.Deliverable_Capacity_MW = Var(
        m.EOA_PRM_PROJECT_OPERATIONAL_PERIODS, within=NonNegativeReals
    )
    m.Energy_Only_Capacity_MW = Var(
        m.EOA_PRM_PROJECT_OPERATIONAL_PERIODS, within=NonNegativeReals
    )

    def max_deliverable_capacity_constraint(mod, g, p):
        """
        The fully deliverable capacity can't exceed the total project capacity
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        return mod.Deliverable_Capacity_MW[g, p] + \
            mod.Energy_Only_Capacity_MW[g, p] \
            == mod.Capacity_MW[g, p]

    m.Max_Deliverable_Capacity_Constraint = Constraint(
        m.EOA_PRM_PROJECT_OPERATIONAL_PERIODS,
        rule=max_deliverable_capacity_constraint
    )

    # Costs for having fully deliverable capacity by project group
    # We'll need to figure out how much capacity is built in groups of
    # projects, not by individual project
    m.DELIVERABILITY_GROUPS = Set()
    # Add to list of sets we'll join to get the final PRM_COST_GROUPS set
    getattr(d, prm_cost_group_sets).append("DELIVERABILITY_GROUPS",)
    getattr(d, prm_cost_group_prm_type)["DELIVERABILITY_GROUPS"] = \
        "energy_only_allowed"

    # This is the number of MW in the group that can be built without
    # incurring an additional cost for full deliverability
    m.deliverability_group_no_cost_deliverable_capacity_mw = Param(
        m.DELIVERABILITY_GROUPS, within=NonNegativeReals
    )
    m.deliverability_group_deliverability_cost_per_mw = Param(
        m.DELIVERABILITY_GROUPS, within=NonNegativeReals,
        default=0
    )

    # We'll also constrain how much energy-only capacity can be built
    # This is the maximum amount of energy-only capacity that can be built
    # in this group
    m.deliverability_group_energy_only_capacity_limit_mw = Param(
        m.DELIVERABILITY_GROUPS, within=NonNegativeReals
    )

    # Limit this to EOA_PRM_PROJECTS; if another project is
    # included, we need to throw an error
    m.DELIVERABILITY_GROUP_PROJECTS = Set(
        dimen=2,
        within=m.DELIVERABILITY_GROUPS * m.EOA_PRM_PROJECTS
    )

    m.PROJECTS_BY_DELIVERABILITY_GROUP = Set(
        m.DELIVERABILITY_GROUPS,
        within=m.EOA_PRM_PROJECTS,
        initialize=
        lambda mod, g: [p for (group, p) in
                        mod.DELIVERABILITY_GROUP_PROJECTS
                        if group == g]
    )

    def total_capacity_of_deliverability_group_rule(mod, g, p):
        """
        Total capacity of projects in each threshold group
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        return sum(mod.Capacity_MW[prj, p]
                   for prj
                   in mod.PROJECTS_BY_DELIVERABILITY_GROUP[g]
                   if (prj, p) in mod.EOA_PRM_PROJECT_OPERATIONAL_PERIODS
                   )

    m.Deliverability_Group_Total_Capacity_MW = Expression(
        m.DELIVERABILITY_GROUPS, m.PERIODS,
        rule=total_capacity_of_deliverability_group_rule
    )

    def deliverable_capacity_of_deliverability_group_rule(mod, g, p):
        """
        ELCC-eligible capacity of projects in each threshold group
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        return sum(mod.Deliverable_Capacity_MW[prj, p]
                   for prj
                   in mod.PROJECTS_BY_DELIVERABILITY_GROUP[g]
                   if (prj, p) in mod.EOA_PRM_PROJECT_OPERATIONAL_PERIODS
                   )

    m.Deliverability_Group_Deliverable_Capacity_MW = Expression(
        m.DELIVERABILITY_GROUPS, m.PERIODS,
        rule=deliverable_capacity_of_deliverability_group_rule
    )

    def energy_only_capacity_of_deliverability_group_rule(mod, g, p):
        """
        Energy-only capacity of projects in each threshold group
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        return sum(mod.Energy_Only_Capacity_MW[prj, p]
                   for prj
                   in mod.PROJECTS_BY_DELIVERABILITY_GROUP[g]
                   if (prj, p) in mod.PROJECT_OPERATIONAL_PERIODS
                   )

    m.Deliverability_Group_Energy_Only_Capacity_MW = Expression(
        m.DELIVERABILITY_GROUPS, m.PERIODS,
        rule=energy_only_capacity_of_deliverability_group_rule
    )

    # Calculate costs for ELCC-eligibility
    m.Deliverability_Group_Deliverable_Capacity_Cost = Var(
        m.DELIVERABILITY_GROUPS, m.PERIODS,
        within=NonNegativeReals
    )

    def deliverable_capacity_cost_constraint_rule(mod, g, p):
        """
        Costs incurred if total capacity built in threshold group is 
        higher than the threshold; otherwise, the cost can be set to 0 (and 
        in fact has to be set to 0 since Capacity_Threshold_Cost must be 
        non-negative)
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        if mod.deliverability_group_deliverability_cost_per_mw[g] == 0:
            return Constraint.Skip
        else:
            return mod.Deliverability_Group_Deliverable_Capacity_Cost[g, p] \
                >= \
                (mod.Deliverability_Group_Deliverable_Capacity_MW[g, p]
                 - mod.deliverability_group_no_cost_deliverable_capacity_mw[g]
                 ) \
                * mod.deliverability_group_deliverability_cost_per_mw[g]

    m.Deliverability_Group_Deliverable_Capacity_Cost_Constraint = Constraint(
        m.DELIVERABILITY_GROUPS, m.PERIODS,
        rule=deliverable_capacity_cost_constraint_rule
    )

    def energy_only_limit_rule(mod, g, p):
        """
        Maximum energy-only capacity that can be built
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        return mod.Deliverability_Group_Energy_Only_Capacity_MW[g, p] \
            <= mod.deliverability_group_energy_only_capacity_limit_mw[g]
    m.Deliverability_Group_Energy_Only_Capacity_Limit_Constraint = Constraint(
        m.DELIVERABILITY_GROUPS, m.PERIODS,
        rule=energy_only_limit_rule
    )


def elcc_eligible_capacity_rule(mod, proj, period):
    """
    
    :param mod: 
    :param proj:
    :param period:
    :return: 
    """
    return mod.Deliverable_Capacity_MW[proj, period]


def group_cost_rule(mod, group, period):
    """
    
    :param mod: 
    :param group: 
    :param period:
    :return: 
    """
    return mod.Deliverability_Group_Deliverable_Capacity_Cost[group, period]


def load_module_specific_data(
        m, data_portal, scenario_directory, subproblem, stage
):
    """
    Optionally load data for costs incurred only when a capacity threshold 
    is reached; if file is not found, sets in this modules will be empty and 
    params will have default values of 0
    :param m: 
    :param d: 
    :param data_portal: 
    :param scenario_directory: 
    :param subproblem:
    :param stage: 
    :return: 
    """

    group_threshold_costs_file = os.path.join(
        scenario_directory, subproblem, stage, "inputs",
        "deliverability_group_params.tab"
    )
    if os.path.exists(group_threshold_costs_file):
        data_portal.load(
            filename=group_threshold_costs_file,
            index=m.DELIVERABILITY_GROUPS,
            param=(m.deliverability_group_no_cost_deliverable_capacity_mw,
                   m.deliverability_group_deliverability_cost_per_mw,
                   m.deliverability_group_energy_only_capacity_limit_mw)
        )
    else:
        pass

    group_projects_file = os.path.join(
        scenario_directory, subproblem, stage, "inputs",
        "deliverability_group_projects.tab"
    )

    if os.path.exists(group_projects_file):
        data_portal.load(
            filename=group_projects_file,
            set=m.DELIVERABILITY_GROUP_PROJECTS
        )
    else:
        pass


def export_module_specific_results(m, d, scenario_directory, subproblem, stage,):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Energy-only vs deliverable capacity by project
    with open(os.path.join(
            scenario_directory, subproblem, stage, "results",
            "project_prm_energy_only_and_deliverable_capacity.csv"
    ), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "project", "period", "prm_zone",
            "total_capacity_mw",
            "deliverable_capacity_mw",
            "energy_only_capacity"])
        for (prj, p) in m.EOA_PRM_PROJECT_OPERATIONAL_PERIODS:
            writer.writerow([
                prj,
                p,
                m.prm_zone[prj],
                value(m.Capacity_MW[prj, p]),
                value(m.Deliverable_Capacity_MW[prj, p]),
                value(m.Energy_Only_Capacity_MW[prj, p])
            ])

    # Total capacity for all projects in group
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "deliverability_group_capacity_and_costs.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "deliverability_group", "period",
            "deliverability_group_no_cost_deliverable_capacity_mw",
            "deliverability_group_deliverability_cost_per_mw",
            "total_capacity_built_mw",
            "elcc_eligible_capacity_built_mw",
            "energy_only_capacity_built_mw",
            "deliverability_cost"])
        for g in m.DELIVERABILITY_GROUPS:
            for p in m.PERIODS:
                writer.writerow([
                    g,
                    p,
                    m.deliverability_group_no_cost_deliverable_capacity_mw[g],
                    m.deliverability_group_deliverability_cost_per_mw[g],
                    value(m.Deliverability_Group_Total_Capacity_MW[g, p]),
                    value(
                        m.Deliverability_Group_Deliverable_Capacity_MW[g, p]
                    ),
                    value(
                        m.Deliverability_Group_Energy_Only_Capacity_MW[g, p]
                    ),
                    value(
                        m.Deliverability_Group_Deliverable_Capacity_Cost[g, p]
                    )
                ])


def get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    if subscenarios.PRM_ENERGY_ONLY_SCENARIO_ID is None:
        group_threshold_costs = []
        project_deliverability_groups = []
    else:
        c1 = conn.cursor()
        # Threshold groups with threshold for ELCC eligibility, cost,
        # and energy-only limit
        group_threshold_costs = c1.execute(
            """SELECT deliverability_group, 
            deliverability_group_no_cost_deliverable_capacity_mw, 
            deliverability_group_deliverability_cost_per_mw,
            deliverability_group_energy_only_capacity_limit_mw
            FROM inputs_project_prm_energy_only
            WHERe prm_energy_only_scenario_id = {}""".format(
                subscenarios.PRM_ENERGY_ONLY_SCENARIO_ID
            )
        )

        c2 = conn.cursor()
        # Projects by group
        project_deliverability_groups = c2.execute(
            """SELECT deliverability_group, project 
            FROM 
            (SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}) as prj_tbl
            LEFT OUTER JOIN 
            (SELECT deliverability_group, project 
            FROM inputs_project_elcc_chars
            WHERE project_elcc_chars_scenario_id = {}
            ORDER BY deliverability_group, project) as grp_tbl
            USING (project)
            WHERE deliverability_group IS NOT NULL;""".format(
                subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
                subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
            )
        )

    return group_threshold_costs, project_deliverability_groups


def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass
    # Validation to be added
    # group_threshold_costs, project_deliverability_groups = \
    #   get_module_specific_inputs_from_database(
    #       subscenarios, subproblem, stage, conn)


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    deliverability_group_params.tab and
    deliverability_group_projects.tab files.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    group_threshold_costs, project_deliverability_groups = \
        get_module_specific_inputs_from_database(
            subscenarios, subproblem, stage, conn)

    if group_threshold_costs:
        with open(os.path.join(
                inputs_directory,
                "deliverability_group_params.tab"), "w", newline="") as \
                elcc_eligibility_thresholds_file:
            writer = csv.writer(elcc_eligibility_thresholds_file,
                                delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow([
                "deliverability_group",
                "deliverability_group_no_cost_deliverable_capacity_mw",
                "deliverability_group_deliverability_cost_per_mw",
                "deliverability_group_energy_only_capacity_limit_mw"
            ])

            # Input data
            for row in group_threshold_costs:
                writer.writerow(row)

        with open(os.path.join(
                inputs_directory,
                "deliverability_group_projects.tab"), "w"
        ) as group_projects_file:
            writer = csv.writer(group_projects_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(["deliverability_group", "project"])

            # Input data
            for row in project_deliverability_groups:
                writer.writerow(row)
    else:
        pass


def import_module_specific_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """

    # Energy-only and deliverable capacity by project
    if not quiet:
        print("project energy-only and deliverable capacities")
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_prm_deliverability",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(
            results_directory,
            "project_prm_energy_only_and_deliverable_capacity.csv"),
              "r") as deliv_file:
        reader = csv.reader(deliv_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            prm_zone = row[2]
            total_capacity_mw = row[3]
            deliverable_capacity = row[4]
            energy_only_capacity = row[5]
            
            results.append(
                (scenario_id, project, period, subproblem, stage,
                 prm_zone, total_capacity_mw,
                 deliverable_capacity, energy_only_capacity)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_prm_deliverability{}
        (scenario_id, project, period, subproblem_id, stage_id,
        prm_zone, capacity_mw, 
        deliverable_capacity_mw, energy_only_capacity_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_prm_deliverability
        (scenario_id, project, period, subproblem_id, stage_id,
        prm_zone, capacity_mw, 
        deliverable_capacity_mw, energy_only_capacity_mw)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        prm_zone, capacity_mw, 
        deliverable_capacity_mw, energy_only_capacity_mw
        FROM temp_results_project_prm_deliverability{}
         ORDER BY scenario_id, project, period, subproblem_id, stage_id;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)

    # Group capacity cost results
    if not quiet:
        print("project prm group deliverability costs")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_prm_deliverability_group_capacity_and_costs",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(
            results_directory, "deliverability_group_capacity_and_costs.csv"),
              "r") as capacity_costs_file:
        reader = csv.reader(capacity_costs_file)

        next(reader)  # skip header
        for row in reader:
            group = row[0]
            period = row[1]
            deliverability_group_no_cost_deliverable_capacity_mw = row[2]
            deliverability_group_deliverability_cost_per_mw = row[3]
            total_capacity_mw = row[4]
            deliverable_capacity = row[5]
            energy_only_capacity_mw = row[6]
            deliverable_capacity_cost = row[7]
            
            results.append(
                (scenario_id, group, period, subproblem, stage,
                 deliverability_group_no_cost_deliverable_capacity_mw,
                 deliverability_group_deliverability_cost_per_mw,
                 total_capacity_mw,
                 deliverable_capacity, energy_only_capacity_mw,
                 deliverable_capacity_cost)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_prm_deliverability_group_capacity_and_costs{}
        (scenario_id, deliverability_group, period, subproblem_id, 
        stage_id,
        deliverability_group_no_cost_deliverable_capacity_mw, 
        deliverability_group_deliverability_cost_per_mw,
        total_capacity_mw, 
        deliverable_capacity_mw, 
        energy_only_capacity_mw,
        deliverable_capacity_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO 
        results_project_prm_deliverability_group_capacity_and_costs
        (scenario_id, deliverability_group, period, subproblem_id, stage_id,
        deliverability_group_no_cost_deliverable_capacity_mw, 
        deliverability_group_deliverability_cost_per_mw,
        total_capacity_mw, 
        deliverable_capacity_mw, energy_only_capacity_mw,
        deliverable_capacity_cost)
        SELECT
        scenario_id, deliverability_group, period, subproblem_id, stage_id,
        deliverability_group_no_cost_deliverable_capacity_mw, 
        deliverability_group_deliverability_cost_per_mw,
        total_capacity_mw, 
        deliverable_capacity_mw, energy_only_capacity_mw,
        deliverable_capacity_cost
        FROM 
        temp_results_project_prm_deliverability_group_capacity_and_costs{}
        ORDER BY scenario_id, deliverability_group, period, subproblem_id, 
        stage_id;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


def process_module_specific_results(db, c, subscenarios, quiet):
    """

    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
        print("update energy-only capacities")

    # Figure out RPS zone for each project
    project_period_eocap = c.execute(
        """SELECT project, period, energy_only_capacity_mw
        FROM results_project_prm_deliverability
            WHERE scenario_id = {};""".format(
            subscenarios.SCENARIO_ID
        )
    ).fetchall()

    tables_to_update = [
        "results_project_elcc_simple",
        "results_project_elcc_surface"
    ]

    results = []
    for row in project_period_eocap:
        results.append(
            (row[2], subscenarios.SCENARIO_ID, row[0], row[1])
        )

    for table in tables_to_update:
        sql = """
            UPDATE {}
            SET energy_only_capacity_mw = ?
            WHERE scenario_id = ?
            AND project = ?
            AND period = ?;""".format(table)

        spin_on_database_lock(conn=db, cursor=c, sql=sql, data=results)

