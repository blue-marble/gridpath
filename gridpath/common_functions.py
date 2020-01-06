#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

import os.path

from argparse import ArgumentParser


def determine_scenario_directory(scenario_location, scenario_name):
    """
    :param scenario_location: string, the base directory
    :param scenario_name: string, the scenario name
    :return: the scenario directory (string)

    Determine the scenario directory given a base directory and the scenario
    name. If no base directory is specified, use a directory named
    'scenarios' in the root directory (one level down from the current
    working directory).
    """
    if scenario_location is None:
        main_directory = os.path.join(
            os.getcwd(), "..", "scenarios")
    else:
        main_directory = scenario_location

    scenario_directory = os.path.join(
        main_directory, str(scenario_name)
    )

    return scenario_directory


def create_directory_if_not_exists(directory):
    """
    :param directory: string; the directory path

    Check if a directory exists and create it if not.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_scenario_location_parser():
    """
    Create ArgumentParser object which has the common set of arguments for
    accessing local scenario data.

    We can then simply add 'parents=[get_scenario_location_parser()]' when we
    create a parser for a script to inherit these common arguments.

    Note that 'add_help' is set to 'False' to avoid multiple `-h/--help` options
    (one for parent and one for each child), which will throw an error.
    :return:
    """

    parser = ArgumentParser(add_help=False)
    parser.add_argument("--scenario_location", default="../scenarios",
                        help="The path to the directory in which to create "
                             "the scenario directory. Defaults to "
                             "'../scenarios' if not specified.")

    return parser


def get_scenario_name_parser():
    """
    Create ArgumentParser object which has the common set of arguments for
    getting the scenario name

    We can then simply add 'parents=[get_scenario_names_parser()]' when we
    create a parser for a script to inherit these common arguments.

    Note that 'add_help' is set to 'False' to avoid multiple `-h/--help` options
    (one for parent and one for each child), which will throw an error.
    :return:
    """

    parser = ArgumentParser(add_help=False)
    required = parser.add_argument_group('required arguments')
    required.add_argument("--scenario", required=True, type=str,
                          help="Name of the scenario problem to solve.")

    return parser


def get_db_parser():
    """
    Create ArgumentParser object which has the common set of arguments for
    accessing scenario data from the database.

    We can then simply add 'parents=[get_db_parser()]' when we create a
    parser for a script to inherit these common arguments.

    Note that 'add_help' is set to 'False' to avoid multiple `-h/--help` options
    (one for parent and one for each child), which will throw an error.
    :return:
    """

    parser = ArgumentParser(add_help=False)
    parser.add_argument("--database", default="../db/io.db",
                        help="The database file path. Defaults to ../db/io.db "
                             "if not specified")
    parser.add_argument("--scenario_id", type=int,
                        help="The scenario_id from the database. Not needed "
                             "if scenario is specified.")
    parser.add_argument("--scenario", type=str,
                        help="The scenario_name from the database. Not "
                             "needed if scenario_id is specified.")

    return parser


def get_solve_parser():
    """
    Create ArgumentParser object which has the common set of arguments for
    solving a scenario (see run_scenario.py and run_end_to_end.py).

    We can then simply add 'parents=[get_solve_parser()]' when we create a
    parser for a script to inherit these common arguments.

    Note that 'add_help' is set to 'False' to avoid multiple `-h/--help` options
    (one for parent and one for each child), which will throw an error.
    :return:
    """

    parser = ArgumentParser(add_help=False)

    # Output options
    parser.add_argument("--log", default=False, action="store_true",
                        help="Log output to a file in the scenario's 'logs' "
                             "directory as well as the terminal.")
    parser.add_argument("--quiet", default=False, action="store_true",
                        help="Don't print run output.")
    # Solver options
    parser.add_argument("--solver", help="Name of the solver to use. "
                                         "GridPath will use Cbc if solver is "
                                         "not specified here and a "
                                         "'solver_options.csv' file does not "
                                         "exist in the scenario directory.")
    parser.add_argument("--solver_executable",
                        help="The path to the solver executable to use. This "
                             "is optional; if you don't specify it, "
                             "Pyomo will look for the solver executable in "
                             "your PATH. The solver specified with the "
                             "--solver option must be the same as the solver "
                             "for which you are providing an executable.")
    parser.add_argument("--mute_solver_output", default=False,
                        action="store_true",
                        help="Don't print solver output.")
    parser.add_argument("--write_solver_files_to_logs_dir", default=False,
                        action="store_true", help="Write the temporary "
                                                  "solver files to the logs "
                                                  "directory.")
    parser.add_argument("--keepfiles", default=False, action="store_true",
                        help="Save temporary solver files.")
    parser.add_argument("--symbolic", default=False, action="store_true",
                        help="Use symbolic labels in solver files.")
    # Flag for test runs (various changes in behavior)
    parser.add_argument("--testing", default=False, action="store_true",
                        help="Flag for test suite runs. Results not saved.")

    return parser
