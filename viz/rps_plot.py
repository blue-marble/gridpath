#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create plot of rps by period for a given zone/subproblem/stage.

Note: Generally capacity expansion problems will have only one subproblem/stage
If not specified, the plotting module assumes the subproblem/stage is equal to
1, which is the default if there's only one subproblem/stage.
"""

# TODO: maybe create a generic rescale function that checks dataframe and
#    rescales anything with mw or mwh in it to appropriate metric (could be
#    GWh, kWh, ... depending one results.


from argparse import ArgumentParser
from bokeh.models import ColumnDataSource, Legend, NumeralTickFormatter
from bokeh.plotting import figure
from bokeh.models.tools import HoverTool
from bokeh.embed import json_item

import pandas as pd
import sys

# GridPath modules
from db.common_functions import connect_to_database
from viz.common_functions import show_hide_legend, show_plot, \
    get_scenario_and_scenario_id, get_parent_parser


def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True, parents=[get_parent_parser()])
    parser.add_argument("--scenario_id", help="The scenario ID. Required if "
                                              "no --scenario is specified.")
    parser.add_argument("--scenario", help="The scenario name. Required if "
                                           "no --scenario_id is specified.")
    parser.add_argument("--rps_zone", required=True, type=str,
                        help="The name of the RPS zone. Required")
    parser.add_argument("--subproblem", default=1, type=int,
                        help="The subproblem ID. Defaults to 1.")
    parser.add_argument("--stage", default=1, type=int,
                        help="The stage ID. Defaults to 1.")

    # Parse arguments
    parsed_arguments = parser.parse_args(args=arguments)

    return parsed_arguments


def get_plotting_data(conn, scenario_id, rps_zone, subproblem, stage):
    """
    Get the RPS results by period for a given scenario/rps_zone/subproblem/stage
    :param conn:
    :param scenario_id:
    :param rps_zone:
    :param subproblem:
    :param stage:
    :return:
    """

    sql = """
        SELECT 
            period, 
            rps_target_mwh/1000000 AS rps_target_twh, 
            delivered_rps_energy_mwh/1000000 AS delivered_rps_energy_twh, 
            curtailed_rps_energy_mwh/1000000 AS curtailed_rps_energy_twh, 
            fraction_of_rps_target_met, 
            fraction_of_rps_energy_curtailed,
            rps_marginal_cost_per_mwh
        FROM results_system_rps
        WHERE scenario_id = ?
        AND rps_zone = ?
        AND subproblem_id = ?
        AND stage_id = ?
        ;"""

    df = pd.read_sql(
        sql,
        con=conn,
        params=(scenario_id, rps_zone, subproblem, stage)
    )

    # Change period type from int to string (required for categorical bar chart)
    df["period"] = df["period"].map(str)

    # Add rps delivered fraction
    df["fraction_of_rps_energy_delivered"] = \
        1 - df["fraction_of_rps_energy_curtailed"]

    return df


def create_plot(df, title, ylimit=None):
    """

    :param df:
    :param title: string, plot title
    :param ylimit: float/int, upper limit of y-axis; optional
    :return:
    """

    if df.empty:
        return figure()

    # Set up data source
    source = ColumnDataSource(data=df)

    # Determine column types for plotting, legend and colors
    # Order of stacked_cols will define order of stacked areas in chart
    x_col = "period"
    line_col = "rps_target_twh"
    stacked_cols = ["delivered_rps_energy_twh", "curtailed_rps_energy_twh"]

    # Stacked Area Colors
    colors = ["#75968f", "#933b41"]

    # Set up the figure
    plot = figure(
        plot_width=800, plot_height=500,
        tools=["pan", "reset", "zoom_in", "zoom_out", "save", "help"],
        title=title,
        x_range=df[x_col]
        # sizing_mode="scale_both"
    )

    # Add stacked bar chart to plot
    bar_renderers = plot.vbar_stack(
        stackers=stacked_cols,
        x=x_col,
        source=source,
        color=colors,
        width=0.5,
    )

    # Add RPS target line chart to plot
    target_renderer = plot.circle(
        x=x_col,
        y=line_col,
        source=source,
        size=20,
        color="black",
        fill_alpha=0.2,
        line_width=2
    )

    # Create legend items
    legend_items = [
        ("Delivered RPS Energy", [bar_renderers[0]]),
        ("Curtailed RPS Energy", [bar_renderers[1]]),
        ("RPS Target", [target_renderer])
    ]

    # Add Legend
    legend = Legend(items=legend_items)
    plot.add_layout(legend, 'right')
    plot.legend[0].items.reverse()  # Reverse legend to match stacked order
    plot.legend.click_policy = 'hide'  # Add interactivity to the legend
    # Note: Doesn't rescale the graph down, simply hides the area
    # Note2: There's currently no way to auto-size legend based on graph size(?)
    # except for maybe changing font size automatically?
    show_hide_legend(plot=plot)  # Hide legend on double click

    # Format Axes (labels, number formatting, range, etc.)
    plot.xaxis.axis_label = "Period"
    plot.yaxis.axis_label = "Energy (TWh)"
    plot.yaxis.formatter = NumeralTickFormatter(format="0,0")
    plot.y_range.end = ylimit  # will be ignored if ylimit is None

    # Add delivered RPS HoverTool
    r_delivered = bar_renderers[0]  # renderer for delivered RPS
    hover = HoverTool(
        tooltips=[
            ("Period", "@period"),
            ("Delivered RPS Energy",
             "@%s{0,0} TWh (@fraction_of_rps_energy_delivered{0%%})"
             % stacked_cols[0]),
        ],
        renderers=[r_delivered],
        toggleable=False)
    plot.add_tools(hover)

    # Add curtailed RPS HoverTool
    r_curtailed = bar_renderers[1]  # renderer for curtailed RPS
    hover = HoverTool(
        tooltips=[
            ("Period", "@period"),
            ("Curtailed RPS Energy",
             "@%s{0,0} TWh (@fraction_of_rps_energy_curtailed{0%%})"
             % stacked_cols[1]),
        ],
        renderers=[r_curtailed],
        toggleable=False)
    plot.add_tools(hover)

    # Add RPS Target HoverTool
    hover = HoverTool(
        tooltips=[
            ("Period", "@period"),
            ("RPS Target", "@%s{0,0} TWh" % line_col),
            ("Fraction of RPS Met", "@fraction_of_rps_target_met{0%}"),
            ("Marginal Cost", "@rps_marginal_cost_per_mwh{0,0} $/MWh")
        ],
        renderers=[target_renderer],
        toggleable=False)
    plot.add_tools(hover)

    return plot


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

    scenario, scenario_id = get_scenario_and_scenario_id(
        parsed_arguments=parsed_args,
        c=c
    )

    plot_title = "RPS Result by Period - {} - Subproblem {} - Stage {}".format(
        parsed_args.rps_zone, parsed_args.subproblem, parsed_args.stage)
    plot_name = "RPSPlot-{}-{}-{}".format(
        parsed_args.rps_zone, parsed_args.subproblem, parsed_args.stage)

    df = get_plotting_data(
        conn=conn,
        scenario_id=scenario_id,
        rps_zone=parsed_args.rps_zone,
        subproblem=parsed_args.subproblem,
        stage=parsed_args.stage
    )

    plot = create_plot(
        df=df,
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
