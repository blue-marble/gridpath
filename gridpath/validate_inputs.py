#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
import csv
import os.path
import sqlite3
import sys
from argparse import ArgumentParser

from gridpath.auxiliary.auxiliary import get_scenario_id_and_name, \
    write_validation_to_database
from gridpath.auxiliary.module_list import determine_modules, load_modules
from gridpath.auxiliary.scenario_chars import OptionalFeatures, SubScenarios, \
    SubProblems


def validate_inputs(subproblems, loaded_modules, subscenarios, conn):
    """"
    For each module, load the inputs from the database and validate them

    :param subproblems: SubProblems object with info on the subproblem/stage
        structure
    :param loaded_modules: list of imported modules (Python <class 'module'>
        objects)
    :param subscenarios: SubScenarios object with all subscenario info
    :param conn: database connection
    :return:
    """

    # TODO: check if we even need database cursor (and subscenarios?)
    #   since presumably we already have our data in the inputs.
    #   need to go through each module's input validation to check this

    # TODO: see if we can do some sort of automatic dtype validation for
    #  each table in the database? Problem is that you don't necessarily want
    #  to check the full table but only the appropriate subscenario

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
                        conn=conn
                    )
                else:
                    pass

            # 2. input validation across modules
            #    make sure geography and projects are in line
            #    ... (see Evernote validation list)
            #    create separate function for each validation that you call here

    # check that SU and SD * timepoint duration is larger than Pmin
    # this requires multiple tables so cross validation?

    # check that specified load zones are actual load zones that are available
    # --> isn't that easy to do w foreign key?


def validate_subscenarios_vs_features(subscenarios, optional_features, conn):
    """
    Check whether features and subscenarios are self-consistent

    :param subscenarios:
    :param optional_features:
    :param conn:
    :return: valid_features: list of features with valid subscenario_ids
    """

    validation_results = []

    subscenario_ids_by_feature = optional_features.subscenario_ids_by_feature
    feature_list = optional_features.determine_feature_list()

    invalid_features = set()
    for feature, subscenario_ids in subscenario_ids_by_feature.items():
        for sc_id in subscenario_ids:
            # If the feature is requested, and the associated subscenarios are
            # not specified, raise a validation error and track invalid feature
            if feature in feature_list and \
                    getattr(subscenarios, sc_id) is None:
                validation_results.append(
                    (subscenarios.SCENARIO_ID,
                     "N/A",
                     sc_id,
                     "scenarios",
                     "Missing subscenario ID",
                     "Requested feature '{}' requires an input for '{}'".format(
                         feature, sc_id
                     )
                     )
                )
                invalid_features.add(feature)
            # If the feature is not requested, and the associated subscenarios
            # are specified, raise a validation error
            elif feature not in feature_list and \
                    getattr(subscenarios, sc_id) is not None:
                validation_results.append(
                    (subscenarios.SCENARIO_ID,
                     "N/A",
                     sc_id,
                     "scenarios",
                     "Unnecessary subscenario ID",
                     "Detected inputs for '{}' while related feature '{}' is not requested".format(
                         sc_id, feature
                     )
                     )
                )

    # Keep track of the valid features. The second phase of the input validation
    # will run module-level input validation that checks the actual input data
    # data related to the valid features (and skips invalid features since
    # these will by definition result in erroneous inputs).
    valid_features = list(set(feature_list) - invalid_features)

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)

    return valid_features


def validate_required_subscenario_ids(subscenarios, conn):
    """
    Check whether the required subscenario_ids are specified in the db
    :param subscenarios:
    :param conn:
    :return: boolean, True if all required subscenario_ids are specified
    """
    validation_results = []
    for sc_id in subscenarios.required_subscenario_ids:
        if getattr(subscenarios, sc_id) is None:
            validation_results.append(
                (subscenarios.SCENARIO_ID,
                 "N/A",
                 sc_id,
                 "scenarios",
                 "Missing required subscenario ID",
                 "'{}' is a required input in the 'scenarios' table".format(
                     sc_id
                 )
                 )
            )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)

    # Return True if all required subscenario_ids are valid (list is empty)
    return not bool(validation_results)


def reset_input_validation(conn, scenario_id):
    """
    Reset input validation: delete old input validation outputs and reset the
    input validation status.
    :param conn: database connection
    :param scenario_id: scenario_id
    :return: 
    """
    c = conn.cursor()
    c.execute(
        """DELETE FROM mod_input_validation
        WHERE scenario_id = {};""".format(str(scenario_id))
    )

    c.execute(
        """UPDATE scenarios
        SET validation_status_id = 0
        WHERE scenario_id = {};""".format(str(scenario_id))
    )

    conn.commit()


def update_validation_status(conn, scenario_id):
    """

    :param conn:
    :param scenario_id:
    :return:
    """
    c = conn.cursor()
    validations = c.execute(
        """SELECT scenario_id 
        FROM mod_input_validation
        WHERE scenario_id = {}""".format(str(scenario_id))
    ).fetchall()

    if validations:
        status = 2
    else:
        status = 1

    c.execute(
        """UPDATE scenarios
        SET validation_status_id = {}
        WHERE scenario_id = {};""".format(str(status), str(scenario_id))
    )

    conn.commit()


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)
    parser.add_argument("--database", help="The database file path.")
    parser.add_argument("--scenario_id",
                        help="The scenario_id from the database.")
    parser.add_argument("--scenario",
                        help="The scenario_name from the database.")
    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def main(args=None):
    """

    :return:
    """
    print("Validating inputs...")

    # Retrieve scenario_id and/or name from args
    if args is None:
        args = sys.argv[1:]
    parsed_arguments = parse_arguments(args=args)

    db_path = parsed_arguments.database
    scenario_id_arg = parsed_arguments.scenario_id
    scenario_name_arg = parsed_arguments.scenario

    # Database
    # If no database is specified, assume script is run from the 'gridpath'
    # directory and the database is in ../db and named io.db
    if db_path is None:
        db_path = os.path.join(os.getcwd(), "..", "db", "io.db")

    if not os.path.isfile(db_path):
        raise OSError(
            "The database file {} was not found. Did you mean to "
            "specify a different database file?".format(
                os.path.abspath(db_path)
            )
        )

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    scenario_id, scenario_name = get_scenario_id_and_name(
        scenario_id_arg=scenario_id_arg,
        scenario_name_arg=scenario_name_arg,
        c=c,
        script="validate_inputs"
    )

    # Reset input validation status and results
    reset_input_validation(conn, scenario_id)

    # Get scenario characteristics (features, subscenarios, subproblems)
    optional_features = OptionalFeatures(cursor=c, scenario_id=scenario_id)
    subscenarios = SubScenarios(cursor=c, scenario_id=scenario_id)
    subproblems = SubProblems(cursor=c, scenario_id=scenario_id)

    # Check whether selected features and subscenario_ids are self-consistent
    # and return the valid features
    valid_features = validate_subscenarios_vs_features(
        subscenarios, optional_features, conn)

    # Check whether required "core" subscenario_ids are specified
    is_valid = validate_required_subscenario_ids(subscenarios, conn)

    # Only do the detailed input validation if all required subscenario_ids
    # are specified (otherwise will get errors when loading data)
    if is_valid:
        # Load modules for features that have valid subscenario_id inputs
        modules_to_use = determine_modules(features=valid_features)
        loaded_modules = load_modules(modules_to_use=modules_to_use)

        # Read in inputs from db and validate inputs for loaded modules
        validate_inputs(subproblems, loaded_modules, subscenarios, conn)
    else:
        print("Missing required subscenario ID(s). "
              "Skipped detailed input validation.")

    # Update validation status:
    update_validation_status(conn, subscenarios.SCENARIO_ID)


if __name__ == "__main__":
    main()
