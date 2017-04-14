#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from argparse import ArgumentParser
import csv
import os.path
import sqlite3
import sys

from gridpath.auxiliary.module_list import get_modules, load_modules


# Get subscenarios
class SubScenarios:
    def __init__(self, cursor):
        self.TIMEPOINT_SCENARIO_ID = cursor.execute(
            """SELECT timepoint_scenario_id
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

        self.FREQUENCY_RESPONSE_BA_SCENARIO_ID = cursor.execute(
            """SELECT frequency_response_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.RPS_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT rps_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.CARBON_CAP_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT carbon_cap_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.PROJECT_PORTFOLIO_SCENARIO_ID = cursor.execute(
            """SELECT project_portfolio_scenario_id
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

        self.PROJECT_FREQUENCY_RESPONSE_BA_SCENARIO_ID = cursor.execute(
            """SELECT project_frequency_response_ba_scenario_id
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

        self.PROJECT_EXISTING_CAPACITY_SCENARIO_ID = cursor.execute(
            """SELECT project_existing_capacity_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.PROJECT_EXISTING_FIXED_COST_SCENARIO_ID = cursor.execute(
            """SELECT project_existing_fixed_cost_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.PROJECT_NEW_COST_SCENARIO_ID = cursor.execute(
            """SELECT project_new_cost_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.PROJECT_NEW_POTENTIAL_SCENARIO_ID = cursor.execute(
            """SELECT project_new_potential_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID = cursor.execute(
            """SELECT project_operational_chars_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.FUEL_SCENARIO_ID = cursor.execute(
            """SELECT fuel_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.FUEL_PRICE_SCENARIO_ID = cursor.execute(
            """SELECT fuel_price_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_PORTFOLIO_SCENARIO_ID = cursor.execute(
            """SELECT transmission_portfolio_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_LOAD_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT transmission_load_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_EXISTING_CAPACITY_SCENARIO_ID = cursor.execute(
            """SELECT transmission_existing_capacity_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_OPERATIONAL_CHARS_SCENARIO_ID = cursor.execute(
            """SELECT transmission_operational_chars_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_HURDLE_RATE_SCENARIO_ID = cursor.execute(
            """SELECT transmission_hurdle_rate_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_CARBON_CAP_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT transmission_carbon_cap_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_SCENARIO_ID = cursor.execute(
            """SELECT transmission_simultaneous_flow_limit_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_LINE_SCENARIO_ID = \
            cursor.execute(
                """SELECT
                transmission_simultaneous_flow_limit_line_group_scenario_id
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

        self.FREQUENCY_RESPONSE_SCENARIO_ID = cursor.execute(
            """SELECT frequency_response_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.RPS_TARGET_SCENARIO_ID = cursor.execute(
            """SELECT rps_target_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.CARBON_CAP_TARGET_SCENARIO_ID = cursor.execute(
            """SELECT carbon_cap_target_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]

        self.TUNING_SCENARIO_ID = cursor.execute(
            """SELECT tuning_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(SCENARIO_ID)
        ).fetchone()[0]


def get_inputs_from_database(loaded_modules, subscenarios, cursor,
                             inputs_directory):
    """

    :param loaded_modules:
    :param subscenarios:
    :param cursor:
    :param inputs_directory:
    :return:
    """
    for m in loaded_modules:
        if hasattr(m, "get_inputs_from_database"):
            m.get_inputs_from_database(subscenarios, cursor, inputs_directory)
        else:
            pass


def delete_prior_inputs(inputs_directory):
    """
    Delete all .tab files that may exist in the inputs directory
    :param inputs_directory: 
    :return: 
    """
    prior_input_tab_files = [
        f for f in os.listdir(inputs_directory) if f.endswith('.tab')
    ]

    for f in prior_input_tab_files:
        os.remove(os.path.join(inputs_directory, f))


if __name__ == "__main__":
    arguments = sys.argv[1:]
    parser = ArgumentParser(add_help=True)
    parser.add_argument("--scenario_id",
                        help="The scenario_id from the database.")
    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    SCENARIO_ID = parsed_arguments.scenario_id

    # For now, assume script is run from root directory and the the
    # database is ./db and named io.db
    io = sqlite3.connect(
        os.path.join(os.getcwd(), 'db', 'io.db')
    )
    c = io.cursor()

    # Get scenario name and make inputs directory
    SCENARIO_NAME = c.execute(
        """SELECT scenario_name
           FROM scenarios
           WHERE scenario_id = {};""".format(SCENARIO_ID)
    ).fetchone()[0]

    SCENARIOS_MAIN_DIRECTORY = os.path.join(
        os.getcwd(), "scenarios")
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

    # Delete input files that may have existed before to avoid phantom inputs
    delete_prior_inputs(INPUTS_DIRECTORY)

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

    OPTIONAL_MODULE_TRANSMISSION_HURDLE_RATES = c.execute(
        """SELECT om_transmission_hurdle_rates
           FROM scenarios
           WHERE scenario_id = {};""".format(SCENARIO_ID)
    ).fetchone()[0]
    if OPTIONAL_MODULE_TRANSMISSION_HURDLE_RATES:
        MODULE_LIST.append("transmission_hurdle_rates")

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

    OPTIONAL_MODULE_FREQUENCY_RESPONSE = c.execute(
        """SELECT om_frequency_response
           FROM scenarios
           WHERE scenario_id = {};""".format(SCENARIO_ID)
    ).fetchone()[0]
    if OPTIONAL_MODULE_FREQUENCY_RESPONSE:
        MODULE_LIST.append("frequency_response")

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

    MODULES_TO_USE = get_modules(SCENARIO_DIRECTORY)
    LOADED_MODULES = load_modules(MODULES_TO_USE)
    SUBSCENARIOS = SubScenarios(cursor=c)
    get_inputs_from_database(LOADED_MODULES, SUBSCENARIOS, c, INPUTS_DIRECTORY)
