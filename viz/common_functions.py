#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""

import os.path
import sqlite3

from bokeh import events
from bokeh.models import CustomJS
from bokeh.plotting import output_file, show


def connect_to_database(parsed_arguments):
    """
    Connect to the database

    :param parsed_arguments:
    :return:
    """
    if parsed_arguments.database is None:
        db_path = os.path.join(os.getcwd(), "..", "db", "io.db")
    else:
        db_path = parsed_arguments.database

    if not os.path.isfile(db_path):
        raise OSError(
            "The database file {} was not found. Did you mean to "
            "specify a different database file?".format(
                os.path.abspath(db_path)
            )
        )

    conn = sqlite3.connect(db_path)

    return conn


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


def show_plot(scenario, plot, plot_name):
    """
    Show plot in HTML browser file if requested

    :param scenario:
    :param plot:
    :param plot_name:
    :return:
    """

    figures_directory = os.path.join(
        os.getcwd(), "..", "scenarios", scenario, "results", "figures"
    )
    if not os.path.exists(figures_directory):
        os.makedirs(figures_directory)

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
