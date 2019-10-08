#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create plot of total capacity by period and technology for a given
scenario/zone/subproblem/stage.
"""

from argparse import ArgumentParser
from bokeh.embed import json_item

import pandas as pd
import sys

# GridPath modules
from db.common_functions import connect_to_database
from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from viz.common_functions import create_stacked_bar_plot, show_plot, \
    get_parent_parser


def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True, parents=[get_parent_parser()])
    parser.add_argument("--scenario_id", help="The scenario ID. Required if "
                                              "no --scenario is specified.")
    parser.add_argument("--scenario", help="The scenario name. Required if "
                                           "no --scenario_id is specified.")
    parser.add_argument("--load_zone", required=True, type=str,
                        help="The name of the load zone. Required.")
    parser.add_argument("--subproblem", default=1, type=int,
                        help="The subproblem ID. Defaults to 1.")
    parser.add_argument("--stage", default=1, type=int,
                        help="The stage ID. Defaults to 1.")

    # Parse arguments
    parsed_arguments = parser.parse_args(args=arguments)

    return parsed_arguments


def get_plotting_data(conn, scenario_id, load_zone, subproblem, stage):
    """
    Get capacity results by period/technology for a given
    scenario/oad_zone/subproblem/stage.
    :param conn:
    :param scenario_id:
    :param load_zone:
    :param subproblem:
    :param stage:
    :return:
    """

    # Total capacity by period and technology
    sql = """SELECT period, technology, sum(capacity_mw) as capacity_mw
        FROM results_project_capacity_all
        WHERE scenario_id = ?
        AND load_zone = ?
        AND subproblem_id = ?
        AND stage_id = ?
        GROUP BY period, technology;"""

    df = pd.read_sql(
        sql,
        con=conn,
        params=(scenario_id, load_zone, subproblem, stage)
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

    conn = connect_to_database(db_path=parsed_args.database)
    c = conn.cursor()

    scenario_id, scenario = get_scenario_id_and_name(
        scenario_id_arg=parsed_args.scenario_id,
        scenario_name_arg=parsed_args.scenario,
        c=c,
        script="capacity_total_plot"
    )

    plot_title = \
        "Total Capacity by Period - {} - Subproblem {} - Stage {}".format(
            parsed_args.load_zone,
            parsed_args.subproblem,
            parsed_args.stage
        )
    plot_name = \
        "TotalCapacityPlot-{}-{}-{}".format(
            parsed_args.load_zone,
            parsed_args.subproblem,
            parsed_args.stage
        )

    df = get_plotting_data(
        conn=conn,
        scenario_id=scenario_id,
        load_zone=parsed_args.load_zone,
        subproblem=parsed_args.subproblem,
        stage=parsed_args.stage
    )

    plot = create_stacked_bar_plot(
        df=df,
        title=plot_title,
        y_axis_column="capacity_mw",
        x_axis_column="period",
        group_column="technology",
        column_mapper={"capacity_mw": "Capacity (MW)",
                       "period": "Period",
                       "technology": "Technology"},
        ylimit=parsed_args.ylimit
    )

    # Show plot in HTML browser file if requested
    if parsed_args.show:
        show_plot(plot=plot,
                  plot_name=plot_name,
                  plot_write_directory=parsed_args.plot_write_directory,
                  scenario=scenario)

    # Return plot in json format if requested
    if parsed_args.return_json:
        return json_item(plot, plot_name)


if __name__ == "__main__":
    main()
