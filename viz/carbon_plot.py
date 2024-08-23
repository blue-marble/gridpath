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
Create plot of carbon emissions by period for a given zone/subproblem/stage.
"""


from argparse import ArgumentParser
from bokeh.models import ColumnDataSource, Legend, NumeralTickFormatter
from bokeh.plotting import figure
from bokeh.models.tools import HoverTool
from bokeh.embed import json_item

import pandas as pd
import sys

# GridPath modules
from db.common_functions import connect_to_database
from gridpath.auxiliary.db_interface import get_scenario_id_and_name
from viz.common_functions import (
    show_hide_legend,
    show_plot,
    get_parent_parser,
    get_unit,
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
        "--carbon_cap_zone",
        required=True,
        type=str,
        help="The name of the carbon cap zone. Required",
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


def get_plotting_data(conn, scenario_id, carbon_cap_zone, subproblem, stage, **kwargs):
    """
    Get the carbon results by period for a given
    scenario/carbon_cap_zone/subproblem/stage.

    Note: Emissions in spinup and lookahead timepoints are included
    since the emissions in those timepoints will still count towards the cap.

    **kwargs needed, so that an error isn't thrown when calling this
    function with extra arguments from the UI.

    :param conn:
    :param scenario_id:
    :param carbon_cap_zone:
    :param subproblem:
    :param stage:
    :return:
    """

    sql = """
        SELECT 
            period, 
            carbon_cap_target, 
            project_emissions, 
            import_emissions_degen, 
            total_emissions_degen,
            carbon_cap_marginal_cost_per_emission
        FROM results_system_carbon_cap
        WHERE scenario_id = ?
        AND carbon_cap_zone = ?
        AND subproblem_id = ?
        AND stage_id = ?
        ;"""

    df = pd.read_sql(
        sql, con=conn, params=(scenario_id, carbon_cap_zone, subproblem, stage)
    )

    # For Testing:
    # df = pd.DataFrame(
    #     data=[[2018, 50, 40, 5, 45, 0],
    #           [2020, 20, 15, 5, 20, 100]],
    #     columns=["period", "carbon_cap_target", "project_emissions",
    #              "import_emissions_degen", "total_emissions_degen",
    #              "carbon_cap_marginal_cost_per_emission"]
    # )

    # Change period type from int to string (required for categorical bar chart)
    df["period"] = df["period"].map(str)

    # TODO: division will fail if total_emissions_degen is NULL, e.g. when
    #  there are no carbon transmission lines.
    # Add project/import fractions
    df["fraction_of_project_emissions"] = (
        df["project_emissions"] / df["total_emissions_degen"]
    )

    df["fraction_of_import_emissions"] = (
        df["import_emissions_degen"] / df["total_emissions_degen"]
    )

    return df


def create_plot(df, title, carbon_unit, cost_unit, ylimit=None):
    """

    :param df:
    :param title: string, plot title
    :param carbon_unit: string, the unit of carbon emissions used in the
    database/model, e.g. "tCO2"
    :param cost_unit: string, the unit of cost used in the database/model,
    e.g. "USD"
    :param ylimit: float/int, upper limit of y-axis; optional
    :return:
    """

    if df.empty:
        return figure()

    # Set up data source
    source = ColumnDataSource(data=df)

    # Determine column types for plotting, legend and colors
    # Order of stacked_cols will define order of stacked areas in chart
    x_col = "period"
    line_col = "carbon_cap"
    stacked_cols = ["project_emissions", "import_emissions_degen"]

    # Stacked Area Colors
    colors = ["#666666", "#999999"]

    # Set up the figure
    plot = figure(
        plot_width=800,
        plot_height=500,
        tools=["pan", "reset", "zoom_in", "zoom_out", "save", "help"],
        title=title,
        x_range=df[x_col],
        # sizing_mode="scale_both"
    )

    # Add stacked bar chart to plot
    bar_renderers = plot.vbar_stack(
        stackers=stacked_cols,
        x=x_col,
        source=source,
        color=colors,
        width=0.5,
    )

    # Add Carbon Cap target line chart to plot
    target_renderer = plot.circle(
        x=x_col,
        y=line_col,
        source=source,
        size=20,
        color="black",
        fill_alpha=0.2,
        line_width=2,
    )

    # Create legend items
    legend_items = [
        ("Project Emissions", [bar_renderers[0]]),
        ("Import Emissions", [bar_renderers[1]]),
        ("Carbon Target", [target_renderer]),
    ]

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
    plot.xaxis.axis_label = "Period"
    plot.yaxis.axis_label = "Emissions ({})".format(carbon_unit)
    plot.yaxis.formatter = NumeralTickFormatter(format="0,0")
    plot.y_range.end = ylimit  # will be ignored if ylimit is None

    # Add delivered RPS HoverTool
    r_delivered = bar_renderers[0]  # renderer for delivered RPS
    hover = HoverTool(
        tooltips=[
            ("Period", "@period"),
            (
                "Project Emissions",
                "@%s{0,0} %s (@fraction_of_project_emissions{0%%})"
                % (stacked_cols[0], carbon_unit),
            ),
        ],
        renderers=[r_delivered],
        toggleable=False,
    )
    plot.add_tools(hover)

    # Add curtailed RPS HoverTool
    r_curtailed = bar_renderers[1]  # renderer for curtailed RPS
    hover = HoverTool(
        tooltips=[
            ("Period", "@period"),
            (
                "Import Emissions",
                "@%s{0,0} %s (@fraction_of_import_emissions{0%%})"
                % (stacked_cols[1], carbon_unit),
            ),
        ],
        renderers=[r_curtailed],
        toggleable=False,
    )
    plot.add_tools(hover)

    # Add RPS Target HoverTool
    hover = HoverTool(
        tooltips=[
            ("Period", "@period"),
            ("Carbon Target", "@%s{0,0} %s" % (line_col, carbon_unit)),
            (
                "Marginal Cost",
                "@carbon_cap_marginal_cost_per_emission{0,0} %s/%s"
                % (cost_unit, carbon_unit),
            ),
        ],
        renderers=[target_renderer],
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
        script="carbon_plot",
    )

    carbon_unit = get_unit(c, "carbon_emissions")
    cost_unit = get_unit(c, "cost")

    plot_title = "{}Carbon Emissions by Period - {} - Subproblem {} - Stage {}".format(
        "{} - ".format(scenario) if parsed_args.scenario_name_in_title else "",
        parsed_args.carbon_cap_zone,
        parsed_args.subproblem,
        parsed_args.stage,
    )
    plot_name = "CarbonPlot-{}-{}-{}".format(
        parsed_args.carbon_cap_zone, parsed_args.subproblem, parsed_args.stage
    )

    df = get_plotting_data(
        conn=conn,
        scenario_id=scenario_id,
        carbon_cap_zone=parsed_args.carbon_cap_zone,
        subproblem=parsed_args.subproblem,
        stage=parsed_args.stage,
    )

    plot = create_plot(
        df=df,
        title=plot_title,
        carbon_unit=carbon_unit,
        cost_unit=cost_unit,
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
