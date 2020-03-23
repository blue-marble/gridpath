#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This script iterates over all modules required for a GridPath scenario and
calls their *validate_inputs()* method, which performs various validations
of the input data and scenario setup.
"""


from __future__ import print_function

from builtins import str
import sqlite3
import sys
from argparse import ArgumentParser

from db.common_functions import connect_to_database, spin_on_database_lock
from gridpath.auxiliary.auxiliary import get_scenario_id_and_name, \
    write_validation_to_database
from gridpath.common_functions import get_db_parser
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
                        getattr(subscenarios, sc_id) == "NULL":
                    validation_results.append(
                        (subscenarios.SCENARIO_ID,
                         "N/A",
                         "N/A",
                         "N/A",
                         sc_id,
                         "scenarios",
                         "High",
                         "Missing subscenario ID",
                         "Requested feature '{}' requires an input for '{}'"
                         .format(feature, sc_id)
                         )
                    )
                # If the feature is not requested, and the associated
                # subscenarios are specified, raise a validation error
                elif feature not in feature_list and \
                        getattr(subscenarios, sc_id) != "NULL":
                    validation_results.append(
                        (subscenarios.SCENARIO_ID,
                         "N/A",
                         "N/A",
                         "N/A",
                         sc_id,
                         "scenarios",
                         "Low",
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
                 "High",
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
        "gen_new_lin,",
        "gen_new_bin",
        "stor_new_lin",
        "stor_new_bin",
        "dr_new"
    }
    existing_build_types = {
        "gen_spec",
        "gen_ret_bin",
        "gen_ret_lin",
        "stor_spec",
    }
    dr_types = {
        "dr_new"
    }

    # Determine required subscenario_ids
    sc_id_type = []
    if bool(req_cap_types & new_build_types):
        sc_id_type.append(("PROJECT_NEW_COST_SCENARIO_ID",
                           "New Build"))
    if bool(req_cap_types & existing_build_types):
        sc_id_type.append(("PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID",
                           "Existing"))
        sc_id_type.append(("PROJECT_SPECIFIED_FIXED_COST_SCENARIO_ID",
                           "Existing"))
    if bool(req_cap_types & dr_types):
        sc_id_type.append(("PROJECT_NEW_POTENTIAL_SCENARIO_ID",
                           "Demand Response (DR)"))

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
                 "High",
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


def validate_multi_stage_settings(optional_features, subscenarios, subproblems,
                                  conn):
    """

    :param optional_features:
    :param subscenarios:
    :param subproblems:
    :param conn:
    :return:
    """

    multi_stage = optional_features.OPTIONAL_FEATURE_MULTI_STAGE

    # Check whether multi_stage setting is consistent with actual inputs
    max_stages = max([len(stages) for subproblem, stages in
                      subproblems.SUBPROBLEM_STAGE_DICT.items()])
    if max_stages > 1 and not multi_stage:
        validation_results = [(
            subscenarios.SCENARIO_ID,
            "N/A",
            "N/A",
            "N/A",
            "temporal_scenario_id",
            "scenarios and inputs_temporal_subproblems_stages",
            "Low",
            "Invalid multi-stage settings",
            "The inputs contain multiple dispatch stages while the multi-stage "
            "optional feature is not selected. Please select the multi-stage "
            "feature or remove the extra stages."
        )]
    elif max_stages <= 1 and multi_stage:
        validation_results = [(
            subscenarios.SCENARIO_ID,
            "N/A",
            "N/A",
            "N/A",
            "temporal_scenario_id",
            "scenarios and inputs_temporal_subproblems_stages",
            "Low",
            "Invalid multi-stage settings",
            "The inputs contain only a single dispatch stage so the multi-stage"
            " optional feature should not be selected. Please turn off the "
            "multi-stage feature or add additional stages."
        )]
    else:
        validation_results = []

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)


def reset_input_validation(conn, scenario_id):
    """
    Reset input validation: delete old input validation outputs and reset the
    input validation status.
    :param conn: database connection
    :param scenario_id: scenario_id
    :return: 
    """
    c = conn.cursor()

    sql = """
        DELETE FROM status_validation
        WHERE scenario_id = ?;
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=sql, data=(scenario_id,),
                          many=False)

    sql = """
        UPDATE scenarios
        SET validation_status_id = 0
        WHERE scenario_id = ?;
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=sql,  data=(scenario_id,),
                          many=False)


def update_validation_status(conn, scenario_id):
    """

    :param conn:
    :param scenario_id:
    :return:
    """
    c = conn.cursor()
    validations = c.execute(
        """SELECT scenario_id 
        FROM status_validation
        WHERE scenario_id = {}""".format(str(scenario_id))
    ).fetchall()

    if validations:
        status = 2
    else:
        status = 1

    sql = """
        UPDATE scenarios
        SET validation_status_id = ?
        WHERE scenario_id = ?;
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=sql,
                          data=(status, scenario_id), many=False)


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(
        add_help=True,
        parents=[get_db_parser()]
    )

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

    conn = connect_to_database(db_path=db_path,
                               detect_types=sqlite3.PARSE_DECLTYPES)
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

    # Validate multi-stage settings
    validate_multi_stage_settings(optional_features, subscenarios, subproblems,
                                  conn)

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

    # Close the database connection explicitly
    conn.close()


if __name__ == "__main__":
    main()
