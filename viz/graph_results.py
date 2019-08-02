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
    conn = sqlite3.connect(
        os.path.join(
            str(parsed_arguments.db_location),
            str(parsed_arguments.db_name)+".db"
        )
    )

    return conn


def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True)

    # Scenario name and location options
    parser.add_argument("--db_name", default="io",
                        help="Name of the database.")
    parser.add_argument("--db_location", default="../db",
                        help="Path to the database (relative to script).")
    parser.add_argument("--scenario", help="The scenario name.")
    parser.add_argument("--load_zone", help="The name of the load zone.")
    parser.add_argument("--horizon", help="The horizon ID.")
    parser.add_argument("--save",
                        default=False, action="store_true",
                        help="Save figure to "
                             "results/figures directory "
                             "under scenario directory.")
    parser.add_argument("--save_only",
                        default=False, action="store_true",
                        help="Don't show figure, but save to "
                             "results/figures/dispatch directory "
                             "under scenario directory."
                        )
    parser.add_argument("--dispatch_plot", default=False, action="store_true",
                        help="Draw a dispatch plot. Requires specifying a "
                             "horizon and load zone.")
    parser.add_argument("--xmin", help="Minimum value for the x axis.")
    parser.add_argument("--xmax", help="Maximum value for the x axis.")
    parser.add_argument("--ymin", help="Minimum value for the y axis.")
    parser.add_argument("--ymax", help="Maximum value for the y axis.")

    # Parse arguments
    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    return parsed_arguments


if __name__ == "__main__":
    args = sys.argv[1:]
    parsed_args = parse_arguments(arguments=args)

    # Which dispatch plot are we making
    SCENARIO_NAME = parsed_args.scenario
    HORIZON = parsed_args.horizon
    LOAD_ZONE = parsed_args.load_zone

    # Connect to database
    io = connect_to_database(parsed_args)
    c = io.cursor()

    # Get the scenario ID
    SCENARIO_ID = c.execute(
        """SELECT scenario_id
        FROM scenarios
        WHERE scenario_name = '{}';""".format(SCENARIO_NAME)
    ).fetchone()[0]

    # Draw a dispatch plot if requested
    if parsed_args.dispatch_plot:
        draw_dispatch_plot(
            c=c,
            scenario_id=SCENARIO_ID,
            horizon=HORIZON,
            load_zone=LOAD_ZONE,
            arguments=parsed_args
        )
