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


def validate_inputs(subproblems, loaded_modules, subscenarios, cursor):
    """"
    For each module, load the inputs from the database and validate them

    :param subproblems: SubProblems object with info on the subproblem/stage
        structure
    :param loaded_modules: list of imported modules (Python <class 'module'>
        objects)
    :param subscenarios: SubScenarios object with all subscenario info
    :param cursor: database cursor
    :return:
    """

    # TODO: check if we even need database cursor (and subscenarios?)
    #   since presumably we already have our data in the inputs.
    #   need to go through each module's input validation to check this

    # TODO: do we need to pass a data container that collects all the input
    #   validation outputs (since we don't want to print)?
    #   dictionary could work, see project/__init__

    # TODO: output a general validation status. If the data container is empty
    #   i.e. no invalid inputs, return True, otherwise false

    subproblems_list = subproblems.SUBPROBLEMS
    for subproblem in subproblems_list:
        stages = subproblems.SUBPROBLEM_STAGE_DICT[subproblem]
        for stage in stages:
            # 1. input validation within each module
            for m in loaded_modules:
                if hasattr(m, "validate_inputs"):
                    m.validate_inputs(
                        subscenarios=subscenarios,
                        subproblem=subproblem,
                        stage=stage,
                        c=cursor
                    )
                else:
                    pass

            # 2. input validation across modules
            #    make sure geography and projects are in line
            #    ... (see Evernote validation list)
            #    create separate function for each validation that you call here


    # check that must-run and no_commit have only one segment, i.e. constant
    # heat rate
    # This requires checking other tables so is a cross validation!

    # check that SU and SD * timepoint duration is larger than Pmin
    # this requires multiple tables so cross validation?


# TODO: add this somewhere?
def delete_prior_input_validation(c):
    """
    Delete old input validation outputs
    :param c: database cursor
    :return: 
    """
    query = """DELETE FROM mod_input_validation;"""
    c.execute(query)


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

    
def main(args=None):
    """

    :return:
    """
    print("Validating inputs...")

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
        script="validate_inputs"
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

    # Delete validation files that may have existed before to avoid phantom validations
    delete_prior_input_validation(c)
    io.commit()

    # Get scenario characteristics (features, subscenarios, subproblems)
    optional_features = OptionalFeatures(cursor=c, scenario_id=scenario_id)
    subscenarios = SubScenarios(cursor=c, scenario_id=scenario_id)
    subproblems = SubProblems(cursor=c, scenario_id=scenario_id)

    # Determine requested features and use this to determine what modules to
    # load for Gridpath
    feature_list = optional_features.determine_feature_list()
    modules_to_use = determine_modules(features=feature_list)
    loaded_modules = load_modules(modules_to_use=modules_to_use)

    # Read in appropriate inputs from database and validate inputs
    validate_inputs(subproblems, loaded_modules, subscenarios, c)

    # Commit changes to database
    # --> input validation populates mod_input_validation
    io.commit()


if __name__ == "__main__":
    main()
