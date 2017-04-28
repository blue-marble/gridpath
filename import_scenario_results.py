#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from argparse import ArgumentParser
import os.path
import sqlite3
import sys

from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from gridpath.auxiliary.module_list import get_features, load_modules


def import_results_into_database(
        loaded_modules, scenario_id, cursor, db, results_directory
):
    """

    :param loaded_modules:
    :param scenario_id:
    :param cursor:
    :param db:
    :param results_directory:
    :return:
    """
    for m in loaded_modules:
        if hasattr(m, "import_results_into_database"):
            m.import_results_into_database(
                scenario_id, cursor, db, results_directory)
        else:
            pass


if __name__ == "__main__":
    arguments = sys.argv[1:]
    parser = ArgumentParser(add_help=True)
    parser.add_argument("--scenario",
                        help="The name of the scenario (the same as "
                             "the directory name)")
    parser.add_argument("--scenario_id",
                        help="The scenario_id from the database.")
    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    scenario_id_arg = parsed_arguments.scenario_id
    scenario_name_arg = parsed_arguments.scenario

    # Database
    # Assume script is run from root directory and that the database is named
    # io.db and is in a subdirectory ./db
    io = sqlite3.connect(
        os.path.join(os.getcwd(), 'db', 'io.db')
    )
    c = io.cursor()

    SCENARIO_ID, SCENARIO_NAME = get_scenario_id_and_name(
        scenario_id_arg=scenario_id_arg, scenario_name_arg=scenario_name_arg,
        c=c, script="import_scenario_results")

    # Directory structure
    SCENARIOS_MAIN_DIRECTORY = os.path.join(
        os.getcwd(), "scenarios")

    SCENARIO_DIRECTORY = os.path.join(
        SCENARIOS_MAIN_DIRECTORY, str(SCENARIO_NAME)
    )

    RESULTS_DIRECTORY = os.path.join(
        SCENARIO_DIRECTORY, "results"
    )

    # Check that the saved scenario_id matches
    with open(os.path.join(SCENARIO_DIRECTORY, "scenario_id.txt")) as \
            scenario_id_file:
        scenario_id_saved = scenario_id_file.read()
        if scenario_id_saved != SCENARIO_ID:
            raise AssertionError("ERROR: saved scenario_id does not match")

    # Go through modules
    FEATURES_TO_USE = get_features(SCENARIO_DIRECTORY)
    LOADED_MODULES = load_modules(FEATURES_TO_USE)

    import_results_into_database(
        loaded_modules=LOADED_MODULES, scenario_id=SCENARIO_ID, cursor=c,
        db=io, results_directory=RESULTS_DIRECTORY
    )
