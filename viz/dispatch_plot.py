#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make results dispatch plot (by load zone, stage, horizon).
"""

# TODO: adjust x-axis for timepoint duration? (assumes 1h now)
# TODO: create a database table with technologies and colors for each tech
#   note: currently technology more narrowly defined than tech color (latter
#   includes curtailment etc.)
# TODO: add example df for testing?

from argparse import ArgumentParser
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure, output_file, show
from bokeh.models.tools import HoverTool
from bokeh.embed import json_item
import pandas as pd
import os
import sys

# GridPath modules
from viz.common_functions import connect_to_database


# TODO: add some error-handling for when the user does not specify all
#  required arguments, as the traceback is rather unhelpful
#  We should also not allow both scenario and scenario_id to be specified
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
    parser.add_argument("--load_zone", help="The name of the load zone.")
    parser.add_argument("--horizon", help="The horizon ID.")
    parser.add_argument("--stage", default=1,
                        help="The stage ID. Defaults to 1 if not specified.")
    # TODO: I suggest having an option to not show the plot (default to
    #  show) and a separate option to save the plot (default to not save)
    #  Also, I maybe we should have an option to save to an image
    parser.add_argument("--show",
                        default=False, action="store_true",
                        help="Show and save figure to "
                             "results/figures directory "
                             "under scenario directory.")
    parser.add_argument("--return_json",
                        default=False, action="store_true",
                        help="Return plot as a json file."
                        )
    # TODO: okay to default stage to 1 for cases with only one stage? Need to
    #   make sure this is aligned with SQL tables (default value for column)
    #   and data validation
    # Parse arguments
    parsed_arguments = parser.parse_known_args(args=arguments)[0]

    return parsed_arguments


# TODO: we need to have the ability to take different technologies, e.g. a
#  user might want to show onshore wind and offshore wind separately,
#  etc. So we should take the list of technologies for the scenario from  the
#  database; for the colors we could use a palette and perhaps allow the user
#  to specify a dictionary of technology and color. It would, of course,
#  be even better if it could be done interactively.
#   Relatedly, we should think about how to allow the user to re-order the
#   stack
# These are the technologies we are expecting
# At this stage, if other technologies are specified, the script will break
TECHNOLOGIES = [
    "Battery",
    "Biomass",
    "Coal",
    "CCGT",
    "CHP",
    "Geothermal",
    "Hydro",
    "Nuclear",
    "Peaker",
    "Pumped_Storage",
    "Small_Hydro",
    "Solar",
    "Solar_BTM",
    "Steam",
    "unspecified",
    "Wind"
]

# Assign colors to each technology (+ curtailment/imports)
COLORS = dict([
    ("unspecified", "ghostwhite"),
    ("Nuclear", "purple"),
    ("Coal", "dimgrey"),
    ("CHP", "darkkhaki"),
    ("Geothermal", "yellowgreen"),
    ("Biomass", "olivedrab"),
    ("Small_Hydro", "mediumaquamarine"),
    ("Steam", "whitesmoke"),
    ("CCGT", "lightgrey"),
    ("Hydro", "darkblue"),
    ("Imports", "darkgrey"),
    ("Peaker", "grey"),
    ("Wind", "deepskyblue"),
    ("Solar_BTM", "orange"),
    ("Solar", "gold"),
    ("Pumped_Storage", "darkslategrey"),
    ("Battery", "teal"),
    ("Curtailment_Variable", "indianred"),
    ("Curtailment_Hydro", "firebrick")
])


# TODO: should we slice by subproblem too? Horizon should be fine, right?
def determine_x_axis(c, scenario_id, load_zone, horizon, stage):
    """
    Determine the number of timepoints for the x axis and make a list of
    timepoints from 1 to that number
    :param c:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :param stage:
    :return:
    """
    # Get x-axis values
    x_axis_count = c.execute(
        """SELECT COUNT(DISTINCT timepoint)
           FROM results_project_dispatch_all
           WHERE scenario_id = {}
           AND load_zone = '{}'
           AND horizon = {}
           AND stage_id = {}""".format(
            scenario_id, load_zone, horizon, stage
        )
    ).fetchone()[0]

    x_axis = list(range(1, x_axis_count + 1))

    return x_axis_count, x_axis


def get_power_by_tech_results(c, scenario_id, load_zone, horizon, stage):
    """
    Get results for power by technology and create dictionary
    :param c:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :param stage:
    :return:
    """

    # Power by technology
    query = """SELECT technology, power_mw
        FROM results_project_dispatch_by_technology
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND horizon = {}
        AND stage_id = {};""".format(
            scenario_id, load_zone, horizon, stage
        )

    power_by_technology_list = c.execute(query).fetchall()

    power_by_technology_dict = dict()
    for tech, power in power_by_technology_list:
        if tech in list(power_by_technology_dict.keys()):
            power_by_technology_dict[str(tech)].append(power)
        else:
            power_by_technology_dict[str(tech)] = [power]

    # TODO: Make this easier easier/faster with df?
    #   df.pivot(index=df.index, columns='technology')['power_mw']

    return power_by_technology_dict


def fill_out_missing_techs(power_by_tech, expected_techs):
    """
    Check if the power_by_tech includes all expected technologies. If not, fill
    out missing techs with 0s as values.
    :param power_by_tech:
    :param expected_techs:
    """

    technologies = power_by_tech.keys()
    x_axis_length = len(list(power_by_tech.values())[0])

    for tech in expected_techs:
        if tech not in technologies:
            power_by_tech[tech] = [0] * x_axis_length


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
            AND horizon = {}
            AND stage_id = {};""".format(
                scenario_id, load_zone, horizon, stage
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
            AND horizon = {}
            AND stage_id = {};""".format(
                scenario_id, load_zone, horizon, stage
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
        AND horizon = {}
        AND stage_id = {};""".format(
            scenario_id, load_zone, horizon, stage
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
        AND horizon = {}
        AND stage_id = {};""".format(
            scenario_id, load_zone, horizon, stage
        )
    ).fetchall()

    load = [i[0] for i in load]

    return load


def create_data_df(c, scenario_id, load_zone, horizon, stage):
    """

    :param c:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :param stage:
    :return:
    """

    x_axis_count, x_axis = determine_x_axis(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        horizon=horizon,
        stage=stage
    )

    power_by_tech = get_power_by_tech_results(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        horizon=horizon,
        stage=stage
    )
    fill_out_missing_techs(power_by_tech, TECHNOLOGIES)

    curtailment_variable = get_variable_curtailment_results(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        horizon=horizon,
        stage=stage
    )

    curtailment_hydro = get_hydro_curtailment_results(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        horizon=horizon,
        stage=stage
    )

    imports, exports = get_imports_exports_results(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        horizon=horizon,
        stage=stage
    )

    load = get_load(
        c=c,
        scenario_id=scenario_id,
        load_zone=load_zone,
        horizon=horizon,
        stage=stage
    )

    # Create data df
    # NOTE: can also do pd.DataFrame(power_by_tech)
    # NOTE: column order in this df sets the order for the chart/legend!
    # Has to match tech color tech names at top of file
    df = pd.DataFrame(
        data={
            "unspecified": power_by_tech["unspecified"],
            "Nuclear": power_by_tech["Nuclear"],
            "Coal": power_by_tech["Coal"],
            "CHP": power_by_tech["CHP"],
            "Geothermal": power_by_tech["Geothermal"],
            "Biomass": power_by_tech["Biomass"],
            "Small_Hydro": power_by_tech["Small_Hydro"],
            "Steam": power_by_tech["Steam"],
            "CCGT": power_by_tech["CCGT"],
            "Hydro": power_by_tech["Hydro"],
            "Imports": [0] * x_axis_count if not imports else imports,
            "Peaker": power_by_tech["Peaker"],
            "Wind": power_by_tech["Wind"],
            "Solar_BTM": power_by_tech["Solar_BTM"],
            "Solar": power_by_tech["Solar"],
            "Pumped_Storage": [i if i > 0 else 0
                               for i in power_by_tech["Pumped_Storage"]],
            "Battery": [i if i > 0 else 0
                        for i in power_by_tech["Battery"]],
            "Curtailment_Variable": [0] * x_axis_count
            if not curtailment_variable else curtailment_variable,
            "Curtailment_Hydro": [0] * x_axis_count
            if not curtailment_hydro else curtailment_hydro,
            "x": x_axis,
            "Load": load,
            "Exports": [0] * x_axis_count if not exports else exports,
            "Pumped_Storage_Charging": [-i if i < 0 else 0 for i in
                                        power_by_tech["Pumped_Storage"]],
            "Battery_Charging": [-i if i < 0 else 0
                                 for i in power_by_tech["Battery"]]
        }
    )

    return df


def create_plot(df):
    """

    :param df:
    :return:
    """

    # Set up data source
    source = ColumnDataSource(data=df)

    # Determine column types for plotting, legend and colors
    # Order of stacked_cols will define order of stacked areas in chart
    all_cols = list(df.columns)
    x_col = "x"
    line_cols = ["Load", "Exports",
                 "Battery_Charging", "Pumped_Storage_Charging"]
    stacked_cols = [c for c in all_cols if c not in line_cols + [x_col]]

    # Stacked Area Colors
    colors = [COLORS[c] for c in stacked_cols]
    # Example using palettes
    #   from bokeh.palettes import d3
    #   colors = d3['Category20b'][len(stacked_cols)]

    # TODO: include horizon in title? (would need to add function arg)
    #   Yes, include load zone and horizon in title
    # Set up the figure

    plot = figure(
        plot_width=800, plot_height=500,
        tools=["pan", "reset", "zoom_in", "zoom_out", "save", "help"],
        title="Dispatch Plot",
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
    inactive_exports = (df[line_cols[1]] == 0).all()
    inactive_pumped_storage = (df[line_cols[2]] == 0).all()
    inactive_batteries = (df[line_cols[3]] == 0).all()

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

    if not inactive_pumped_storage:
        # Add pumped storage line to plot
        label = legend_items[-1][0] + " + Pumped Storage"
        ps_renderer = plot.line(
            x=df[x_col],
            y=df[line_cols[0:3]].sum(axis=1),
            line_color=COLORS["Pumped_Storage"],
            line_width=2,
            line_dash="dotted",
            name=label
        )
        legend_items.append((label, [ps_renderer]))
        load_renderers.append(ps_renderer)

    if not inactive_batteries:
        # Add batteries line to plot
        label = legend_items[-1][0] + " + Batteries"
        batt_renderer = plot.line(
            x=df[x_col],
            y=df[line_cols].sum(axis=1),
            line_color=COLORS["Battery"],
            line_width=2,
            line_dash="dotdash",
            name=label
        )
        legend_items.append((label, [batt_renderer]))
        load_renderers.append(batt_renderer)

    # Add Legend
    legend = Legend(items=legend_items)
    plot.add_layout(legend, 'right')
    plot.legend[0].items.reverse()  # Reverse legend to match stacked order
    plot.legend.click_policy = 'hide'  # Add interactivity to the legend
    # Note: Doesn't rescale the graph down, simply hides the area
    # Note2: There's currently no way to auto-size legend based on graph size(?)
    # except for maybe changing font size automatically?
    # TODO: how do we deal with possible legend overflow (e.g. if there are
    #  too many technologies)

    # Add axis labels
    plot.xaxis.axis_label = "Hour Ending"
    plot.yaxis.axis_label = "Dispatch (MW)"

    # Add HoverTools for stacked bars/areas
    for r in area_renderers:
        power_source = r.name
        hover = HoverTool(
            tooltips=[
                ("Hour Ending", "@x"),
                ("Source", power_source),
                ("Dispatch", "@%s{int} MW" % power_source)
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
                (load_type, "@y{int} MW"),
            ],
            renderers=[r],
            toggleable=False)
        plot.add_tools(hover)

    return plot


def draw_dispatch_plot(c, scenario_id, load_zone, horizon, stage):
    """

    :param c:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :param stage:
    :return:
    """
    df = create_data_df(c, scenario_id, load_zone, horizon, stage)
    plot = create_plot(df)

    return plot


def main(args=None):
    """

    :return:
    """
    if args is None:
        args = sys.argv[1:]
    parsed_args = parse_arguments(arguments=args)

    print(parsed_args)

    db = connect_to_database(parsed_arguments=parsed_args)
    c = db.cursor()

    if parsed_args.scenario_id is None:
        scenario = parsed_args.scenario
        # Get the scenario ID
        scenario_id = c.execute(
            """SELECT scenario_id
            FROM scenarios
            WHERE scenario_name = '{}';""".format(parsed_args.scenario)
        ).fetchone()[0]
    else:
        scenario_id = parsed_args.scenario_id
        # Get the scenario name
        scenario = c.execute(
            """SELECT scenario_name
            FROM scenarios
            WHERE scenario_id = {};""".format(parsed_args.scenario_id)
        ).fetchone()[0]

    print(scenario_id)

    plot = draw_dispatch_plot(
        c=c,
        scenario_id=scenario_id,
        load_zone=parsed_args.load_zone,
        horizon=parsed_args.horizon,
        stage=parsed_args.stage
    )

    # Show plot in HTML browser file if requested
    # TODO: deal with non-default scenario locations (Ana WIP)
    if parsed_args.show:
        figures_directory = os.path.join(
            os.getcwd(), "..", "scenarios", scenario, "results",
            "figures"
        )
        if not os.path.exists(figures_directory):
            os.makedirs(figures_directory)
        # TODO: file name should include load zone and horizon arguments
        output_file(os.path.join(figures_directory, 'dispatch_plot.html'))
        show(plot)

    # Return plot in json format if requested
    if parsed_args.return_json:
        return json_item(
            plot,
            "dispatchPlot-{}-{}".format(
                parsed_args.load_zone, parsed_args.horizon
            )
        )


if __name__ == "__main__":
    main()
