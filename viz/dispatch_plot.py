#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make results dispatch plot for a specified zone/stage/horizon
"""

# TODO: adjust x-axis for timepoint duration? (assumes 1h now)
# TODO: create a database table with technologies and colors for each tech
#   note: currently technology more narrowly defined than tech color (latter
#   includes curtailment etc.)
# TODO: okay to default stage to 1 for cases with only one stage? Need to
#   make sure this is aligned with SQL tables (default value for column)
#   and data validation

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
from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from viz.common_functions import show_hide_legend, show_plot, \
    get_parent_parser, get_tech_color_mapper


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
    parser.add_argument("--horizon", required=True, type=int,
                        help="The horizon ID. Required.")
    parser.add_argument("--stage", default=1, type=int,
                        help="The stage ID. Defaults to 1.")

    # Parse arguments
    parsed_arguments = parser.parse_args(args=arguments)

    return parsed_arguments


# Assign colors to each technology (+ curtailment/imports)
# COLORS = dict([
#     ("unspecified", "ghostwhite"),
#     ("Nuclear", "purple"),
#     ("Coal", "dimgrey"),
#     ("CHP", "darkkhaki"),
#     ("Geothermal", "yellowgreen"),
#     ("Biomass", "olivedrab"),
#     ("Small_Hydro", "mediumaquamarine"),
#     ("Steam", "whitesmoke"),
#     ("CCGT", "lightgrey"),
#     ("Hydro", "darkblue"),
#     ("Imports", "darkgrey"),
#     ("Peaker", "grey"),
#     ("Wind", "deepskyblue"),
#     ("Solar_BTM", "orange"),
#     ("Solar", "gold"),
#     ("Pumped_Storage", "darkslategrey"),
#     ("Battery", "teal"),
#     ("Curtailment_Variable", "indianred"),
#     ("Curtailment_Hydro", "firebrick")
# ])


def get_power_by_tech_results(conn, scenario_id, load_zone, horizon, stage):
    """
    Get results for power by technology and create dictionary
    :param conn:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :param stage:
    :return:
    """

    # Power by technology
    query = """SELECT timepoint, technology, power_mw
        FROM results_project_dispatch_by_technology
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND timepoint IN (
        SELECT DISTINCT timepoint
        FROM results_project_dispatch_all
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND horizon = {}
        AND stage_id = {})
        AND stage_id = {};""".format(
            scenario_id, load_zone, scenario_id, load_zone, horizon, stage,
        stage
        )

    df = pd.read_sql(query, conn)
    if not df.empty:
        df = df.pivot(index="timepoint", columns="technology")["power_mw"]

    return df


def get_variable_curtailment_results(
        c, scenario_id, load_zone, horizon, stage):
    """
    Get variable generator curtailment by load_zone, horizon, and stage
    :param c:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :param stage:
    :return:
    """
    query = """SELECT scheduled_curtailment_mw
            FROM results_project_curtailment_variable
            WHERE scenario_id = {}
            AND load_zone = '{}'
            AND timepoint IN (
            SELECT DISTINCT timepoint
            FROM results_project_dispatch_all
            WHERE scenario_id = {}
            AND load_zone = '{}'
            AND horizon = {}
            AND stage_id = {})
            AND stage_id = {};""".format(
                scenario_id, load_zone, scenario_id, load_zone, horizon,
                stage, stage
            )

    curtailment = [i[0] for i in c.execute(query).fetchall()]

    return curtailment


def get_hydro_curtailment_results(c, scenario_id, load_zone, horizon, stage):
    """
    Get conventional hydro curtailment by load_zone, horizon, and stage
    :param c:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :param stage:
    :return:
    """
    query = """SELECT scheduled_curtailment_mw
            FROM results_project_curtailment_hydro
            WHERE scenario_id = {}
            AND load_zone = '{}'
            AND timepoint IN (
            SELECT DISTINCT timepoint
            FROM results_project_dispatch_all
            WHERE scenario_id = {}
            AND load_zone = '{}'
            AND horizon = {}
            AND stage_id = {})
            AND stage_id = {};""".format(
                scenario_id, load_zone, scenario_id, load_zone, horizon,
                stage, stage
            )

    curtailment = [i[0] for i in c.execute(query).fetchall()]

    return curtailment


def get_imports_exports_results(c, scenario_id, load_zone, horizon, stage):
    """
    Get imports/exports results for the load zone, horizon, and stage
    :param c:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :param stage:
    :return:
    """
    net_imports = c.execute(
        """SELECT net_imports_mw
        FROM results_transmission_imports_exports
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND timepoint IN (
        SELECT DISTINCT timepoint
        FROM results_project_dispatch_all
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND horizon = {}
        AND stage_id = {})
        AND stage_id = {};""".format(
            scenario_id, load_zone, scenario_id, load_zone, horizon,
            stage, stage
        )
    ).fetchall()

    imports = [i[0] if i[0] > 0 else 0 for i in net_imports]
    exports = [-e[0] if e[0] < 0 else 0 for e in net_imports]

    return imports, exports


def get_load(c, scenario_id, load_zone, horizon, stage):
    """

    :param c:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :param stage:
    :return:
    """

    load = c.execute(
        """SELECT load_mw
        FROM results_system_load_balance
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND timepoint IN (
        SELECT DISTINCT timepoint
        FROM results_project_dispatch_all
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND horizon = {}
        AND stage_id = {})
        AND stage_id = {};""".format(
            scenario_id, load_zone, scenario_id, load_zone, horizon,
            stage, stage
        )
    ).fetchall()

    load = [i[0] for i in load]

    return load


def get_plotting_data(conn, scenario_id, load_zone, horizon, stage, **kwargs):
    """
    Get the dispatch data by timepoint and technology for a given
    scenario/load_zone/horizon/stage.

    **kwargs needed, so that an error isn't thrown when calling this
    function with extra arguments from the UI.

    :param conn:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :param stage:
    :return:
    """

    c = conn.cursor()

    # Get dispatch by technology
    # TODO: Let tech order depend on specified order in database table.
    #  Storage might be tricky because we manipulate it! Simply remove negatives
    #  for all teech?
    df = get_power_by_tech_results(
        conn=conn,
        scenario_id=scenario_id,
        load_zone=load_zone,
        horizon=horizon,
        stage=stage
    )

    # Add x axis
    # TODO: assumes hourly timepoints for now, make it flexible instead
    df["x"] = range(0, len(df))

    # Split storage into charging and discharging and aggregate storage charging
    # Assume any dispatch that is negative is storage charging
    df["Storage_Charging"] = 0
    stor_techs = df.columns[(df < 0).any()]
    for tech in stor_techs:
        df["Storage_Charging"] += -df[tech].clip(upper=0)
        df[tech] = df[tech].clip(lower=0)

    # Add variable curtailment (if any)
    curtailment_variable = get_variable_curtailment_results(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        horizon=horizon,
        stage=stage
    )
    if curtailment_variable:
        df["Curtailment_Variable"] = curtailment_variable

    # Add hydro curtailment (if any)
    curtailment_hydro = get_hydro_curtailment_results(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        horizon=horizon,
        stage=stage
    )
    if curtailment_hydro:
        df["Curtailment_Hydro"] = curtailment_hydro

    # Add imports and exports (if any)
    imports, exports = get_imports_exports_results(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        horizon=horizon,
        stage=stage
    )
    if imports:
        df["Imports"] = imports
    if exports:
        df["Exports"] = exports

    # Add load
    load = get_load(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        horizon=horizon,
        stage=stage
    )
    df["Load"] = load

    # Dataframe for testing without database
    # df = pd.DataFrame(
    #     data={
    #         "unspecified": range(10),
    #         "Nuclear": range(10),
    #         "Coal": range(10),
    #         "CHP": range(10),
    #         "Geothermal": range(10),
    #         "Biomass": range(10),
    #         "Small_Hydro": range(10),
    #         "Steam": range(10),
    #         "CCGT": range(10),
    #         "Hydro": range(10),
    #         "Imports": range(10),
    #         "Peaker": range(10),
    #         "Wind": range(10),
    #         "Solar_BTM": range(10),
    #         "Solar": range(10),
    #         "Pumped_Storage": range(10),
    #         "Battery": range(10),
    #         "Curtailment_Variable": range(10),
    #         "Curtailment_Hydro": range(10),
    #         "x": range(10),
    #         "Load": range(10),
    #         "Exports": range(10),
    #         "Pumped_Storage_Charging": [-5] * 10,
    #         "Battery_Charging": [-10] * 10
    #     }
    # )

    return df


def create_plot(df, title, color_mapper={}, ylimit=None):
    """

    :param df:
    :param title: string, plot title
    :param color_mapper: optional dict that maps column names to colors. Colors
        without specified color map will use default cividis palette
    :param ylimit: float/int, upper limit of y-axis; optional
    :return:
    """

    # Set up data source
    source = ColumnDataSource(data=df)

    # Determine column types for plotting, legend and colors
    # Order of stacked_cols will define order of stacked areas in chart
    all_cols = list(df.columns)
    x_col = "x"
    # TODO: remove hard-coding?
    line_cols = ["Load", "Exports", "Storage_Charging"]
    stacked_cols = [c for c in all_cols if c not in line_cols + [x_col]]

    # Set up color scheme. Use cividis palette for unspecified colors
    unspecified_columns = [c for c in stacked_cols
                           if c not in color_mapper.keys()]
    unspecified_color_mapper = dict(zip(unspecified_columns,
                                        cividis(len(unspecified_columns))))
    colors = []
    for tech in stacked_cols:
        if tech in color_mapper:
            colors.append(color_mapper[tech])
        else:
            colors.append(unspecified_color_mapper[tech])

    # TODO: include horizon in title? (would need to add function arg)
    # Set up the figure
    plot = figure(
        plot_width=800, plot_height=500,
        tools=["pan", "reset", "zoom_in", "zoom_out", "save", "help"],
        title=title,
        # sizing_mode="scale_both"
    )

    # Add stacked area chart to plot
    area_renderers = plot.vbar_stack(
        stackers=stacked_cols,
        x=x_col,
        source=source,
        color=colors,
        width=1,
    )
    # Note: can easily change vbar_stack to varea_stack by replacing the plot
    # function and removing the width argument. However, hovertools don't work
    # with varea_stack.

    # Add load line chart to plot
    load_renderer = plot.line(
        x=df[x_col],
        y=df[line_cols[0]],
        line_color="black",
        line_width=2,
        name="Load"
    )

    # Keep track of legend items and load renderers
    legend_items = [(x, [area_renderers[i]]) for i, x in enumerate(stacked_cols)
                    if df[x].mean() > 0] + [("Load", [load_renderer])]
    load_renderers = [load_renderer]

    # Add 'Load + ...' lines
    if line_cols[1] not in df.columns:
        inactive_exports = True
    else:
        inactive_exports = (df[line_cols[1]] == 0).all()
    inactive_storage = (df[line_cols[2]] == 0).all()

    if not inactive_exports:
        # Add export line to plot
        label = "Load + Exports"
        exports_renderer = plot.line(
            x=df[x_col],
            y=df[line_cols[0:2]].sum(axis=1),
            line_color="black",
            line_width=2,
            line_dash="dashed",
            name=label
        )
        legend_items.append((label, [exports_renderer]))
        load_renderers.append(exports_renderer)

    if not inactive_storage:
        # Add storage line to plot
        label = legend_items[-1][0] + " + Storage Charging"
        stor_renderer = plot.line(
            x=df[x_col],
            y=df[line_cols].sum(axis=1),
            line_color="black",
            line_width=2,
            line_dash="dotted",
            name=label
        )
        legend_items.append((label, [stor_renderer]))
        load_renderers.append(stor_renderer)

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
    plot.xaxis.axis_label = "Hour Ending"
    plot.yaxis.axis_label = "Dispatch (MW)"
    plot.yaxis.formatter = NumeralTickFormatter(format="0,0")
    plot.y_range.end = ylimit  # will be ignored if ylimit is None

    # Add HoverTools for stacked bars/areas
    for r in area_renderers:
        power_source = r.name
        hover = HoverTool(
            tooltips=[
                ("Hour Ending", "@x"),
                ("Source", power_source),
                ("Dispatch", "@%s{0,0} MW" % power_source)
            ],
            renderers=[r],
            toggleable=False)
        plot.add_tools(hover)

    # Add HoverTools for load lines
    for r in load_renderers:
        load_type = r.name
        hover = HoverTool(
            tooltips=[
                ("Hour Ending", "@x"),
                (load_type, "@y{0,0} MW"),
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

    scenario_id, scenario = get_scenario_id_and_name(
        scenario_id_arg=parsed_args.scenario_id,
        scenario_name_arg=parsed_args.scenario,
        c=c,
        script="dispatch_plot"
    )

    color_mapper = get_tech_color_mapper(c)

    plot_title = "Dispatch Plot - {} - Stage {} - Horizon {}".format(
        parsed_args.load_zone, parsed_args.stage, parsed_args.horizon)
    plot_name = "dispatchPlot-{}-{}".format(
        parsed_args.load_zone, parsed_args.horizon)

    df = get_plotting_data(
        conn=conn,
        scenario_id=scenario_id,
        load_zone=parsed_args.load_zone,
        horizon=parsed_args.horizon,
        stage=parsed_args.stage
    )

    plot = create_plot(
        df=df,
        title=plot_title,
        color_mapper=color_mapper,
        ylimit=parsed_args.ylimit,
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
