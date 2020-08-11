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
from viz.common_functions import reformat_stacked_plot_data, \
    create_stacked_bar_plot, show_plot, \
    get_parent_parser, get_tech_colors, get_tech_plotting_order, get_unit


# TODO: update parser to allow for list of inputs (using nargs)
#  see here: https://stackoverflow.com/questions/15753701/how-can-i-pass-a-list-as-a-command-line-argument-with-argparse
def create_parser():
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

    return parser


def parse_arguments(arguments):
    """

    :return:
    """
    parser = create_parser()
    parsed_arguments = parser.parse_args(args=arguments)

    return parsed_arguments


def get_plotting_data(conn, subproblem, stage, scenario_id=None,
                      load_zone=None, period=None, **kwargs):
    """
    Get capacity results by scenario/period/technology. Users can
    optionally provide a subset of scenarios/load_zones/periods.
    Note: if load zone is not provided, will aggregate across load zones.

    **kwargs needed, so that an error isn't thrown when calling this
    function with extra arguments from the UI.

    :param conn:
    :param subproblem:
    :param stage:
    :param scenario_id: int or list of int, optional (default: return all
        scenarios)
    :param load_zone: str or list of str, optional (default: aggregate across
        load_zones)
    :param period: int or list of int, optional (default: return all periods)
    :return: DataFrame with columns scenario_id, period, technology, capacity_mw
    """

    # TODO: add scenario name?
    params = [subproblem, stage]
    sql = """SELECT scenario_id, period, technology, 
        sum(capacity_mw) AS capacity_mw
        FROM results_project_capacity
        WHERE subproblem_id = ?
        AND stage_id = ?"""
    if period is not None:
        period = period if isinstance(period, list) else [period]
        sql += " AND period in ({})".format(",".join("?"*len(period)))
        params += period
    if scenario_id is not None:
        scenario_id = scenario_id if isinstance(scenario_id, list) else [scenario_id]
        sql += " AND scenario_id in ({})".format(",".join("?"*len(scenario_id)))
        params += scenario_id
    if load_zone is not None:
        load_zone = load_zone if isinstance(load_zone, list) else [load_zone]
        sql += " AND load_zone in ({})".format(",".join("?"*len(load_zone)))
        params += load_zone
    sql += " GROUP BY scenario_id, period, technology;"

    df = pd.read_sql(
        sql,
        con=conn,
        params=params
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

    tech_colors = get_tech_colors(c)
    tech_plotting_order = get_tech_plotting_order(c)
    power_unit = get_unit(c, "power")

    # Update title for different use cases (multi-period or multi-scenario)
    plot_title = \
        "{}Total Capacity by Period - {} - Subproblem {} - Stage {}".format(
            "{} - ".format(scenario)
            if parsed_args.scenario_name_in_title else "",
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

    # TODO: do hard-code testing here where we set scenario_ids=[2,25]
    #  or load_zone=['CAISO', 'LDWP']
    df = get_plotting_data(
        conn=conn,
        scenario_id=scenario_id,
        load_zone=parsed_args.load_zone,
        subproblem=parsed_args.subproblem,
        stage=parsed_args.stage
    )

    source, x_col = reformat_stacked_plot_data(
        df=df,
        y_col="capacity_mw",
        x_col="period",
        category_col="technology"
    )

    # TODO: base x_col on x_col above (if list, x_col will be different in CDS!)
    plot = create_stacked_bar_plot(
        source=source,
        x_col="period",
        x_label="Period",
        y_label="Capacity ({})".format(power_unit),
        category_label="Technology",
        category_colors=tech_colors,
        category_order=tech_plotting_order,
        title=plot_title,
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
