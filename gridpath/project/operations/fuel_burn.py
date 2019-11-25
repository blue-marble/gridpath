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

    # Get fuel burn from operations for each project
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
        rule=lambda mod, g, tmp: fuel_burn_rule(mod, g, tmp)
    )

    # Get startup fuel burn if it applies
    def startup_rule(mod, g, tmp, l):
        """
        Track units started up from timepoint to timepoint; get appropriate
        expression from the generator's operational module.
        :param mod:
        :param g:
        :param tmp:
        :param l:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            startup_rule(mod, g, tmp, l)

    m.Startup_Expression_for_Fuel_Burn = Expression(
        m.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES,
        rule=startup_rule
    )

    # Constrain startup fuel burn
    m.Startup_Fuel_Burn_MMBtu = Var(
        m.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES,
        within=NonNegativeReals
    )

    def startup_fuel_burn_rule(mod, g, tmp, l):
        """
        TODO: UPDATE SINCE NO LONGER NEGATIVE
        Startup expression is positive when more units are on in the current
        timepoint that were on in the previous timepoint. Startup_Fuel_Burn_MMBtu is
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
        :param l:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] == "linear":
            return Constraint.Skip
        else:
            return mod.Startup_Fuel_Burn_MMBtu[g, tmp, l] \
                   >= mod.Startup_Shutdown_Expression_for_Fuel_Burn[g, tmp, l] \
                   * mod.startup_fuel_mmbtu_per_mw[g, l]

    m.Startup_Fuel_Burn_Constraint = \
        Constraint(m.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS_TYPES,
                   rule=startup_fuel_burn_rule)

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
                    for l in m.STARTUP_TYPES_BY_STARTUP_FUEL_PROJECT[g])
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
             "fuel_burn_operations_mmbtu", "fuel_burn_startup_mmbtu",
             "total_fuel_burn_mmbtu"]
        )
        # TODO: need to somehow take out the startup trajectory fuel burn from
        #  fuel_burn_operations and add it into startup_fuel.
        for (p, tmp) in m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS:
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
            fuel_burn_tons = row[9]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                    horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, fuel, fuel_burn_tons)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_fuel_burn{}
         (scenario_id, project, period, subproblem_id, stage_id, 
         horizon, timepoint, timepoint_weight,
         number_of_hours_in_timepoint,
         load_zone, technology, fuel, fuel_burn_mmbtu)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_fuel_burn
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, fuel, fuel_burn_mmbtu)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, fuel, fuel_burn_mmbtu
        FROM temp_results_project_fuel_burn{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
