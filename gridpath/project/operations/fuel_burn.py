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

    # Get startup fuel burn if it applies
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

    m.Startup_Shutdown_Expression_for_Fuel_Burn = Expression(
        m.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=startup_shutdown_rule
    )

    m.Startup_Fuel_Burn_MMBtu = Var(
        m.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS, within=NonNegativeReals
    )

    def startup_fuel_burn_rule(mod, g, tmp):
        """
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
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        else:
            return mod.Startup_Fuel_Burn_MMBtu[g, tmp] \
                   >= mod.Startup_Shutdown_Expression_for_Fuel_Burn[g, tmp] \
                   * mod.startup_fuel_mmbtu_per_mw[g]

    m.Startup_Fuel_Burn_Constraint = \
        Constraint(m.STARTUP_FUEL_PROJECT_OPERATIONAL_TIMEPOINTS,
                   rule=startup_fuel_burn_rule)

    m.Operations_Fuel_Burn_MMBtu = Expression(
        m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod, g, tmp: fuel_burn_rule(mod, g, tmp)
    )

    def total_fuel_burn_rule(mod, g, tmp):
        """
        Fuel for power production + fuel for startups
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Operations_Fuel_Burn_MMBtu[g, tmp] \
            + (mod.Startup_Fuel_Burn_MMBtu[g, tmp]
               if g in mod.STARTUP_FUEL_PROJECTS else 0)

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
            ["project", "period", "horizon", "timepoint", "horizon_weight",
             "number_of_hours_in_timepoint", "load_zone", "technology", "fuel",
             "fuel_burn_operations_mmbtu", "fuel_burn_startup_mmbtu",
             "total_fuel_burn_mmbtu"]
        )
        for (p, tmp) in m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp],
                tmp,
                m.horizon_weight[m.horizon[tmp]],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone[p],
                m.technology[p],
                m.fuel[p],
                value(m.Operations_Fuel_Burn_MMBtu[p, tmp]),
                value(m.Startup_Fuel_Burn_MMBtu[p, tmp])
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
    c.execute(
        """DELETE FROM results_project_fuel_burn 
        WHERE scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};
        """.format(scenario_id, subproblem, stage)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS 
        temp_results_project_fuel_burn"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_fuel_burn"""
        + str(scenario_id) + """(
         scenario_id INTEGER,
         project VARCHAR(64),
         period INTEGER,
         subproblem_id INTEGER,
         stage_id INTEGER,
         horizon INTEGER,
         timepoint INTEGER,
         horizon_weight FLOAT,
         number_of_hours_in_timepoint FLOAT,
         load_zone VARCHAR(32),
         technology VARCHAR(32),
         fuel VARCHAR(32),
         fuel_burn_mmbtu FLOAT,
         PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
         );"""
    )
    db.commit()

    # Load results into the temporary table
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
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[6]
            technology = row[7]
            fuel = row[8]
            fuel_burn_tons = row[9]

            c.execute(
                """INSERT INTO 
                temp_results_project_fuel_burn"""
                + str(scenario_id) + """
                 (scenario_id, project, period, subproblem_id, stage_id, 
                 horizon, timepoint, horizon_weight,
                 number_of_hours_in_timepoint,
                 load_zone, technology, fuel, fuel_burn_mmbtu)
                 VALUES ({}, '{}', {}, {}, {}, {}, {}, {}, {}, '{}', '{}', '{}',
                 {});""".format(
                    scenario_id, project, period, subproblem, stage,
                    horizon, timepoint, horizon_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, fuel, fuel_burn_tons
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_fuel_burn
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, fuel, fuel_burn_mmbtu)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, fuel, fuel_burn_mmbtu
        FROM temp_results_project_fuel_burn"""
        + str(scenario_id)
        + """
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_fuel_burn"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
