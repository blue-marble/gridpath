#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Get inputs, run scenario, and import results.
"""

from argparse import ArgumentParser
import sys

import get_scenario_inputs
import run_scenario
import import_scenario_results


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
                             "run_scenario.py.")

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


if __name__ == "__main__":
    args = sys.argv[1:]

    get_scenario_inputs.main(args=args)
    run_scenario.main(args=args)
    import_scenario_results.main(args=args)
