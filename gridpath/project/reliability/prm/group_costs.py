# Copyright 2016-2020 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import csv
import os.path
from pyomo.environ import Set, Var, Expression, Param, Constraint, NonNegativeReals, \
    value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """
    # Costs for having fully deliverable capacity by project group
    # We'll need to figure out how much capacity is built in groups of
    # projects, not by individual project
    m.DELIVERABILITY_GROUPS = Set()

    # This is the number of MW in the group that can be built without
    # incurring an additional cost for full deliverability
    m.deliverability_group_no_cost_deliverable_capacity_mw = Param(
        m.DELIVERABILITY_GROUPS, within=NonNegativeReals
    )
    m.deliverability_group_deliverability_cost_per_mw = Param(
        m.DELIVERABILITY_GROUPS, within=NonNegativeReals, default=0
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
        dimen=2, within=m.DELIVERABILITY_GROUPS * m.EOA_PRM_PROJECTS
    )

    m.PROJECTS_BY_DELIVERABILITY_GROUP = Set(
        m.DELIVERABILITY_GROUPS,
        within=m.EOA_PRM_PROJECTS,
        initialize=lambda mod, g: [
            p for (group, p) in mod.DELIVERABILITY_GROUP_PROJECTS if group == g
        ],
    )

    def total_capacity_of_deliverability_group_rule(mod, g, p):
        """
        Total capacity of projects in each threshold group
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return sum(
            mod.Capacity_MW[prj, p]
            for prj in mod.PROJECTS_BY_DELIVERABILITY_GROUP[g]
            if (prj, p) in mod.EOA_PRM_PRJ_OPR_PRDS
        )

    m.Deliverability_Group_Total_Capacity_MW = Expression(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        rule=total_capacity_of_deliverability_group_rule,
    )

    def deliverable_capacity_of_deliverability_group_rule(mod, g, p):
        """
        ELCC-eligible capacity of projects in each threshold group
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return sum(
            mod.Deliverable_Capacity_MW[prj, p]
            for prj in mod.PROJECTS_BY_DELIVERABILITY_GROUP[g]
            if (prj, p) in mod.EOA_PRM_PRJ_OPR_PRDS
        )

    m.Deliverability_Group_Deliverable_Capacity_MW = Expression(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        rule=deliverable_capacity_of_deliverability_group_rule,
    )

    def energy_only_capacity_of_deliverability_group_rule(mod, g, p):
        """
        Energy-only capacity of projects in each threshold group
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return sum(
            mod.Energy_Only_Capacity_MW[prj, p]
            for prj in mod.PROJECTS_BY_DELIVERABILITY_GROUP[g]
            if (prj, p) in mod.PRJ_OPR_PRDS
        )

    m.Deliverability_Group_Energy_Only_Capacity_MW = Expression(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        rule=energy_only_capacity_of_deliverability_group_rule,
    )

    # Calculate costs for ELCC-eligibility
    m.Deliverability_Group_Deliverable_Capacity_Cost = Var(
        m.DELIVERABILITY_GROUPS, m.PERIODS, within=NonNegativeReals
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
            return (
                mod.Deliverability_Group_Deliverable_Capacity_Cost[g, p]
                >= (
                    mod.Deliverability_Group_Deliverable_Capacity_MW[g, p]
                    - mod.deliverability_group_no_cost_deliverable_capacity_mw[g]
                )
                * mod.deliverability_group_deliverability_cost_per_mw[g]
            )

    m.Deliverability_Group_Deliverable_Capacity_Cost_Constraint = Constraint(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        rule=deliverable_capacity_cost_constraint_rule,
    )

    def energy_only_limit_rule(mod, g, p):
        """
        Maximum energy-only capacity that can be built
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return (
            mod.Deliverability_Group_Energy_Only_Capacity_MW[g, p]
            <= mod.deliverability_group_energy_only_capacity_limit_mw[g]
        )

    m.Deliverability_Group_Energy_Only_Capacity_Limit_Constraint = Constraint(
        m.DELIVERABILITY_GROUPS, m.PERIODS, rule=energy_only_limit_rule
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
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
        scenario_directory,
        subproblem,
        stage,
        "inputs",
        "deliverability_group_params.tab",
    )
    if os.path.exists(group_threshold_costs_file):
        data_portal.load(
            filename=group_threshold_costs_file,
            index=m.DELIVERABILITY_GROUPS,
            param=(
                m.deliverability_group_no_cost_deliverable_capacity_mw,
                m.deliverability_group_deliverability_cost_per_mw,
                m.deliverability_group_energy_only_capacity_limit_mw,
            ),
        )
    else:
        pass

    group_projects_file = os.path.join(
        scenario_directory,
        subproblem,
        stage,
        "inputs",
        "deliverability_group_projects.tab",
    )

    if os.path.exists(group_projects_file):
        data_portal.load(
            filename=group_projects_file, set=m.DELIVERABILITY_GROUP_PROJECTS
        )
    else:
        pass


def export_results(
    m,
    d,
    scenario_directory,
    subproblem,
    stage,
):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Total capacity for all projects in group
    with open(
            os.path.join(
                scenario_directory,
                str(subproblem),
                str(stage),
                "results",
                "deliverability_group_capacity_and_costs.csv",
            ),
            "w",
            newline="",
    ) as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "deliverability_group",
                "period",
                "deliverability_group_no_cost_deliverable_capacity_mw",
                "deliverability_group_deliverability_cost_per_mw",
                "total_capacity_built_mw",
                "elcc_eligible_capacity_built_mw",
                "energy_only_capacity_built_mw",
                "deliverability_cost",
            ]
        )
        for g in m.DELIVERABILITY_GROUPS:
            for p in m.PERIODS:
                writer.writerow(
                    [
                        g,
                        p,
                        m.deliverability_group_no_cost_deliverable_capacity_mw[g],
                        m.deliverability_group_deliverability_cost_per_mw[g],
                        value(m.Deliverability_Group_Total_Capacity_MW[g, p]),
                        value(m.Deliverability_Group_Deliverable_Capacity_MW[g, p]),
                        value(m.Deliverability_Group_Energy_Only_Capacity_MW[g, p]),
                        value(m.Deliverability_Group_Deliverable_Capacity_Cost[g, p]),
                    ]
                )

def get_model_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    if subscenarios.PRM_ENERGY_ONLY_SCENARIO_ID is None:
        # If we call this module, it's because we specified the feature, so we can
        # raise an error if an energy_only_scenario_id is not specified.
        raise ValueError("You must specify a energy_only_scenario_id for this "
                         "scenario to use the 'energy only' feature.")
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
                subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID,
            )
        )

    return group_threshold_costs, project_deliverability_groups


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
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
    #   get_model_inputs_from_database(
    #       scenario_id, subscenarios, subproblem, stage, conn)


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    deliverability_group_params.tab and
    deliverability_group_projects.tab files.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    (
        group_threshold_costs,
        project_deliverability_groups,
    ) = get_model_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    if group_threshold_costs:
        with open(
            os.path.join(
                scenario_directory,
                subproblem,
                stage,
                "inputs",
                "deliverability_group_params.tab",
            ),
            "w",
            newline="",
        ) as elcc_eligibility_thresholds_file:
            writer = csv.writer(
                elcc_eligibility_thresholds_file, delimiter="\t", lineterminator="\n"
            )

            # Write header
            writer.writerow(
                [
                    "deliverability_group",
                    "deliverability_group_no_cost_deliverable_capacity_mw",
                    "deliverability_group_deliverability_cost_per_mw",
                    "deliverability_group_energy_only_capacity_limit_mw",
                ]
            )

            # Input data
            for row in group_threshold_costs:
                writer.writerow(row)

        with open(
            os.path.join(
                scenario_directory,
                subproblem,
                stage,
                "inputs",
                "deliverability_group_projects.tab",
            ),
            "w",
        ) as group_projects_file:
            writer = csv.writer(
                group_projects_file, delimiter="\t", lineterminator="\n"
            )

            # Write header
            writer.writerow(["deliverability_group", "project"])

            # Input data
            for row in project_deliverability_groups:
                writer.writerow(row)
    else:
        pass


def import_results_into_database(
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

    # Group capacity cost results
    if not quiet:
        print("project prm group deliverability costs")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_project_prm_deliverability_group_capacity_and_costs",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
            os.path.join(results_directory,
                         "deliverability_group_capacity_and_costs.csv"),
            "r",
    ) as capacity_costs_file:
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
                (
                    scenario_id,
                    group,
                    period,
                    subproblem,
                    stage,
                    deliverability_group_no_cost_deliverable_capacity_mw,
                    deliverability_group_deliverability_cost_per_mw,
                    total_capacity_mw,
                    deliverable_capacity,
                    energy_only_capacity_mw,
                    deliverable_capacity_cost,
                )
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
            """.format(
        scenario_id
    )
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
            """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)

