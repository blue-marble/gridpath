# Copyright 2016-2023 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Create plot of scheduled curtailment heatmap (by month and hour)
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
from bokeh.models import NumeralTickFormatter, LinearColorMapper, ColorBar, BasicTicker
from bokeh.plotting import figure
from bokeh.models.tools import HoverTool
from bokeh.embed import json_item
from bokeh.palettes import Reds

import pandas as pd
import sys

# GridPath modules
from db.common_functions import connect_to_database
from gridpath.auxiliary.db_interface import get_scenario_id_and_name
from viz.common_functions import show_plot, get_parent_parser, get_unit


def create_parser():
    """

    :return:
    """
    parser = ArgumentParser(add_help=True, parents=[get_parent_parser()])
    parser.add_argument(
        "--scenario_id",
        help="The scenario ID. Required if " "no --scenario is specified.",
    )
    parser.add_argument(
        "--scenario",
        help="The scenario name. Required if " "no --scenario_id is specified.",
    )
    parser.add_argument(
        "--load_zone",
        required=True,
        type=str,
        help="The name of the load zone. Required.",
    )
    parser.add_argument(
        "--period",
        required=True,
        type=int,
        help="The desired modeling period to plot. Required.",
    )
    parser.add_argument(
        "--stage", default=1, type=int, help="The stage ID. Defaults to 1."
    )

    return parser


def parse_arguments(arguments):
    """

    :return:
    """
    parser = create_parser()
    parsed_arguments = parser.parse_args(args=arguments)

    return parsed_arguments


def get_plotting_data(conn, scenario_id, load_zone, period, stage, **kwargs):
    """
    Get curtailment results by month-hour for a given
    scenario/load_zone/period/stage.

    **kwargs needed, so that an error isn't thrown when calling this
    function with extra arguments from the UI.

    :param conn:
    :param scenario_id:
    :param load_zone:
    :param period:
    :param stage:
    :return:
    """

    # Curtailment by month and hour of day
    # Spinup/lookahead timepoints are ignored by adding the resp. column tag
    # through inner joins and adding a conditional to ignore those timepoints
    sql = """SELECT month, hour_of_day, 
        SUM(scheduled_curtailment_mw) AS scheduled_curtailment_mwh
        FROM results_project_curtailment_hydro_periodagg
        
        -- add temporal scenario id so we can join timepoints table
        INNER JOIN
        
        (SELECT temporal_scenario_id, scenario_id FROM scenarios)
        USING (scenario_id)
        
        -- filter out spinup_or_lookahead timepoints
        INNER JOIN
        
        (SELECT temporal_scenario_id, stage_id, subproblem_id, timepoint, 
        spinup_or_lookahead
        FROM inputs_temporal
        WHERE spinup_or_lookahead = 0)
        USING (temporal_scenario_id, stage_id, subproblem_id, timepoint)
        
        WHERE scenario_id = ?
        AND load_zone = ?
        AND period = ?
        AND stage_id = ? 
      
        GROUP BY month, hour_of_day
        ORDER BY month, hour_of_day
        ;"""

    df = pd.read_sql(sql, con=conn, params=(scenario_id, load_zone, period, stage))

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
        12: "Dec",
    }
    df.replace({"month": mapper}, inplace=True)

    # Round df to avoid near-zero results that should be zero.
    df = df.round(decimals=5)

    return df


def create_plot(df, title, energy_unit, ylimit=None):
    """

    :param df:
    :param title: string, plot title
    :param energy_unit: string, the unit of energy used in the database/model
    :param ylimit: float/int, upper limit of heatmap colorbar; optional
    :return:
    """

    if df.empty:
        return figure()

    # Round hours and convert to string (required for x-axis)
    # TODO: figure out a way to handle subhourly data properly!
    df["hour_of_day"] = df["hour_of_day"].map(int).map(str)

    # Get list of hours and months (used in xrange/yrange)
    hours = list(df["hour_of_day"].unique())
    months = list(reversed(df["month"].unique()))

    # Set up color mapper
    # colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce",
    #           "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
    colors = list(reversed(Reds[9]))

    high = ylimit if ylimit is not None else df.scheduled_curtailment_mwh.max()
    mapper = LinearColorMapper(
        palette=colors, low=df.scheduled_curtailment_mwh.min(), high=high
    )

    # Set up the figure
    plot = figure(
        plot_width=800,
        plot_height=500,
        tools=["pan", "reset", "zoom_in", "zoom_out", "save", "help"],
        toolbar_location="below",
        x_axis_location="above",
        title=title,
        x_range=hours,
        y_range=months,
    )

    # Plot heatmap rectangles
    hm = plot.rect(
        x="hour_of_day",
        y="month",
        width=1,
        height=1,
        source=df,
        fill_color={"field": "scheduled_curtailment_mwh", "transform": mapper},
        line_color="white",
    )

    # Add color bar legend
    color_bar = ColorBar(
        color_mapper=mapper,
        major_label_text_font_size="7pt",
        ticker=BasicTicker(desired_num_ticks=len(colors)),
        formatter=NumeralTickFormatter(format="0,0"),
        label_standoff=12,
        border_line_color=None,
        location=(0, 0),
    )
    plot.add_layout(color_bar, "right")

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
            ("Hour", "@hour_of_day"),
            ("Curtailment", "@scheduled_curtailment_mwh{0,0} %s" % energy_unit),
        ],
        renderers=[hm],
        toggleable=True,
    )
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

    scenario_id, scenario = get_scenario_id_and_name(
        scenario_id_arg=parsed_args.scenario_id,
        scenario_name_arg=parsed_args.scenario,
        c=c,
        script="curtailment_hydro_heatmap_plot",
    )

    energy_unit = get_unit(c, "energy")

    plot_title = "{}Hydro Curtailment by Month-Hour - {} - {} - {}".format(
        "{} - ".format(scenario) if parsed_args.scenario_name_in_title else "",
        parsed_args.load_zone,
        parsed_args.period,
        parsed_args.stage,
    )
    plot_name = "HydroCurtailmentPlot-{}-{}-{}".format(
        parsed_args.load_zone, parsed_args.period, parsed_args.stage
    )

    df = get_plotting_data(
        conn=conn,
        scenario_id=scenario_id,
        load_zone=parsed_args.load_zone,
        period=parsed_args.period,
        stage=parsed_args.stage,
    )

    plot = create_plot(
        df=df, title=plot_title, energy_unit=energy_unit, ylimit=parsed_args.ylimit
    )

    # Show plot in HTML browser file if requested
    if parsed_args.show:
        show_plot(
            plot=plot,
            plot_name=plot_name,
            plot_write_directory=parsed_args.plot_write_directory,
            scenario=scenario,
        )

    # Return plot in json format if requested
    if parsed_args.return_json:
        return json_item(plot, "plotHTMLTarget")


if __name__ == "__main__":
    main()
