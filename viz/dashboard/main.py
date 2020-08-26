#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
To run: navigate ./viz/ folder and run:
"bokeh serve dashboard --show"

TODO:
 - NEW: add scenario ID as drop down
 - NEW: link capacity plots and eneryg plot to real data
 - NEW: link summary plot to real data
 - replace dummy data with real sql scripts pulling data
     also requires adding database connection and parsers
 - add a PreText title that summaries everything
   (which load_zones selected etc.)
 - allow "all zones" option
 - add stage selector
 - add tabs with more info:
    - storage tab (on duration and charge/discharge behavior + losses?)
    - transmission tab
    - policy tab
    - violations table (unserved energy, reserves, rps, carbon, etc.)
    - duals table
 - add additional plots/info on main screen (think about what makes sense)
 - try and re-use existing stacked bar functionality
    might have to break it out since want to use CDS as function arg
    at the very least, should also use custom colors/order and custom units
 - could have a global variable that specifies whether dashboard is across
   periods or across scenarios? (if across periods, specify scenario, if
   across scenarios, specify periods)?
   --> on UI side, would select scenario and have button to generate dashboard,
   or similarly, select period, and generate dashboard that compares scenarios

Notes:
    General idea should be to load in all data (all periods / load zones)
    ONCE in general scope, and then have updater functions in callbacks
    that slice out appropriate data (and perhaps do some pivoting)


Questions:
    how to integrate with UI
    using Bokeh framework vs. using UI framework to combine charts and provide
    interactivity (easier with Bokeh?)
    duplicate efforts between the inputs overview and results overview? (how
    to overcome; maybe re-use plotting functions? --> requires some rewrite).

"""

from argparse import ArgumentParser
from bokeh.embed import json_item
from bokeh.models import Tabs, Panel, PreText, Select, ColumnDataSource, \
    Legend, NumeralTickFormatter, DataTable, TableColumn
from bokeh.models.tools import HoverTool
from bokeh.io import curdoc, show
from bokeh.layouts import column, row
from bokeh.plotting import figure
from bokeh.palettes import cividis

import pandas as pd
import sys

# GridPath modules
from db.common_functions import connect_to_database
from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from viz.common_functions import show_hide_legend

# TODO: base on actual data
ZONE_OPTIONS = ['Zone1', 'Zone2']  # todo: Add "all" option
CAP_OPTIONS = ['new_cap', 'cumulative_new_cap', 'retired_cap',
               'cumulative_retired_cap', 'total_cap']
COST_COMPONENTS = ["capacity_cost", "fuel_cost", "vom_cost", "startup_cost",
                   "shutdown_cost"]


# Data gathering functions
def get_all_summary_data(conn, scenario_id):
    df = pd.DataFrame(
        columns=['period', 'stage', 'load_zone', 'total_cost', 'load',
                 'average_cost', 'emissions', 'rps_gen_pct', 'curtailment_pct',
                 'cumulative_new_capacity', 'unserved_energy'],
        data=[[2020, 1, 'Zone1', 20000, 8000, 50, 3000, 0.6, 0.04, 30000, 0],
              [2030, 1, 'Zone1', 20000, 8000, 50, 3000, 0.6, 0.04, 30000, 0],
              [2040, 1, 'Zone1', 20000, 8000, 50, 3000, 0.6, 0.04, 30000, 0],
              [2020, 1, 'Zone2', 10000, 5000, 40, 3000, 0.5, 0.02, 20000, 0],
              [2030, 1, 'Zone2', 10000, 5000, 40, 3000, 0.5, 0.02, 20000, 0],
              [2040, 1, 'Zone2', 20000, 8000, 50, 3000, 0.6, 0.04, 30000, 0],
              ]
    )
    #  TODO: look at results tool RESOLVE for more metrics
    # 'Unpivot' from wide to long format
    df = pd.melt(
        df,
        id_vars=['period', 'stage', 'load_zone'],
        var_name='summary_metric',
        value_name='value'
    )
    # TODO: sort metrics in a way that we want them (not alphabetically)
    df['period'] = df['period'].astype(str)  # Bokeh CDS needs string columns

    # Pivot periods into columms
    df = pd.pivot_table(
        df,
        index=['stage', 'load_zone', 'summary_metric'],
        columns='period',
        values='value'
    ).fillna(0).reset_index()

    # df = df.drop(["stage", "load_zone"], axis=1)
    return df


def get_all_cost_data(conn, scenario_id):
    # get data for all zones and periods
    # TODO: use COST COMPONENTS var?
    idx_cols = ['period', 'stage', 'load_zone']
    value_cols = ['capacity_cost', 'fuel_cost', 'vom_cost',
                  'startup_cost', 'shutdown_cost']
    df = pd.DataFrame(
        columns=['period', 'stage', 'load_zone',
                 'capacity_cost', 'fuel_cost', 'vom_cost',
                 'startup_cost', 'shutdown_cost'],
        data=[[2020, 1, 'Zone1', 10, 10, 10, 10, 10],
              [2020, 1, 'Zone2', 0, 0, 0, 0, 0],
              [2030, 1, 'Zone1', 20, 20, 20, 20, 20],
              [2030, 1, 'Zone2', 0, 0, 0, 0, 0],
              [2040, 1, 'Zone1', 30, 30, 30, 30, 30],
              [2040, 1, 'Zone2', 20, 20, 20, 20, 20]
              ]
    )

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh

    return df, idx_cols, value_cols


def get_all_capacity_data(conn, scenario_id):
    # get data for all zones and periods
    df = pd.DataFrame(
        columns=['period', 'stage', 'load_zone', 'technology'] + CAP_OPTIONS,
        data=[[2020, 1, 'Zone1', 'Solar', 10, 10, 0, 0, 50],
              [2030, 1, 'Zone1', 'Solar', 10, 20, 0, 0, 60],
              [2040, 1, 'Zone1', 'Solar', 10, 30, 0, 0, 70],
              [2020, 1, 'Zone1', 'Wind', 10, 10, 0, 0, 20],
              [2030, 1, 'Zone1', 'Wind', 10, 20, 0, 0, 30],
              [2040, 1, 'Zone1', 'Wind', 10, 30, 0, 0, 40],
              [2020, 1, 'Zone2', 'Solar', 0, 0, 0, 0, 20],
              [2030, 1, 'Zone2', 'Solar', 10, 10, 0, 0, 30],
              [2040, 1, 'Zone2', 'Solar', 10, 20, 0, 0, 40],
              [2020, 1, 'Zone2', 'Wind', 20, 20, 0, 0, 30],
              [2030, 1, 'Zone2', 'Wind', 10, 30, 0, 0, 40],
              [2040, 1, 'Zone2', 'Wind', 10, 40, 0, 0, 50]
              ]
    )

    # 'Unpivot' from wide to long format
    df = pd.melt(
        df,
        id_vars=['period', 'stage', 'load_zone', 'technology'],
        var_name='capacity_metric',
        value_name='capacity'
    )

    # Pivot technologies to wide format (for stack chart)
    # Note: df.pivot does not work with multi-index as of pandas 1.0.5
    idx_cols = ['period', 'stage', 'load_zone', 'capacity_metric']
    value_cols = list(df['technology'].unique())
    df = pd.pivot_table(
        df,
        index=idx_cols,
        columns='technology',
        values='capacity'
    ).fillna(0).reset_index()

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh

    return df, idx_cols, value_cols


def get_all_energy_data(conn, scenario_id):
    # get data for all zones and periods
    df = pd.DataFrame(
        columns=['period', 'stage', 'load_zone', 'technology', 'energy'],
        data=[[2020, 1, 'Zone1', 'Solar', 10],
              [2030, 1, 'Zone1', 'Solar', 10],
              [2040, 1, 'Zone1', 'Solar', 10],
              [2020, 1, 'Zone1', 'Wind', 20],
              [2030, 1, 'Zone1', 'Wind', 20],
              [2040, 1, 'Zone1', 'Wind', 20],
              [2020, 1, 'Zone2', 'Solar', 0],
              [2030, 1, 'Zone2', 'Solar', 10],
              [2040, 1, 'Zone2', 'Solar', 20],
              [2020, 1, 'Zone2', 'Wind', 20],
              [2030, 1, 'Zone2', 'Wind', 30],
              [2040, 1, 'Zone2', 'Wind', 40]
              ]
    )

    # Pivot technologies to wide format (for stack chart)
    # Note: df.pivot does not work with multi-index as of pandas 1.0.5
    idx_cols = ['period', 'stage', 'load_zone']
    value_cols = list(df['technology'].unique())
    df = pd.pivot_table(
        df,
        index=idx_cols,
        columns='technology',
        values='energy'
    ).fillna(0).reset_index()

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh

    return df, idx_cols, value_cols


# Plot creation functions
def get_stacked_plot_by_period(source, stackers, title,
                               y_axis_label="", legend_title=""):
    # TODO: configure layout better (less tall)
    # TODO: add axes
    # TODO: add legend title
    # Note: x_range is necessary for categorical plot; make sure dtype is str
    plot = figure(
        title=title,
        x_range=source.data['period'],
        plot_width=600, plot_height=300,

    )
    area_renderers = plot.vbar_stack(
        stackers=stackers,
        x='period',
        source=source,
        color=cividis(len(stackers)),
        width=0.5
    )
    # Note: cannot use legend=stackers because there is an issue when the legend
    # and column names are the same, see here:
    # https://github.com/bokeh/bokeh/issues/5365

    # Add Legend
    legend_items = [(y, [area_renderers[i]]) for i, y in enumerate(stackers)
                    if source.data[y].mean() > 0]
    legend = Legend(items=legend_items)
    plot.add_layout(legend, 'right')
    plot.legend.title = legend_title
    plot.legend[0].items.reverse()  # Reverse legend to match stacked order
    plot.legend.click_policy = 'hide'  # Add interactivity to the legend
    show_hide_legend(plot=plot)  # Hide legend on double click

    # Format Axes (labels, number formatting, range, etc.)
    x_axis_label = "Period"
    plot.xaxis.axis_label = x_axis_label
    plot.yaxis.axis_label = y_axis_label
    plot.yaxis.formatter = NumeralTickFormatter(format="0,0")
    # plot.y_range.end = ylimit  # will be ignored if ylimit is None

    # Add HoverTools
    for r in area_renderers:
        group = r.name
        if "$" in y_axis_label or "USD" in y_axis_label:
            y_axis_formatter = "@%s{$0,0}" % group
        else:
            y_axis_formatter = "@%s{0,0}" % group
        hover = HoverTool(
            tooltips=[
                ("%s" % x_axis_label, "@{period}"),
                ("%s" % legend_title, group),
                ("%s" % y_axis_label, y_axis_formatter)
            ],
            renderers=[r],
            toggleable=False)
        plot.add_tools(hover)

    return plot


# Define callbacks
def zone_change(attr, old, new):
    """
    When the selected load zone changes, update the cost, energy and capacity.
    """
    active_zone = new  # global var
    update_summary_data(zone=new)
    update_cost_data(zone=new)
    update_energy_data(zone=new)
    update_capacity_data(zone=new, capacity_metric=capacity_select.value)


def capacity_change(attr, old, new):
    """
    When the selected capacity metric changes, update the capacity.
    """
    update_capacity_data(zone=zone_select.value, capacity_metric=new)


# TODO: Update summary table when zone changes!
def update_summary_data(zone="Zone1"):
    """
    Update the ColumnDataSource object 'summary_source' with the appropriate
    load_zone slice of the data.
    :param zone:
    :return:
    """
    slice = summary[summary["load_zone"] == zone]
    slice = slice.drop(['load_zone', 'stage'], axis=1)
    new_src = ColumnDataSource(slice)
    summary_source.data.update(new_src.data)
    # Can als do <cost_source.data = slice> but this is better?


# TODO: deal with default zone more generally (dynamic link or "All" or first
#  one)
def update_cost_data(zone="Zone1"):
    """
    Update the ColumnDataSource object 'cost_source' with the appropriate
    load_zone slice of the data.
    :param zone:
    :return:
    """
    slice = cost[cost["load_zone"] == zone]
    new_src = ColumnDataSource(slice)
    cost_source.data.update(new_src.data)
    # Can als do <cost_source.data = slice> but '.update' is better?


def update_energy_data(zone="Zone1"):
    """
    Update the ColumnDataSource object 'energy_source' with the appropriate
    load_zone slice of the data.
    :param zone:
    :return:
    """
    slice = energy[energy["load_zone"] == zone]
    new_src = ColumnDataSource(slice)
    energy_source.data.update(new_src.data)


def update_capacity_data(zone="Zone1", capacity_metric="new_cap"):
    """
    Update the ColumnDataSource object 'cost_source' with the appropriate
    load_zone slice of the data, and with the appropriate capacity metric.
    :param zone:
    :param capacity_metric:
    :return:
    """
    slice = capacity[(capacity["load_zone"] == zone)
                     & (capacity["capacity_metric"] == capacity_metric)]
    new_src = ColumnDataSource(slice)
    capacity_source.data.update(new_src.data)


# TODO: need to dynamically link initial zone value (or set to "all"?)
# Set up widgets
zone_select = Select(title="Load Zone:", value='Zone1', options=ZONE_OPTIONS)
capacity_select = Select(title="Capacity Metric:", value='new_cap',
                         options=CAP_OPTIONS)

# Get the data (make sure we do this in global scope vs. in callbacks)
# TODO: get actual connection and data
conn = "dbtest"
scenario_id = 1
summary = get_all_summary_data(conn, scenario_id)
cost, cost_idx_cols, cost_value_cols = get_all_cost_data(conn, scenario_id)
capacity, capacity_idx_cols, capacity_value_cols = \
    get_all_capacity_data(conn, scenario_id)
energy, energy_idx_cols, energy_value_cols = \
    get_all_energy_data(conn, scenario_id)

# Set up CDS and update with default values
# TODO: is there better way to set up initial CDS?
summary_source = ColumnDataSource()
cost_source = ColumnDataSource()
energy_source = ColumnDataSource()
capacity_source = ColumnDataSource()

# TODO: maybe deal with defaults here? (e.g. update with first zone in list)
update_summary_data()
update_cost_data()
update_capacity_data()
update_energy_data()

# Set up Bokeh DataTable for summary
cols_to_use = [c for c in summary.columns if c not in ['load_zone', 'stage']]
columns = [TableColumn(field=c, title=c) for c in cols_to_use]
summary_table = DataTable(columns=columns, source=summary_source, height=250)

# Set up plots
cost_plot = get_stacked_plot_by_period(
    cost_source,
    stackers=cost_value_cols,
    title="Cost by Component",
    legend_title="Cost Component",
    y_axis_label="Cost (million USD)"  # TODO: link to units
)
energy_plot = get_stacked_plot_by_period(
    energy_source,
    stackers=energy_value_cols,
    title="Energy by Technology",
    legend_title="Technology",
    y_axis_label="Energy (MWh)"  # TODO: link to units
)
cap_plot = get_stacked_plot_by_period(
    capacity_source,
    stackers=capacity_value_cols,
    title="Capacity by Technology",
    legend_title="Technology",
    y_axis_label="Capacity (MW)"  # TODO: link to units
)

active_zone = 'Zone1'

# Set up callback behavior
zone_select.on_change('value', zone_change)
capacity_select.on_change('value', capacity_change)

# Set up layout
title = PreText(text="title goes here specifying active zone: {} "
                     "etc.".format(active_zone))
top_row = row(summary_table, column(zone_select, capacity_select))
middle_row = row(cap_plot, energy_plot)
bottom_row = row(cost_plot)
layout = column(title, top_row, middle_row, bottom_row)

# Set up tabs
# TODO: have main.py just assemble tabs and each tab in a different script?
tab1 = Panel(child=layout, title='General')
storage_dummy = PreText(text='storage summary here, incl. duration', width=600)
policy_dummy = PreText(text='policy summary here, including duals', width=600)
inputs_dummy = PreText(text='inputs summary here, e.g. loads (profile charts, min, max, avg), costs',
                       width=600)
tab2 = Panel(child=storage_dummy, title='Storage')
tab3 = Panel(child=policy_dummy, title='Policy Targets')
tab4 = Panel(child=inputs_dummy, title='Inputs')
# Put all the tabs into one application
tabs = Tabs(tabs=[tab1, tab2, tab3, tab4])

# Set up curdoc
curdoc().add_root(tabs)
curdoc().title = "Dashboard"
