#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
import os.path
import sqlite3
import sys
from argparse import ArgumentParser

from db.common_functions import connect_to_database
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


def validate_subscenario_ids(subscenarios, optional_features, conn):
    """
    Check whether subscenarios_ids are consistent with:
     - core required subscenario_ids
     - data dependent subscenario_ids (e.g. new build)
     - optional features
    data.

    :param subscenarios:
    :param optional_features:
    :param conn:
    :return: Boolean, True is all subscenario IDs are valid.
    """

    valid_core = validate_required_subscenario_ids(subscenarios, conn)

    if valid_core:
        valid_data_dependent = validate_data_dependent_subscenario_ids(
            subscenarios, conn)
    else:
        valid_data_dependent = False

    valid_feature = validate_feature_subscenario_ids(
        subscenarios, optional_features, conn)

    return valid_core and valid_data_dependent and valid_feature


def validate_feature_subscenario_ids(subscenarios, optional_features, conn):
    """

    :param subscenarios:
    :param optional_features:
    :param conn:
    :return:
    """

    subscenario_ids_by_feature = subscenarios.subscenario_ids_by_feature
    feature_list = optional_features.determine_feature_list()

    validation_results = []
    for feature, subscenario_ids in subscenario_ids_by_feature.items():
        if feature not in ["core", "optional", "data_dependent"]:
            for sc_id in subscenario_ids:
                # If the feature is requested, and the associated subscenarios
                # are not specified, raise a validation error
                if feature in feature_list and \
                        getattr(subscenarios, sc_id) is None:
                    validation_results.append(
                        (subscenarios.SCENARIO_ID,
                         "N/A",
                         "N/A",
                         "N/A",
                         sc_id,
                         "scenarios",
                         "Missing subscenario ID",
                         "Requested feature '{}' requires an input for '{}'"
                         .format(feature, sc_id)
                         )
                    )
                # If the feature is not requested, and the associated
                # subscenarios are specified, raise a validation error
                elif feature not in feature_list and \
                        getattr(subscenarios, sc_id) is not None:
                    validation_results.append(
                        (subscenarios.SCENARIO_ID,
                         "N/A",
                         "N/A",
                         "N/A",
                         sc_id,
                         "scenarios",
                         "Unnecessary subscenario ID",
                         "Detected inputs for '{}' while related feature '{}' "
                         "is not requested".format(sc_id, feature)
                         )
                    )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)

    # Return True if all required subscenario_ids are valid (list is empty)
    return not bool(validation_results)


def validate_required_subscenario_ids(subscenarios, conn):
    """
    Check whether the required subscenario_ids are specified in the db
    :param subscenarios:
    :param conn:
    :return: boolean, True if all required subscenario_ids are specified
    """

    required_subscenario_ids = subscenarios.subscenario_ids_by_feature["core"]

    validation_results = []
    for sc_id in required_subscenario_ids:
        if getattr(subscenarios, sc_id) is None:
            validation_results.append(
                (subscenarios.SCENARIO_ID,
                 "N/A",
                 "N/A",
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


def validate_data_dependent_subscenario_ids(subscenarios, conn):
    """

    :param subscenarios:
    :param conn:
    :return:
    """

    assert subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID is not None
    c = conn.cursor()
    req_cap_types = set(subscenarios.get_required_capacity_type_modules(c))

    new_build_types = {
        "new_build_generator,",
        "new_build_storage",
        "new_shiftable_load_supply_curve"
    }
    existing_build_types = {
        "existing_gen_no_economic_retirement",
        "existing_gen_binary_economic_retirement",
        "existing_gen_linear_economic_retirement"
    }
    load_shift_types = {
        "new_shiftable_load_supply_curve"
    }

    # Determine required subscenario_ids
    sc_id_type = []
    if bool(req_cap_types & new_build_types):
        sc_id_type.append(("PROJECT_NEW_COST_SCENARIO_ID",
                           "New Build"))
    if bool(req_cap_types & existing_build_types):
        sc_id_type.append(("PROJECT_EXISTING_CAPACITY_SCENARIO_ID",
                           "Existing"))
        sc_id_type.append(("PROJECT_EXISTING_FIXED_COST_SCENARIO_ID",
                           "Existing"))
    if bool(req_cap_types & load_shift_types):
        sc_id_type.append(("PROJECT_NEW_POTENTIAL_SCENARIO_ID",
                           "New Shiftable Load Supply Curve"))

    # Check whether required subscenario_ids are present
    validation_results = []
    for sc_id, build_type in sc_id_type:
        if getattr(subscenarios, sc_id) is None:
            validation_results.append(
                (subscenarios.SCENARIO_ID,
                 "N/A",
                 "N/A",
                 "N/A",
                 sc_id,
                 "scenarios",
                 "Missing data dependent subscenario ID",
                 "'{}' is a required input in the 'scenarios' table if there "
                 "are '{}' resources in the portfolio"
                 .format(sc_id, build_type)
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

    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()
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

    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
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

    # Check whether subscenario_ids are valid
    is_valid = validate_subscenario_ids(subscenarios, optional_features, conn)

    # Only do the detailed input validation if all required subscenario_ids
    # are specified (otherwise will get errors when loading data)
    if is_valid:
        # Load modules for all requested features
        feature_list = optional_features.determine_feature_list()
        modules_to_use = determine_modules(features=feature_list)
        loaded_modules = load_modules(modules_to_use=modules_to_use)

        # Read in inputs from db and validate inputs for loaded modules
        validate_inputs(subproblems, loaded_modules, subscenarios, conn)
    else:
        print("Invalid subscenario ID(s). Skipped detailed input validation.")

    # Update validation status:
    update_validation_status(conn, subscenarios.SCENARIO_ID)


if __name__ == "__main__":
    main()
