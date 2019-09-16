#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

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
from viz.common_functions import show_hide_legend, show_plot, \
    get_scenario_and_scenario_id


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
                        help="The name of the load zone. Required")
    parser.add_argument("--stage", default=1,
                        help="The stage ID. Defaults to 1.")
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


def get_cap_factors(c, scenario_id, load_zone, stage):
    """
    Get capacity_factors

    :param c:
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
        FROM results_project_dispatch_all
        
        INNER JOIN
        
        (SELECT temporal_scenario_id, scenario_id FROM scenarios)
        USING (scenario_id)
        
        INNER JOIN
        
        (SELECT temporal_scenario_id, stage_id, subproblem_id, timepoint, 
        spinup_or_lookahead
        FROM inputs_temporal_timepoints)
        USING (temporal_scenario_id, stage_id, subproblem_id, timepoint)
        
        WHERE scenario_id = ?
        AND stage_id = ?
        AND load_zone = ?
        AND spinup_or_lookahead is NULL
        group by period, project) AS energy_table
        
        INNER JOIN
        
        (SELECT scenario_id, project, period, avg(capacity_mw) as capacity_mw
        FROM results_project_capacity_all
        GROUP BY scenario_id, project, period) AS capacity_table
        USING (scenario_id, project, period)
        ;"""

    cap_factors = c.execute(sql, (scenario_id, stage, load_zone))

    return cap_factors


def create_data_df(c, scenario_id, load_zone, stage):
    """
    Get cap_factor results and pivot into data df
    :param c:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :return:
    """

    cap_factors = get_cap_factors(c, scenario_id, load_zone, stage)

    df = pd.DataFrame(
        data=cap_factors.fetchall(),
        columns=[n[0] for n in cap_factors.description]
    )
    df = df[pd.notna(df["cap_factor"])]  # filter out projects with 0 capacity

    return df


def create_plot(df, title):
    """

    :param df:
    :param title: string, plot title
    :return:
    """
    # TODO: handle empty dataframe (will give bokeh warning)

    technologies = df["technology"].unique()

    # Create a map between factor/technology and color.
    colors = cividis(len(technologies))
    colormap = {t: colors[i] for i, t in enumerate(technologies)}

    # Set up the figure
    plot = figure(
        plot_width=800, plot_height=500,
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
            alpha=0.4
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
                ("Capacity Factor", "@cap_factor{0%}")
            ],
            renderers=[r],
            toggleable=False)
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

    scenario_location = parsed_args.scenario_location
    scenario, scenario_id = get_scenario_and_scenario_id(
        parsed_arguments=parsed_args,
        c=c
    )

    plot_title = "Capacity Factors by Period - {} - Stage {}".format(
        parsed_args.load_zone, parsed_args.stage)
    plot_name = "CapFactorPlot-{}-{}".format(
        parsed_args.load_zone, parsed_args.stage)

    df = create_data_df(
        c=c,
        scenario_id=scenario_id,
        load_zone=parsed_args.load_zone,
        stage=parsed_args.stage
    )

    plot = create_plot(
        df=df,
        title=plot_title,
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
