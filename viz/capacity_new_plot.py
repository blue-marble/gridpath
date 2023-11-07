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
Create plot of new capacity by period and technology for a given
scenario/zone/subproblem/stage.
"""

# TODO: should we calculate cumulative new capacity instead?

from argparse import ArgumentParser
from bokeh.embed import json_item

import pandas as pd
import sys

# GridPath modules
from db.common_functions import connect_to_database
from gridpath.auxiliary.db_interface import get_scenario_id_and_name
from viz.common_functions import (
    create_stacked_bar_plot,
    show_plot,
    get_parent_parser,
    get_tech_colors,
    get_tech_plotting_order,
    get_unit,
    get_capacity_data,
    process_stacked_plot_data,
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
        help="The name of the load zone. Required.",
    )
    parser.add_argument(
        "--subproblem", default=1, type=int, help="The subproblem ID. Defaults to 1."
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


def get_plotting_data(
    conn, subproblem, stage, scenario_id=None, load_zone=None, period=None, **kwargs
):
    """
    See get_capacity_data()

    **kwargs needed, so that an error isn't thrown when calling this
    function with extra arguments from the UI.
    """

    return get_capacity_data(
        conn, subproblem, stage, "new_build_mw", scenario_id, load_zone, period
    )


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
        script="capacity_new_plot",
    )

    tech_colors = get_tech_colors(c)
    tech_plotting_order = get_tech_plotting_order(c)
    power_unit = get_unit(c, "power")

    plot_title = "{}New Capacity by Period - {} - Subproblem {} - Stage {}".format(
        "{} - ".format(scenario) if parsed_args.scenario_name_in_title else "",
        parsed_args.load_zone,
        parsed_args.subproblem,
        parsed_args.stage,
    )
    plot_name = "NewCapacityPlot-{}-{}-{}".format(
        parsed_args.load_zone, parsed_args.subproblem, parsed_args.stage
    )

    df = get_plotting_data(
        conn=conn,
        scenario_id=scenario_id,
        load_zone=parsed_args.load_zone,
        subproblem=parsed_args.subproblem,
        stage=parsed_args.stage,
    )

    source, x_col_reordered = process_stacked_plot_data(
        df=df,
        y_col="capacity_mw",
        x_col=["period", "scenario"],
        category_col="technology",
    )

    # Multi-level index in CDS will be joined into one column with "_" separator
    x_col_cds = "_".join(x_col_reordered)
    x_col_label = ", ".join([x.capitalize() for x in x_col_reordered])
    plot = create_stacked_bar_plot(
        source=source,
        x_col=x_col_cds,
        x_label=x_col_label,
        y_label="New Capacity ({})".format(power_unit),
        category_label="Technology",
        category_colors=tech_colors,
        category_order=tech_plotting_order,
        title=plot_title,
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
