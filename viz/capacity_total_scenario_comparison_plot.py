#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create plot of total capacity by scenario and technology for a given
period/zone/subproblem/stage.

"""

from argparse import ArgumentParser
from bokeh.embed import json_item

import pandas as pd
import sys

# GridPath modules
from viz.common_functions import connect_to_database, create_stacked_bar_plot, \
    show_plot, get_scenario_and_scenario_id, get_parent_parser


def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True, parents=[get_parent_parser()])
    parser.add_argument("--period", required=True, type=int,
                        help="The selected modeling period. Required.")
    parser.add_argument("--load_zone", required=True, type=str,
                        help="The name of the load zone. Required.")
    parser.add_argument("--subproblem", default=1, type=int,
                        help="The subproblem ID. Defaults to 1.")
    parser.add_argument("--stage", default=1, type=int,
                        help="The stage ID. Defaults to 1.")

    # Parse arguments
    parsed_arguments = parser.parse_args(args=arguments)

    return parsed_arguments


def get_plotting_data(conn, period, load_zone, subproblem, stage):
    """
    Get total capacity results by scenario/technology for a given
    period/load_zone/subproblem/stage.
    :param conn:
    :param period:
    :param load_zone:
    :param subproblem:
    :param stage:
    :return:
    """

    # Total capacity by scenario and technology
    sql = """SELECT scenario_id, technology, sum(capacity_mw) as capacity_mw
        FROM results_project_capacity_all
        WHERE period = ?
        AND load_zone = ?
        AND subproblem_id = ?
        AND stage_id = ?
        GROUP BY scenario_id, technology;"""

    df = pd.read_sql(
        sql,
        con=conn,
        params=(period, load_zone, subproblem, stage)
    )

    return df


def main(args=None):
    """
    Parse the arguments, get the data in a df, and create the plot

    :return: if requested, return the plot as JSON object
    """
    if args is None:
        args = sys.argv[1:]
    parsed_args = parse_arguments(arguments=args)

    conn = connect_to_database(parsed_arguments=parsed_args)

    plot_title = "Total Capacity by Scenario - {} - Subproblem {} - Stage {}"\
        .format(
            parsed_args.load_zone,
            parsed_args.subproblem,
            parsed_args.stage
        )
    plot_name = "TotalCapacityPlot-{}-{}-{}"\
        .format(
            parsed_args.load_zone,
            parsed_args.subproblem,
            parsed_args.stage
        )

    df = get_plotting_data(
        conn=conn,
        period=parsed_args.period,
        load_zone=parsed_args.load_zone,
        subproblem=parsed_args.subproblem,
        stage=parsed_args.stage
    )

    plot = create_stacked_bar_plot(
        df=df,
        title=plot_title,
        y_axis_column="capacity_mw",
        x_axis_column="scenario_id",
        group_column="technology",
        column_mapper={"capacity_mw": "Total Capacity (MW)",
                       "scenario_id": "Scenario",
                       "technology": "Technology"},
        ylimit=parsed_args.ylimit
    )

    # Show plot in HTML browser file if requested
    if parsed_args.show:
        show_plot(scenario_directory=parsed_args.scenario_location,
                  scenario="scenario_comparison",
                  plot=plot,
                  plot_name=plot_name)

    # Return plot in json format if requested
    if parsed_args.return_json:
        return json_item(plot, plot_name)


if __name__ == "__main__":
    main()
