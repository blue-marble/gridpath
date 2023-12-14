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
Make plot of capacity factor by period and project for a specified
scenario/stage.
"""

from argparse import ArgumentParser
from bokeh.models import ColumnDataSource, Legend, NumeralTickFormatter
from bokeh.plotting import figure
from bokeh.models.tools import HoverTool
from bokeh.embed import json_item
from bokeh.palettes import cividis

import pandas as pd
import sys

# GridPath modules
from db.common_functions import connect_to_database
from gridpath.auxiliary.db_interface import get_scenario_id_and_name
from viz.common_functions import (
    show_hide_legend,
    show_plot,
    get_parent_parser,
    get_tech_colors,
)


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
        help="The name of the load zone. Required",
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


def get_plotting_data(conn, scenario_id, load_zone, stage, **kwargs):
    """
    Get capacity_factors by period/project for a given scenario/load_zone/stage.

    **kwargs needed, so that an error isn't thrown when calling this
    function with extra arguments from the UI.

    :param conn:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :return:
    """

    # TODO: This assumes that capacity does not vary by stage or subproblem!
    #   Need to make sure that there won't be exceptional use cases that violate
    #   this assumption.

    # Cap Factor by period and stage
    # Spinup/lookahead timepoints are ignored by adding the resp. column tag
    # through inner joins and adding a conditional to ignore those timepoints
    sql = """SELECT project, period, technology, 
        period_mwh/(period_weight*capacity_mw) AS cap_factor
        FROM
            (SELECT scenario_id, project, period, technology,
            sum(power_mw * timepoint_weight * number_of_hours_in_timepoint) 
            AS period_mwh,
            sum(timepoint_weight * number_of_hours_in_timepoint) 
            AS period_weight
            FROM results_project_timepoint

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
            AND stage_id = ?
            AND load_zone = ?
            
            group by period, project) 
            
            AS energy_table
        
        INNER JOIN
        
        (SELECT scenario_id, project, period, avg(capacity_mw) as capacity_mw
        FROM results_project_period
        GROUP BY scenario_id, project, period) AS capacity_table
        USING (scenario_id, project, period)
        
        WHERE cap_factor IS NOT NULL  -- filter out projects with 0 capacity
        ;"""

    df = pd.read_sql(sql, con=conn, params=(scenario_id, stage, load_zone))

    return df


def create_plot(df, title, tech_colors={}):
    """

    :param df:
    :param title: string, plot title
    :param tech_colors: optional dict that maps technologies to colors.
        Technologies without a specified color will use a default palette
    :return:
    """
    # TODO: handle empty dataframe (will give bokeh warning)

    technologies = df["technology"].unique()

    # Create a map between factor (technology) and color.
    techs_wo_colors = [t for t in technologies if t not in tech_colors.keys()]
    default_cmap = dict(zip(techs_wo_colors, cividis(len(techs_wo_colors))))
    colormap = {}
    for t in technologies:
        if t in tech_colors:
            colormap[t] = tech_colors[t]
        else:
            colormap[t] = default_cmap[t]

    # Set up the figure
    plot = figure(
        plot_width=800,
        plot_height=500,
        tools=["pan", "reset", "zoom_in", "zoom_out", "save", "help"],
        title=title,
        # sizing_mode="scale_both"
    )

    # Add scattered cap factors to plot. Do this one tech at a time so as to
    # allow interactivity such as hiding cap factors by tech by clicking
    # on legend
    renderers = []
    for tech in technologies:
        sub_df = df[df["technology"] == tech]
        source = ColumnDataSource(data=sub_df)

        r = plot.circle(
            x="period",
            y="cap_factor",
            # legend=tech,
            source=source,
            line_color=colormap[tech],
            fill_color=colormap[tech],
            size=12,
            alpha=0.4,
        )
        renderers.append(r)

    # Keep track of legend items
    legend_items = [(y, [renderers[i]]) for i, y in enumerate(technologies)]

    # Add Legend
    legend = Legend(items=legend_items)
    plot.add_layout(legend, "right")
    plot.legend.click_policy = "hide"  # Add interactivity to the legend
    plot.legend.title = "Technology"
    # # Note: Doesn't rescale the graph down, simply hides the area
    # # Note2: There's currently no way to auto-size legend based on graph size(?)
    # # except for maybe changing font size automatically?
    show_hide_legend(plot=plot)  # Hide legend on double click

    # Format Axes (labels, number formatting, range, etc.)
    plot.xaxis.axis_label = "Period"
    plot.yaxis.axis_label = "Capacity Factor (%)"
    plot.xaxis[0].ticker = df["period"].unique()
    plot.yaxis.formatter = NumeralTickFormatter(format="0%")

    for r in renderers:
        hover = HoverTool(
            tooltips=[
                ("Project", "@project"),
                ("Technology", "@technology"),
                ("Period", "@period"),
                ("Capacity Factor", "@cap_factor{0%}"),
            ],
            renderers=[r],
            toggleable=False,
        )
        plot.add_tools(hover)

    # Alternative, more succinct approach that uses factor_cmap and plots all
    # circles at once (but less legend interactivity and customizable)
    #
    # colors = factor_cmap(
    #     field_name='technology',
    #     palette=cividis,
    #     factors=df["technology"].unique()
    # )
    #
    # r = plot.circle(
    #     x="period",
    #     y="cap_factor",
    #     legend="technology",
    #     source=source,
    #     line_color=colors,
    #     fill_color=colors,
    #     size=12,
    #     alpha=0.4
    # )
    #
    # Add HoverTools
    # hover = HoverTool(
    #     tooltips=[
    #         ("Project", "@project"),
    #         ("Technology", "@technology"),
    #         ("Period", "@period"),
    #         ("Capacity Factor", "@cap_factor{0%}")
    #     ],
    #     renderers=[r],
    #     toggleable=False)
    # plot.add_tools(hover)

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
        script="capacity_factor_plot",
    )

    tech_colors = get_tech_colors(c)

    plot_title = "{}Capacity Factors by Period - {} - Stage {}".format(
        "{} - ".format(scenario) if parsed_args.scenario_name_in_title else "",
        parsed_args.load_zone,
        parsed_args.stage,
    )
    plot_name = "CapFactorPlot-{}-{}".format(parsed_args.load_zone, parsed_args.stage)

    df = get_plotting_data(
        conn=conn,
        scenario_id=scenario_id,
        load_zone=parsed_args.load_zone,
        stage=parsed_args.stage,
    )

    plot = create_plot(df=df, title=plot_title, tech_colors=tech_colors)

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
