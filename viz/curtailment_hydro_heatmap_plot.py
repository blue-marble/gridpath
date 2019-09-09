#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make plot of scheduled curtailment heatmap (by month and hour)
"""

# TODO: Find a color palette that is more continuous? E.g. like 'grey' but then
#   for red. Right now the number of ticks will not always match the 9 colors
#   in the color bar since the tickmarks are made such that each tick is a round
#   number but the max value is not always close to 9 * that round number so
#   sometimes there are less than 9 ticks (or more).
#   If the palette is continuous, where ticks fall doesn't matter.
#   Alternatively we can make sure that the maximum value is divisable by the
#   number of colors/ticks, but that often results in sub-optimal resolution.


from argparse import ArgumentParser
from bokeh.models import NumeralTickFormatter, LinearColorMapper, ColorBar, \
    BasicTicker
from bokeh.plotting import figure
from bokeh.models.tools import HoverTool
from bokeh.embed import json_item
from bokeh.palettes import Reds

import pandas as pd
import sys

# GridPath modules
from db.common_functions import connect_to_database
from viz.common_functions import show_plot, get_scenario_and_scenario_id


def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True)

    # Scenario name and location options
    parser.add_argument("--database",
                        help="The database file path. Defaults to ../db/io.db "
                             "if not specified")
    parser.add_argument("--scenario_id", help="The scenario ID. Required if "
                                              "no --scenario is specified.")
    parser.add_argument("--scenario", help="The scenario name. Required if "
                                           "no --scenario_id is specified.")
    parser.add_argument("--scenario_location",
                        help="The path to the directory in which to create "
                             "the scenario directory. Defaults to "
                             "'../scenarios' if not specified.")
    parser.add_argument("--load_zone",
                        help="The name of the load zone. Required.")
    parser.add_argument("--period",
                        help="The desired modeling period to plot. Required.")
    parser.add_argument("--stage", default=1,
                        help="The stage ID. Defaults to 1.")
    parser.add_argument("--ylimit", help="Set y-axis limit.", type=float)
    parser.add_argument("--show",
                        default=False, action="store_true",
                        help="Show and save figure to "
                             "results/figures directory "
                             "under scenario directory.")
    parser.add_argument("--return_json",
                        default=False, action="store_true",
                        help="Return plot as a json file."
                        )
    # Parse arguments
    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    return parsed_arguments


def get_curtailment(c, scenario_id, load_zone, period, stage):
    """
    Get curtailment results by month-hour
    :param c:
    :param scenario_id:
    :param load_zone:
    :param period:
    :param stage:
    :return:
    """

    # Curtailment by period and timepoint
    sql = """SELECT month, hour_on_horizon, 
        SUM(scheduled_curtailment_mwh) AS scheduled_curtailment_mwh
        FROM (
            SELECT scenario_id, horizon, period, timepoint, 
            (scheduled_curtailment_mw * horizon_weight * 
            number_of_hours_in_timepoint) as scheduled_curtailment_mwh, 
            month, SUM(number_of_hours_in_timepoint) OVER (
            PARTITION BY horizon ORDER BY timepoint) AS hour_on_horizon
            FROM results_project_curtailment_hydro

            INNER JOIN

            (SELECT scenario_id, temporal_scenario_id 
            FROM scenarios)
            USING (scenario_id)

            INNER JOIN

            (SELECT temporal_scenario_id, period, horizon, month 
            FROM inputs_temporal_horizons)
            USING (temporal_scenario_id, period, horizon)

            WHERE scenario_id = ?
            AND load_zone = ?
            AND period = ?
            AND stage_id = ?
        )
        GROUP BY month, hour_on_horizon
        ORDER BY month, hour_on_horizon
        ;"""

    curtailment = c.execute(sql, (scenario_id, load_zone, period, stage))

    return curtailment


def create_data_df(c, scenario_id, load_zone, period, stage):
    """
    Get curtailment results into df
    :param c:
    :param scenario_id:
    :param load_zone:
    :param period:
    :param stage:
    :return:
    """

    # Get curtailment from db
    curtailment = get_curtailment(c, scenario_id, load_zone, period, stage)

    # Convert SQL query results into DataFrame
    df = pd.DataFrame(
        data=curtailment.fetchall(),
        columns=[n[0] for n in curtailment.description]
    )

    # Convert month numbers to strings
    mapper = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec"
    }
    df.replace({"month": mapper}, inplace=True)

    # Round df (lots of rounding errors it where it should be 0)
    df = df.round(decimals=5)

    return df


def create_plot(df, title, ylimit=None):
    """

    :param df:
    :param title: string, plot title
    :param ylimit: float/int, upper limit of heatmap colorbar; optional
    :return:
    """

    if df.empty:
        return figure()

    # Round hours and convert to string (required for x-axis)
    # TODO: figure out a way to handle subhourly data properly!
    df["hour_on_horizon"] = df["hour_on_horizon"].map(int).map(str)

    # Get list of hours and months (used in xrange/yrange)
    hours = list(df["hour_on_horizon"].unique())
    months = list(reversed(df["month"].unique()))

    # Set up color mapper
    # colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce",
    #           "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
    colors = list(reversed(Reds[9]))

    high = ylimit if ylimit is not None else df.scheduled_curtailment_mwh.max()
    mapper = LinearColorMapper(
        palette=colors,
        low=df.scheduled_curtailment_mwh.min(),
        high=high
    )

    # Set up the figure
    plot = figure(
        plot_width=800, plot_height=500,
        tools=["pan", "reset", "zoom_in", "zoom_out", "save", "help"],
        toolbar_location="below",
        x_axis_location="above",
        title=title,
        x_range=hours,
        y_range=months,
    )

    # Plot heatmap rectangles
    hm = plot.rect(
        x="hour_on_horizon",
        y="month",
        width=1, height=1,
        source=df,
        fill_color={'field': 'scheduled_curtailment_mwh', 'transform': mapper},
        line_color="white"
    )

    # Add color bar legend
    color_bar = ColorBar(
        color_mapper=mapper,
        major_label_text_font_size="7pt",
        ticker=BasicTicker(desired_num_ticks=len(colors)),
        formatter=NumeralTickFormatter(format="0,0"),
        label_standoff=12,
        border_line_color=None,
        location=(0, 0)
    )
    plot.add_layout(color_bar, 'right')

    # Format Axes (labels, number formatting, range, etc.)
    plot.xaxis.axis_label = "Hour Ending"
    plot.yaxis.axis_label = "Month"
    plot.grid.grid_line_color = None
    plot.axis.axis_line_color = None
    plot.axis.major_tick_line_color = None
    plot.axis.major_label_standoff = 0

    # Add HoverTool
    hover = HoverTool(
        tooltips=[
            ("Month", "@month"),
            ("Hour", "@hour_on_horizon"),
            ("Curtailment", "@scheduled_curtailment_mwh{0,0} MWh")
        ],
        renderers=[hm],
        toggleable=True)
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

    db, c = connect_to_database(db_path=parsed_args.database)

    scenario_location = parsed_args.scenario_location
    scenario, scenario_id = get_scenario_and_scenario_id(
        parsed_arguments=parsed_args,
        c=c
    )

    plot_title = "Hydro Curtailment by Month-Hour - {} - {} - {}".format(
        parsed_args.load_zone, parsed_args.period, parsed_args.stage
    )
    plot_name = "HydroCurtailmentPlot-{}-{}-{}".format(
        parsed_args.load_zone, parsed_args.period, parsed_args.stage)

    df = create_data_df(
        c=c,
        scenario_id=scenario_id,
        load_zone=parsed_args.load_zone,
        period=parsed_args.period,
        stage=parsed_args.stage
    )

    plot = create_plot(
        df=df,
        title=plot_title,
        ylimit=parsed_args.ylimit
    )

    # Show plot in HTML browser file if requested
    if parsed_args.show:
        show_plot(scenario_directory=scenario_location,
                  scenario=scenario,
                  plot=plot,
                  plot_name=plot_name)

    # Return plot in json format if requested
    if parsed_args.return_json:
        return json_item(plot, plot_name)


if __name__ == "__main__":
    main()
