#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from argparse import ArgumentParser
import os.path
import sqlite3
import sys

from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from gridpath.auxiliary.module_list import determine_modules, load_modules


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


def parse_arguments(args):
    """
    Parse arguments
    :param args: 
    :return: 
    """
    parser = ArgumentParser(add_help=True)
    parser.add_argument("--scenario",
                        help="The name of the scenario (the same as "
                             "the directory name)")
    parser.add_argument("--scenario_id",
                        help="The scenario_id from the database.")
    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def main(args=None):
    """

    :return:
    """
    print("Importing results to database...")

    if args is None:
        args = sys.argv[1:]

    parsed_arguments = parse_arguments(args=args)

    scenario_id_arg = parsed_arguments.scenario_id
    scenario_name_arg = parsed_arguments.scenario

    # Database
    # Assume script is run from root directory and that the database is named
    # io.db and is in a subdirectory ./db
    io = sqlite3.connect(
        os.path.join(os.getcwd(), 'db', 'io.db')
    )
    c = io.cursor()

    scenario_id, scenario_name = get_scenario_id_and_name(
        scenario_id_arg=scenario_id_arg, scenario_name_arg=scenario_name_arg,
        c=c, script="import_scenario_results")

    # Directory structure
    scenarios_main_directory = os.path.join(
        os.getcwd(), "scenarios")

    scenario_directory = os.path.join(
        scenarios_main_directory, str(scenario_name)
    )

    results_directory = os.path.join(
        scenario_directory, "results"
    )

    # Check that the saved scenario_id matches
    with open(os.path.join(scenario_directory, "scenario_id.txt")) as \
            scenario_id_file:
        scenario_id_saved = scenario_id_file.read()
        if int(scenario_id_saved) != scenario_id:
            raise AssertionError("ERROR: saved scenario_id does not match")

    # Go through modules
    modules_to_use = determine_modules(scenario_directory)
    loaded_modules = load_modules(modules_to_use)

    import_results_into_database(
        loaded_modules=loaded_modules, scenario_id=scenario_id, cursor=c,
        db=io, results_directory=results_directory
    )


if __name__ == "__main__":
    main()
