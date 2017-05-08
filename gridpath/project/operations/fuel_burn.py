#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Keep track of fuel burn
"""

import csv
import os.path
from pyomo.environ import Param, Set, Expression, value

from gridpath.auxiliary.dynamic_components import \
    required_operational_modules, carbon_cap_balance_emission_components
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

    # Get emissions for each carbon cap project
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

    m.Fuel_Burn_MMBtu = Expression(
        m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=fuel_burn_rule
    )


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export fuel burn results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
              "fuel_burn.csv"), "wb") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "horizon", "timepoint", "horizon_weight",
             "number_of_hours_in_timepoint", "load_zone", "technology", "fuel",
             "fuel_burn_mmbtu"]
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
                value(m.Fuel_Burn_MMBtu[p, tmp])
            ])


def import_results_into_database(
        scenario_id, c, db, results_directory
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
        WHERE scenario_id = {};""".format(
            scenario_id
        )
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
         horizon INTEGER,
         timepoint INTEGER,
         horizon_weight FLOAT,
         number_of_hours_in_timepoint FLOAT,
         load_zone VARCHAR(32),
         technology VARCHAR(32),
         fuel VARCHAR(32),
         fuel_burn_mmbtu FLOAT,
         PRIMARY KEY (scenario_id, project, timepoint)
         );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "fuel_burn.csv"), "r") as \
            fuel_burn_file:
        reader = csv.reader(fuel_burn_file)

        reader.next()  # skip header
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
                 (scenario_id, project, period, horizon, timepoint, 
                 horizon_weight, number_of_hours_in_timepoint, load_zone,
                 technology, fuel, fuel_burn_mmbtu)
                 VALUES ({}, '{}', {}, {}, {}, {}, {}, '{}', '{}', '{}',
                 {});""".format(
                    scenario_id, project, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint, load_zone,
                    technology, fuel, fuel_burn_tons
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_fuel_burn
        (scenario_id, project, period, horizon, timepoint, 
        horizon_weight, number_of_hours_in_timepoint, load_zone,
        technology, fuel, fuel_burn_mmbtu)
        SELECT
        scenario_id, project, period, horizon, timepoint, 
        horizon_weight, number_of_hours_in_timepoint, load_zone,
        technology, fuel, fuel_burn_mmbtu
        FROM temp_results_project_fuel_burn"""
        + str(scenario_id)
        + """
         ORDER BY scenario_id, project, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_fuel_burn"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
