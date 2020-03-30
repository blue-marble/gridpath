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
from gridpath.auxiliary.dynamic_components import required_capacity_modules
from gridpath.auxiliary.auxiliary import \
    load_gen_storage_capacity_type_modules, setup_results_import


def add_model_components(m, d):
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
    | module.                                                                 |
    +-------------------------------------------------------------------------+

    """

    # Dynamic Components
    ###########################################################################

    imported_capacity_modules = load_gen_storage_capacity_type_modules(
        getattr(d, required_capacity_modules)
    )

    # Expressions
    ###########################################################################

    def capacity_cost_rule(mod, g, p):
        """
        Get capacity cost for each generator's respective capacity module.
        """
        return imported_capacity_modules[mod.capacity_type[g]].\
            capacity_cost_rule(mod, g, p)

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
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "costs_capacity_all_projects.csv"),
              "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "technology", "load_zone",
             "annualized_capacity_cost"]
        )
        for (prj, p) in m.PRJ_OPR_PRDS:
            writer.writerow([
                prj,
                p,
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
            technology = row[2]
            load_zone = row[3]
            annualized_capacity_cost = row[4]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 technology, load_zone, annualized_capacity_cost)
            )

    insert_temp_sql = """
        INSERT INTO temp_results_project_costs_capacity{}
        (scenario_id, project, period, subproblem_id, stage_id,
        technology, load_zone, annualized_capacity_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_costs_capacity
        (scenario_id, project, period, subproblem_id, stage_id,
        technology, load_zone, annualized_capacity_cost)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        technology, load_zone, annualized_capacity_cost
        FROM temp_results_project_costs_capacity{}
        ORDER BY scenario_id, project, period, subproblem_id, 
        stage_id;""".format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
