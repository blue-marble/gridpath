#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make plot of energy by period and technology for a specified zone/stage
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


def get_energy(c, scenario_id, load_zone, stage):
    """
    Get energy results and pivot into data df
    :param c:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :return:
    """

    # TODO: add curtailment and imports? What about storage charging?

    # Energy by period, stage and technology
    # Spinup/lookahead timepoints are ignored by adding the resp. column tag
    # through inner joins and adding a conditional to ignore those timepoints
    sql = """SELECT period, technology, 
        sum(power_mw * horizon_weight * number_of_hours_in_timepoint)/1000000
        as energy_twh
        FROM results_project_dispatch_by_technology
        INNER JOIN
        (SELECT temporal_scenario_id, scenario_id
        FROM scenarios)
        USING (scenario_id)
        INNER JOIN
        (SELECT temporal_scenario_id, stage_id, subproblem_id, timepoint, 
        spinup_or_lookahead
        FROM inputs_temporal_timepoints)
        USING (temporal_scenario_id, stage_id, subproblem_id, timepoint)
        WHERE scenario_id = ?
        AND load_zone = ?
        AND stage_id = ?
        AND spinup_or_lookahead is NULL
        GROUP BY period, technology"""

    energy = c.execute(sql, (scenario_id, load_zone, stage))

    return energy


def create_data_df(c, scenario_id, load_zone, stage):
    """
    Get energy results and pivot into data df
    :param c:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :return:
    """

    energy = get_energy(c, scenario_id, load_zone, stage)

    df = pd.DataFrame(
        data=energy.fetchall(),
        columns=[n[0] for n in energy.description]
    )

    df = df.pivot(
        index='period',
        columns='technology',
        values='energy_twh'
    )
    # Change index type from int to string (required for categorical bar chart)
    df.index = df.index.map(str)

    # For Testing:
    # df = pd.DataFrame(
    #     index=["2018", "2020"],
    #     data=[[0, 3000, 500, 1500],
    #           [0, 6000, 4500, 2300]],
    #     columns=["Biomass", "Hydro", "Solar", "Wind"]
    # )
    # df.index.name = "period"

    return df


def create_plot(df, title, ylimit=None):
    """

    :param df:
    :param title: string, plot title
    :param ylimit: float/int, upper limit of y-axis; optional
    :return:
    """
    # TODO: handle empty dataframe (will give bokeh warning)

    # Set up data source
    source = ColumnDataSource(data=df)

    # Determine column types for plotting, legend and colors
    # Order of stacked_cols will define order of stacked areas in chart
    stacked_cols = list(df.columns)

    # Stacked Area Colors
    colors = cividis(len(stacked_cols))

    # Set up the figure
    plot = figure(
        plot_width=800, plot_height=500,
        tools=["pan", "reset", "zoom_in", "zoom_out", "save", "help"],
        title=title,
        x_range=df.index.values
        # sizing_mode="scale_both"
    )

    # Add stacked area chart to plot
    area_renderers = plot.vbar_stack(
        stackers=stacked_cols,
        x="period",
        source=source,
        color=colors,
        width=0.5,
    )

    # Keep track of legend items
    legend_items = [(y, [area_renderers[i]]) for i, y in enumerate(stacked_cols)
                    if df[y].mean() > 0]

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

    # Add HoverTools for stacked bars/areas
    for r in area_renderers:
        technology = r.name
        hover = HoverTool(
            tooltips=[
                ("Period", "@period"),
                ("Technology", technology),
                ("Energy", "@%s{0,0} TWh" % technology)
            ],
            renderers=[r],
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

    db, c = connect_to_database(db_path=parsed_args.database)

    scenario_location = parsed_args.scenario_location
    scenario, scenario_id = get_scenario_and_scenario_id(
        parsed_arguments=parsed_args,
        c=c
    )

    plot_title = "Energy by Period - {} - Stage {}".format(
        parsed_args.load_zone, parsed_args.stage)
    plot_name = "EnergyPlot-{}-{}".format(
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
