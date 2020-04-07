#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.project.operations.costs** module is a project-level
module that adds to the formulation components that describe the
operations-related costs of projects (e.g. variable O&M costs, fuel costs,
startup and shutdown costs).
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Var, Expression, Constraint, NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.dynamic_components import required_operational_modules
from gridpath.auxiliary.auxiliary import load_operational_type_modules,\
    setup_results_import
from gridpath.project.common_functions import \
    check_if_linear_horizon_first_timepoint


def add_model_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Variable_OM_Cost`                                              |
    | | *Defined over*: :code:`PRJ_OPR_TMPS`                                  |
    |                                                                         |
    | This expression defines the variable cost of a project in all of its    |
    | operational timepoints, and is simply equal to the project's power      |
    | output times its variable cost.                                         |
    +-------------------------------------------------------------------------+
    | | :code:`Fuel_Cost`                                                     |
    | | *Defined over*: :code:`FUEL_PRJ_OPR_TMPS`                             |
    |                                                                         |
    | This expression defines the fuel cost of a project in all of its        |
    | operational timepoints, and is simply equal to the project's fuel burn  |
    | in that timepoint times the fuel price (fuel price is currently defined |
    | by period and month). The fuel burn expression is formulated in the     |
    | gridpath.project.operations.fuel_burn module by calling the *fuel_burn* |
    | method of a project's *operational_type* module.                        |
    +-------------------------------------------------------------------------+
    | | :code:`Startup_Cost`                                                  |
    | | *Defined over*: :code:`PRJ_OPR_TMPS`                                  |
    |                                                                         |
    | This expression defines the startup cost of a project in all of its     |
    | operational timepoints. We obtain the expression by calling the         |
    | *startup_cost_rule* method of a project's *operational_type* module.    |
    +-------------------------------------------------------------------------+
    | | :code:`Shutdown_Cost`                                                 |
    | | *Defined over*: :code:`PRJ_OPR_TMPS`                                  |
    |                                                                         |
    | This expression defines the shutdown cost of a project in all of its    |
    | operational timepoints. We obtain the expression by calling the         |
    | *shutdown_cost_rule* method of a project's *operational_type* module.   |
    +-------------------------------------------------------------------------+

    """

    # Dynamic Components
    ###########################################################################

    imported_operational_modules = load_operational_type_modules(
        getattr(d, required_operational_modules)
    )

    # Expressions
    ###########################################################################

    def fuel_cost_rule(mod, g, tmp):
        """
        **Expression Name**: Fuel_Cost
        **Defined Over**: FUEL_PRJ_OPR_TMPS
        """
        return mod.Total_Fuel_Burn_MMBtu[g, tmp] * mod.fuel_price_per_mmbtu[
            mod.fuel[g], mod.period[tmp], mod.month[tmp]]

    m.Fuel_Cost = Expression(
        m.FUEL_PRJ_OPR_TMPS,
        rule=fuel_cost_rule
    )

    def variable_om_cost_rule(mod, g, tmp):
        """
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type].\
            variable_om_cost_rule(mod, g, tmp)

    m.Variable_OM_Cost = Expression(
        m.PRJ_OPR_TMPS,
        rule=variable_om_cost_rule
    )

    def startup_cost_rule(mod, g, tmp):
        """
        Startup costs are defined for some operational types while they are
        zero for others. Get the appropriate expression for each generator
        based on its operational type.
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type].\
            startup_cost_rule(mod, g, tmp)

    m.Startup_Cost = Expression(
        m.PRJ_OPR_TMPS,
        rule=startup_cost_rule
    )

    def shutdown_cost_rule(mod, g, tmp):
        """
        Shutdown costs are defined for some operational types while they are
        zero for others. Get the appropriate expression for each generator
        based on its operational type.
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type].\
            shutdown_cost_rule(mod, g, tmp)

    m.Shutdown_Cost = Expression(
        m.PRJ_OPR_TMPS,
        rule=shutdown_cost_rule
    )


# Input-Output
###############################################################################

def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export operations results. Note: fuel cost includes startup fuel as well
    if applicable, in which case this is startup fuel cost is additional to
    the startup costs reported here.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "costs_operations.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "horizon", "timepoint", "timepoint_weight",
             "number_of_hours_in_timepoint", "load_zone", "technology",
             "variable_om_cost", "fuel_cost", "startup_cost", "shutdown_cost"]
        )
        for (p, tmp) in m.PRJ_OPR_TMPS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type_project[p]],
                tmp,
                m.tmp_weight[tmp],
                m.hrs_in_tmp[tmp],
                m.load_zone[p],
                m.technology[p],
                value(m.Variable_OM_Cost[p, tmp]),
                value(m.Fuel_Cost[p, tmp]) if p in m.FUEL_PRJS else 0,
                value(m.Startup_Cost[p, tmp]),
                value(m.Shutdown_Cost[p, tmp])
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
    if not quiet:
        print("project costs operations")

    # costs_operations.csv
    # Delete prior results and create temporary import table for ordering
    setup_results_import(conn=db, cursor=c,
                         table="results_project_costs_operations",
                         scenario_id=scenario_id, subproblem=subproblem,
                         stage=stage)

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory, "costs_operations.csv"),
              "r") as dispatch_file:
        reader = csv.reader(dispatch_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            timepoint_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[6]
            technology = row[7]
            variable_om_cost = row[8]
            fuel_cost = row[9]
            startup_cost = row[10]
            shutdown_cost = row[11]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 horizon, timepoint, timepoint_weight,
                 number_of_hours_in_timepoint, load_zone, technology,
                 variable_om_cost, fuel_cost, startup_cost, shutdown_cost)
            )

    insert_temp_sql = """
        INSERT INTO
        temp_results_project_costs_operations{}
        (scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight,
        number_of_hours_in_timepoint, load_zone, technology, 
        variable_om_cost, fuel_cost, startup_cost, shutdown_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""".format(
        scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO 
        results_project_costs_operations
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint, load_zone, technology, 
        variable_om_cost, fuel_cost, startup_cost, shutdown_cost)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint, load_zone, technology, 
        variable_om_cost, fuel_cost, startup_cost, shutdown_cost
        FROM temp_results_project_costs_operations{}
        ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
