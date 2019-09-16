#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make plot of costs by period for a certain zone/stage
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
                        help="The name of the load zone. Required.")
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


def get_costs(c, scenario_id, load_zone, stage):
    """
    Get costs results
    :param c:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :return:
    """

    # TODO: move this into a view that keeps all scenarios and periods
    #   and then select from it? (but full table takes 19s to load, whereas
    #   a slice is much faster!) Perhaps we can move each cost by scen/period
    #   into a view, but that won't make things faster, just shorter queries?
    # TODO: will this work when there are no capacity cost (left join would
    #   start with empty capacity table
    # TODO: what hurdle rates should we include? load_zone_to, load_zone_from
    #   or both?

    # System costs by scenario and period -- by source and total
    sql = """SELECT period,
        capacity_cost/1000000 as Capacity_Additions,
        fuel_cost/1000000 as Fuel,
        variable_om_cost/1000000 as Variable_OM,
        startup_cost/1000000 as Startups,
        shutdown_cost/1000000 as Shutdowns,
        hurdle_cost/1000000 as Hurdle_Rates

        FROM

        (SELECT scenario_id, period, sum(annualized_capacity_cost) 
        AS capacity_cost
        FROM  results_project_costs_capacity
        WHERE scenario_id = ?
        AND stage_id = ?
        AND load_zone = ?
        GROUP BY scenario_id, period) AS cap_costs

        LEFT JOIN

        (SELECT scenario_id, period, 
        sum(fuel_cost * timepoint_weight * number_of_hours_in_timepoint) 
        AS fuel_cost
        FROM results_project_costs_operations_fuel
        WHERE scenario_id = ?
        AND stage_id = ?
        AND load_zone = ?
        GROUP BY scenario_id, period) AS fuel_costs
        USING (scenario_id, period)

        LEFT JOIN

        (SELECT scenario_id, period, 
        sum(variable_om_cost * timepoint_weight * number_of_hours_in_timepoint) 
        AS variable_om_cost
        FROM results_project_costs_operations_variable_om
        WHERE scenario_id = ?
        AND stage_id = ?
        AND load_zone = ?
        GROUP BY scenario_id, period) AS variable_om_costs
        USING (scenario_id, period)

        LEFT JOIN

        (SELECT scenario_id, period, 
        sum(startup_cost * timepoint_weight) AS startup_cost
        FROM results_project_costs_operations_startup
        WHERE scenario_id = ?
        AND stage_id = ?
        AND load_zone = ?
        GROUP BY scenario_id, period) AS startup_costs
        USING (scenario_id, period)

        LEFT JOIN

        (SELECT scenario_id, period, 
        sum(shutdown_cost * timepoint_weight) AS shutdown_cost
        FROM results_project_costs_operations_shutdown
        WHERE scenario_id = ?
        AND stage_id = ?
        AND load_zone = ?
        GROUP BY scenario_id, period) AS shutdown_costs
        USING (scenario_id, period)

        LEFT JOIN

        (SELECT scenario_id, period, 
        sum((hurdle_cost_positive_direction + hurdle_cost_negative_direction) * 
        timepoint_weight * number_of_hours_in_timepoint) AS hurdle_cost
        FROM
        results_transmission_hurdle_costs
        WHERE scenario_id = ?
        AND stage_id = ?
        AND load_zone_to = ?
        GROUP BY scenario_id, period) AS hurdle_costs
        USING (scenario_id, period)
        ;"""

    costs = c.execute(sql, (scenario_id, stage, load_zone,
                            scenario_id, stage, load_zone,
                            scenario_id, stage, load_zone,
                            scenario_id, stage, load_zone,
                            scenario_id, stage, load_zone,
                            scenario_id, stage, load_zone)
                      )

    return costs


def create_data_df(c, scenario_id, load_zone, stage):
    """
    Get costs results and put into df
    :param c:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :return:
    """

    costs = get_costs(c, scenario_id, load_zone, stage)

    df = pd.DataFrame(
        data=costs.fetchall(),
        columns=[n[0] for n in costs.description]
    )

    # Set index to period and change index type from int to string
    # (required for categorical bar chart)
    df.set_index("period", inplace=True)
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
    plot.yaxis.axis_label = "Cost ($MM)"
    plot.yaxis.formatter = NumeralTickFormatter(format="$0,0")
    plot.y_range.end = ylimit  # will be ignored if ylimit is None

    # Add HoverTools for stacked bars/areas
    for r in area_renderers:
        category = r.name
        hover = HoverTool(
            tooltips=[
                ("Period", "@period"),
                ("Cost Category", category),
                ("Cost", "@%s{$0,0} MM" % category)
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

    conn = connect_to_database(db_path=parsed_args.database)
    c = conn.cursor()

    scenario_location = parsed_args.scenario_location
    scenario, scenario_id = get_scenario_and_scenario_id(
        parsed_arguments=parsed_args,
        c=c
    )

    plot_title = "Total Cost by Period - {} - Stage {}".format(
        parsed_args.load_zone, parsed_args.stage)
    plot_name = "CostPlot-{}-{}".format(
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
