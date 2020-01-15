#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""

import os.path
from argparse import ArgumentParser

from bokeh import events
from bokeh.plotting import figure, output_file, show
from bokeh.models import CustomJS, ColumnDataSource, Legend, \
    NumeralTickFormatter
from bokeh.models.tools import HoverTool
from bokeh.palettes import cividis

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
                        help="The database file path. Defaults to ../db/io.db "
                             "if not specified")
    parser.add_argument("--plot_write_directory", default="../scenarios",
                        help="The path to the base directory in which to save "
                             "the plot html file. Note: the file will be saved "
                             "in a subfolder of this base directory, generally "
                             "'scenario_name/results/figures'")
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


def create_stacked_bar_plot(df, title, y_axis_column, x_axis_column,
                            group_column, column_mapper={}, group_colors={},
                            group_order={}, ylimit=None):
    """
    Create a stacked bar chart based on a DataFrame and the desired x-axis,
    y-axis, and group (category). Different groups/categories will be stacked.

    Example:
        data = {'year': [2018, 2018], 'mw': [5, 8], 'tech': ['t1', 't2']}
        df = pd.DataFrame(data)
        create_stacked_bar_plot(
            df=df,
            title="example_plot",
            y_axis_column="mw",
            x_axis_column="year",
            group_column="tech"
        )

    :param df: a data-base style DataFrame which should at least include the
        columns 'y_axis_column', 'x_axis_column' and 'group_column'. The
        'x_axis_column' and 'group_column' should uniquely identify the value of
        the 'y_axis_column' (e.g. capacity should be uniquely defined by the
        period and the technology).
    :param title: string, plot title
    :param y_axis_column:
    :param x_axis_column:
    :param group_column:
    :param column_mapper: optional dict that maps columns names to cleaner
        labels, e.g. 'capacity_mw' becomes 'Capacity (MW)'
    :param group_colors: optional dict that maps groups to colors. Groups
        without a specified color will use a default palette
    :param group_order: optional dict that maps groups to their plotting order
        in the stacked bar chart (lower = bottom)
    :param ylimit: float/int, upper limit of y-axis; optional
    :return:
    """

    # Rename axis/group labels using mapper (if specified)
    for k, v in column_mapper.items():
        y_axis_column = y_axis_column.replace(k, v)
        x_axis_column = x_axis_column.replace(k, v)
        group_column = group_column.replace(k, v)

    # Pre-process DataFrame:
    # 1. rename
    df.rename(columns=column_mapper, inplace=True)
    # 2. Pivot such that values in group column become column headers
    df = df.pivot(
        index=x_axis_column,
        columns=group_column,
        values=y_axis_column
    ).fillna(0)
    # 3. Change type of index to str, required for categorical bar chart
    df.index = df.index.map(str)

    # Set up data source
    source = ColumnDataSource(data=df)

    # Determine column types for plotting, legend and colors
    # Order of stacked_cols will define order of stacked areas in chart
    for col in df.columns:
        if col not in group_order:
            group_order[col] = max(group_order.values(), default=0) + 1
    stacked_cols = sorted(df.columns, key=lambda x: group_order[x])

    # Set up color scheme. Use cividis palette for unspecified colors
    unspecified_columns = [c for c in stacked_cols
                           if c not in group_colors.keys()]
    unspecified_group_colors = dict(zip(unspecified_columns,
                                        cividis(len(unspecified_columns))))
    colors = []
    for column in stacked_cols:
        if column in group_colors:
            colors.append(group_colors[column])
        else:
            colors.append(unspecified_group_colors[column])

    # Set up the figure
    plot = figure(
        plot_width=800, plot_height=500,
        tools=["pan", "reset", "zoom_in", "zoom_out", "save", "help"],
        title=title,
        x_range=df.index.values
        # sizing_mode="scale_both"
    )

    # Add stacked area chart to plot
    area_renderers = plot.vbar_stack(
        stackers=stacked_cols,
        x=x_axis_column,
        source=source,
        color=colors,
        width=0.5,
    )

    # Add Legend
    legend_items = [(y, [area_renderers[i]]) for i, y in enumerate(stacked_cols)
                    if df[y].mean() > 0]
    legend = Legend(items=legend_items)
    plot.add_layout(legend, 'right')
    plot.legend.title = group_column
    plot.legend[0].items.reverse()  # Reverse legend to match stacked order
    plot.legend.click_policy = 'hide'  # Add interactivity to the legend
    show_hide_legend(plot=plot)  # Hide legend on double click

    # Format Axes (labels, number formatting, range, etc.)
    plot.xaxis.axis_label = "{}".format(x_axis_column)
    plot.yaxis.axis_label = "{}".format(y_axis_column)
    plot.yaxis.formatter = NumeralTickFormatter(format="0,0")
    plot.y_range.end = ylimit  # will be ignored if ylimit is None

    # Add HoverTools for stacked bars/areas
    for r in area_renderers:
        group = r.name
        if "$" in y_axis_column:
            y_axis_formatter = "@%s{$0,0}" % group
        else:
            y_axis_formatter = "@%s{0,0}" % group
        hover = HoverTool(
            tooltips=[
                ("%s" % x_axis_column, "@{%s}" % x_axis_column),
                ("%s" % group_column, group),
                ("%s" % y_axis_column, y_axis_formatter)
            ],
            renderers=[r],
            toggleable=False)
        plot.add_tools(hover)

    return plot
