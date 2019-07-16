#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
import csv
import os.path
import sqlite3
import sys
from argparse import ArgumentParser

from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from gridpath.auxiliary.module_list import determine_modules, load_modules
from gridpath.auxiliary.scenario_chars import OptionalFeatures, SubScenarios, \
    SubProblems

# 3 STEP PROCESS
# 1. load inputs for each module. Store into dict with module name as key
# 2. OPTIONAL - validate inputs (can stop here)
# 3. write modules for each dict
# TODO: is this too memory intensive?
#   Does this help us eventually skip the .tab files and work with a giant dict?


def load_inputs_from_database(subproblems, loaded_modules, subscenarios,
                              cursor):
    """
    Load all database inputs into a dictionary with the module name as key
    and the module-specific raw inputs as value.

    NOTE: for modules with submodules, such as capacity_types, the dictionary
    will be nested.

    :param subproblems: SubProblems object with info on the subproblem/stage
        structure
    :param loaded_modules: list of imported modules (Python <class 'module'>
        objects)
    :param subscenarios: SubScenarios object with all subscenario info

    :param cursor: database cursor
    :return:
    """

    # TODO: initialize an empty dict with a full nested structure with all
    #  modules somewhere beforehand and simply fill it up?
    #  Would make it a bit easier for someone to understand the
    #  data structure and could build in some checks that way?
    inputs = {}

    subproblems_list = subproblems.SUBPROBLEMS
    for subproblem in subproblems_list:
        stages = subproblems.SUBPROBLEM_STAGE_DICT[subproblem]
        for stage in stages:
            nested_inputs = {}
            for m in loaded_modules:
                if hasattr(m, "load_inputs_from_database"):
                    nested_inputs[m.__name__] = m.load_inputs_from_database(
                        subscenarios=subscenarios,
                        subproblem=subproblem,
                        stage=stage,
                        c=cursor
                    )
                else:
                    pass

            # if there are subproblems/stages, inputs dictionary will be nested
            if len(subproblems_list) > 1 and len(stages) > 1:
                inputs[str(subproblem)] = {}
                inputs[str(subproblem)][str(stage)] = nested_inputs
            elif len(subproblems.SUBPROBLEMS) > 1:
                inputs[str(subproblem)] = nested_inputs
            elif len(stages) > 1:
                inputs[str(stage)] = nested_inputs
            else:
                inputs = nested_inputs

    return inputs


# TODO: move validation into separate script similar to get_scenarip_inputs.py?
#   like get get_scenario_inputs.py you will have a separate script that just
#   does the validation
def validate_inputs(subproblems, loaded_modules, inputs, subscenarios, cursor):
    """""
    :param subproblems: SubProblems object with info on the subproblem/stage
        structure
    :param loaded_modules: list of imported modules (Python <class 'module'>
        objects)
    :param inputs: dictionary with inputs (loaded from database) by module name
    :param subscenarios: SubScenarios object with all subscenario info
    :param cursor: database cursor
    :return:
    """

    # TODO: check if we even need database cursor and (and subscenarios?)
    #   since presumably we already have our data in the inputs.
    #   need to go through each module's input validation to check this

    # TODO: do we need to pass a data container that collects all the input
    #   validation outputs (since we don't want to print)?

    subproblems_list = subproblems.SUBPROBLEMS
    for subproblem in subproblems_list:
        stages = subproblems.SUBPROBLEM_STAGE_DICT[subproblem]
        for stage in stages:

            # if there are subproblems/stages, inputs dictionary will be nested
            if len(subproblems_list) > 1 and len(stages) > 1:
                relevant_inputs = inputs[str(subproblem)][str(stage)]
            elif len(subproblems.SUBPROBLEMS) > 1:
                relevant_inputs = inputs[str(subproblem)]
            elif len(stages) > 1:
                relevant_inputs = inputs[str(stage)]
            else:
                relevant_inputs = inputs

            # 1. input validation within each module
            for m in loaded_modules:
                if hasattr(m, "validate_inputs"):
                    m.validate_inputs(
                        inputs=relevant_inputs,
                        subscenarios=subscenarios,
                        c=cursor
                    )
                else:
                    pass

            # 2. input validation across modules
            #    validate_operational_and_capacity_types:
            #    check that you don't combine new build with continuous or
            #    binary commit
            #
            #    make sure geography and projects are in line
            #    ... (see Evernote validation list)
            #    create separate function for each validation that you call here


# TODO: verify there is no complicated pre-processing of inputs before writing
#   them into .tab files that would not allow the current structure
def write_model_inputs(subproblems, loaded_modules, inputs, scenario_directory,
                       subscenarios):
    """
    After loading the inputs from the database into a dictionary, write out the
    the inputs into .tab files, which will be used to construct the optimization
    problem.

    For each module, pass the inputs to the 'write_model_inputs' function and
    write out the inputs (if applicable).

    :param subproblems: SubProblems object with info on the subproblem/stage
        structure
    :param loaded_modules: list of imported modules (Python <class 'module'>
        objects)
    :param inputs: dictionary with inputs (loaded from database) by module name
    :param scenario_directory: local scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :return:
    """
    subproblems_list = subproblems.SUBPROBLEMS
    # create subproblem.csv file for subproblems if appropriate:
    if len(subproblems_list) > 1:
        write_subproblems_csv(scenario_directory, subproblems_list)

    for subproblem in subproblems_list:
        stages = subproblems.SUBPROBLEM_STAGE_DICT[subproblem]
        # create subproblem.csv file for stages if appropriate:
        if len(stages) > 1:
            target_directory = os.path.join(scenario_directory, str(subproblem))
            write_subproblems_csv(target_directory, stages)

        for stage in stages:
            # if there are subproblems/stages, inputs from database will be
            # nested dictioanry and and inputs directory will be nested folder
            if len(subproblems_list) > 1 and len(stages) > 1:
                inputs_directory = os.path.join(scenario_directory,
                                                str(subproblem),
                                                str(stage),
                                                "inputs")
                relevant_inputs = inputs[str(subproblem)][str(stage)]
            elif len(subproblems.SUBPROBLEMS) > 1:
                inputs_directory = os.path.join(scenario_directory,
                                                str(subproblem),
                                                "inputs")
                relevant_inputs = inputs[str(subproblem)]
            elif len(stages) > 1:
                inputs_directory = os.path.join(scenario_directory,
                                                str(stage),
                                                "inputs")
                relevant_inputs = inputs[str(stage)]
            else:
                inputs_directory = os.path.join(scenario_directory,
                                                "inputs")
            if not os.path.exists(inputs_directory):
                os.makedirs(inputs_directory)

            delete_prior_inputs(inputs_directory)

            # Write model input .tab files for each of the loaded_modules if
            # appropriate. Note that all input files are saved in the
            # input_directory, even the non-temporal inputs that are not
            # dependent on the subproblem or stage. This simplifies the file
            # structure at the expense ofunnecessarily duplicating non-temporal
            # input files such as projects.tab.
            for m in loaded_modules:
                if hasattr(m, "write_model_inputs"):
                    m.write_model_inputs(
                        inputs=relevant_inputs,
                        inputs_directory=inputs_directory,
                        subscenarios=subscenarios
                    )
                else:
                    pass


def delete_prior_inputs(inputs_directory):
    """
    Delete all .tab files that may exist in the specified directory
    :param inputs_directory: local directory where .tab files are saved
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


def write_subproblems_csv(scenario_directory, subproblems):
    """
    Write the subproblems.csv file that will be used when solving multiple
    subproblems/stages in 'production cost' mode.
    :return:
    """

    if not os.path.exists(scenario_directory):
        os.makedirs(scenario_directory)
    with open(os.path.join(scenario_directory, "subproblems.csv"), "w") as \
            subproblems_csv_file:
        writer = csv.writer(subproblems_csv_file, delimiter=",")

        # Write header
        writer.writerow(["subproblems"])

        for subproblem in subproblems:
            writer.writerow([subproblem])


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
            ["of_spinning_reserves",
             optional_features.OPTIONAL_FEATURE_SPINNING_RESERVES]
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
        writer.writerow(
            ["of_local_capacity",
             optional_features.OPTIONAL_FEATURE_LOCAL_CAPACITY]
        )

        # Subscenarios
        writer.writerow(["temporal_scenario_id",
                         subscenarios.TEMPORAL_SCENARIO_ID])
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
        writer.writerow(["local_capacity_zone_scenario_id",
                         subscenarios.LOCAL_CAPACITY_ZONE_SCENARIO_ID])
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
        writer.writerow(["project_spinning_reserves_ba_scenario_id",
                         subscenarios.PROJECT_SPINNING_RESERVES_BA_SCENARIO_ID]
                        )
        writer.writerow(["project_rps_zone_scenario_id",
                         subscenarios.PROJECT_RPS_ZONE_SCENARIO_ID])
        writer.writerow(["project_carbon_cap_zone_scenario_id",
                         subscenarios.PROJECT_CARBON_CAP_ZONE_SCENARIO_ID])
        writer.writerow(["project_prm_zone_scenario_id",
                         subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID])
        writer.writerow(["project_elcc_chars_scenario_id",
                         subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID])
        writer.writerow(["project_local_capacity_zone_scenario_id",
                         subscenarios.PROJECT_LOCAL_CAPACITY_ZONE_SCENARIO_ID])
        writer.writerow(["project_local_capacity_chars_scenario_id",
                         subscenarios.PROJECT_LOCAL_CAPACITY_CHARS_SCENARIO_ID]
                        )
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
        writer.writerow(["prm_energy_only_scenario_id",
                         subscenarios.PRM_ENERGY_ONLY_SCENARIO_ID])
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
        writer.writerow(["spinning_reserves_scenario_id",
                         subscenarios.SPINNING_RESERVES_SCENARIO_ID])
        writer.writerow(["rps_target_scenario_id",
                         subscenarios.RPS_TARGET_SCENARIO_ID])
        writer.writerow(["carbon_cap_target_scenario_id",
                         subscenarios.CARBON_CAP_TARGET_SCENARIO_ID])
        writer.writerow(["prm_requirement_scenario_id",
                         subscenarios.PRM_REQUIREMENT_SCENARIO_ID])
        writer.writerow(["local_capacity_requirement_scenario_id",
                         subscenarios.LOCAL_CAPACITY_REQUIREMENT_SCENARIO_ID])
        writer.writerow(["elcc_surface_scenario_id",
                         subscenarios.ELCC_SURFACE_SCENARIO_ID])
        writer.writerow(["tuning_scenario_id",
                         subscenarios.TUNING_SCENARIO_ID])

    
def main(args=None):
    """

    :return:
    """
    print("Getting inputs...")

    # Retrieve scenario_id and/or name from args
    if args is None:
        args = sys.argv[1:]
    parsed_arguments = parse_arguments(args=args)
    scenario_id_arg = parsed_arguments.scenario_id
    scenario_name_arg = parsed_arguments.scenario

    # Connect to database; For now, assume script is run from root directory
    # and the the database is ./db and named io.db
    io = sqlite3.connect(os.path.join(os.getcwd(), 'db', 'io.db'))
    c = io.cursor()

    scenario_id, scenario_name = get_scenario_id_and_name(
        scenario_id_arg=scenario_id_arg,
        scenario_name_arg=scenario_name_arg,
        c=c,
        script="get_scenario_inputs"
    )

    # Make scenario directories
    scenarios_main_directory = os.path.join(
        os.getcwd(), "scenarios")
    if not os.path.exists(scenarios_main_directory):
        os.makedirs(scenarios_main_directory)

    scenario_directory = os.path.join(
        scenarios_main_directory, str(scenario_name)
    )
    if not os.path.exists(scenario_directory):
        os.makedirs(scenario_directory)

    # Delete input files that may have existed before to avoid phantom inputs
    delete_prior_inputs(scenario_directory)

    # Get scenario characteristics (features, subscenarios, subproblems)
    optional_features = OptionalFeatures(cursor=c, scenario_id=scenario_id)
    subscenarios = SubScenarios(cursor=c, scenario_id=scenario_id)
    subproblems = SubProblems(cursor=c, scenario_id=scenario_id)

    # Write features.csv file with optional features and use this feature
    # file to determine what modules to load for GridPath
    feature_list = optional_features.determine_feature_list()
    write_features_csv(scenario_directory, feature_list)
    modules_to_use = determine_modules(scenario_directory=scenario_directory)
    loaded_modules = load_modules(modules_to_use=modules_to_use)

    # Read in appropriate inputs from database
    inputs = load_inputs_from_database(loaded_modules, subscenarios, c)
    # Validate inputs
    # TODO: add option to skip this
    validate_inputs(inputs, loaded_modules, subscenarios, c)
    # Write .tab file model inputs
    # TODO: add option to stop here (if only validating)
    write_model_inputs(inputs, inputs_directory, loaded_modules, subscenarios)

    # Save the scenario ID to a file
    save_scenario_id(scenario_directory=scenario_directory,
                     scenario_id=scenario_id)
    # Write full scenario description
    write_scenario_description(
        scenario_directory=scenario_directory, 
        scenario_id=scenario_id, scenario_name=scenario_name,
        optional_features=optional_features, subscenarios=subscenarios
    )


if __name__ == "__main__":
    main()
