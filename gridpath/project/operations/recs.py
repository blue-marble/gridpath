#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Get RECs for each project
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Param, Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import load_operational_type_modules, \
    setup_results_import
from gridpath.auxiliary.dynamic_components import required_operational_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # First figure out which projects are RPS-eligible
    m.RPS_PROJECTS = Set(within=m.PROJECTS)
    m.rps_zone = Param(m.RPS_PROJECTS, within=m.RPS_ZONES)

    def determine_rps_generators_by_rps_zone(mod, rps_z):
        return [p for p in mod.RPS_PROJECTS if mod.rps_zone[p] == rps_z]

    m.RPS_PROJECTS_BY_RPS_ZONE = \
        Set(m.RPS_ZONES, within=m.RPS_PROJECTS,
            initialize=determine_rps_generators_by_rps_zone)

    # Get operational RPS projects - timepoints combinations
    m.RPS_PROJECT_OPERATIONAL_TIMEPOINTS = Set(
        within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod: [(p, tmp) for (p, tmp) in
                          mod.PROJECT_OPERATIONAL_TIMEPOINTS
                          if p in mod.RPS_PROJECTS]
    )
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    def scheduled_recs_rule(mod, g, tmp):
        """
        This how many RECs are scheduled to be delivered at the timepoint
        (hourly) schedule
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            rec_provision_rule(mod, g, tmp)

    m.Scheduled_RPS_Energy_MW = Expression(
        m.RPS_PROJECT_OPERATIONAL_TIMEPOINTS, 
        rule=scheduled_recs_rule
    )

    # Keep track of curtailment
    def scheduled_curtailment_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the scheduled
        curtailment component
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            scheduled_curtailment_rule(mod, g, tmp)

    m.Scheduled_Curtailment_MW = Expression(
        m.RPS_PROJECT_OPERATIONAL_TIMEPOINTS, rule=scheduled_curtailment_rule
    )

    def subhourly_curtailment_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the subhourly
        curtailment component
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            subhourly_curtailment_rule(mod, g, tmp)

    m.Subhourly_Curtailment_MW = Expression(
        m.RPS_PROJECT_OPERATIONAL_TIMEPOINTS, rule=subhourly_curtailment_rule
    )

    def subhourly_recs_delivered_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the subhourly
        curtailment component
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            subhourly_energy_delivered_rule(mod, g, tmp)

    m.Subhourly_RPS_Energy_Delivered_MW = Expression(
        m.RPS_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=subhourly_recs_delivered_rule
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
                     select=("project", "rps_zone"),
                     param=(m.rps_zone,)
                     )

    data_portal.data()['RPS_PROJECTS'] = {
        None: list(data_portal.data()['rps_zone'].keys())
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
                           "rps_by_project.csv"), "w", newline="") as rps_results_file:
        writer = csv.writer(rps_results_file)
        writer.writerow(["project", "load_zone", "rps_zone",
                         "timepoint", "period", "horizon", "timepoint_weight",
                         "number_of_hours_in_timepoint", "technology",
                         "scheduled_rps_energy_mw",
                         "scheduled_curtailment_mw",
                         "subhourly_rps_energy_delivered_mw",
                         "subhourly_curtailment_mw"])
        for (p, tmp) in m.RPS_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.load_zone[p],
                m.rps_zone[p],
                tmp,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type_project[p]],
                m.timepoint_weight[tmp],
                m.number_of_hours_in_timepoint[tmp],
                m.technology[p],
                value(m.Scheduled_RPS_Energy_MW[p, tmp]),
                value(m.Scheduled_Curtailment_MW[p, tmp]),
                value(m.Subhourly_RPS_Energy_Delivered_MW[p, tmp]),
                value(m.Subhourly_Curtailment_MW[p, tmp])
            ])

    # Export list of RPS projects and their zones for later use
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "rps_project_zones.csv"), "w", newline="") as \
            rps_project_zones_file:
        writer = csv.writer(rps_project_zones_file)
        writer.writerow(["project", "rps_zone"])
        for p in m.RPS_PROJECTS:
            writer.writerow([p, m.rps_zone[p]])



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
        """SELECT project, rps_zone
        FROM inputs_project_rps_zones
            WHERE rps_zone_scenario_id = {}
            AND project_rps_zone_scenario_id = {}""".format(
            subscenarios.RPS_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_RPS_ZONE_SCENARIO_ID
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
        reader = csv.reader(projects_file_in, delimiter="\t")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("rps_zone")
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
        writer = csv.writer(projects_file_out, delimiter="\t")
        writer.writerows(new_rows)


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
    # REC provision by project and timepoint
    print("project recs")
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_rps",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "rps_by_project.csv"), "r") as \
            rps_file:
        reader = csv.reader(rps_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            load_zone = row[1]
            rps_zone = row[2]
            timepoint = row[3]
            period = row[4]
            horizon = row[5]
            timepoint_weight = row[6]
            hours_in_tmp = row[7]
            technology = row[8]
            scheduled_energy = row[9]
            scheduled_curtailment = row[10]
            subhourly_energy = row[11]
            subhourly_curtailment = row[12]
            
            results.append(
                (scenario_id, project, period, subproblem, stage,
                    horizon, timepoint, timepoint_weight, hours_in_tmp,
                    load_zone, rps_zone, technology,
                    scheduled_energy, scheduled_curtailment,
                    subhourly_energy, subhourly_curtailment)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_rps{}
         (scenario_id, project, period, subproblem_id, stage_id, 
         horizon, timepoint, timepoint_weight, 
         number_of_hours_in_timepoint, 
         load_zone, rps_zone, technology, 
         scheduled_rps_energy_mw, scheduled_curtailment_mw, 
         subhourly_rps_energy_delivered_mw, subhourly_curtailment_mw)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_rps
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, rps_zone, technology, 
        scheduled_rps_energy_mw, scheduled_curtailment_mw, 
        subhourly_rps_energy_delivered_mw, subhourly_curtailment_mw)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, rps_zone, technology, 
        scheduled_rps_energy_mw, scheduled_curtailment_mw, 
        subhourly_rps_energy_delivered_mw, subhourly_curtailment_mw
        FROM temp_results_project_rps{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


def process_results(db, c, subscenarios):
    """
    
    :param db: 
    :param c: 
    :param subscenarios: 
    :return: 
    """
    print("update rps zones")
    # Figure out RPS zone for each project
    project_zones = c.execute(
        """SELECT project, rps_zone
        FROM inputs_project_rps_zones
            WHERE rps_zone_scenario_id = {}
            AND project_rps_zone_scenario_id = {}""".format(
            subscenarios.RPS_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_RPS_ZONE_SCENARIO_ID
        )
    ).fetchall()

    # TODO: update this with all latest types
    # Update tables with RPS zone
    tables_to_update = [
        "results_project_capacity_all",
        "results_project_capacity_gen_new_lin",
        "results_project_capacity_gen_new_bin",
        "results_project_capacity_stor_new_lin",
        "results_project_capacity_new_binary_build_storage",
        "results_project_capacity_linear_economic_retirement",
        "results_project_dispatch_all",
        "results_project_dispatch_variable",
        "results_project_dispatch_capacity_commit",
        "results_project_dispatch_hydro_curtailable",
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

    results = []
    for (prj, zone) in project_zones:
        results.append(
            (zone, subscenarios.SCENARIO_ID, prj)
        )

    for tbl in tables_to_update:
        sql = """
            UPDATE {}
            SET rps_zone = ?
            WHERE scenario_id = ?
            AND project = ?;
            """.format(tbl)
        spin_on_database_lock(conn=db, cursor=c, sql=sql, data=results)
