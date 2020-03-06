#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Carbon emissions from each carbonaceous project.
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Param, Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import


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
        return mod.Total_Fuel_Burn_MMBtu[g, tmp] \
            * mod.co2_intensity_tons_per_mmbtu[mod.fuel[g]]

    m.Carbon_Emissions_Tons = Expression(
        m.CARBONACEOUS_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=carbon_emissions_rule
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(
                        scenario_directory, subproblem, stage, "inputs",
                        "projects.tab"),
                     select=("project", "carbon_cap_zone"),
                     param=(m.carbon_cap_zone,)
                     )

    data_portal.data()['CARBONACEOUS_PROJECTS'] = {
        None: list(data_portal.data()['carbon_cap_zone'].keys())
    }


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "carbon_emissions_by_project.csv"), "w", newline="") as \
            carbon_emissions_results_file:
        writer = csv.writer(carbon_emissions_results_file)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "timepoint_weight",
                         "number_of_hours_in_timepoint", "load_zone",
                         "carbon_emissions_tons"])
        for (p, tmp) in m.CARBONACEOUS_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type_project[p]],
                tmp,
                m.timepoint_weight[tmp],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone[p],
                value(m.Carbon_Emissions_Tons[p, tmp])
            ])


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    project_zones = c.execute(
        """SELECT project, carbon_cap_zone
        FROM inputs_project_carbon_cap_zones
            WHERE project_carbon_cap_zone_scenario_id = {}""".format(
            subscenarios.PROJECT_CARBON_CAP_ZONE_SCENARIO_ID
        )
    )

    return project_zones


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # project_zones = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

    # do stuff here to validate inputs


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    projects.tab file (to be precise, amend it).
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    project_zones = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Make a dict for easy access
    prj_zone_dict = dict()
    for (prj, zone) in project_zones:
        prj_zone_dict[str(prj)] = "." if zone is None else str(zone)

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t", lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("carbon_cap_zone")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_zone_dict.keys()):
                row.append(prj_zone_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(inputs_directory, "projects.tab"), "w", newline="") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)


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
    # Carbon emission imports by project and timepoint
    if not quiet:
        print("project carbon emissions")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_carbon_emissions",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "carbon_emissions_by_project.csv"), "r") as \
            emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            timepoint_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[6]
            carbon_emissions_tons = row[7]
            
            results.append(
                (scenario_id, project, period, subproblem, stage,
                    horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, carbon_emissions_tons)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_carbon_emissions{}
         (scenario_id, project, period, subproblem_id, stage_id,
         horizon, timepoint, timepoint_weight,
         number_of_hours_in_timepoint,
         load_zone, carbon_emission_tons)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_carbon_emissions
        (scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, carbon_emission_tons)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, carbon_emission_tons
        FROM temp_results_project_carbon_emissions{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


def process_results(db, c, subscenarios, quiet):
    """

    :param db: 
    :param c: 
    :param subscenarios:
    :param quiet:
    :return: 
    """
    if not quiet:
        print("update carbon cap zones")
    # Figure out carbon_cap zone for each project
    project_zones = c.execute(
        """SELECT project, carbon_cap_zone
        FROM inputs_project_carbon_cap_zones
            WHERE project_carbon_cap_zone_scenario_id = {}""".format(
            subscenarios.PROJECT_CARBON_CAP_ZONE_SCENARIO_ID
        )
    ).fetchall()

    # Update tables with carbon cap zone
    tables_to_update = [
        "results_project_capacity",
        "results_project_dispatch",
        "results_project_fuel_burn",
        "results_project_frequency_response",
        "results_project_lf_reserves_up",
        "results_project_lf_reserves_down",
        "results_project_regulation_up",
        "results_project_regulation_down",
        "results_project_costs_capacity",
        "results_project_costs_operations_variable_om",
        "results_project_costs_operations_fuel",
        "results_project_costs_operations_startup",
        "results_project_costs_operations_shutdown",
        "results_project_carbon_emissions",
        "results_project_elcc_simple",
        "results_project_elcc_surface"
    ]

    updates = []
    for (prj, zone) in project_zones:
        updates.append(
            (zone, subscenarios.SCENARIO_ID, prj)
        )
    for tbl in tables_to_update:
        sql = """
            UPDATE {}
            SET carbon_cap_zone = ?
            WHERE scenario_id = ?
            AND project = ?;
            """.format(tbl)
        spin_on_database_lock(conn=db, cursor=c, sql=sql, data=updates)

    # Set carbon_cap_zone to 'no_carbon_cap' for all other projects
    # This helps for later joins (can't join on NULL values)
    for tbl in tables_to_update:
        no_cc_sql = """
            UPDATE {}
            SET carbon_cap_zone = 'no_carbon_cap'
            WHERE scenario_id = ?
            AND carbon_cap_zone IS NULL;
            """.format(tbl)
        spin_on_database_lock(conn=db, cursor=c, sql=no_cc_sql,
                              data=(subscenarios.SCENARIO_ID,),
                              many=False)
