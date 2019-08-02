#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import str
from argparse import ArgumentParser
import os.path
import sqlite3
import sys

from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from gridpath.auxiliary.module_list import determine_modules, load_modules
from gridpath.auxiliary.scenario_chars import SubScenarios


def process_results(
        loaded_modules, db, cursor, subscenarios
):
    """
    
    :param loaded_modules: 
    :param db: 
    :param cursor: 
    :param subscenarios: 
    :return: 
    """
    for m in loaded_modules:
        if hasattr(m, "process_results"):
            m.process_results(
                db, cursor, subscenarios)
        else:
            pass


def parse_arguments(args):
    """
    :param arguments: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)
    parser.add_argument("--database", help="The database file path.")
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

    print("Processing results... (connected to database {})".format(db_path))

    scenario_id, scenario_name = get_scenario_id_and_name(
        scenario_id_arg=scenario_id_arg, scenario_name_arg=scenario_name_arg,
        c=c, script="process_results"
    )

    # Directory structure
    scenarios_main_directory = os.path.join(
        os.getcwd(), "..", "scenarios")

    scenario_directory = os.path.join(
        scenarios_main_directory, str(scenario_name)
    )

    # Go through modules
    modules_to_use = determine_modules(scenario_directory=scenario_directory)
    loaded_modules = load_modules(modules_to_use)

    # Subscenarios
    subscenarios = SubScenarios(cursor=c, scenario_id=scenario_id)

    process_results(
        loaded_modules=loaded_modules, db=conn, cursor=c,
        subscenarios=subscenarios
    )


if __name__ == "__main__":
    main()
