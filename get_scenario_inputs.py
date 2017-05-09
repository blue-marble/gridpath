#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
import sqlite3
import sys
from argparse import ArgumentParser

from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from gridpath.auxiliary.module_list import determine_modules, load_modules
from gridpath.auxiliary.scenario_chars import OptionalFeatures, SubScenarios


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
            m.get_inputs_from_database(
                subscenarios=subscenarios, c=cursor,
                inputs_directory=inputs_directory
            )
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


def parse_arguments(args):
    """
    Parse arguments
    :param args: 
    :return: 
    """
    parser = ArgumentParser(add_help=True)
    parser.add_argument("--scenario_id",
                        help="The scenario_id from the database.")
    parser.add_argument("--scenario",
                        help="The scenario_name from the database.")
    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def write_features_csv(scenario_directory, feature_list):
    """
    Write the features.csv file that will be used to determine which 
    GridPath modules to include
    :return: 
    """
    with open(os.path.join(scenario_directory, "features.csv"), "w") as \
            features_csv_file:
        writer = csv.writer(features_csv_file, delimiter=",")

        # Write header
        writer.writerow(["features"])

        for feature in feature_list:
            writer.writerow([feature])


def save_scenario_id(scenario_directory, scenario_id):
    """
    Save the scenario ID to file
    :param scenario_directory: 
    :param scenario_id: 
    :return: 
    """
    with open(os.path.join(scenario_directory, "scenario_id.txt"), "w") as \
            scenario_id_file:
        scenario_id_file.write(str(scenario_id))


def write_scenario_description(
        scenario_directory, scenario_id, scenario_name, 
        optional_features, subscenarios
):
    """
    
    :param scenario_directory: 
    :param scenario_id: 
    :param scenario_name: 
    :param optional_features: 
    :param subscenarios: 
    :return: 
    """
    with open(os.path.join(scenario_directory, "scenario_description.csv"),
              "w") as \
            scenario_description_file:
        writer = csv.writer(scenario_description_file, delimiter=",")

        # Scenario ID and scenario name
        writer.writerow(
            ["scenario_id", scenario_id]
        )
        writer.writerow(
            ["scenario_name", scenario_name]
        )

        # Optional features
        writer.writerow(
            ["of_fuels", optional_features.OPTIONAL_FEATURE_FUELS]
        )
        writer.writerow(
            ["of_multi_stage", optional_features.OPTIONAL_FEATURE_MULTI_STAGE]
        )
        writer.writerow(
            ["of_transmission",
             optional_features.OPTIONAL_FEATURE_TRANSMISSION]
        )
        writer.writerow(
            ["of_transmission_hurdle_rates",
             optional_features.OPTIONAL_FEATURE_TRANSMISSION_HURDLE_RATES]
        )
        writer.writerow(
            ["of_simultaneous_flow_limits",
             optional_features.OPTIONAL_FEATURE_SIMULTANEOUS_FLOW_LIMITS]
        )
        writer.writerow(
            ["of_lf_reserves_up",
             optional_features.OPTIONAL_FEATURE_LF_RESERVES_UP]
        )
        writer.writerow(
            ["of_lf_reserves_down",
             optional_features.OPTIONAL_FEATURE_LF_RESERVES_DOWN]
        )
        writer.writerow(
            ["of_regulation_up",
             optional_features.OPTIONAL_FEATURE_REGULATION_UP]
        )
        writer.writerow(
            ["of_regulation_down",
             optional_features.OPTIONAL_FEATURE_REGULATION_DOWN]
        )
        writer.writerow(
            ["of_frequency_response",
             optional_features.OPTIONAL_FEATURE_FREQUENCY_RESPONSE]
        )
        writer.writerow(
            ["of_rps", optional_features.OPTIONAL_FEATURE_RPS]
        )
        writer.writerow(
            ["of_carbon_cap", optional_features.OPTIONAL_FEATURE_CARBON_CAP]
        )
        writer.writerow(
            ["of_track_carbon_imports",
             optional_features.OPTIONAL_FEATURE_TRACK_CARBON_IMPORTS]
        )
        writer.writerow(
            ["of_prm", optional_features.OPTIONAL_FEATURE_PRM]
        )
        writer.writerow(
            ["of_elcc_surface",
             optional_features.OPTIONAL_FEATURE_ELCC_SURFACE]
        )

        # Subscenarios
        writer.writerow(["timepoint_scenario_id",
                         subscenarios.TIMEPOINT_SCENARIO_ID])
        writer.writerow(["load_zone_scenario_id",
                         subscenarios.LOAD_ZONE_SCENARIO_ID])
        writer.writerow(["lf_reserves_up_ba_scenario_id",
                         subscenarios.LF_RESERVES_UP_BA_SCENARIO_ID])
        writer.writerow(["lf_reserves_down_ba_scenario_id",
                         subscenarios.LF_RESERVES_DOWN_BA_SCENARIO_ID])
        writer.writerow(["frequency_response_ba_scenario_id",
                         subscenarios.FREQUENCY_RESPONSE_BA_SCENARIO_ID])
        writer.writerow(["rps_zone_scenario_id",
                         subscenarios.RPS_ZONE_SCENARIO_ID])
        writer.writerow(["carbon_cap_zone_scenario_id",
                         subscenarios.CARBON_CAP_ZONE_SCENARIO_ID])
        writer.writerow(["prm_zone_scenario_id",
                         subscenarios.PRM_ZONE_SCENARIO_ID])
        writer.writerow(["project_portfolio_scenario_id",
                         subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID])
        writer.writerow(["project_load_zone_scenario_id",
                         subscenarios.PROJECT_LOAD_ZONE_SCENARIO_ID])
        writer.writerow(["project_lf_reserves_up_ba_scenario_id",
                         subscenarios.PROJECT_LF_RESERVES_UP_BA_SCENARIO_ID])
        writer.writerow(["project_lf_reserves_down_ba_scenario_id",
                         subscenarios.PROJECT_LF_RESERVES_DOWN_BA_SCENARIO_ID])
        writer.writerow(["project_frequency_response_ba_scenario_id",
                         subscenarios.PROJECT_FREQUENCY_RESPONSE_BA_SCENARIO_ID
                         ])
        writer.writerow(["project_rps_zone_scenario_id",
                         subscenarios.PROJECT_RPS_ZONE_SCENARIO_ID])
        writer.writerow(["project_carbon_cap_zone_scenario_id",
                         subscenarios.PROJECT_CARBON_CAP_ZONE_SCENARIO_ID])
        writer.writerow(["project_prm_zone_scenario_id",
                         subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID])
        writer.writerow(["project_elcc_chars_scenario_id",
                         subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID])
        writer.writerow(["project_existing_capacity_scenario_id",
                         subscenarios.PROJECT_EXISTING_CAPACITY_SCENARIO_ID])
        writer.writerow(["project_existing_fixed_cost_scenario_id",
                         subscenarios.PROJECT_EXISTING_FIXED_COST_SCENARIO_ID])
        writer.writerow(["project_operational_chars_scenario_id",
                         subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID])
        writer.writerow(["project_availability_scenario_id",
                         subscenarios.PROJECT_AVAILABILITY_SCENARIO_ID])
        writer.writerow(["fuel_scenario_id",
                         subscenarios.FUEL_SCENARIO_ID])
        writer.writerow(["fuel_price_scenario_id",
                         subscenarios.FUEL_PRICE_SCENARIO_ID])
        writer.writerow(["project_new_cost_scenario_id",
                         subscenarios.PROJECT_NEW_COST_SCENARIO_ID])
        writer.writerow(["project_new_potential_scenario_id",
                         subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID])
        writer.writerow(["capacity_threshold_cost_scenario_id",
                         subscenarios.CAPACITY_THRESHOLD_COST_SCENARIO_ID])
        writer.writerow(["transmission_portfolio_scenario_id",
                         subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID])
        writer.writerow(["transmission_load_zone_scenario_id",
                         subscenarios.TRANSMISSION_LOAD_ZONE_SCENARIO_ID])
        writer.writerow(["transmission_existing_capacity_scenario_id",
                         subscenarios.
                        TRANSMISSION_EXISTING_CAPACITY_SCENARIO_ID])
        writer.writerow(["transmission_operational_chars_scenario_id",
                         subscenarios.
                        TRANSMISSION_OPERATIONAL_CHARS_SCENARIO_ID])
        writer.writerow(["transmission_hurdle_rate_scenario_id",
                         subscenarios.TRANSMISSION_HURDLE_RATE_SCENARIO_ID])
        writer.writerow(["transmission_carbon_cap_zone_scenario_id",
                         subscenarios.TRANSMISSION_CARBON_CAP_ZONE_SCENARIO_ID]
                        )
        writer.writerow(["transmission_simultaneous_flow_limit_scenario_id",
                         subscenarios.
                        TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_SCENARIO_ID])
        writer.writerow([
            "transmission_simultaneous_flow_limit_line_group_scenario_id",
            subscenarios.TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_LINE_SCENARIO_ID]
        )
        writer.writerow(["load_scenario_id",
                         subscenarios.LOAD_SCENARIO_ID])
        writer.writerow(["lf_reserves_up_scenario_id",
                         subscenarios.LF_RESERVES_UP_SCENARIO_ID])
        writer.writerow(["lf_reserves_down_scenario_id",
                         subscenarios.LF_RESERVES_DOWN_SCENARIO_ID])
        writer.writerow(["frequency_response_scenario_id",
                         subscenarios.FREQUENCY_RESPONSE_SCENARIO_ID])
        writer.writerow(["rps_target_scenario_id",
                         subscenarios.RPS_TARGET_SCENARIO_ID])
        writer.writerow(["carbon_cap_target_scenario_id",
                         subscenarios.CARBON_CAP_TARGET_SCENARIO_ID])
        writer.writerow(["prm_requirement_scenario_id",
                         subscenarios.PRM_REQUIREMENT_SCENARIO_ID])
        writer.writerow(["elcc_surface_scenario_id",
                         subscenarios.ELCC_SURFACE_SCENARIO_ID])
        writer.writerow(["tuning_scenario_id",
                         subscenarios.TUNING_SCENARIO_ID])

    
def main(args=None):
    """

    :return:
    """
    print("Getting inputs...")

    if args is None:
        args = sys.argv[1:]

    parsed_arguments = parse_arguments(args=args)

    scenario_id_arg = parsed_arguments.scenario_id
    scenario_name_arg = parsed_arguments.scenario

    # For now, assume script is run from root directory and the the
    # database is ./db and named io.db
    io = sqlite3.connect(
        os.path.join(os.getcwd(), 'db', 'io.db')
    )
    c = io.cursor()

    scenario_id, scenario_name = get_scenario_id_and_name(
        scenario_id_arg=scenario_id_arg, scenario_name_arg=scenario_name_arg,
        c=c, script="get_scenario_inputs"
    )

    # Make inputs directory
    scenarios_main_directory = os.path.join(
        os.getcwd(), "scenarios")
    if not os.path.exists(scenarios_main_directory):
        os.makedirs(scenarios_main_directory)

    scenario_directory = os.path.join(
        scenarios_main_directory, str(scenario_name)
    )
    if not os.path.exists(scenario_directory):
        os.makedirs(scenario_directory)

    inputs_directory = os.path.join(
        scenario_directory, "inputs")
    if not os.path.exists(inputs_directory):
        os.makedirs(inputs_directory)

    # Delete input files that may have existed before to avoid phantom inputs
    delete_prior_inputs(inputs_directory)

    # Save the scenario ID to a file
    save_scenario_id(
        scenario_directory=scenario_directory, scenario_id=scenario_id
    )

    # What optional features are needed for this scenario
    optional_features = OptionalFeatures(cursor=c, scenario_id=scenario_id)
    feature_list = optional_features.determine_feature_list()

    # Write the features file that is used to determine which GridPath 
    # modules to include
    write_features_csv(
        scenario_directory=scenario_directory, feature_list=feature_list
    )
    
    # Determine features
    modules_to_use = determine_modules(scenario_directory=scenario_directory)
    loaded_modules = load_modules(modules_to_use=modules_to_use)
    subscenarios = SubScenarios(cursor=c, scenario_id=scenario_id)
    get_inputs_from_database(loaded_modules, subscenarios, c, inputs_directory)

    # Write full scenario description
    write_scenario_description(
        scenario_directory=scenario_directory, 
        scenario_id=scenario_id, scenario_name=scenario_name,
        optional_features=optional_features, subscenarios=subscenarios
    )


if __name__ == "__main__":
    main()
