#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Carbon emissions from each carbonaceous project.
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
    # First figure out which projects we need to track for the carbon cap
    m.CARBONACEOUS_PROJECTS = Set(within=m.PROJECTS)
    m.carbon_cap_zone = Param(m.CARBONACEOUS_PROJECTS,
                              within=m.CARBON_CAP_ZONES)

    m.CARBONACEOUS_PROJECTS_BY_CARBON_CAP_ZONE = \
        Set(m.CARBON_CAP_ZONES, within=m.CARBONACEOUS_PROJECTS,
            initialize=lambda mod, co2_z:
            [p for p in mod.CARBONACEOUS_PROJECTS
             if mod.carbon_cap_zone[p] == co2_z])

    # Get operational carbon cap projects - timepoints combinations
    m.CARBONACEOUS_PROJECT_OPERATIONAL_TIMEPOINTS = Set(
        within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod: [(p, tmp) for (p, tmp) in
                          mod.PROJECT_OPERATIONAL_TIMEPOINTS
                          if p in mod.CARBONACEOUS_PROJECTS]
    )
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # Get emissions for each carbon cap project
    def carbon_emissions_rule(mod, g, tmp):
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
                                        "'.' in projects.tab.".format(g)) \
            * mod.co2_intensity_tons_per_mmbtu[mod.fuel[g]]

    m.Carbon_Emissions_Tons = Expression(
        m.CARBONACEOUS_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=carbon_emissions_rule
    )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     select=("project", "carbon_cap_zone"),
                     param=(m.carbon_cap_zone,)
                     )

    data_portal.data()['CARBONACEOUS_PROJECTS'] = {
        None: data_portal.data()['carbon_cap_zone'].keys()
    }


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "carbon_emissions_by_project.csv"), "wb") as \
            carbon_emissions_results_file:
        writer = csv.writer(carbon_emissions_results_file)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "horizon_weight",
                         "number_of_hours_in_timepoint", "load_zone",
                         "carbon_emissions_tons"])
        for (p, tmp) in m.CARBONACEOUS_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp],
                tmp,
                m.horizon_weight[m.horizon[tmp]],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone[p],
                value(m.Carbon_Emissions_Tons[p, tmp])
            ])


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    project_zones = c.execute(
        """SELECT project, carbon_cap_zone
        FROM inputs_project_carbon_cap_zones
            WHERE carbon_cap_zone_scenario_id = {}
            AND project_carbon_cap_zone_scenario_id = {}""".format(
            subscenarios.CARBON_CAP_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_CARBON_CAP_ZONE_SCENARIO_ID
        )
    ).fetchall()

    # Make a dict for easy access
    prj_zone_dict = dict()
    for (prj, zone) in project_zones:
        prj_zone_dict[str(prj)] = "." if zone is None else str(zone)

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t")

        new_rows = list()

        # Append column header
        header = reader.next()
        header.append("carbon_cap_zone")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in prj_zone_dict.keys():
                row.append(prj_zone_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(inputs_directory, "projects.tab"), "w") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t")
        writer.writerows(new_rows)


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
    # Carbon emission imports by project and timepoint
    print("project carbon emissions")
    c.execute(
        """DELETE FROM results_project_carbon_emissions 
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS 
        temp_results_project_carbon_emissions"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_carbon_emissions"""
        + str(scenario_id) + """(
         scenario_id INTEGER,
         project VARCHAR(64),
         period INTEGER,
         horizon INTEGER,
         timepoint INTEGER,
         horizon_weight FLOAT,
         number_of_hours_in_timepoint FLOAT,
         load_zone VARCHAR(32),
         carbon_emission_tons FLOAT,
         PRIMARY KEY (scenario_id, project, timepoint)
         );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "carbon_emissions_by_project.csv"), "r") as \
            emissions_file:
        reader = csv.reader(emissions_file)

        reader.next()  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[6]
            carbon_emissions_tons = row[7]

            c.execute(
                """INSERT INTO 
                temp_results_project_carbon_emissions"""
                + str(scenario_id) + """
                 (scenario_id, project, period, horizon, timepoint, 
                 horizon_weight, number_of_hours_in_timepoint, load_zone,
                 carbon_emission_tons)
                 VALUES ({}, '{}', {}, {}, {}, {}, {}, '{}', {});""".format(
                    scenario_id, project, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint, load_zone,
                    carbon_emissions_tons
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_carbon_emissions
        (scenario_id, project, period, horizon, timepoint, 
        horizon_weight, number_of_hours_in_timepoint, load_zone,
        carbon_emission_tons)
        SELECT
        scenario_id, project, period, horizon, timepoint, 
        horizon_weight, number_of_hours_in_timepoint, load_zone,
        carbon_emission_tons
        FROM temp_results_project_carbon_emissions"""
        + str(scenario_id)
        + """
         ORDER BY scenario_id, project, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_carbon_emissions"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
