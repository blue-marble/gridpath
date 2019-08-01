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

    # TODO: link db outputs for validation to validation status

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


    # check that must-run and no_commit have only one segment, i.e. constant
    # heat rate
    # This requires checking other tables so is a cross validation!

    # check that SU and SD * timepoint duration is larger than Pmin
    # this requires multiple tables so cross validation?

    # check that specified load zones are actual load zones that are available

    # Update Validation Status:
    update_validation_status(conn.cursor(), subscenarios.SCENARIO_ID)
    conn.commit()


def reset_input_validation(c, scenario_id):
    """
    Reset input validation: delete old input validation outputs and reset the
    input validation status.
    :param c: database cursor
    :param scenario_id: scenario_id
    :return: 
    """
    c.execute(
        """DELETE FROM mod_input_validation
        WHERE scenario_id = {};""".format(str(scenario_id))
    )

    c.execute(
        """UPDATE scenarios
        SET validation_status_id = 0
        WHERE scenario_id = {};""".format(str(scenario_id))
    )


def update_validation_status(c, scenario_id):
    """

    :param c:
    :param scenario_id:
    :return:
    """
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
    conn = sqlite3.connect(os.path.join(os.getcwd(), "..", "db", "io.db"))
    c = conn.cursor()

    scenario_id, scenario_name = get_scenario_id_and_name(
        scenario_id_arg=scenario_id_arg,
        scenario_name_arg=scenario_name_arg,
        c=c,
        script="validate_inputs"
    )

    # Reset input validation status and results
    reset_input_validation(c, scenario_id)
    conn.commit()

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
    validate_inputs(subproblems, loaded_modules, subscenarios, conn)


if __name__ == "__main__":
    main()
