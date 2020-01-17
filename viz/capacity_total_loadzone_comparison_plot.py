#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create plot of total capacity by load zone and technology for a given
scenario/period/subproblem/stage.

"""

from argparse import ArgumentParser
from bokeh.embed import json_item

import pandas as pd
import sys

# GridPath modules
from db.common_functions import connect_to_database
from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from viz.common_functions import create_stacked_bar_plot, show_plot, \
    get_parent_parser, get_tech_colors, get_tech_plotting_order


def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True, parents=[get_parent_parser()])
    parser.add_argument("--scenario_id", help="The scenario ID. Required if "
                                              "no --scenario is specified.")
    parser.add_argument("--scenario", help="The scenario name. Required if "
                                           "no --scenario_id is specified.")
    parser.add_argument("--period", required=True, type=int,
                        help="The name of the load zone. Required.")
    parser.add_argument("--subproblem", default=1, type=int,
                        help="The subproblem ID. Defaults to 1.")
    parser.add_argument("--stage", default=1, type=int,
                        help="The stage ID. Defaults to 1.")

    # Parse arguments
    parsed_arguments = parser.parse_args(args=arguments)

    return parsed_arguments


def get_plotting_data(conn, scenario_id, period, subproblem, stage, **kwargs):
    """
    Get total capacity results by load zone/technology for a given
    scenario/period/subproblem/stage.

    **kwargs needed, so that an error isn't thrown when calling this
    function with extra arguments from the UI.

    :param conn:
    :param scenario_id:
    :param period:
    :param subproblem:
    :param stage:
    :return:
    """

    # Total capacity by load_zone and technology
    sql = """SELECT load_zone, technology, sum(capacity_mw) as capacity_mw
        FROM results_project_capacity_all
        WHERE scenario_id = ?
        AND period = ?
        AND subproblem_id = ?
        AND stage_id = ?
        GROUP BY load_zone, technology;"""

    df = pd.read_sql(
        sql,
        con=conn,
        params=(scenario_id, period, subproblem, stage)
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
        script="capacity_total_loadzone_comparison_plot"
    )

    tech_colors = get_tech_colors(c)
    tech_plotting_order = get_tech_plotting_order(c)

    plot_title = "Total Capacity by Load Zone - {} - Subproblem {} - Stage {}"\
        .format(
            parsed_args.period,
            parsed_args.subproblem,
            parsed_args.stage
        )
    plot_name = "TotalCapacityPlot-{}-{}-{}"\
        .format(
            parsed_args.period,
            parsed_args.subproblem,
            parsed_args.stage
        )

    df = get_plotting_data(
        conn=conn,
        scenario_id=scenario_id,
        period=parsed_args.period,
        subproblem=parsed_args.subproblem,
        stage=parsed_args.stage
    )

    plot = create_stacked_bar_plot(
        df=df,
        title=plot_title,
        y_axis_column="capacity_mw",
        x_axis_column="load_zone",
        group_column="technology",
        column_mapper={"capacity_mw": "New Capacity (MW)",
                       "load_zone": "Load Zone",
                       "technology": "Technology"},
        group_colors=tech_colors,
        group_order=tech_plotting_order,
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
