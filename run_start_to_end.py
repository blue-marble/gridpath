#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Get inputs, run scenario, and import results.
"""

from argparse import ArgumentParser
import os.path
import sys
import sqlite3
import traceback

# GridPath modules
import get_scenario_inputs
import run_scenario
import import_scenario_results
import process_results


# TODO: can these be consolidated with run scenario
def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True)

    # Scenario name and location options
    parser.add_argument("--scenario",
                        help="The name of the scenario (the same as "
                             "the directory name)")
    parser.add_argument("--scenario_location", default="scenarios",
                        help="Scenario directory path (relative to "
                             "run_start_to_end.py.")

    # TODO: add database path as argument

    # Output options
    parser.add_argument("--log", default=False, action="store_true",
                        help="Log output to a file in the logs directory as "
                             "well as the terminal.")
    parser.add_argument("--quiet", default=False, action="store_true",
                        help="Don't print run output.")

    # Solve options
    parser.add_argument("--solver", default="cbc",
                        help="Name of the solver to use. Default is cbc.")
    parser.add_argument("--mute_solver_output", default=True,
                        action="store_false",
                        help="Don't print solver output if set to true.")
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

    # Parse arguments
    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    return parsed_arguments


def update_run_status(scenario, status_id):
    # For now, assume script is run from root directory and the the
    # database is ./db and named io.db
    io = sqlite3.connect(
        os.path.join(os.getcwd(), 'db', 'io.db')
    )
    c = io.cursor()

    c.execute(
        """UPDATE scenarios
        SET run_status_id = {}
        WHERE scenario_name = '{}';""".format(status_id, scenario)
    )
    io.commit()


# TODO: add more run status types?
def main(args):
    parsed_args = parse_arguments(args)
    update_run_status(parsed_args.scenario, 1)

    try:
        get_scenario_inputs.main(args=args)
    except Exception:
        print("Made it to the exception")
        update_run_status(parsed_args.scenario, 3)
        print('Error encountered when getting inputs from the database for '
              'scenario {}.'.format(args.scenario))
        traceback.print_exc()
    try:
        run_scenario.main(args=args)
    except Exception:
        print('Made it here')
        update_run_status(parsed_args.scenario, 3)
        print('Error encountered when running scenario {}.'.format(
            args.scenario))
        traceback.print_exc()

    try:
        import_scenario_results.main(args=args)
    except Exception:
        update_run_status(args.scenario, 3)
        print('Error encountered when importing results for '
              'scenario {}.'.format(parsed_args.scenario))
        traceback.print_exc()

    try:
        process_results.main(args=args)
    except Exception:
        update_run_status(args.scenario, 3)
        print('Error encountered when importing results for '
              'scenario {}.'.format(parsed_args.scenario))
        traceback.print_exc()

    # If we make it here, mark run as complete
    update_run_status(parsed_args.scenario, 2)


if __name__ == "__main__":
    main(args=sys.argv[1:])
