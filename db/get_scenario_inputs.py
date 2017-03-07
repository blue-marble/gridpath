#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from argparse import ArgumentParser
import csv
import os.path
import sqlite3
import sys

from gridpath.auxiliary.module_list import get_modules, load_modules

arguments = sys.argv[1:]
parser = ArgumentParser(add_help=True)
parser.add_argument("--scenario_id", help="The scenario_id from the database.")
parsed_arguments = parser.parse_known_args(args=arguments)[0]

SCENARIO_ID = parsed_arguments.scenario_id

# Assume script is run from same directory a the database, which is named io.db
io = sqlite3.connect(
    os.path.join(os.getcwd(), 'io.db')
)
c = io.cursor()

# Get scenario name and make inputs directory
SCENARIO_NAME = c.execute(
    """SELECT scenario_name
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

SCENARIOS_MAIN_DIRECTORY = os.path.join(
    os.getcwd(), "..", "scenarios")
if not os.path.exists(SCENARIOS_MAIN_DIRECTORY):
    os.makedirs(SCENARIOS_MAIN_DIRECTORY)

SCENARIO_DIRECTORY = os.path.join(
    SCENARIOS_MAIN_DIRECTORY, str(SCENARIO_NAME)
)
if not os.path.exists(SCENARIO_DIRECTORY):
    os.makedirs(SCENARIO_DIRECTORY)

INPUTS_DIRECTORY = os.path.join(
    SCENARIO_DIRECTORY, "inputs")
if not os.path.exists(INPUTS_DIRECTORY):
    os.makedirs(INPUTS_DIRECTORY)

# Save scenario_id
with open(os.path.join(SCENARIO_DIRECTORY, "scenario_id.txt"), "w") as \
        scenario_id_file:
    scenario_id_file.write(str(SCENARIO_ID))

# Get modules we'll be using
MODULE_LIST = list()

OPTIONAL_MODULE_FUELS = c.execute(
    """SELECT om_fuels
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_FUELS:
    MODULE_LIST.append("fuels")

OPTIONAL_MULTI_STAGE = c.execute(
    """SELECT om_multi_stage
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MULTI_STAGE:
    MODULE_LIST.append("multi_stage")

OPTIONAL_MODULE_TRANSMISSION = c.execute(
    """SELECT om_transmission
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_TRANSMISSION:
    MODULE_LIST.append("transmission")

OPTIONAL_MODULE_SIMULTANEOUS_FLOW_LIMITS = c.execute(
    """SELECT om_simultaneous_flow_limits
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_SIMULTANEOUS_FLOW_LIMITS:
    MODULE_LIST.append("simultaneous_flow_limits")

OPTIONAL_MODULE_LF_RESERVES_UP = c.execute(
    """SELECT om_lf_reserves_up
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_LF_RESERVES_UP:
    MODULE_LIST.append("lf_reserves_up")

OPTIONAL_MODULE_LF_RESERVES_DOWN = c.execute(
    """SELECT om_lf_reserves_down
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_LF_RESERVES_DOWN:
    MODULE_LIST.append("lf_reserves_down")

OPTIONAL_MODULE_REGULATION_UP = c.execute(
    """SELECT om_regulation_up
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_REGULATION_UP:
    MODULE_LIST.append("regulation_up")

OPTIONAL_MODULE_REGULATION_DOWN = c.execute(
    """SELECT om_regulation_down
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_REGULATION_DOWN:
    MODULE_LIST.append("regulation_down")

OPTIONAL_MODULE_RPS = c.execute(
    """SELECT om_rps
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_RPS:
    MODULE_LIST.append("rps")

OPTIONAL_MODULE_CARBON_CAP = c.execute(
    """SELECT om_carbon_cap
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_CARBON_CAP:
    MODULE_LIST.append("carbon_cap")

OPTIONAL_MODULE_TRACK_CARBON_IMPORTS = c.execute(
    """SELECT om_track_carbon_imports
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]
if OPTIONAL_MODULE_TRACK_CARBON_IMPORTS:
    MODULE_LIST.append("track_carbon_imports")

# modules.csv
with open(os.path.join(SCENARIO_DIRECTORY, "modules.csv"), "w") as \
        modules_csv_file:
    writer = csv.writer(modules_csv_file, delimiter=",")

    # Write header
    writer.writerow(["modules"])

    for module in MODULE_LIST:
        writer.writerow([module])


# Get subscenarios
class SubScenarios:
    def __init__(self, cursor):
        self.HORIZON_SCENARIO_ID = cursor.execute(
            """SELECT horizon_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TIMEPOINT_SCENARIO_ID = cursor.execute(
            """SELECT timepoint_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.PERIOD_SCENARIO_ID = cursor.execute(
            """SELECT period_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.LOAD_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT load_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.LF_RESERVES_UP_BA_SCENARIO_ID = cursor.execute(
            """SELECT lf_reserves_up_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.LF_RESERVES_DOWN_BA_SCENARIO_ID = cursor.execute(
            """SELECT lf_reserves_down_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.RPS_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT rps_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.RPS_TARGET_SCENARIO_ID = cursor.execute(
            """SELECT rps_target_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.CARBON_CAP_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT carbon_cap_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.CARBON_CAP_TARGET_SCENARIO_ID = cursor.execute(
            """SELECT carbon_cap_target_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.PROJECT_LOAD_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT project_load_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.PROJECT_LF_RESERVES_UP_BA_SCENARIO_ID = cursor.execute(
            """SELECT project_lf_reserves_up_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.PROJECT_LF_RESERVES_DOWN_BA_SCENARIO_ID = cursor.execute(
            """SELECT project_lf_reserves_down_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.PROJECT_RPS_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT project_rps_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.PROJECT_CARBON_CAP_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT project_carbon_cap_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.EXISTING_PROJECT_SCENARIO_ID = cursor.execute(
            """SELECT existing_project_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.NEW_PROJECT_SCENARIO_ID = cursor.execute(
            """SELECT new_project_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.EXISTING_PROJECT_CAPACITY_SCENARIO_ID = cursor.execute(
            """SELECT existing_project_capacity_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.NEW_PROJECT_COST_SCENARIO_ID = cursor.execute(
            """SELECT new_project_cost_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.NEW_PROJECT_POTENTIAL_SCENARIO_ID = cursor.execute(
            """SELECT new_project_potential_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.FUEL_SCENARIO_ID = cursor.execute(
            """SELECT fuel_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID = cursor.execute(
            """SELECT project_operational_chars_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.HYDRO_OPERATIONAL_CHARS_SCENARIO_ID = cursor.execute(
            """SELECT hydro_operational_chars_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.VARIABLE_GENERATOR_PROFILES_SCENARIO_ID = cursor.execute(
            """SELECT variable_generator_profiles_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.LOAD_SCENARIO_ID = cursor.execute(
            """SELECT load_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.LF_RESERVES_UP_SCENARIO_ID = cursor.execute(
            """SELECT lf_reserves_up_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.LF_RESERVES_DOWN_SCENARIO_ID = cursor.execute(
            """SELECT lf_reserves_down_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_LINE_SCENARIO_ID = cursor.execute(
            """SELECT transmission_line_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_LINE_EXISTING_CAPACITY_SCENARIO_ID = cursor.execute(
            """SELECT transmission_line_existing_capacity_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_SIMULTANEOUS_FLOW_GROUP_LINES_SCENARIO_ID = cursor.execute(
            """SELECT transmission_simultaneous_flow_group_lines_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_SCENARIO_ID = cursor.execute(
            """SELECT transmission_simultaneous_flow_limit_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_LINE_CARBON_CAP_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT transmission_line_carbon_cap_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

HORIZON_SCENARIO_ID = c.execute(
    """SELECT horizon_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

TIMEPOINT_SCENARIO_ID = c.execute(
    """SELECT timepoint_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PERIOD_SCENARIO_ID = c.execute(
    """SELECT period_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

LOAD_ZONE_SCENARIO_ID = c.execute(
    """SELECT load_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

LF_RESERVES_UP_BA_SCENARIO_ID = c.execute(
    """SELECT lf_reserves_up_ba_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

LF_RESERVES_DOWN_BA_SCENARIO_ID = c.execute(
    """SELECT lf_reserves_down_ba_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

RPS_ZONE_SCENARIO_ID = c.execute(
    """SELECT rps_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

RPS_TARGET_SCENARIO_ID = c.execute(
    """SELECT rps_target_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

CARBON_CAP_ZONE_SCENARIO_ID = c.execute(
    """SELECT carbon_cap_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

CARBON_CAP_TARGET_SCENARIO_ID = c.execute(
    """SELECT carbon_cap_target_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PROJECT_LOAD_ZONE_SCENARIO_ID = c.execute(
    """SELECT project_load_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PROJECT_LF_RESERVES_UP_BA_SCENARIO_ID = c.execute(
    """SELECT project_lf_reserves_up_ba_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PROJECT_LF_RESERVES_DOWN_BA_SCENARIO_ID = c.execute(
    """SELECT project_lf_reserves_down_ba_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PROJECT_RPS_ZONE_SCENARIO_ID = c.execute(
    """SELECT project_rps_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PROJECT_CARBON_CAP_ZONE_SCENARIO_ID = c.execute(
    """SELECT project_carbon_cap_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

EXISTING_PROJECT_SCENARIO_ID = c.execute(
    """SELECT existing_project_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

NEW_PROJECT_SCENARIO_ID = c.execute(
    """SELECT new_project_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

EXISTING_PROJECT_CAPACITY_SCENARIO_ID = c.execute(
    """SELECT existing_project_capacity_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

NEW_PROJECT_COST_SCENARIO_ID = c.execute(
    """SELECT new_project_cost_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

NEW_PROJECT_POTENTIAL_SCENARIO_ID = c.execute(
    """SELECT new_project_potential_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

FUEL_SCENARIO_ID = c.execute(
    """SELECT fuel_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

PROJECT_OPERATIONAL_CHARS_SCENARIO_ID = c.execute(
    """SELECT project_operational_chars_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

HYDRO_OPERATIONAL_CHARS_SCENARIO_ID = c.execute(
    """SELECT hydro_operational_chars_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

VARIABLE_GENERATOR_PROFILES_SCENARIO_ID = c.execute(
    """SELECT variable_generator_profiles_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

LOAD_SCENARIO_ID = c.execute(
    """SELECT load_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

LF_RESERVES_UP_SCENARIO_ID = c.execute(
    """SELECT lf_reserves_up_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

LF_RESERVES_DOWN_SCENARIO_ID = c.execute(
    """SELECT lf_reserves_down_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

TRANSMISSION_LINE_SCENARIO_ID = c.execute(
    """SELECT transmission_line_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

TRANSMISSION_LINE_EXISTING_CAPACITY_SCENARIO_ID = c.execute(
    """SELECT transmission_line_existing_capacity_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

TRANSMISSION_SIMULTANEOUS_FLOW_GROUP_LINES_SCENARIO_ID = c.execute(
    """SELECT transmission_simultaneous_flow_group_lines_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_SCENARIO_ID = c.execute(
    """SELECT transmission_simultaneous_flow_limit_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]

TRANSMISSION_LINE_CARBON_CAP_ZONE_SCENARIO_ID = c.execute(
    """SELECT transmission_line_carbon_cap_zone_scenario_id
       FROM scenarios
       WHERE scenario_id = {};""".format(SCENARIO_ID)
).fetchone()[0]


MODULES_TO_USE = get_modules(SCENARIO_DIRECTORY)
LOADED_MODULES = load_modules(MODULES_TO_USE)
SUBSCENARIOS = SubScenarios(cursor=c)


def get_inputs_from_database(loaded_modules):
    """

    :return:
    """
    for m in loaded_modules:
        if hasattr(m, "get_inputs_from_database"):
            m.get_inputs_from_database(SUBSCENARIOS, c, INPUTS_DIRECTORY)
        else:
            pass

# Main
get_inputs_from_database(LOADED_MODULES)


# TODO: how to handle optional columns (e.g. lf_reserves_up_ba, rps_zone, etc.)
# TODO: add heat rate for new advanced ccgt and aero ct
# TODO: if fuel specified, can't have '.' -- must be 0 instead
# TODO: why is there a startup cost for CAISO_Nuclear and CAISO_CHP
# projects.tab
prj_db_table_optional_select = dict()
prj_file_optional_headers = list()
if OPTIONAL_MODULE_LF_RESERVES_UP:
    prj_db_table_optional_select["lf_reserves_up"] = {
        "db_column_name": ", lf_reserves_up_ba",
        "db_join_statement": "\nJOIN project_lf_reserves_up_bas "
                             "USING (existing_project_scenario_id, "
                             "new_project_scenario_id, project) ",
        "db_and_statement": "\nAND lf_reserves_up_ba_scenario_id = {} "
                            "AND project_lf_reserves_up_ba_scenario_id = {}"
        }
    prj_file_optional_headers.append("lf_reserves_up_zone")
else:
    prj_db_table_optional_select["lf_reserves_up"] = {
        "db_column_name": "",
        "db_join_statement": ""
        }
    
if OPTIONAL_MODULE_LF_RESERVES_DOWN:
    prj_db_table_optional_select["lf_reserves_down"] = {
        "db_column_name": ", lf_reserves_down_ba",
        "db_join_statement": "\nJOIN project_lf_reserves_down_bas "
                               "USING (existing_project_scenario_id, "
                               "new_project_scenario_id, project) ",
        "db_and_statement": "\nAND lf_reserves_down_ba_scenario_id = {} "
                            "AND project_lf_reserves_down_ba_scenario_id = "
                            "{}"
        }
    prj_file_optional_headers.append("lf_reserves_down_zone")
else:
    prj_db_table_optional_select["lf_reserves_down"] = {
        "db_column_name": "",
        "db_join_statement": ""
        }

if OPTIONAL_MODULE_RPS:
    prj_db_table_optional_select["rps"] = {
        "db_column_name": ", rps_zone",
        "db_join_statement": "\nJOIN project_rps_zones "
                             "USING (existing_project_scenario_id, "
                             "new_project_scenario_id, project) ",
        "db_and_statement": "\nAND rps_zone_scenario_id = {} "
                            "AND project_rps_zone_scenario_id = {}"
    }
    prj_file_optional_headers.append("rps_zone")
else:
    prj_db_table_optional_select["rps"] = {
        "db_column_name": "",
        "db_join_statement": ""
    }

if OPTIONAL_MODULE_CARBON_CAP:
    prj_db_table_optional_select["carbon_cap"] = {
        "db_column_name": ", carbon_cap_zone",
        "db_join_statement": "\nJOIN project_carbon_cap_zones "
                             "USING (existing_project_scenario_id, "
                             "new_project_scenario_id, project) ",
        "db_and_statement": "\nAND carbon_cap_zone_scenario_id = {} "
                            "AND project_carbon_cap_zone_scenario_id = {}"
    }
    prj_file_optional_headers.append("carbon_cap_zone")
else:
    prj_db_table_optional_select["carbon_cap"] = {
        "db_column_name": "",
        "db_join_statement": "",
        "db_and_statement": ""
    }


with open(os.path.join(INPUTS_DIRECTORY, "projects.tab"), "w") as \
        projects_tab_file:
    writer = csv.writer(projects_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["project", "load_zone",
         "capacity_type", "operational_type", "fuel",
         "minimum_input_mmbtu_per_hr", "inc_heat_rate_mmbtu_per_mwh",
         "min_stable_level_fraction", "unit_size_mw", "startup_cost",
         "shutdown_cost", "min_up_time_hours", "min_down_time_hours",
         "charging_efficiency", "discharging_efficiency",
         "minimum_duration_hours", "variable_om_cost_per_mwh", "technology"]
        + prj_file_optional_headers
    )

    query = \
        """SELECT project, load_zone, capacity_type, operational_type, fuel,
        minimum_input_mmbtu_per_hr, inc_heat_rate_mmbtu_per_mwh,
        min_stable_level, unit_size_mw, startup_cost, shutdown_cost,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours, variable_cost_per_mwh, technology""" + \
        prj_db_table_optional_select["lf_reserves_up"]["db_column_name"] + \
        prj_db_table_optional_select["lf_reserves_down"]["db_column_name"] +\
        prj_db_table_optional_select["rps"]["db_column_name"] + \
        prj_db_table_optional_select["carbon_cap"]["db_column_name"] +\
        """ FROM all_projects
        JOIN project_operational_chars
        USING (project)
        JOIN project_load_zones
        USING (existing_project_scenario_id, new_project_scenario_id,
        project)""" + \
        prj_db_table_optional_select["lf_reserves_up"]["db_join_statement"] + \
        prj_db_table_optional_select["lf_reserves_down"][
            "db_join_statement"] \
        + \
        prj_db_table_optional_select["rps"]["db_join_statement"] + \
        prj_db_table_optional_select["carbon_cap"]["db_join_statement"] + \
        """
        WHERE load_zone_scenario_id = {}
        AND existing_project_scenario_id = {}
        AND new_project_scenario_id = {}
        AND project_operational_chars_scenario_id = {}
        AND project_load_zone_scenario_id = {}""" + \
        prj_db_table_optional_select["lf_reserves_up"]["db_and_statement"] + \
        prj_db_table_optional_select["lf_reserves_down"]["db_and_statement"] \
        + \
        prj_db_table_optional_select["rps"]["db_and_statement"] + \
        prj_db_table_optional_select["carbon_cap"]["db_and_statement"] + \
        """;"""

    projects = c.execute(query.format(
            LOAD_ZONE_SCENARIO_ID,
            EXISTING_PROJECT_SCENARIO_ID,
            NEW_PROJECT_SCENARIO_ID,
            PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            PROJECT_LOAD_ZONE_SCENARIO_ID,
            LF_RESERVES_UP_BA_SCENARIO_ID,
            PROJECT_LF_RESERVES_UP_BA_SCENARIO_ID,
            LF_RESERVES_DOWN_BA_SCENARIO_ID,
            PROJECT_LF_RESERVES_DOWN_BA_SCENARIO_ID,
            RPS_ZONE_SCENARIO_ID,
            PROJECT_RPS_ZONE_SCENARIO_ID,
            CARBON_CAP_ZONE_SCENARIO_ID,
            PROJECT_CARBON_CAP_ZONE_SCENARIO_ID
        )
    ).fetchall()

    for row in projects:
        replace_nulls = ["." if i is None else i for i in row]
        writer.writerow(replace_nulls)

# existing_generation_period_params.tab
with open(os.path.join(INPUTS_DIRECTORY,
                       "existing_generation_period_params.tab"), "w") as \
        existing_project_capacity_tab_file:
    writer = csv.writer(existing_project_capacity_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["GENERATORS", "PERIODS", "existing_capacity_mw",
         "fixed_cost_per_mw_yr"]
    )

    ep_capacities = c.execute(
        """SELECT project, period, existing_capacity_mw,
        annual_fixed_cost_per_mw_year
        FROM existing_project_capacity
        WHERE existing_project_scenario_id = {}
        AND period_scenario_id = {}
        AND existing_project_capacity_scenario_id = {};""".format(
            EXISTING_PROJECT_SCENARIO_ID, PERIOD_SCENARIO_ID,
            EXISTING_PROJECT_CAPACITY_SCENARIO_ID
        )
    )
    for row in ep_capacities:
        writer.writerow(row)

# storage_specified_capacities.tab
with open(os.path.join(INPUTS_DIRECTORY,
                       "storage_specified_capacities.tab"), "w") as \
        storage_specified_capacities_tab_file:
    writer = csv.writer(storage_specified_capacities_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["storage_project", "period",
         "storage_specified_power_capacity_mw",
         "storage_specified_energy_capacity_mwh"]
    )

    # TODO: more robust way to get storage projects than selecting non-null
    # rows
    stor_capacities = c.execute(
        """SELECT project, period, existing_capacity_mw, existing_capacity_mwh,
        annual_fixed_cost_per_mw_year, annual_fixed_cost_per_mwh_year
        FROM existing_project_capacity
        WHERE existing_project_scenario_id = {}
        AND period_scenario_id = {}
        AND existing_project_capacity_scenario_id = {}
        AND existing_capacity_mwh IS NOT NULL;""".format(
            EXISTING_PROJECT_SCENARIO_ID, PERIOD_SCENARIO_ID,
            EXISTING_PROJECT_CAPACITY_SCENARIO_ID
        )
    )
    for row in stor_capacities:
        writer.writerow(row)

# new_build_generator_vintage_costs.tab
with open(os.path.join(INPUTS_DIRECTORY,
                       "new_build_generator_vintage_costs.tab"), "w") as \
        new_gen_costs_tab_file:
    writer = csv.writer(new_gen_costs_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["new_build_generator", "vintage", "lifetime_yrs",
         "annualized_real_cost_per_mw_yr", "min_cumulative_new_build_mw",
         "max_cumulative_new_build_mw"]
    )

    # TODO: select only rows with NULL for cost per kWh-yr for generators
    # only (i.e to exclude storage), but need to make this more robust
    new_gen_costs = c.execute(
        """SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr * 1000,
        minimum_cumulative_new_build_mw, maximum_cumulative_new_build_mw
        FROM new_project_cost
        JOIN new_project_potential
        USING (new_project_scenario_id, period_scenario_id, project, period)
        WHERE annualized_real_cost_per_kwh_yr IS NULL
        AND new_project_scenario_id = {}
        AND period_scenario_id = {}
        AND new_project_cost_scenario_id = {}
        AND new_project_potential_scenario_id = {};""".format(
            NEW_PROJECT_SCENARIO_ID, PERIOD_SCENARIO_ID,
            NEW_PROJECT_COST_SCENARIO_ID,
            NEW_PROJECT_POTENTIAL_SCENARIO_ID
        )
    )
    for row in new_gen_costs:
        replace_nulls = ["." if i is None else i for i in row]
        writer.writerow(replace_nulls)

# new_build_storage_vintage_costs.tab
with open(os.path.join(INPUTS_DIRECTORY,
                       "new_build_storage_vintage_costs.tab"), "w") as \
        new_storage_costs_tab_file:
    writer = csv.writer(new_storage_costs_tab_file, delimiter="\t")

    # Write header
    writer.writerow(
        ["new_build_storage", "vintage", "lifetime_yrs",
         "annualized_real_cost_per_mw_yr", "annualized_real_cost_per_mwh_yr"]
    )

    # TODO: select only rows with non NULL for cost per kWh-yr for storage
    # only (not generators), but need to make this more robust
    new_stor_costs = c.execute(
        """SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr * 1000,
        annualized_real_cost_per_kwh_yr * 1000
        FROM new_project_cost
        WHERE annualized_real_cost_per_kwh_yr IS NOT NULL
        AND new_project_scenario_id = {}
        AND period_scenario_id = {}
        AND new_project_cost_scenario_id = {};""".format(
            NEW_PROJECT_SCENARIO_ID, PERIOD_SCENARIO_ID,
            NEW_PROJECT_COST_SCENARIO_ID
        )
    )
    for row in new_stor_costs:
        writer.writerow(row)


if OPTIONAL_MODULE_TRANSMISSION:
    # transmission_lines.tab
    with open(os.path.join(INPUTS_DIRECTORY,
                           "transmission_lines.tab"), "w") as \
            transmission_lines_tab_file:
        writer = csv.writer(transmission_lines_tab_file, delimiter="\t")

        # Are we tracking carbon?
        line_file_optional_headers = list()
        line_db_table_optional_args = {}

        if OPTIONAL_MODULE_CARBON_CAP and OPTIONAL_MODULE_TRACK_CARBON_IMPORTS:
            line_file_optional_headers = [
                "carbon_cap_zone", "carbon_cap_zone_import_direction",
                "tx_co2_intensity_tons_per_mwh"
            ]
            line_db_table_optional_args["select"] = \
                """, carbon_cap_zone, carbon_cap_zone_import_direction,
                tx_co2_intensity_tons_per_mwh """
            line_db_table_optional_args["join"] = \
                """\nJOIN transmission_line_carbon_cap_zones
                USING (load_zone_scenario_id, transmission_line_scenario_id,
                transmission_line)"""
            line_db_table_optional_args["and"] = \
                """\nAND carbon_cap_zone_scenario_id = {}
                AND transmission_line_carbon_cap_zone_scenario_id = {}"""
        else:
            line_db_table_optional_args = {
                "select": "",
                "join": "",
                "and": ""
            }

        # Write header
        writer.writerow(
            ["TRANSMISSION_LINES", "tx_capacity_type", "load_zone_from",
             "load_zone_to"] + line_file_optional_headers
        )

        tx_query = \
            """SELECT transmission_line, tx_capacity_type,
            load_zone_from, load_zone_to""" \
            + line_db_table_optional_args["select"] + \
            """ FROM transmission_lines""" + \
            line_db_table_optional_args["join"] + \
            """
            WHERE load_zone_scenario_id = {}
            AND transmission_line_scenario_id = {} """ + \
            line_db_table_optional_args["and"] + \
            """;"""

        transmission_lines = c.execute(
            tx_query.format(
                LOAD_ZONE_SCENARIO_ID, TRANSMISSION_LINE_SCENARIO_ID,
                CARBON_CAP_ZONE_SCENARIO_ID,
                TRANSMISSION_LINE_CARBON_CAP_ZONE_SCENARIO_ID
            )
        ).fetchall()
        for row in transmission_lines:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
