#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Keep track of fuel burn
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Expression, value, Var, NonNegativeReals, Constraint

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import
from gridpath.auxiliary.dynamic_components import \
    required_operational_modules
from gridpath.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # Operations fuel burn (excludes startup/shutdown)
    def fuel_burn_rule(mod, g, tmp):
        """
        Emissions from each project based on operational type
        (and whether a project burns fuel)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            fuel_burn_rule(mod, g, tmp, "Project {} has no fuel, so should "
                                        "not be labeled carbonaceous: "
                                        "replace its carbon_cap_zone with "
                                        "'.' in projects.tab.".format(g))

    m.Operations_Fuel_Burn_MMBtu = Expression(
        m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=fuel_burn_rule
    )

    # Shutdown fuel burn
    m.Shutdown_Fuel_Burn_MMBtu = Var(
        m.SHUTDOWN_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )

    def shutdown_fuel_burn_rule(mod, g, tmp):
        """
        Shutdown expression is positive when less units are on in the current
        timepoint that were on in the previous timepoint.
        Shutdown_Fuel_Burn_MMBtu is defined to be non-negative, so if
        Shutdown_MW is 0 or negative (i.e. no units started or units shut down
        since the previous timepoint), Shutdown_Fuel will be 0.
        If horizon is circular, the last timepoint of the horizon is the
        previous_timepoint for the first timepoint if the horizon;
        if the horizon is linear, no previous_timepoint is defined for the first
        timepoint of the horizon, so skip constraint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[
                    tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[mod.horizon[
                    tmp, mod.balancing_type_project[g]]] == "linear":
            return Constraint.Skip
        else:
            return mod.Shutdown_Fuel_Burn_MMBtu[g, tmp] \
                   >= mod.Shutdown_MW[g, tmp] \
                   * mod.shutdown_fuel_mmbtu_per_mw[g]

    m.Shutdown_Fuel_Burn_Constraint = \
        Constraint(m.SHUTDOWN_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS,
                   rule=shutdown_fuel_burn_rule)

    # Startup fuel burn
    # TODO: can we remove var construct and replace with expression or do we
    #  need this construct for capacity commit module to deal with start/stop
    #  distinction without binary variables
    m.Startup_Fuel_Burn_MMBtu = Var(
        m.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES,
        within=NonNegativeReals
    )

    def startup_fuel_burn_rule(mod, g, tmp, l):
        """
        Startup expression is positive when more units are on in the current
        timepoint that were on in the previous timepoint.
        Startup_Fuel_Burn_MMBtu is defined to be non-negative, so if Startup_MW
        is 0 or negative (i.e. no units started or units shut down since the
        previous timepoint), Startup_Fuel will be 0.
        If horizon is circular, the last timepoint of the horizon is the
        previous_timepoint for the first timepoint if the horizon;
        if the horizon is linear, no previous_timepoint is defined for the first
        timepoint of the horizon, so skip constraint.
        :param mod:
        :param g:
        :param tmp:
        :param l:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[
                    tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[mod.horizon[
                    tmp, mod.balancing_type_project[g]]] == "linear":
            return Constraint.Skip
        else:
            return mod.Startup_Fuel_Burn_MMBtu[g, tmp, l] \
                   >= mod.Startup_MW[g, tmp, l] \
                   * mod.startup_fuel_mmbtu_per_mw[g, l]

    m.Startup_Fuel_Burn_Constraint = Constraint(
        m.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES,
        rule=startup_fuel_burn_rule
    )

    # Calculate total startup fuel burn
    def total_startup_fuel_burn_rule(mod, g, tmp):
        """
        Aggregate fuel burn across startup types (note: only one type can be
        active at the same time).
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return (sum(mod.Startup_Fuel_Burn_MMBtu[g, tmp, l]
                    for l in mod.STARTUP_TYPES_BY_STARTUP_FUEL_PROJECT[g])
                if g in mod.STARTUP_FUEL_PROJECTS else 0)

    m.Total_Startup_Fuel_Burn_MMBtu = Expression(
        m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=total_startup_fuel_burn_rule
    )

    # Calculate total fuel burn
    def total_fuel_burn_rule(mod, g, tmp):
        """
        Fuel for power production + fuel for startups
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Operations_Fuel_Burn_MMBtu[g, tmp] \
            + (mod.Shutdown_Fuel_Burn_MMBtu[g, tmp]
               if g in mod.SHUTDOWN_FUEL_PROJECTS else 0) \
            + mod.Total_Startup_Fuel_Burn_MMBtu[g, tmp]

    m.Total_Fuel_Burn_MMBtu = Expression(
        m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=total_fuel_burn_rule
    )


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export fuel burn results.
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
              "fuel_burn.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "horizon", "timepoint", "timepoint_weight",
             "number_of_hours_in_timepoint", "load_zone", "technology", "fuel",
             "fuel_burn_operations_mmbtu", "fuel_burn_shutdown_mmbtu",
             "fuel_burn_startup_mmbtu", "fuel_burn_total_mmbtu"]
        )
        for (p, tmp) in sorted(m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS):
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type_project[p]],
                tmp,
                m.timepoint_weight[tmp],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone[p],
                m.technology[p],
                m.fuel[p],
                value(m.Operations_Fuel_Burn_MMBtu[p, tmp]),
                value(m.Shutdown_Fuel_Burn_MMBtu[p, tmp])
                if p in m.SHUTDOWN_FUEL_PROJECTS
                else None,
                value(m.Total_Startup_Fuel_Burn_MMBtu[p, tmp])
                if p in m.STARTUP_FUEL_PROJECTS
                else None,
                value(m.Total_Fuel_Burn_MMBtu[p, tmp])
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
    # Fuel burned by project and timepoint
    print("project fuel burn")
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_fuel_burn",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "fuel_burn.csv"), "r") as \
            fuel_burn_file:
        reader = csv.reader(fuel_burn_file)

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
            fuel = row[8]
            fuel_burn_operations_mmbtu = row[9]
            fuel_burn_shutdown_mmbtu = row[10]
            fuel_burn_startup_mmbtu = row[11]
            fuel_burn_total_mmbtu = row[12]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 horizon, timepoint, timepoint_weight,
                 number_of_hours_in_timepoint,
                 load_zone, technology, fuel,
                 fuel_burn_operations_mmbtu, fuel_burn_shutdown_mmbtu,
                 fuel_burn_startup_mmbtu, fuel_burn_total_mmbtu)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_fuel_burn{}
         (scenario_id, project, period, subproblem_id, stage_id, 
         horizon, timepoint, timepoint_weight,
         number_of_hours_in_timepoint,
         load_zone, technology, fuel, 
         fuel_burn_operations_mmbtu, fuel_burn_shutdown_mmbtu,
         fuel_burn_startup_mmbtu, fuel_burn_total_mmbtu)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_fuel_burn
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, fuel, 
        fuel_burn_operations_mmbtu, fuel_burn_shutdown_mmbtu,
        fuel_burn_startup_mmbtu, fuel_burn_total_mmbtu)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, fuel, 
        fuel_burn_operations_mmbtu, fuel_burn_shutdown_mmbtu,
        fuel_burn_startup_mmbtu, fuel_burn_total_mmbtu
        FROM temp_results_project_fuel_burn{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
