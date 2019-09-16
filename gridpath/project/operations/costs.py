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

from gridpath.auxiliary.dynamic_components import required_operational_modules
from gridpath.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    Three types of project costs are included here: variable O&M cost,
    fuel cost, and startup and shutdown costs.

    The Pyomo expression *Variable_OM_Cost*\ :sub:`r,tmp`\ (:math:`(r,
    tmp)\in RT`) defines the variable cost of a project in all of its
    operational timepoints, and is simply equal to the project's power
    output times its variable cost.

    The Pyomo expression *Fuel_Cost*\ :sub:`r,tmp`\ (:math:`(r,
    tmp)\in RT`) defines the fuel cost of a project in all of its
    operational timepoints, and is simply equal to the project's fuel burn
    in that timepoint times the fuel price (fuel price is currently defined
    by period and month). The fuel burn expression is formulated in the
    gridpath.project.operations.fuel_burn module by calling the *fuel_burn*
    method of a project's *capacity_type* module.

    The variables *Startup_Cost*\ :sub:`r,tmp`\ and
    *Shutdown_Cost*\ :sub:`r,tmp`\ (:math:`(r, tmp)\in RT`) define the
    startup and shutdown cost of a project in all of its operational
    timepoints, and are formulated by first calling the
    *startup_shutdown_rule* method of a project's *capacity_type* module,
    which calculates the number of units that were started up or shut down,
    i.e. the *Startup_Shutdown_Expressiont*\ :sub:`r,tmp`\.
    These variables are defined to be non-negative and further constrained
    as follows:

    .. todo: figure out how to deal with the fuel/startup/shutdown project
        subsets and update indices and docs in general accordingly

    :math:`Startup\_Cost_{r, tmp} \geq Startup\_Shutdown\_Expression_{r,
    tmp} \\times startup\_cost\_per\_mw_r`

    :math:`Shutdown\_Cost_{r, tmp} \geq -Startup\_Shutdown\_Expression_{r,
    tmp} \\times startup\_cost\_per\_mw_r`


    """
    def variable_om_cost_rule(m, g, tmp):
        """

        :param m:
        :param g:
        :param tmp:
        :return:
        """
        return m.Power_Provision_MW[g, tmp] * m.variable_om_cost_per_mwh[g]

    m.Variable_OM_Cost = Expression(m.PROJECT_OPERATIONAL_TIMEPOINTS,
                                    rule=variable_om_cost_rule)

    # From here, the operational modules determine how the model components are
    # formulated
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # ### Fuel cost ### #
    def fuel_cost_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Total_Fuel_Burn_MMBtu[g, tmp] * \
            mod.fuel_price_per_mmbtu[
                mod.fuel[g], mod.period[tmp], mod.month[tmp]]

    m.Fuel_Cost = Expression(m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS,
                             rule=fuel_cost_rule)

    # ### Startup and shutdown costs ### #
    def startup_shutdown_rule(mod, g, tmp):
        """
        Track units started up from timepoint to timepoint; get appropriate
        expression from the generator's operational module.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            startup_shutdown_rule(mod, g, tmp)

    m.Startup_Shutdown_Expression = Expression(
        m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS
        | m.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=startup_shutdown_rule)

    m.Startup_Cost = Var(m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS,
                         within=NonNegativeReals)
    m.Shutdown_Cost = Var(m.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS,
                          within=NonNegativeReals)

    def startup_cost_rule(mod, g, tmp):
        """
        Startup expression is positive when more units are on in the current
        timepoint that were on in the previous timepoint. Startup_Cost is
        defined to be non-negative, so if Startup_Expression is 0 or negative
        (i.e. no units started or units shut down since the previous timepoint),
        Startup_Cost will be 0.
        If horizon is circular, the last timepoint of the horizon is the
        previous_timepoint for the first timepoint if the horizon;
        if the horizon is linear, no previous_timepoint is defined for the first
        timepoint of the horizon, so skip constraint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp, mod.balancing_type[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] == "linear":
            return Constraint.Skip
        else:
            return mod.Startup_Cost[g, tmp] \
                   >= mod.Startup_Shutdown_Expression[g, tmp] \
                   * mod.startup_cost_per_mw[g]

    m.Startup_Cost_Constraint = \
        Constraint(m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS,
                   rule=startup_cost_rule)

    # TODO: this looks like a bug -- this constraint is missing a negative
    #  Needs to be:
    #  Shutdown_Cost >= - Startup_Shutdown_Expression X shutdown_cost
    def shutdown_cost_rule(mod, g, tmp):
        """
        Shutdown expression is positive when more units were on in the previous
        timepoint that are on in the current timepoint. Shutdown_Cost is
        defined to be non-negative, so if Shutdown_Expression is 0 or negative
        (i.e. no units shut down or units started since the previous 
        timepoint),
        Shutdown_Cost will be 0.
        If horizon is circular, the last timepoint of the horizon is the
        previous_timepoint for the first timepoint if the horizon;
        if the horizon is linear, no previous_timepoint is defined for the 
        first timepoint of the horizon, so skip constraint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp, mod.balancing_type[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type[g]]] == "linear":
            return Constraint.Skip
        else:
            return mod.Shutdown_Cost[g, tmp] \
                   >= mod.Startup_Shutdown_Expression[g, tmp] \
                   * mod.shutdown_cost_per_mw[g]

    m.Shutdown_Cost_Constraint = Constraint(
        m.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_cost_rule)


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export operations results.
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
                           "costs_operations_variable_om.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "horizon", "timepoint", "timepoint_weight",
             "number_of_hours_in_timepoint", "load_zone",
             "technology", "variable_om_cost"]
        )
        for (p, tmp) in m.PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type[p]],
                tmp,
                m.timepoint_weight[tmp],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone[p],
                m.technology[p],
                value(m.Variable_OM_Cost[p, tmp])
            ])

    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "costs_operations_fuel.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "horizon", "timepoint", "timepoint_weight",
             "number_of_hours_in_timepoint", "load_zone",
             "technology", "fuel_cost"]
        )
        for (p, tmp) in m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type[p]],
                tmp,
                m.timepoint_weight[tmp],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone[p],
                m.technology[p],
                value(m.Fuel_Cost[p, tmp])
            ])

    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "costs_operations_startup.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "horizon", "timepoint", "timepoint_weight",
             "number_of_hours_in_timepoint", "load_zone",
             "technology", "startup_cost"]
        )
        for (p, tmp) in m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type[p]],
                tmp,
                m.timepoint_weight[tmp],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone[p],
                m.technology[p],
                value(m.Startup_Cost[p, tmp])
            ])

    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "costs_operations_shutdown.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "horizon", "timepoint", "timepoint_weight",
             "number_of_hours_in_timepoint", "load_zone",
             "technology", "shutdown_cost"]
        )
        for (p, tmp) in m.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type[p]],
                tmp,
                m.timepoint_weight[tmp],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone[p],
                m.technology[p],
                value(m.Shutdown_Cost[p, tmp])
            ])


def import_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    print("project costs operations")

    # costs_operations_variable_om.csv
    c.execute(
        """DELETE FROM results_project_costs_operations_variable_om
        WHERE scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};
        """.format(scenario_id, subproblem, stage)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS
        temp_results_project_costs_operations_variable_om"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_costs_operations_variable_om"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        project VARCHAR(64),
        period INTEGER,
        subproblem_id INTEGER,
        stage_id INTEGER,
        horizon INTEGER,
        timepoint INTEGER,
        timepoint_weight FLOAT,
        number_of_hours_in_timepoint FLOAT,
        load_zone VARCHAR(32),
        technology VARCHAR(32),
        variable_om_cost FLOAT,
        PRIMARY KEY (scenario_id, project, timepoint)
            );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "costs_operations_variable_om.csv"), "r") as \
            dispatch_file:
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
            c.execute(
                """INSERT INTO
                temp_results_project_costs_operations_variable_om"""
                + str(scenario_id) + """
                (scenario_id, project, period, subproblem_id, stage_id,
                horizon, timepoint, timepoint_weight,
                number_of_hours_in_timepoint,
                load_zone, technology, variable_om_cost)
                VALUES ({}, '{}', {}, {}, {}, {}, {}, {}, {}, '{}', '{}',
                {});""".format(
                    scenario_id, project, period, subproblem, stage,
                    horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, variable_om_cost
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_costs_operations_variable_om
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, variable_om_cost)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, variable_om_cost
        FROM temp_results_project_costs_operations_variable_om"""
        + str(scenario_id) +
        """
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_costs_operations_variable_om"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    # costs_operations_fuel.csv
    c.execute(
        """DELETE FROM results_project_costs_operations_fuel
        WHERE scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};
        """.format(scenario_id, subproblem, stage)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS
        temp_results_project_costs_operations_fuel"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_costs_operations_fuel"""
        + str(scenario_id) + """(
            scenario_id INTEGER,
            project VARCHAR(64),
            period INTEGER,
            subproblem_id INTEGER,
            stage_id INTEGER,
            horizon INTEGER,
            timepoint INTEGER,
            timepoint_weight FLOAT,
            number_of_hours_in_timepoint FLOAT,
            load_zone VARCHAR(32),
            technology VARCHAR(32),
            fuel_cost FLOAT,
            PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
                );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "costs_operations_fuel.csv"), "r") as \
            dispatch_file:
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
            fuel_cost = row[8]
            c.execute(
                """INSERT INTO
                temp_results_project_costs_operations_fuel"""
                + str(scenario_id) + """
                    (scenario_id, project, period, subproblem_id, stage_id,
                    horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, fuel_cost)
                    VALUES ({}, '{}', {}, {}, {}, {}, {}, {}, {},
                    '{}', '{}', {});""".format(
                    scenario_id, project, period, subproblem, stage,
                    horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, fuel_cost
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_costs_operations_fuel
        (scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, fuel_cost)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, fuel_cost
        FROM temp_results_project_costs_operations_fuel"""
        + str(scenario_id) +
        """
        ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_costs_operations_fuel"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    # costs_operations_startup.csv
    c.execute(
        """DELETE FROM results_project_costs_operations_startup
        WHERE scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};
        """.format(scenario_id, subproblem, stage)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS
        temp_results_project_costs_operations_startup"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_costs_operations_startup"""
        + str(scenario_id) + """(
            scenario_id INTEGER,
            project VARCHAR(64),
            period INTEGER,
            subproblem_id INTEGER,
            stage_id INTEGER,
            horizon INTEGER,
            timepoint INTEGER,
            timepoint_weight FLOAT,
            number_of_hours_in_timepoint FLOAT,
            load_zone VARCHAR(32),
            technology VARCHAR(32),
            startup_cost FLOAT,
            PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
                );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "costs_operations_startup.csv"), "r") as \
            dispatch_file:
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
            startup_cost = row[8]
            c.execute(
                """INSERT INTO
                temp_results_project_costs_operations_startup"""
                + str(scenario_id) + """
                    (scenario_id, project, period, subproblem_id, stage_id,
                    horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, startup_cost)
                    VALUES ({}, '{}', {}, {}, {}, {}, {}, {}, {},
                    '{}', '{}', {});""".format(
                    scenario_id, project, period, subproblem, stage,
                    horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, startup_cost
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_costs_operations_startup
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, startup_cost)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, startup_cost
        FROM temp_results_project_costs_operations_startup"""
        + str(scenario_id) +
        """
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_costs_operations_startup"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    # costs_operations_shutdown.csv
    c.execute(
        """DELETE FROM results_project_costs_operations_shutdown
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS
        temp_results_project_costs_operations_shutdown"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_costs_operations_shutdown"""
        + str(scenario_id) + """(
            scenario_id INTEGER,
            project VARCHAR(64),
            period INTEGER,
            subproblem_id INTEGER,
            stage_id INTEGER,
            horizon INTEGER,
            timepoint INTEGER,
            timepoint_weight FLOAT,
            number_of_hours_in_timepoint FLOAT,
            load_zone VARCHAR(32),
            technology VARCHAR(32),
            shutdown_cost FLOAT,
            PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
                );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "costs_operations_shutdown.csv"), "r") as \
            dispatch_file:
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
            shutdown_cost = row[8]
            c.execute(
                """INSERT INTO
                temp_results_project_costs_operations_shutdown"""
                + str(scenario_id) + """
                    (scenario_id, project, period, subproblem_id, stage_id,
                    horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, shutdown_cost)
                    VALUES ({}, '{}', {}, {}, {}, {}, {}, {}, {},
                    '{}', '{}', {});""".format(
                    scenario_id, project, period, subproblem, stage,
                    horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, shutdown_cost
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_costs_operations_shutdown
        (scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, shutdown_cost)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, shutdown_cost
        FROM temp_results_project_costs_operations_shutdown"""
        + str(scenario_id) +
        """
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_costs_operations_shutdown""" + str(
            scenario_id) +
        """;"""
    )
    db.commit()
