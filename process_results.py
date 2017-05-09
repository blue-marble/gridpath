#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

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
    print("Processing results...")

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
        c=c, script="process_results"
    )

    # Directory structure
    scenarios_main_directory = os.path.join(
        os.getcwd(), "scenarios")

    scenario_directory = os.path.join(
        scenarios_main_directory, str(scenario_name)
    )

    # Go through modules
    modules_to_use = determine_modules(scenario_directory)
    loaded_modules = load_modules(modules_to_use)

    # Subscenarios
    subscenarios = SubScenarios(cursor=c, scenario_id=scenario_id)

    process_results(
        loaded_modules=loaded_modules, db=io, cursor=c,
        subscenarios=subscenarios
    )


if __name__ == "__main__":
    main()
