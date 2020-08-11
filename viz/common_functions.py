#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""

import os.path
from argparse import ArgumentParser

from bokeh import events
from bokeh.plotting import figure, output_file, show
from bokeh.models import CustomJS, ColumnDataSource, Legend, FactorRange, \
    NumeralTickFormatter
from bokeh.models.tools import HoverTool
from bokeh.palettes import cividis
import numpy as np
import pandas as pd

from gridpath.common_functions import create_directory_if_not_exists


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


def show_plot(plot, plot_name, plot_write_directory, scenario=None):
    """
    Show plot in HTML browser file if requested.

    When comparing scenario, the plot will be saved in the "scenario_comparison"
    subfolfder of the plot_write_directory.

    When looking at a particular scenario, the plot will be saved in the
    "scenario/results/figures" subfolder of the plot_write_directory.

    :param plot:
    :param plot_name:
    :param plot_write_directory:
    :param scenario: str, optional (not required if comparing scenarios)
    :return:
    """

    if scenario is None:
        plot_write_subdir = os.path.join(plot_write_directory,
                                         "scenario_comparison", "figures")
    else:
        plot_write_subdir = os.path.join(plot_write_directory, scenario,
                                         "results", "figures")

    create_directory_if_not_exists(plot_write_subdir)
    file_path = os.path.join(plot_write_subdir, plot_name + ".html")

    output_file(file_path)
    show(plot)


def get_parent_parser():
    """
    Create "parent" ArgumentParser object which has the common set of arguments
    that each plot requires. We can then simply add 'parents=[parent_parser]'
    when we create a parser for a plot to inherit these common arguments.

    Note that 'add_help' is set to 'False' to avoid multiple `-h/--help` options
    (one for parent and one for each child), which will throw an error.
    :return: 
    """

    parser = ArgumentParser(add_help=False)
    parser.add_argument("--database",
                        help="The database file path relative to the current "
                             "working directory. Defaults to ../db/io.db")
    parser.add_argument("--plot_write_directory", default="../scenarios",
                        help="The path to the base directory in which to save "
                             "the plot html file. Note: the file will be saved "
                             "in a subfolder of this base directory, generally "
                             "'scenario_name/results/figures'")
    parser.add_argument("--scenario_name_in_title", default=False,
                        action="store_true",
                        help="Include the scenario name in the plot title.")
    parser.add_argument("--ylimit", help="Set y-axis limit.", type=float)
    parser.add_argument("--show",
                        default=False, action="store_true",
                        help="Show figure and save html file")
    parser.add_argument("--return_json",
                        default=False, action="store_true",
                        help="Return plot as a json file.")

    return parser


def get_tech_colors(c):
    """
    Get the colors by technology as specified in the viz_technologies db
    table.

    :param c:
    :return:
    """
    colors = c.execute(
        """
        SELECT technology, color
        FROM viz_technologies
        WHERE color is not NULL
        """
    ).fetchall()

    return dict(colors)


def get_tech_plotting_order(c):
    """
    Get the plotting order of each technology as specified in the
    viz_technologies db table.

    :param c:
    :return:
    """

    order = c.execute(
        """
        SELECT technology, plotting_order
        FROM viz_technologies
        WHERE plotting_order is not NULL
        """
    ).fetchall()

    return dict(order)


def get_unit(c, metric):
    """
    Get the unit of measurement for a given metric

    :param c:
    :param metric: str, the metric for which we want the unit of measurement
    :return:
    """

    unit = c.execute("SELECT unit FROM mod_units WHERE metric=?", (metric,))

    if unit.rowcount == 0:
        raise ValueError(
            """
            Error! The metric '{}' does not exists in the mod_units table.
            Please specify an existing metric. 
            """.format(metric)
        )
    else:
        return unit.fetchone()[0]


def reformat_stacked_plot_data(df, y_col, x_col, category_col,
                               column_mapper={}):
    """
    TODO: update docstrings
    Rename columns, pivot, and convert to Bokeh ColumnDataSource
    :param df: a data-base style DataFrame which should at least include the
    columns 'y_col', 'x_col' and 'category_col'. The
    'x_col' and 'category_col' should uniquely identify the value of
    the 'y_col' (e.g. capacity should be uniquely defined by the
    period and the technology).

    Example:
    data = {'year': [2018, 2018], 'mw': [5, 8], 'tech': ['t1', 't2']}
    df = pd.DataFrame(data)
    create_stacked_bar_plot(
        df=df,
        title="example_plot",
        y_col="mw",
        x_col="year",
        category_label="tech"
    )

    :param y_col:
    :param x_col:
    :param category_col: str, name of column to pivot
    :param column_mapper:
    :return:
    """

    # Change type of index to str, required for categorical bar chart
    # df.index = df.index.map(str)
    # x_col = ["period", "scenario_id"]
    x_col = x_col if isinstance(x_col, list) else [x_col]
    for col in x_col:
        df[col] = df[col].astype(str)

    # TODO: figure out if we need to index by all entries in x_col
    #  only do so if there are more than 1 unique

    # Pivot such that values in category column become column headers
    # Note: df.pivot doesn't work with list of indexes in v1.0.5. Fixed in 1.1.0
    df = pd.pivot_table(
        data=df,
        index=x_col,
        columns=category_col,
        values=y_col
    ).fillna(0).sort_index()  # sorting for grouped x-axis format

    # TODO: does this work for multi-index?
    # TODO: need to make sure that if index is not x_col, we need to remove
    #  the index from the CDS.

    # Rename columns (optional)
    df.rename(columns=column_mapper, index=column_mapper, inplace=True)
    # Set up Bokeh ColumnDataSource
    source = ColumnDataSource(data=df)

    # TODO: remove
    # df = pd.DataFrame(
    #     columns=["period", "solar", "wind", "gas"],
    #     data=[[("2020", "test_long_scenario_name"), 10, 5, 8],
    #           [("2030", "test"), 10, 5, 8],
    #           [("2040", "test"), 10, 5, 8],
    #           [("2020", "test2a;dlkjadsf;kj"), 10, 5, 8],
    #           [("2030", "test2eq;hda;hdd"), 10, 5, 8],
    #           [("2040", "test2"), 10, 5, 8],
    #           [("2020", "test3"), 10, 5, 8],
    #           [("2030", "test3"), 10, 5, 8],
    #           [("2040", "test3"), 10, 5, 8]
    #           ]
    # ).set_index(['period']).sort_index()  # sorting for grouped x-axis format
    #
    # source = ColumnDataSource(df)

    return source, x_col


def create_stacked_bar_plot(source, x_col, x_label=None, y_label=None,
                            category_label="Category", category_colors={},
                            category_order={}, title=None, ylimit=None
                            ):
    """
    Create a stacked bar chart from a Bokeh ColumnDataSource (CDS). The CDS
    should have have a "x_col" column where each element is either a string
    for a simple stacked bar charts or a tuple of strings for a grouped stacked
    bar chart. Note that strings are required for the categorical axis.
    All other columns are assumed to be categories that will be stacked in
    the bar chart.

    :param source: Bokeh ColumnDataSource
    :param x_col: str
    :param x_label: str, optional
    :param y_label: str, optional
    :param category_label: str, optional
    :param category_colors: dict, optional, maps categories to colors.
        Categories without a specified color will use a default palette
    :param category_order: dict, optional, maps categories to their
        plotting order in the stacked bar chart (lower = bottom)
    :param title: string, optional, plot title
    :param ylimit: float/int, optional, upper limit of y-axis
    :return:
    """

    # Determine column types for plotting, legend and colors
    # Order of stacked_cols will define order of stacked areas in chart
    cols = list(source.data.keys())
    cols.remove(x_col)
    for col in cols:
        if col not in category_order:
            category_order[col] = max(category_order.values(), default=0) + 1
    stacked_cols = sorted(cols, key=lambda x: category_order[x])

    # Set up color scheme. Use cividis palette for unspecified colors
    unspecified_columns = [c for c in stacked_cols
                           if c not in category_colors.keys()]
    unspecified_category_colors = dict(
        zip(unspecified_columns, cividis(len(unspecified_columns)))
    )
    colors = []
    for column in stacked_cols:
        if column in category_colors:
            colors.append(category_colors[column])
        else:
            colors.append(unspecified_category_colors[column])

    try:
        # Use FactorRange for stacked, grouped bar chart if x_col is tuple
        if isinstance(source.data[x_col][0], tuple):
            x_range = FactorRange(*source.data[x_col])
        else:
            x_range = source.data[x_col]
    except IndexError as e:
        x_range = []

    # Set up the figure
    plot = figure(
        plot_width=800, plot_height=500,
        tools=["pan", "reset", "zoom_in", "zoom_out", "save", "help"],
        title=title,
        x_range=x_range
        # sizing_mode="scale_both"
    )

    # Add stacked area chart to plot
    area_renderers = plot.vbar_stack(
        stackers=stacked_cols,
        x=x_col,
        source=source,
        color=colors,
        width=0.5,
        alpha=0.7  # transparancy
    )

    # Add Legend
    legend_items = [(y, [area_renderers[i]]) for i, y in enumerate(stacked_cols)
                    if np.mean(source.data[y]) > 0]
    legend = Legend(items=legend_items)
    plot.add_layout(legend, 'right')
    plot.legend.title = category_label
    plot.legend[0].items.reverse()  # Reverse legend to match stacked order
    plot.legend.click_policy = 'hide'  # Add interactivity to the legend
    show_hide_legend(plot=plot)  # Hide legend on double click

    # Format Axes (labels, number formatting, range, etc.)
    x_label = x_col if x_label is None else x_label
    plot.xaxis.axis_label = x_label
    plot.xaxis.major_label_orientation = 1
    plot.xgrid.grid_line_color = None
    if y_label is not None:
        plot.yaxis.axis_label = y_label
    plot.yaxis.formatter = NumeralTickFormatter(format="0,0")
    plot.y_range.end = ylimit  # will be ignored if ylimit is None

    # Add HoverTools for stacked bars/areas
    for r in area_renderers:
        category = r.name
        tooltips = [("%s" % x_label, "@{%s}" % x_col),
                    ("%s" % category_label, category)]
        if y_label is None:
            pass
        elif "$" in y_label or "USD" in y_label:
            tooltips.append(("%s" % y_label, "@%s{$0,0}" % category))
        else:
            tooltips.append(("%s" % y_label, "@%s{0,0}" % category))
        hover = HoverTool(
            tooltips=tooltips,
            renderers=[r],
            toggleable=False)
        plot.add_tools(hover)

    return plot
