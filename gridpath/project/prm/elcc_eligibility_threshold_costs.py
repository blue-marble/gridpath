#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Describe costs incurred when total capacity across groups of projects exceeds 
a pre-specified threshold
These currently include transmission/interconnection costs incurred after a 
certain amount of capacity from a group of projects is installed
"""

import csv
import os.path
from pyomo.environ import Set, Param, Var, Constraint, NonNegativeReals, \
    Expression, value


def add_model_components(m, d):
    """
    Sum up all operational costs and add to the objective function.
    :param m:
    :param d:
    :return:
    """

    m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS = Set()
    m.elcc_eligibility_threshold_mw = Param(
        m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS, within=NonNegativeReals
    )
    m.elcc_eligibility_threshold_cost_per_mw = Param(
        m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS, within=NonNegativeReals,
        default=0
    )
    m.energy_only_limit_mw = Param(
        m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS, within=NonNegativeReals
    )

    m.ELCC_ELIGIBILITY_THRESHOLD_GROUP_PROJECTS = Set(
        dimen=2, within=m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS * m.PROJECTS
    )

    # TODO: should these be within PRM_PROJECTS or all PROJECTS
    m.PROJECTS_BY_ELCC_ELIGIBILITY_THRESHOLD_GROUP = Set(
        m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS, within=m.PROJECTS,
        initialize=
        lambda mod, g: [p for (group, p) in
                        mod.ELCC_ELIGIBILITY_THRESHOLD_GROUP_PROJECTS
                        if group == g]
    )

    # Total capacity, ELCC-eligible capacity, and energy-only capacity
    # TODO: can we replace PROJECT_OPERATIONAL_PERIODS with
    # PRM_PROJECT_OPERATIONAL_PERIODS here?
    def total_capacity_of_threshold_group_rule(mod, g, p):
        """
        Total capacity of projects in each threshold group
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        return sum(mod.Capacity_MW[prj, p]
                   for prj
                   in mod.PROJECTS_BY_ELCC_ELIGIBILITY_THRESHOLD_GROUP[g]
                   if (prj, p) in mod.PROJECT_OPERATIONAL_PERIODS
                   )

    m.Threshold_Group_Total_Capacity_MW = Expression(
        m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS, m.PERIODS,
        rule=total_capacity_of_threshold_group_rule
    )

    def elcc_eligible_capacity_of_threshold_group_rule(mod, g, p):
        """
        ELCC-eligible capacity of projects in each threshold group
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        return sum(mod.ELCC_Eligible_Capacity_MW[prj, p]
                   for prj
                   in mod.PROJECTS_BY_ELCC_ELIGIBILITY_THRESHOLD_GROUP[g]
                   if (prj, p) in mod.PROJECT_OPERATIONAL_PERIODS
                   )

    m.Threshold_Group_ELCC_Eligible_Capacity_MW = Expression(
        m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS, m.PERIODS,
        rule=elcc_eligible_capacity_of_threshold_group_rule
    )

    def energy_only_capacity_of_threshold_group_rule(mod, g, p):
        """
        Energy-only capacity of projects in each threshold group
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        return sum(mod.Energy_Only_Capacity_MW[prj, p]
                   for prj
                   in mod.PROJECTS_BY_ELCC_ELIGIBILITY_THRESHOLD_GROUP[g]
                   if (prj, p) in mod.PROJECT_OPERATIONAL_PERIODS
                   )

    m.Threshold_Group_Energy_Only_Capacity_MW = Expression(
        m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS, m.PERIODS,
        rule=energy_only_capacity_of_threshold_group_rule
    )

    # Calculate costs for ELCC-eligibility
    m.ELCC_Eligible_Capacity_Threshold_Cost = Var(
        m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS, m.PERIODS,
        within=NonNegativeReals
    )

    def elcc_eligibility_threshold_cost_constraint_rule(mod, g, p):
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
        if mod.elcc_eligibility_threshold_cost_per_mw[g] == 0:
            return Constraint.Skip
        else:
            return mod.ELCC_Eligible_Capacity_Threshold_Cost[g, p] \
                >= \
                (mod.Threshold_Group_ELCC_Eligible_Capacity_MW[g, p]
                 - mod.elcc_eligibility_threshold_mw[g]) \
                * mod.elcc_eligibility_threshold_cost_per_mw[g]

    m.ELCC_Eligible_Capacity_Cost_Constraint = Constraint(
        m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS, m.PERIODS,
        rule=elcc_eligibility_threshold_cost_constraint_rule
    )

    def energy_only_limit_rule(mod, g, p):
        """
        Maximum energy-only capacity that can be built
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        return mod.Threshold_Group_Energy_Only_Capacity_MW[g, p] \
            <= mod.energy_only_limit_mw[g]
    m.Energy_Only_Capacity_Limit_Constraint = Constraint(
        m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS, m.PERIODS,
        rule=energy_only_limit_rule
    )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """
    Optionally load data for costs incurred only when a capacity threshold 
    is reached; if file is not found, sets in this modules will be empty and 
    params will have default values of 0
    :param m: 
    :param d: 
    :param data_portal: 
    :param scenario_directory: 
    :param horizon: 
    :param stage: 
    :return: 
    """
    group_projects_file = os.path.join(
        scenario_directory, horizon, stage, "inputs",
        "elcc_eligibility_threshold_group_projects.tab"
    )

    if os.path.exists(group_projects_file):
        data_portal.load(
            filename=group_projects_file,
            set=m.ELCC_ELIGIBILITY_THRESHOLD_GROUP_PROJECTS
        )
    else:
        pass

    group_threshold_costs_file = os.path.join(
        scenario_directory, horizon, stage, "inputs",
        "elcc_eligibility_thresholds.tab"
    )
    if os.path.exists(group_threshold_costs_file):
        data_portal.load(
            filename=group_threshold_costs_file,
            index=m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS,
            param=(m.elcc_eligibility_threshold_mw,
                   m.elcc_eligibility_threshold_cost_per_mw,
                   m.energy_only_limit_mw)
        )
    else:
        pass


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    # Total capacity for all projects
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "costs_elcc_eligibility_thresholds.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["elcc_eligibility_threshold_group", "period",
                         "elcc_eligibility_threshold_mw",
                         "elcc_eligibility_threshold_cost_per_mw",
                         "total_capacity_built_mw",
                         "elcc_eligible_capacity_built_mw",
                         "energy_only_capacity_built_mw",
                         "elcc_eligibility_threshold_cost"])
        for g in m.ELCC_ELIGIBILITY_THRESHOLD_GROUPS:
            for p in m.PERIODS:
                writer.writerow([
                    g,
                    p,
                    m.elcc_eligibility_threshold_mw[g],
                    m.elcc_eligibility_threshold_cost_per_mw[g],
                    value(m.Threshold_Group_Total_Capacity_MW[g, p]),
                    value(m.Threshold_Group_ELCC_Eligible_Capacity_MW[g, p]),
                    value(m.Threshold_Group_Energy_Only_Capacity_MW[g, p]),
                    value(m.ELCC_Eligible_Capacity_Threshold_Cost[g, p])
                ])


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    if subscenarios.ELCC_ELIGIBILITY_THRESHOLD_SCENARIO_ID is None:
        pass
    else:
        # Threshold groups with threshold for ELCC eligibility, cost, 
        # and energy-only limit
        group_threshold_costs = c.execute(
            """SELECT elcc_eligibility_threshold_group, 
            elcc_eligibility_threshold_mw, 
            elcc_eligibility_threshold_cost_per_mw,
            elcc_energy_only_limit_mw
            FROM inputs_project_elcc_eligibility_thresholds
            WHERe elcc_eligibility_threshold_scenario_id = {}""".format(
                subscenarios.ELCC_ELIGIBILITY_THRESHOLD_SCENARIO_ID
            )
        ).fetchall()

        with open(os.path.join(
                inputs_directory,
                "elcc_eligibility_thresholds.tab"), "w") as \
                elcc_eligibility_thresholds_file:
            writer = csv.writer(elcc_eligibility_thresholds_file,
                                delimiter="\t")

            # Write header
            writer.writerow(["elcc_eligibility_threshold_group",
                             "elcc_eligibility_threshold_mw",
                             "elcc_eligibility_threshold_cost_per_mw",
                             "energy_only_limit_mw"])

            # Input data
            for row in group_threshold_costs:
                writer.writerow(row)

        # Projects by group
        project_elcc_eligibility_threshold_cost_groups \
            = c.execute(
                """SELECT elcc_eligibility_threshold_group, 
                project
                FROM inputs_project_portfolios
                LEFT OUTER JOIN inputs_project_elcc_chars
                USING (project)
                WHERE project_elcc_chars_scenario_id = {}
                AND project_portfolio_scenario_id = {}
                AND elcc_eligibility_threshold_group 
                IS NOT NULL
                ORDER BY elcc_eligibility_threshold_group, 
                project""".format(
                    subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID,
                    subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
                )
            )

        with open(os.path.join(
                inputs_directory,
                "elcc_eligibility_threshold_group_projects.tab"), "w"
        ) as group_projects_file:
            writer = csv.writer(group_projects_file, delimiter="\t")

            # Write header
            writer.writerow(["elcc_eligibility_threshold_group", "project"])

            # Input data
            for row in \
                project_elcc_eligibility_threshold_cost_groups:
                    writer.writerow(row)


def import_results_into_database(scenario_id, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # Capacity cost results
    print("project elcc eligiblity capacity threshold costs")
    c.execute(
        """DELETE FROM results_project_costs_elcc_eligibility_thresholds
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS 
        temp_results_project_costs_elcc_eligibility_thresholds"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE 
        temp_results_project_costs_elcc_eligibility_thresholds"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        elcc_eligibility_threshold_group VARCHAR(64),
        period INTEGER,
        elcc_eligibility_threshold_mw FLOAT,
        elcc_eligibility_threshold_cost_per_mw FLOAT,
        total_capacity_mw FLOAT,
        elcc_eligible_capacity_mw FLOAT,
        energy_only_capacity_mw FLOAT,
        elcc_eligibility_threshold_cost FLOAT,
        PRIMARY KEY (scenario_id, elcc_eligibility_threshold_group, period)
        );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "costs_elcc_eligibility_thresholds.csv"), "r") as \
            capacity_costs_file:
        reader = csv.reader(capacity_costs_file)

        reader.next()  # skip header
        for row in reader:
            group = row[0]
            period = row[1]
            elcc_eligibility_threshold_mw = row[2]
            elcc_eligibility_threshold_cost_per_mw = row[3]
            total_capacity_mw = row[4]
            elcc_eligible_capacity_mw = row[5]
            energy_only_capacity_mw = row[6]
            elcc_eligibility_threshold_cost = row[7]

            c.execute(
                """INSERT INTO 
                temp_results_project_costs_elcc_eligibility_thresholds"""
                + str(scenario_id) + """
                (scenario_id, elcc_eligibility_threshold_group, period, 
                elcc_eligibility_threshold_mw, 
                elcc_eligibility_threshold_cost_per_mw,
                total_capacity_mw, 
                elcc_eligible_capacity_mw, 
                energy_only_capacity_mw,
                elcc_eligibility_threshold_cost)
                VALUES ({}, '{}', {}, {}, {}, {}, {}, {}, {});""".format(
                    scenario_id, group, period, elcc_eligibility_threshold_mw,
                    elcc_eligibility_threshold_cost_per_mw, total_capacity_mw,
                    elcc_eligible_capacity_mw, energy_only_capacity_mw,
                    elcc_eligibility_threshold_cost
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_costs_elcc_eligibility_thresholds
        (scenario_id, elcc_eligibility_threshold_group, period, 
        elcc_eligibility_threshold_mw, elcc_eligibility_threshold_cost_per_mw,
        total_capacity_mw, 
        elcc_eligible_capacity_mw, energy_only_capacity_mw,
        elcc_eligibility_threshold_cost)
        SELECT
        scenario_id, elcc_eligibility_threshold_group, period, 
        elcc_eligibility_threshold_mw, elcc_eligibility_threshold_cost_per_mw,
        total_capacity_mw, 
        elcc_eligible_capacity_mw, energy_only_capacity_mw,
        elcc_eligibility_threshold_cost
        FROM temp_results_project_costs_elcc_eligibility_thresholds"""
        + str(scenario_id) + """
        ORDER BY scenario_id, elcc_eligibility_threshold_group, period;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_costs_elcc_eligibility_thresholds"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
