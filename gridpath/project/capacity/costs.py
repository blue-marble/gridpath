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

"""
The **gridpath.project.capacity.costs** module is a project-level
module that adds to the formulation components that describe the
capacity-related costs of projects (e.g. investment capital costs and fixed
O&M costs).
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import (
    get_required_subtype_modules_from_projects_file,
    join_sets,
)
from gridpath.project.capacity.common_functions import (
    load_project_capacity_type_modules,
)
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.dynamic_components import capacity_type_financial_period_sets
import gridpath.project.capacity.capacity_types as cap_type_init


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Capacity_Cost_in_Period`                                       |
    | | *Defined Over*: :code:`PRJ_OPR_PRDS`                                  |
    |                                                                         |
    | This expression describe each project's capacity-related costs for each |
    | operational period, based on its capacity_type. For the purpose, call   |
    | the *capacity_cost_rule* method from the respective capacity-type       |
    | module. If the subproblem is less than a full year (e.g. in production- |
    | cost mode with 365 daily subproblems), the costs are scaled down        |
    | proportionally.                                                         |
    +-------------------------------------------------------------------------+

    """
    
    # Dynamic Inputs
    ###########################################################################

    required_capacity_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        which_type="capacity_type",
    )

    imported_capacity_modules = load_project_capacity_type_modules(
        required_capacity_modules
    )
    
    # Sets
    ###########################################################################

    m.PRJ_FIN_PRDS = Set(
        dimen=2,
        within=m.PROJECTS * m.PERIODS,
        initialize=lambda mod: join_sets(
            mod,
            getattr(d, capacity_type_financial_period_sets),
        ),
    )  # assumes capacity types model components are already added!

    # Expressions
    ###########################################################################

    def capacity_cost_rule(mod, prj, prd):
        """
        Get capacity capital cost for each generator's respective capacity module.
        These are applied in every financial period.

        Note that capacity cost inputs and calculations in the modules are on
        a period basis. Therefore, if the period spans subproblems (the main
        example of this would be specified capacity in, say, a production-cost
        scenario with multiple subproblems), we adjust the capacity costs down
        accordingly.
        """
        cap_type = mod.capacity_type[prj]
        if hasattr(imported_capacity_modules[cap_type], "capacity_cost_rule"):
            capacity_cost = imported_capacity_modules[cap_type].capacity_cost_rule(
                mod, prj, prd
            )
        else:
            capacity_cost = cap_type_init.capacity_cost_rule(mod, prj, prd)

        return (
            capacity_cost
            * mod.hours_in_subproblem_period[prd]
            / mod.hours_in_period_timepoints[prd]
        )

    m.Capacity_Cost_in_Period = Expression(m.PRJ_FIN_PRDS, rule=capacity_cost_rule)


    def fixed_cost_rule(mod, prj, prd):
        """
        Get fixed cost for each generator's respective capacity module. These are
        applied in every operational period.

        Note that fixed cost inputs and calculations in the modules are on
        a period basis. Therefore, if the period spans subproblems (the main
        example of this would be specified capacity in, say, a production-cost
        scenario with multiple subproblems), we adjust the fixed costs down
        accordingly.
        """
        cap_type = mod.capacity_type[prj]
        if hasattr(imported_capacity_modules[cap_type], "fixed_cost_rule"):
            fixed_cost = imported_capacity_modules[cap_type].fixed_cost_rule(
                mod, prj, prd
            )
        else:
            fixed_cost = cap_type_init.fixed_cost_rule(mod, prj, prd)

        return (
            fixed_cost
            * mod.hours_in_subproblem_period[prd]
            / mod.hours_in_period_timepoints[prd]
        )

    # TODO: make sure this gets added to the objective function downstream
    m.Fixed_Cost_in_Period = Expression(m.PRJ_OPR_PRDS, rule=fixed_cost_rule)


# Input-Output
###############################################################################

def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "costs_capacity_all_projects.csv",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "project",
                "period",
                "hours_in_period_timepoints",
                "hours_in_subproblem_period",
                "technology",
                "load_zone",
                "capacity_cost",
            ]
        )
        for (prj, p) in m.PRJ_OPR_PRDS:
            writer.writerow(
                [
                    prj,
                    p,
                    m.hours_in_period_timepoints[p],
                    m.hours_in_subproblem_period[p],
                    m.technology[prj],
                    m.load_zone[prj],
                    value(m.Capacity_Cost_in_Period[prj, p]),
                ]
            )


# Database
###############################################################################


def import_results_into_database(
    scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    # Capacity cost results
    if not quiet:
        print("project capacity costs")
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_project_costs_capacity",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "costs_capacity_all_projects.csv"), "r"
    ) as capacity_costs_file:
        reader = csv.reader(capacity_costs_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            hours_in_period_timepoints = row[2]
            hours_in_subproblem_period = row[3]
            technology = row[4]
            load_zone = row[5]
            capacity_cost = row[6]

            results.append(
                (
                    scenario_id,
                    project,
                    period,
                    subproblem,
                    stage,
                    hours_in_period_timepoints,
                    hours_in_subproblem_period,
                    technology,
                    load_zone,
                    capacity_cost,
                )
            )

    insert_temp_sql = """
        INSERT INTO temp_results_project_costs_capacity{}
        (scenario_id, project, period, subproblem_id, stage_id,
        hours_in_period_timepoints, hours_in_subproblem_period, technology, load_zone, 
        capacity_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_costs_capacity
        (scenario_id, project, period, subproblem_id, stage_id,
        hours_in_period_timepoints, hours_in_subproblem_period, technology, load_zone, 
        capacity_cost)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        hours_in_period_timepoints, hours_in_subproblem_period, technology, load_zone, 
        capacity_cost
        FROM temp_results_project_costs_capacity{}
        ORDER BY scenario_id, project, period, subproblem_id, 
        stage_id;""".format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)

    # Update the capacity cost removing the fraction attributable to the
    # spinup and lookahead hours
    update_sql = """
        UPDATE results_project_costs_capacity
        SET capacity_cost_wo_spinup_or_lookahead = capacity_cost * (
            SELECT fraction_of_hours_in_subproblem
            FROM spinup_or_lookahead_ratios
            WHERE spinup_or_lookahead = 0
            AND results_project_costs_capacity.scenario_id = 
            spinup_or_lookahead_ratios.scenario_id
            AND results_project_costs_capacity.subproblem_id = 
            spinup_or_lookahead_ratios.subproblem_id
            AND results_project_costs_capacity.stage_id = 
            spinup_or_lookahead_ratios.stage_id
            AND results_project_costs_capacity.period = 
            spinup_or_lookahead_ratios.period
        )
        ;
    """

    spin_on_database_lock(conn=db, cursor=c, sql=update_sql, data=(), many=False)


def process_results(db, c, scenario_id, subscenarios, quiet):
    """
    Aggregate capacity costs by load zone, and break out into
    spinup_or_lookahead.
    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
        print("aggregate capacity costs by load zone")

    # Delete old resulst
    del_sql = """
        DELETE FROM results_project_costs_capacity_agg 
        WHERE scenario_id = ?
        """
    spin_on_database_lock(
        conn=db, cursor=c, sql=del_sql, data=(scenario_id,), many=False
    )

    # Insert new results
    agg_sql = """
        INSERT INTO results_project_costs_capacity_agg
        (scenario_id, load_zone, period, subproblem_id, stage_id,
        spinup_or_lookahead, fraction_of_hours_in_subproblem, capacity_cost)
        
        SELECT scenario_id, load_zone, period, subproblem_id, stage_id,
        spinup_or_lookahead, fraction_of_hours_in_subproblem,
        (capacity_cost * fraction_of_hours_in_subproblem) AS capacity_cost
        FROM spinup_or_lookahead_ratios
        
        -- Add load_zones
        LEFT JOIN
        (SELECT scenario_id, load_zone
        FROM inputs_geography_load_zones
        INNER JOIN
        (SELECT scenario_id, load_zone_scenario_id FROM scenarios
        WHERE scenario_id = ?) AS scen_tbl
        USING (load_zone_scenario_id)
        ) AS lz_tbl
        USING (scenario_id)

        -- Now that we have all scenario_id, subproblem_id, stage_id, period, 
        -- load_zone, and spinup_or_lookahead combinations add the capacity 
        -- costs which will be derated by the fraction_of_hours_in_subproblem
        INNER JOIN
        (SELECT scenario_id, subproblem_id, stage_id, period, load_zone,
        SUM(capacity_cost) AS capacity_cost
        FROM results_project_costs_capacity
        GROUP BY scenario_id, subproblem_id, stage_id, period, load_zone
        ) AS cap_table
        USING (scenario_id, subproblem_id, stage_id, period, load_zone)
        ;"""

    spin_on_database_lock(
        conn=db, cursor=c, sql=agg_sql, data=(scenario_id,), many=False
    )
