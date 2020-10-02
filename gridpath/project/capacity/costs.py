#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

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
from pyomo.environ import Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import get_required_subtype_modules, \
    load_gen_storage_capacity_type_modules, setup_results_import


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

    required_capacity_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, which_type="capacity_type"
    )

    imported_capacity_modules = load_gen_storage_capacity_type_modules(
        required_capacity_modules
    )

    # Expressions
    ###########################################################################

    def capacity_cost_rule(mod, g, p):
        """
        Get capacity cost for each generator's respective capacity module.

        Note that capacity cost inputs and calculations in the modules are on
        an annual basis. Therefore, if the subproblem is less than a year we
        adjust the costs down.
        """
        return imported_capacity_modules[mod.capacity_type[g]].\
            capacity_cost_rule(mod, g, p) \
            * mod.hours_in_subproblem_period[p] \
            / mod.hours_in_full_period[p]

    # TODO: right now hours in spinup and lookahead tmps are not included in
    #  the "hours_in_subproblem". If that is not okay (not sure why), we could
    #  move the adjustment to a post-processing step (same for tx cap costs)

    m.Capacity_Cost_in_Period = Expression(
        m.PRJ_OPR_PRDS,
        rule=capacity_cost_rule
    )


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

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "costs_capacity_all_projects.csv"),
              "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "hours_in_full_period",
             "hours_in_subproblem_period", "technology", "load_zone",
             "capacity_cost"]
        )
        for (prj, p) in m.PRJ_OPR_PRDS:
            writer.writerow([
                prj,
                p,
                m.hours_in_full_period[p],
                m.hours_in_subproblem_period[p],
                m.technology[prj],
                m.load_zone[prj],
                value(m.Capacity_Cost_in_Period[prj, p])
            ])


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
    setup_results_import(conn=db, cursor=c,
                         table="results_project_costs_capacity",
                         scenario_id=scenario_id, subproblem=subproblem,
                         stage=stage)

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "costs_capacity_all_projects.csv"),
              "r") as capacity_costs_file:
        reader = csv.reader(capacity_costs_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            hours_in_full_period = row[2]
            hours_in_subproblem_period = row[3]
            technology = row[4]
            load_zone = row[5]
            capacity_cost = row[6]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 hours_in_full_period, hours_in_subproblem_period,
                 technology, load_zone, capacity_cost)
            )

    insert_temp_sql = """
        INSERT INTO temp_results_project_costs_capacity{}
        (scenario_id, project, period, subproblem_id, stage_id,
        hours_in_full_period, hours_in_subproblem_period, technology, load_zone, 
        capacity_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_costs_capacity
        (scenario_id, project, period, subproblem_id, stage_id,
        hours_in_full_period, hours_in_subproblem_period, technology, load_zone, 
        capacity_cost)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        hours_in_full_period, hours_in_subproblem_period, technology, load_zone, 
        capacity_cost
        FROM temp_results_project_costs_capacity{}
        ORDER BY scenario_id, project, period, subproblem_id, 
        stage_id;""".format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


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
    spin_on_database_lock(conn=db, cursor=c, sql=del_sql,
                          data=(scenario_id,),
                          many=False)

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

    spin_on_database_lock(conn=db, cursor=c, sql=agg_sql,
                          data=(scenario_id,),
                          many=False)

