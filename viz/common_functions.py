#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""

import os.path
import sqlite3

from bokeh import events
from bokeh.models import CustomJS
from bokeh.plotting import output_file, show

from gridpath.common_functions import determine_scenario_directory, \
    create_directory_if_not_exists


def show_hide_legend(plot):
    """
    Show/hide the legend on double tap.

    :param plot:
    """
    def show_hide_legend_py(legend=plot.legend[0]):
        legend.visible = not legend.visible

    plot.js_on_event(
        events.DoubleTap,
        CustomJS.from_py_func(show_hide_legend_py)
    )


def show_plot(scenario_directory, scenario, plot, plot_name):
    """
    Show plot in HTML browser file if requested

    :param scenario_directory:
    :param scenario:
    :param plot:
    :param plot_name:
    :return:
    """

    scenario_directory = determine_scenario_directory(
        scenario_location=scenario_directory, scenario_name=scenario)
    figures_directory = os.path.join(scenario_directory, "results", "figures")
    create_directory_if_not_exists(figures_directory)

    filename = plot_name + ".html"
    output_file(os.path.join(figures_directory, filename))
    show(plot)


def get_scenario_and_scenario_id(parsed_arguments, c):
    """
    Get the scenario and the scenario_id from the parsed arguments.

    Usually only one is given, so we determine the missing one from the one
    that is provided.

    :param parsed_arguments:
    :param c:
    :return:
    """

    if parsed_arguments.scenario_id is None:
        scenario = parsed_arguments.scenario
        # Get the scenario ID
        scenario_id = c.execute(
            """SELECT scenario_id
            FROM scenarios
            WHERE scenario_name = '{}';""".format(scenario)
        ).fetchone()[0]
    else:
        scenario_id = parsed_arguments.scenario_id
        # Get the scenario name
        scenario = c.execute(
            """SELECT scenario_name
            FROM scenarios
            WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

    return scenario, scenario_id
