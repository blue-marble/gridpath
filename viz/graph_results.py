#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make results graphs.
"""

from builtins import str
import os.path
import sqlite3
import sys
from argparse import ArgumentParser

from viz.dispatch_plot import draw_dispatch_plot


def connect_to_database(parsed_arguments):
    """
    Connect to the database
    :param parsed_arguments:
    :return:
    """
    if parsed_arguments.database is None:
        db_path = os.path.join(os.getcwd(), "..", "db", "io.db")
    else:
        db_path = parsed_arguments.database

    if not os.path.isfile(db_path):
        raise OSError(
            "The database file {} was not found. Did you mean to "
            "specify a different database file?".format(
                os.path.abspath(db_path)
            )
        )

    conn = sqlite3.connect(db_path)

    return conn


def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True)

    # Scenario name and location options
    parser.add_argument("--database", help="The database file path.")
    parser.add_argument("--scenario", help="The scenario name.")
    parser.add_argument("--load_zone", help="The name of the load zone.")
    parser.add_argument("--horizon", help="The horizon ID.")
    parser.add_argument("--stage", default=1,
                        help="The stage ID. Defaults to 1")
    parser.add_argument("--show",
                        default=False, action="store_true",
                        help="Show and save figure to "
                             "results/figures directory "
                             "under scenario directory.")
    parser.add_argument("--return_json",
                        default=True, action="store_true",
                        help="Return plot as a json file"
                        )
    parser.add_argument("--dispatch_plot", default=False, action="store_true",
                        help="Draw a dispatch plot. Requires specifying a "
                             "horizon and load zone.")
    # TODO: okay to default stage to 1 for cases with only one stage? Need to
    #   make sure this is aligned with SQL tables (default value for column)
    #   and data validation
    # Parse arguments
    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    return parsed_arguments


if __name__ == "__main__":
    args = sys.argv[1:]
    parsed_args = parse_arguments(arguments=args)

    # Dispatch plot settings
    SCENARIO_NAME = parsed_args.scenario
    LOAD_ZONE = parsed_args.load_zone
    HORIZON = parsed_args.horizon
    STAGE = parsed_args.stage
    SHOW_PLOT = parsed_args.show
    RETURN_JSON = parsed_args.return_json

    # Connect to database
    conn = connect_to_database(parsed_args)
    c = conn.cursor()

    # Draw a dispatch plot if requested
    if parsed_args.dispatch_plot:
        if RETURN_JSON:
            json_plot = draw_dispatch_plot(
                c=c,
                scenario=SCENARIO_NAME,
                load_zone=LOAD_ZONE,
                horizon=HORIZON,
                stage=STAGE,
                show_plot=SHOW_PLOT,
                return_json=RETURN_JSON
            )
        else:
            draw_dispatch_plot(
                c=c,
                scenario=SCENARIO_NAME,
                load_zone=LOAD_ZONE,
                horizon=HORIZON,
                stage=STAGE,
                show_plot=SHOW_PLOT,
                return_json=RETURN_JSON
            )

    # TODO: integrate with UI and handle optional returning json more elegantly