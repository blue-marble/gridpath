#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make plot of energy by period and technology for a specified zone/stage
"""

from argparse import ArgumentParser
from bokeh.embed import json_item

import pandas as pd
import sys

# GridPath modules
from db.common_functions import connect_to_database
from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from viz.common_functions import create_stacked_bar_plot, show_plot, \
    get_parent_parser, get_tech_colors, get_tech_plotting_order, get_unit, \
    process_stacked_plot_data


def create_parser():
    """

    :return:
    """
    parser = ArgumentParser(add_help=True, parents=[get_parent_parser()])
    parser.add_argument("--scenario_id", help="The scenario ID. Required if "
                                              "no --scenario is specified.")
    parser.add_argument("--scenario", help="The scenario name. Required if "
                                           "no --scenario_id is specified.")
    parser.add_argument("--load_zone",
                        help="The name of the load zone. Required")
    parser.add_argument("--stage", default=1,
                        help="The stage ID. Defaults to 1.")

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
    Get energy results by period for a given scenario/load_zone/stage.

    **kwargs needed, so that an error isn't thrown when calling this
    function with extra arguments from the UI.

    :param conn:
    :param scenario_id:
    :param load_zone:
    :param stage:
    :return:
    """

    # TODO: add curtailment and imports? What about storage charging?

    # Energy by period and technology
    # Spinup/lookahead timepoints are ignored by adding the resp. column tag
    # through inner joins and adding a conditional to ignore those timepoints
    sql = """SELECT period, technology, 
        sum(power_mw * timepoint_weight * number_of_hours_in_timepoint)
        as energy_mwh
        FROM results_project_dispatch_by_technology
        
        -- add temporal scenario id so we can join timepoints table
        INNER JOIN
        
        (SELECT temporal_scenario_id, scenario_id
        FROM scenarios)
        USING (scenario_id)
        
        -- filter out spinup_or_lookahead timepoints
        INNER JOIN
        
        (SELECT temporal_scenario_id, stage_id, subproblem_id, timepoint, 
        spinup_or_lookahead
        FROM inputs_temporal)
        USING (temporal_scenario_id, stage_id, subproblem_id, timepoint)
        
        WHERE scenario_id = ?
        AND load_zone = ?
        AND stage_id = ?
        AND spinup_or_lookahead is NULL
        
        GROUP BY period, technology"""

    df = pd.read_sql(
        sql,
        con=conn,
        params=(scenario_id, load_zone, stage)
    )

    return df


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
        script="energy_plot"
    )

    tech_colors = get_tech_colors(c)
    tech_plotting_order = get_tech_plotting_order(c)
    energy_unit = get_unit(c, "energy")

    plot_title = "{}Energy by Period - {} - Stage {}".format(
        "{} - ".format(scenario)
        if parsed_args.scenario_name_in_title else "",
        parsed_args.load_zone, parsed_args.stage)
    plot_name = "EnergyPlot-{}-{}".format(
        parsed_args.load_zone, parsed_args.stage)

    df = get_plotting_data(
        conn=conn,
        scenario_id=scenario_id,
        load_zone=parsed_args.load_zone,
        stage=parsed_args.stage
    )

    source, x_col_reordered = process_stacked_plot_data(
        df=df,
        y_col="energy_mwh",
        x_col=["period"],
        category_col="technology"
    )

    # Multi-level index in CDS will be joined into one column with "_" separator
    x_col_cds = "_".join(x_col_reordered)
    x_col_label = ", ".join([x.capitalize() for x in x_col_reordered])
    plot = create_stacked_bar_plot(
        source=source,
        x_col=x_col_cds,
        x_label=x_col_label,
        y_label="Energy ({})".format(energy_unit),
        category_label="Technology",
        category_colors=tech_colors,
        category_order=tech_plotting_order,
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
