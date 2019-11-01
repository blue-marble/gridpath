#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make plot of project operations by timepoint a specified project/period/stage.
Assumes project is of the type "capacity commit"

Note: either there are no hovertools on step function (Bokeh issue #7419) and
working hovertools on stacked bar chart, or we can go continuous but then the
hovertool doesn't work for the stacked areas (#9182)
"""

from argparse import ArgumentParser
from bokeh.models import Legend, NumeralTickFormatter, ColumnDataSource
from bokeh.plotting import figure
from bokeh.models.tools import HoverTool
from bokeh.embed import json_item
from bokeh.palettes import grey

import pandas as pd
import sys

# GridPath modules
from db.common_functions import connect_to_database
from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from viz.common_functions import show_hide_legend, show_plot, get_parent_parser


def parse_arguments(arguments):
    """

    :return:
    """
    parser = ArgumentParser(add_help=True, parents=[get_parent_parser()])
    parser.add_argument("--scenario_id", help="The scenario ID. Required if "
                                              "no --scenario is specified.")
    parser.add_argument("--scenario", help="The scenario name. Required if "
                                           "no --scenario_id is specified.")
    parser.add_argument("--project", required=True, type=str,
                        help="The name of the project. Required")
    parser.add_argument("--period", required=True, type=int,
                        help="The desired modeling period. Required")
    parser.add_argument("--stage", default=1, type=int,
                        help="The stage ID. Defaults to 1.")
    parser.add_argument("--horizon_start", type=int,
                        help="The desired starting horizon. Assumes horizons"
                             "are a set of increasing numbers. Optional")
    parser.add_argument("--horizon_end", type=int,
                        help="The desired ending horizon. Assumes horizons are"
                             "a set of increasing numbers. Optional")

    # Parse arguments
    parsed_arguments = parser.parse_args(args=arguments)

    return parsed_arguments


def get_plotting_data(conn, scenario_id, project, period, stage,
                      horizon_start, horizon_end, **kwargs):
    """
    Get operations by timepoint for a given scenario/project/period/stage and
    horizon range.

    **kwargs needed, so that an error isn't thrown when calling this
    function with extra arguments from the UI.

    :param conn:
    :param scenario_id:
    :param project:
    :param period:
    :param stage:
    :param horizon_start:
    :param horizon_end:
    :return:
    """

    # TODO: this seems a kludgy way to deal with this. It might make more sense
    #    to harmonize the dispatch tables such that there is only one and just
    #    NULL out results that don't apply (e.g. commitment decisions for
    #    projects with no commitments
    # Get operational type to determine table
    c = conn.cursor()
    sql = """SELECT operational_type from inputs_project_operational_chars
        INNER JOIN scenarios
        USING (project_operational_chars_scenario_id)
        WHERE scenario_id = ?
        AND project = ?
        ;"""
    operational_type = c.execute(sql, (scenario_id, project)).fetchone()[0]

    if operational_type == "dispatchable_capacity_commit":
        table = "results_project_dispatch_capacity_commit"
    elif operational_type == "dispatchable_binary_commit":
        table = "results_project_dispatch_binary_commit"
    elif operational_type == "dispatchable_continuous_commit":
        table = "results_project_dispatch_continuous_commit"
    else:
        raise ValueError(
            "Selected project does not have commitment decisions."
            "Please select a project of one of the operational types with "
            "commitment decisions: 'distpachable_capacity_commit', "
            "'dispatchable_binary_commit' or 'dispatchable_continuous_commit'"
        )

    # TODO: Could avoid SQL insertions by addding the WHERE clause anywhere
    #   but changing the value we check
    #   (default would be start = 0 and end = 999999999)
    #   However, the table insertion is unavoidable with this approach
    if horizon_start is not None:
        horizon_start_slice = "AND horizon >= {}".format(horizon_start)
    else:
        horizon_start_slice = ""

    if horizon_end is not None:
        horizon_end_slice = "AND horizon <= {}".format(horizon_end)
    else:
        horizon_end_slice = ""

    # Project operations (commitment, power, and reserves)
    sql = """
        SELECT scenario_id, project, period, horizon, timepoint,
        SUM(number_of_hours_in_timepoint) 
        OVER (PARTITION BY horizon ORDER BY timepoint) AS hour_on_horizon,
        SUM(number_of_hours_in_timepoint) 
        OVER (PARTITION BY period ORDER BY timepoint) AS hour_on_period,
        committed_mw, power_mw, 
        (min_stable_level * committed_mw) AS min_stable_level_mw,
        spin_mw, reg_up_mw, reg_down_mw, lf_up_mw, lf_down_mw, frq_resp_mw
        FROM
        (SELECT scenario_id, project, period, stage_id, horizon, timepoint, 
        number_of_hours_in_timepoint,
        committed_mw, power_mw
        FROM {}
        WHERE scenario_id = ?
        {} 
        {}
        AND project = ?
        AND period = ?
        AND stage_id = ?) AS commitment_table
        
        LEFT JOIN
        
        (SELECT scenario_id, project, period, stage_id, horizon, timepoint,
        reserve_provision_mw as spin_mw 
        FROM results_project_spinning_reserves) AS spin_tbl
        USING (scenario_id, project, period, stage_id, horizon, timepoint)
        
        LEFT JOIN
        
        (SELECT scenario_id, project, period, stage_id, horizon, timepoint,
        reserve_provision_mw as reg_up_mw 
        FROM results_project_regulation_up) AS reg_up_tbl
        USING (scenario_id, project, period, stage_id, horizon, timepoint)
        
        LEFT JOIN
        
        (SELECT scenario_id, project, period, stage_id, horizon, timepoint,
        reserve_provision_mw as reg_down_mw 
        FROM results_project_regulation_down) AS reg_down_tbl
        USING (scenario_id, project, period, stage_id, horizon, timepoint)
        
        LEFT JOIN
        
        (SELECT scenario_id, project, period, stage_id, horizon, timepoint,
        reserve_provision_mw as lf_up_mw 
        FROM results_project_lf_reserves_up) AS lf_up_tbl
        USING (scenario_id, project, period, stage_id, horizon, timepoint)
        
        LEFT JOIN
        
        (SELECT scenario_id, project, period, stage_id, horizon, timepoint,
        reserve_provision_mw as lf_down_mw 
        FROM results_project_lf_reserves_down) AS lf_down_tbl
        USING (scenario_id, project, period, stage_id, horizon, timepoint)
        
        LEFT JOIN
        
        (SELECT scenario_id, project, period, stage_id, horizon, timepoint,
        reserve_provision_mw as frq_resp_mw 
        FROM results_project_frequency_response) AS frq_resp_tbl
        USING (scenario_id, project, period, stage_id, horizon, timepoint)
        
        LEFT JOIN
        
        (SELECT scenario_id, project, min_stable_level
        FROM inputs_project_operational_chars
        JOIN scenarios
        USING (project_operational_chars_scenario_id)
        ) as op_table
        USING (scenario_id, project)
        
        ORDER BY horizon, timepoint
        ;""".format(table, horizon_start_slice, horizon_end_slice)

    df = pd.read_sql(
        sql,
        con=conn,
        params=(scenario_id, project, period, stage)
    )

    # Add additional info for hovers
    df["power_pct_of_committed"] = df["power_mw"] / df["committed_mw"]
    df["min_stable_level_pct_of_committed"] = \
        df["min_stable_level_mw"] / df["committed_mw"]

    # Add helper columns for reserves
    df["bottom_reserves"] = df["power_mw"] - \
        df[["reg_down_mw", "lf_down_mw"]].sum(axis=1)

    # Rename columns for cleaner plotting
    rename_dict = {
        "power_mw": "Power",
        "committed_mw": "Committed Capacity",
        "min_stable_level_mw": "Minimum Output",
        "reg_down_mw": "Regulation Down",
        "lf_down_mw": "Load Following Down",
        "lf_up_mw": "Load Following Up",
        "reg_up_mw": "Regulation Up",
        "frq_resp_mw": "Frequency Response",
        "spin_mw": "Spinning Reserves"
    }
    df.rename(columns=rename_dict, inplace=True)

    return df


def create_plot(df, title, ylimit=None):
    """

    :param df:
    :param title: string, plot title
    :param ylimit: float/int, upper limit of y-axis; optional
    :return:
    """

    # Set up data source
    source = ColumnDataSource(data=df)

    # Determine column types for plotting, legend and colors
    x_col = "hour_on_period"
    power_col = "Power"
    commitment_col = "Committed Capacity"
    stable_level_col = "Minimum Output"
    all_reserves = ["bottom_reserves", "Regulation Down", "Load Following Down",
                    "Load Following Up", "Regulation Up",
                    "Frequency Response", "Spinning Reserves"]
    active_reserves = list(df[all_reserves].columns[
        df[all_reserves].notna().all() &
        df[all_reserves].mean() > 0
    ])

    # Setup the reserve colors
    colors = grey(len(active_reserves)+2)[1:-1]  # skip the white/black colors
    alphas = [0] + [1] * (len(active_reserves)-1) if active_reserves else []

    # Set up the figure
    plot = figure(
        plot_width=800, plot_height=500,
        tools=["pan", "reset", "zoom_in", "zoom_out", "save", "help"],
        title=title,
    )

    # Add reserve area renderers
    area_renderers = plot.vbar_stack(
        stackers=active_reserves,
        x=x_col,
        source=source,
        fill_color=colors,
        fill_alpha=alphas,
        line_color=colors,
        line_alpha=alphas,
        width=1,
    )

    # Add operations to plot
    power_renderer = plot.step(
        name="Power",
        source=source,
        x=x_col,
        y=power_col,
        color="black",
        mode="center",
    )
    commitment_renderer = plot.step(
        name="Committed Capacity",
        source=source,
        x=x_col,
        y=commitment_col,
        color="black",
        line_dash="dashed",
        mode="center",
    )
    stable_level_renderer = plot.step(
        name="Minimum Output",
        source=source,
        x=x_col,
        y=stable_level_col,
        color="black",
        line_dash="dotted",
        mode="center",
    )

    # Add legend items
    legend_items = [
        (commitment_renderer.name, [commitment_renderer]),
        (power_renderer.name, [power_renderer]),
        (stable_level_renderer.name, [stable_level_renderer])
    ] + list(reversed([(r.name, [r]) for r in area_renderers[1:]]))

    # Add Legend
    legend = Legend(items=legend_items)
    plot.add_layout(legend, 'right')
    plot.legend.click_policy = 'hide'  # Add interactivity to the legend
    # Note: Doesn't rescale the graph down, simply hides the area
    # Note2: There's currently no way to auto-size legend based on graph size(?)
    # except for maybe changing font size automatically?
    show_hide_legend(plot=plot)  # Hide legend on double click

    # Format Axes (labels, number formatting, range, etc.)
    plot.xaxis.axis_label = "Hour"
    plot.yaxis.axis_label = "MW"
    plot.yaxis.formatter = NumeralTickFormatter(format="0,0")
    plot.y_range.end = ylimit  # will be ignored if ylimit is None

    # Add HoverTools
    # Note: stepped lines or varea charts not yet supported (lines/bars OK)
    # Note: skip bottom renderer for vbars/areas since it's just a helper
    hover_renderers = area_renderers[1:] + \
        [commitment_renderer, power_renderer, stable_level_renderer]
    for r in hover_renderers:
        tooltips = [("Hour", "@%s" % x_col),
                    (r.name, "@$name{0,0} MW")]
        if r.name == "Power":
            tooltips.append(
                ("% of Committed", "@power_pct_of_committed{0%}")
            )
        elif r.name == "Minimum Output":
            tooltips.append(
                ("% of Committed", "@min_stable_level_pct_of_committed{0%}")
            )
        hover = HoverTool(tooltips=tooltips, renderers=[r], toggleable=False)
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
        script="project_operations_plot"
    )

    plot_title = "Operations Plot - {} - {} - Stage {}".format(
        parsed_args.project, parsed_args.period, parsed_args.stage)
    plot_name = "OperationsPlot-{}-{}-{}".format(
        parsed_args.project, parsed_args.period, parsed_args.stage)

    start = parsed_args.horizon_start
    end = parsed_args.horizon_end
    if start is not None and end is not None:
        appendix = " - Horizon {}-{}".format(start, end)
    elif start is not None and end is None:
        appendix = " - Horizon {}-end".format(start)
    elif start is None and end is not None:
        appendix = " - Horizon start-{}".format(end)
    else:
        appendix = ""

    plot_title += appendix

    df = get_plotting_data(
        conn=conn,
        scenario_id=scenario_id,
        project=parsed_args.project,
        period=parsed_args.period,
        stage=parsed_args.stage,
        horizon_start=parsed_args.horizon_start,
        horizon_end=parsed_args.horizon_end
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
