#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This script iterates over all modules required for a GridPath scenario and
calls their *process_results()* method, which makes updates to database
tables.

The main() function of this script can also be called with the
*gridpath_process_results* command when GridPath is installed.
"""


from __future__ import print_function

from argparse import ArgumentParser
import sys

from db.common_functions import connect_to_database
from gridpath.common_functions import determine_scenario_directory, \
    get_db_parser, get_scenario_location_parser
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
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(
        add_help=True,
        parents=[get_db_parser(), get_scenario_location_parser()]
    )
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
    scenario_location = parsed_arguments.scenario_location

    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    print("Processing results... (connected to database {})".format(db_path))

    scenario_id, scenario_name = get_scenario_id_and_name(
        scenario_id_arg=scenario_id_arg, scenario_name_arg=scenario_name_arg,
        c=c, script="process_results"
    )

    # Determine scenario directory
    scenario_directory = determine_scenario_directory(
        scenario_location=scenario_location,
        scenario_name=scenario_name
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

    # Close the database connection
    conn.close()


if __name__ == "__main__":
    main()
