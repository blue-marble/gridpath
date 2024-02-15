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
Make results dispatch plot for a specified zone/stage/set of timepoints
"""

# TODO: adjust x-axis for timepoint duration? (assumes 1h now) - could
#  use timestamp from inputs_temporal instead and create x-axis automatically
#  using built-in datestime libraries?
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
from gridpath.auxiliary.db_interface import get_scenario_id_and_name
from viz.common_functions import (
    show_hide_legend,
    show_plot,
    get_parent_parser,
    get_tech_colors,
    get_tech_plotting_order,
    get_unit,
)


def create_parser():
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
        "--starting_tmp",
        default=None,
        type=int,
        help="The starting timepoint. Defaults to None (" "first timepoint)",
    )
    parser.add_argument(
        "--ending_tmp",
        default=None,
        type=int,
        help="The ending timepoint. Defaults to None (" "last timepoint)",
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


def get_timepoints(conn, scenario_id, starting_tmp=None, ending_tmp=None, stage_id=1):
    """
    Note: assumes timepoints are ordered!
    :param conn:
    :param scenario_id:
    :param starting_tmp:
    :param ending_tmp:
    :param stage_id:
    :return:
    """

    if starting_tmp is None:
        start_query = ""
    else:
        start_query = "AND timepoint >= {}".format(starting_tmp)

    if ending_tmp is None:
        end_query = ""
    else:
        end_query = "AND timepoint <= {}".format(ending_tmp)

    query = """SELECT timepoint
        FROM inputs_temporal
        INNER JOIN
        (SELECT temporal_scenario_id FROM scenarios WHERE scenario_id = {})
        USING (temporal_scenario_id)
        WHERE stage_id = {}
        {}
        {}
        ;""".format(
        scenario_id, stage_id, start_query, end_query
    )

    tmps = [i[0] for i in conn.execute(query).fetchall()]

    return tmps


def get_power_by_tech_results(conn, scenario_id, load_zone, stage, timepoints):
    """
    Get results for power by technology for a given load_zone and set of
    points.
    :param conn:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :param timepoints
    :return:
    """

    # Power by technology
    query = """SELECT timepoint, technology, power_mw
        FROM results_project_dispatch_by_technology
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND stage_id = {}
        AND timepoint IN ({})
        ;""".format(
        scenario_id, load_zone, stage, ",".join(["?"] * len(timepoints))
    )

    df = pd.read_sql(query, conn, params=timepoints)
    if not df.empty:
        df = df.pivot(index="timepoint", columns="technology")["power_mw"]
        return df
    # If the dataframe was empty, we still need to send the timepoint index
    # downstream
    else:
        index_only_df = pd.DataFrame(index=timepoints)
        return index_only_df


def get_variable_curtailment_results(c, scenario_id, load_zone, stage, timepoints):
    """
    Get variable generator curtailment for a given load_zone and set of
    timepoints.
    :param c:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :param timepoints:
    :return:
    """
    query = """SELECT scheduled_curtailment_mw
            FROM results_project_curtailment_variable_periodagg
            WHERE scenario_id = {}
            AND load_zone = '{}'
            AND stage_id = {}
            AND timepoint IN ({})
            ;""".format(
        scenario_id, load_zone, stage, ",".join(["?"] * len(timepoints))
    )

    curtailment = [i[0] for i in c.execute(query, timepoints).fetchall()]

    return curtailment


def get_hydro_curtailment_results(c, scenario_id, load_zone, stage, timepoints):
    """
    Get conventional hydro curtailment for a given load_zone and set of
    timepoints.
    :param scenario_id:
    :param load_zone:
    :param stage:
    :param timepoints:
    :return:
    """
    query = """SELECT scheduled_curtailment_mw
            FROM results_project_curtailment_hydro_periodagg
            WHERE scenario_id = {}
            AND load_zone = '{}'
            AND stage_id = {}
            AND timepoint IN ({});""".format(
        scenario_id, load_zone, stage, ",".join(["?"] * len(timepoints))
    )

    curtailment = [i[0] for i in c.execute(query, timepoints).fetchall()]

    return curtailment


def get_imports_exports_results(c, scenario_id, load_zone, stage, timepoints):
    """
    Get imports/exports results for a given load_zone and set of timepoints.
    :param c:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :param timepoints:
    :return:
    """
    query = """SELECT net_imports_mw
        FROM results_system_load_zone_timepoint
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND stage_id = {}
        AND timepoint IN ({})
        ;""".format(
        scenario_id, load_zone, stage, ",".join(["?"] * len(timepoints))
    )

    net_imports = c.execute(query, timepoints).fetchall()

    # None values should only happen if the transmission feature was not
    # included
    imports = [0 if i[0] is None else i[0] if i[0] > 0 else 0 for i in net_imports]
    exports = [0 if e[0] is None else -e[0] if e[0] < 0 else 0 for e in net_imports]

    return imports, exports


def get_market_participation_results(c, scenario_id, load_zone, stage, timepoints):
    """
    Get market participation results for a given load_zone and set of timepoints.
    :param c:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :param timepoints:
    :return:
    """
    query = """SELECT net_market_purchases_mw
        FROM results_system_load_zone_timepoint
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND stage_id = {}
        AND timepoint IN ({})
        ;""".format(
        scenario_id, load_zone, stage, ",".join(["?"] * len(timepoints))
    )

    market_participation = c.execute(query, timepoints).fetchall()

    sales = []
    purchases = []
    for i in market_participation:
        if i[0] is None:  # markets feature not included
            sales.append(0)
            purchases.append(0)
        else:
            if i[0] < 0:
                sales.append(-i[0])
                purchases.append(0)
            elif i[0] > 0:
                sales.append(0)
                purchases.append(i[0])
            else:
                sales.append(0)
                purchases.append(0)

    return sales, purchases


def get_load(c, scenario_id, load_zone, stage, timepoints):
    """

    :param c:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :param timepoints
    :return:
    """

    query = """SELECT static_load_mw, unserved_energy_mw
        FROM results_system_load_zone_timepoint
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND stage_id = {}
        AND timepoint IN ({});""".format(
        scenario_id,
        load_zone,
        stage,
        ",".join(["?"] * len(timepoints)),
    )

    load_balance = c.execute(query, timepoints).fetchall()

    load = [i[0] for i in load_balance]
    unserved_energy = [i[1] for i in load_balance]

    return load, unserved_energy


def get_plotting_data(
    conn, scenario_id, load_zone, starting_tmp, ending_tmp, stage, **kwargs
):
    """
    Get the dispatch data by timepoint and technology for a given
    scenario/load_zone/set of timepoints/stage.

    **kwargs needed, so that an error isn't thrown when calling this
    function with extra arguments from the UI.

    :param conn:
    :param scenario_id:
    :param load_zone:
    :param starting_tmp:
    :param ending_tmp:
    :param stage:
    :return:
    """

    c = conn.cursor()

    # Get the relevant timepoints
    timepoints = get_timepoints(conn, scenario_id, starting_tmp, ending_tmp, stage)

    # Get dispatch by technology
    # TODO: Let tech order depend on specified order in database table.
    #  Storage might be tricky because we manipulate it!
    df = get_power_by_tech_results(
        conn=conn,
        scenario_id=scenario_id,
        load_zone=load_zone,
        stage=stage,
        timepoints=timepoints,
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
        stage=stage,
        timepoints=timepoints,
    )
    if curtailment_variable:
        df["Curtailment_Variable"] = curtailment_variable

    # Add hydro curtailment (if any)
    curtailment_hydro = get_hydro_curtailment_results(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        stage=stage,
        timepoints=timepoints,
    )
    if curtailment_hydro:
        df["Curtailment_Hydro"] = curtailment_hydro

    # Add imports and exports (if any)
    imports, exports = get_imports_exports_results(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        stage=stage,
        timepoints=timepoints,
    )
    if imports:
        df["Imports"] = imports
    if exports:
        df["Exports"] = exports

    # Add market participation (if any)
    market_sales, market_purchases = get_market_participation_results(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        stage=stage,
        timepoints=timepoints,
    )
    if market_sales:
        df["Market_Sales"] = market_sales
    if market_purchases:
        df["Market_Purchases"] = market_purchases

    # Add load
    load_balance = get_load(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        stage=stage,
        timepoints=timepoints,
    )

    df["Load"] = load_balance[0]
    df["Unserved_Energy"] = load_balance[1]

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


def create_plot(
    df, title, power_unit, tech_colors={}, tech_plotting_order={}, ylimit=None
):
    """

    :param df:
    :param title: string, plot title
    :param power_unit: string, the unit of power used in the database/model
    :param tech_colors: optional dict that maps technologies to colors.
        Technologies without a specified color map will use a default palette
    :param tech_plotting_order: optional dict that maps technologies to their
        plotting order in the stacked bar/area chart.
    :param ylimit: float/int, upper limit of y-axis; optional
    :return:
    """

    # Re-arrange df according to plotting order
    for col in df.columns:
        if col not in tech_plotting_order:
            tech_plotting_order[col] = max(tech_plotting_order.values()) + 1
    df = df.reindex(sorted(df.columns, key=lambda x: tech_plotting_order[x]), axis=1)

    # Set up data source
    source = ColumnDataSource(data=df)

    # Determine column types for plotting, legend and colors
    # Order of stacked_cols will define order of stacked areas in chart
    all_cols = list(df.columns)
    x_col = "x"
    # TODO: remove hard-coding?
    line_cols_storage_sum_track = [
        "Load",
        "Exports",
        "Storage_Charging",
        "Market_Sales",
    ]
    stacked_cols = [
        c for c in all_cols if c not in line_cols_storage_sum_track + [x_col]
    ]

    # Set up color scheme. Use cividis palette for unspecified colors
    unspecified_columns = [c for c in stacked_cols if c not in tech_colors.keys()]
    unspecified_tech_colors = dict(
        zip(unspecified_columns, cividis(len(unspecified_columns)))
    )
    colors = []
    for tech in stacked_cols:
        if tech in tech_colors:
            colors.append(tech_colors[tech])
        else:
            colors.append(unspecified_tech_colors[tech])

    # Set up the figure
    plot = figure(
        plot_width=800,
        plot_height=500,
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
        x=df[x_col], y=df["Load"], line_color="black", line_width=2, name="Load"
    )

    # Keep track of legend items and load renderers
    legend_items = [
        (x, [area_renderers[i]]) for i, x in enumerate(stacked_cols) if df[x].mean() > 0
    ] + [("Load", [load_renderer])]
    load_renderers = [load_renderer]

    # Add 'Load + ...' lines
    if "Exports" not in df.columns:
        inactive_exports = True
    else:
        inactive_exports = (df["Exports"] == 0).all()

    if "Market_Sales" not in df.columns:
        inactive_markets = True
    else:
        inactive_markets = (df["Market_Sales"] == 0).all()

    inactive_storage = (df["Storage_Charging"] == 0).all()

    if inactive_exports and inactive_markets:
        line_cols_storage_sum_track = ["Load", "Storage_Charging"]
    if not inactive_exports and inactive_markets:
        line_cols_storage_sum_track = ["Load", "Exports", "Storage_Charging"]
        # Add export line to plot
        label = "Load + Exports"
        exports_renderer = plot.line(
            x=df[x_col],
            y=df[["Load", "Exports"]].sum(axis=1),
            line_color="black",
            line_width=2,
            line_dash="dashed",
            name=label,
        )
        legend_items.append((label, [exports_renderer]))
        load_renderers.append(exports_renderer)
    if not inactive_exports and not inactive_markets:
        line_cols_storage_sum_track = [
            "Load",
            "Exports",
            "Market_Sales",
            "Storage_Charging",
        ]
        # Add export and market lines to plot
        label = "Load + Exports + Market Sales"
        exports_renderer = plot.line(
            x=df[x_col],
            y=df[["Load", "Exports", "Market_Sales"]].sum(axis=1),
            line_color="black",
            line_width=3,
            line_dash="dashed",
            name=label,
        )
        legend_items.append((label, [exports_renderer]))
        load_renderers.append(exports_renderer)
    if inactive_exports and not inactive_markets:
        line_cols_storage_sum_track = ["Load", "Storage_Charging", "Market_Sales"]
        # Add export line to plot
        label = "Load + Market Sales"
        exports_renderer = plot.line(
            x=df[x_col],
            y=df[["Load", "Market_Sales"]].sum(axis=1),
            line_color="black",
            line_width=2,
            line_dash="dashed",
            name=label,
        )
        legend_items.append((label, [exports_renderer]))
        load_renderers.append(exports_renderer)

    if not inactive_storage:
        # Add storage line to plot
        label = legend_items[-1][0] + " + Storage Charging"
        stor_renderer = plot.line(
            x=df[x_col],
            y=df[line_cols_storage_sum_track].sum(axis=1),
            line_color="black",
            line_width=2,
            line_dash="dotted",
            name=label,
        )
        legend_items.append((label, [stor_renderer]))
        load_renderers.append(stor_renderer)

    # Add Legend
    legend = Legend(items=legend_items)
    plot.add_layout(legend, "right")
    plot.legend[0].items.reverse()  # Reverse legend to match stacked order
    plot.legend.click_policy = "hide"  # Add interactivity to the legend
    # Note: Doesn't rescale the graph down, simply hides the area
    # Note2: There's currently no way to auto-size legend based on graph size(?)
    # except for maybe changing font size automatically?
    show_hide_legend(plot=plot)  # Hide legend on double click

    # Format Axes (labels, number formatting, range, etc.)
    plot.xaxis.axis_label = "Hour Ending"
    plot.yaxis.axis_label = "Dispatch ({})".format(power_unit)
    plot.yaxis.formatter = NumeralTickFormatter(format="0,0")
    plot.y_range.end = ylimit  # will be ignored if ylimit is None

    # Add HoverTools for stacked bars/areas
    for r in area_renderers:
        power_source = r.name
        hover = HoverTool(
            tooltips=[
                ("Hour Ending", "@x"),
                ("Source", power_source),
                ("Dispatch", "@%s{0,0} %s" % (power_source, power_unit)),
            ],
            renderers=[r],
            toggleable=False,
        )
        plot.add_tools(hover)

    # Add HoverTools for load lines
    for r in load_renderers:
        load_type = r.name
        hover = HoverTool(
            tooltips=[
                ("Hour Ending", "@x"),
                (load_type, "@y{0,0} %s" % power_unit),
            ],
            renderers=[r],
            toggleable=False,
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
        script="dispatch_plot",
    )

    tech_colors = get_tech_colors(c)
    tech_plotting_order = get_tech_plotting_order(c)
    power_unit = get_unit(c, "power")

    plot_title = "{}Dispatch Plot - {} - Stage {} - Timepoints {}-{}".format(
        "{} - ".format(scenario) if parsed_args.scenario_name_in_title else "",
        parsed_args.load_zone,
        parsed_args.stage,
        parsed_args.starting_tmp,
        parsed_args.ending_tmp,
    )
    plot_name = "dispatchPlot-{}-{}-{}-{}".format(
        parsed_args.load_zone,
        parsed_args.stage,
        parsed_args.starting_tmp,
        parsed_args.ending_tmp,
    )

    df = get_plotting_data(
        conn=conn,
        scenario_id=scenario_id,
        load_zone=parsed_args.load_zone,
        starting_tmp=parsed_args.starting_tmp,
        ending_tmp=parsed_args.ending_tmp,
        stage=parsed_args.stage,
    )

    plot = create_plot(
        df=df,
        title=plot_title,
        power_unit=power_unit,
        tech_colors=tech_colors,
        tech_plotting_order=tech_plotting_order,
        ylimit=parsed_args.ylimit,
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
