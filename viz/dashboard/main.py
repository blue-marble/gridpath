#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
To run: navigate ./viz/ folder and run:
"bokeh serve dashboard --show"

TODO:
 - NEW: add scenario ID as drop down (and allow multiple)
 - NEW: allow multiple zones
 - NEW: link capacity plots and energy plot to real data
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
 - New req/dependency: sqlalchemy (not sure why we didn't need it before?)

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
from bokeh.models import Tabs, Panel, PreText, Select, ColumnDataSource, \
    DataTable, TableColumn
from bokeh.io import curdoc
from bokeh.layouts import column, row

import pandas as pd

# GridPath modules
from db.common_functions import connect_to_database
from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from viz.common_functions import create_stacked_bar_plot

# TODO: base on actual data
ZONE_OPTIONS = ['Zone1', 'Zone2']  # todo: Add "all" option
CAP_OPTIONS = ["new_build_capacity", "retired_capacity", "total_capacity",
               "cumulative_new_build_capacity", "cumulative_retired_capacity"]
COST_COMPONENTS = ["capacity_cost", "fuel_cost", "variable_om_cost",
                   "startup_cost", "shutdown_cost"]
# todo: cost components not used
SCENARIO = "test"
scenario_id = 23
DB_PATH = "../db/test_examples2.db"  # TODO: link to UI or parsed arg?


def get_all_cost_data(conn, scenario_id):
    # get data for all zones and periods

    # TODO: add tx deliverability costs, but those aren't by zone!
    #  might just keep zone NULL and make sure filter can deal with it
    # TODO: don't filter for certain scenario
    # TODO: filter for subproblem/stage (?)
    # idx_cols = ["scenario_id", "subproblem_id", "stage_id", "period",
    #             "load_zone"]
    idx_cols = ["period", "load_zone"]
    value_cols = ["capacity_cost", "variable_om_cost", "fuel_cost",
                  "startup_cost", "shutdown_cost", "tx_capacity_cost",
                  "tx_hurdle_cost"]
    sql = """SELECT {}
        FROM results_costs_by_period_load_zone
        WHERE scenario_id = ?;
        """.format(",".join(idx_cols + value_cols))

    df = pd.read_sql(sql, conn, params=(scenario_id,)).fillna(0)

    # idx_cols = ['period', 'load_zone']
    # value_cols = ['capacity_cost', 'fuel_cost', 'variable_om_cost',
    #               'startup_cost', 'shutdown_cost']
    # df = pd.DataFrame(
    #     columns=['period', 'load_zone',
    #              'capacity_cost', 'fuel_cost', 'variable_om_cost',
    #              'startup_cost', 'shutdown_cost'],
    #     data=[[2020, 'Zone1', 10, 10, 10, 10, 10],
    #           [2020, 'Zone2', 0, 0, 0, 0, 0],
    #           [2030, 'Zone1', 20, 20, 20, 20, 20],
    #           [2030, 'Zone2', 0, 0, 0, 0, 0],
    #           [2040, 'Zone1', 30, 30, 30, 30, 30],
    #           [2040, 'Zone2', 20, 20, 20, 20, 20]
    #           ]
    # )

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh
    return df, idx_cols, value_cols


def get_all_capacity_data(conn, scenario_id):
    # TODO: filter for subproblem/stage (?)
    # TODO: don't return value and idx cols (?)
    idx_cols = ["period", "load_zone", "technology"]
    sql = """SELECT {}, 
        SUM(new_build_mw) AS new_build_capacity, 
        SUM(retired_mw) AS retired_capacity, 
        SUM(capacity_mw) AS total_capacity
        FROM results_project_capacity
        WHERE scenario_id = ?
        GROUP BY {};
        """.format(",".join(idx_cols), ",".join(idx_cols))
    df = pd.read_sql(sql, conn, params=(scenario_id,)).fillna(0)

    df["cumulative_new_build_capacity"] = df.groupby(
        ["load_zone", "technology"]
    )["new_build_capacity"].transform(pd.Series.cumsum)
    df["cumulative_retired_capacity"] = df.groupby(
        ["load_zone", "technology"]
    )["retired_capacity"].transform(pd.Series.cumsum)

    # df = pd.DataFrame(
    #     columns=['period', 'load_zone', 'technology'] + CAP_OPTIONS,
    #     data=[[2020, 'Zone1', 'Solar', 10, 10, 0, 0, 50],
    #           [2030, 'Zone1', 'Solar', 10, 20, 0, 0, 60],
    #           [2040, 'Zone1', 'Solar', 10, 30, 0, 0, 70],
    #           [2020, 'Zone1', 'Wind', 10, 10, 0, 0, 20],
    #           [2030, 'Zone1', 'Wind', 10, 20, 0, 0, 30],
    #           [2040, 'Zone1', 'Wind', 10, 30, 0, 0, 40],
    #           [2020, 'Zone2', 'Solar', 0, 0, 0, 0, 20],
    #           [2030, 'Zone2', 'Solar', 10, 10, 0, 0, 30],
    #           [2040, 'Zone2', 'Solar', 10, 20, 0, 0, 40],
    #           [2020, 'Zone2', 'Wind', 20, 20, 0, 0, 30],
    #           [2030, 'Zone2', 'Wind', 10, 30, 0, 0, 40],
    #           [2040, 'Zone2', 'Wind', 10, 40, 0, 0, 50]
    #           ]
    # )

    # 'Unpivot' capacity metrics from wide to long format
    df = pd.melt(
        df,
        id_vars=['period', 'load_zone', 'technology'],
        var_name='capacity_metric',
        value_name='capacity'
    )

    # Pivot technologies to wide format (for stack chart)
    # Note: df.pivot does not work with multi-index as of pandas 1.0.5
    idx_cols = ['period', 'load_zone', 'capacity_metric']
    value_cols = list(df['technology'].unique())
    df = pd.pivot_table(
        df,
        index=idx_cols,
        columns='technology',
        values='capacity'
    ).fillna(0).reset_index()

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh
    return df, idx_cols, value_cols


# Data gathering functions
def get_all_summary_data(conn, scenario_id):
    df = pd.DataFrame(
        columns=['period', 'load_zone', 'total_cost', 'load',
                 'average_cost', 'emissions', 'rps_gen_pct', 'curtailment_pct',
                 'cumulative_new_capacity', 'unserved_energy'],
        data=[[2020, 'Zone1', 20000, 8000, 50, 3000, 0.6, 0.04, 30000, 0],
              [2030, 'Zone1', 20000, 8000, 50, 3000, 0.6, 0.04, 30000, 0],
              [2040, 'Zone1', 20000, 8000, 50, 3000, 0.6, 0.04, 30000, 0],
              [2020, 'Zone2', 10000, 5000, 40, 3000, 0.5, 0.02, 20000, 0],
              [2030, 'Zone2', 10000, 5000, 40, 3000, 0.5, 0.02, 20000, 0],
              [2040, 'Zone2', 20000, 8000, 50, 3000, 0.6, 0.04, 30000, 0],
              ]
    )
    #  TODO: look at results tool RESOLVE for more metrics
    # 'Unpivot' from wide to long format
    df = pd.melt(
        df,
        id_vars=['period', 'load_zone'],
        var_name='summary_metric',
        value_name='value'
    )
    # TODO: sort metrics in a way that we want them (not alphabetically)
    df['period'] = df['period'].astype(str)  # Bokeh CDS needs string columns

    # Pivot periods into columms
    df = pd.pivot_table(
        df,
        index=['load_zone', 'summary_metric'],
        columns='period',
        values='value'
    ).fillna(0).reset_index()

    # df = df.drop(["stage", "load_zone"], axis=1)
    return df


def get_all_energy_data(conn, scenario_id):
    # get data for all zones and periods
    df = pd.DataFrame(
        columns=['period', 'load_zone', 'technology', 'energy'],
        data=[[2020, 'Zone1', 'Solar', 10],
              [2030, 'Zone1', 'Solar', 10],
              [2040, 'Zone1', 'Solar', 10],
              [2020, 'Zone1', 'Wind', 20],
              [2030, 'Zone1', 'Wind', 20],
              [2040, 'Zone1', 'Wind', 20],
              [2020, 'Zone2', 'Solar', 0],
              [2030, 'Zone2', 'Solar', 10],
              [2040, 'Zone2', 'Solar', 20],
              [2020, 'Zone2', 'Wind', 20],
              [2030, 'Zone2', 'Wind', 30],
              [2040, 'Zone2', 'Wind', 40]
              ]
    )

    # Pivot technologies to wide format (for stack chart)
    # Note: df.pivot does not work with multi-index as of pandas 1.0.5
    idx_cols = ['period', 'load_zone']
    value_cols = list(df['technology'].unique())
    df = pd.pivot_table(
        df,
        index=idx_cols,
        columns='technology',
        values='energy'
    ).fillna(0).reset_index()

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh

    return df, idx_cols, value_cols


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
    slice = slice.drop(['load_zone'], axis=1)
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
    slice = slice.drop("load_zone", axis=1)  # drop because not stacked
    new_src = ColumnDataSource(slice)
    new_src.remove("index")  # only keep stackers and x_col
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
    slice = slice.drop("load_zone", axis=1)  # drop because not stacked
    new_src = ColumnDataSource(slice)
    new_src.remove("index")  # only keep stackers and x_col
    energy_source.data.update(new_src.data)


def update_capacity_data(zone="Zone1", capacity_metric=CAP_OPTIONS[2]):
    """
    Update the ColumnDataSource object 'cost_source' with the appropriate
    load_zone slice of the data, and with the appropriate capacity metric.
    :param zone:
    :param capacity_metric:
    :return:
    """
    slice = capacity[(capacity["load_zone"] == zone)
                     & (capacity["capacity_metric"] == capacity_metric)]
    slice = slice.drop(["load_zone", "capacity_metric"], axis=1)  # drop because not stacked
    new_src = ColumnDataSource(slice)
    new_src.remove("index")  # only keep stackers and x_col
    capacity_source.data.update(new_src.data)


# TODO: need to dynamically link initial zone value (or set to "all"?)
# Set up widgets
zone_select = Select(title="Load Zone:", value='Zone1', options=ZONE_OPTIONS)
capacity_select = Select(title="Capacity Metric:", value=CAP_OPTIONS[2],
                         options=CAP_OPTIONS)

# Get the data (make sure we do this in global scope vs. in callbacks)
conn = connect_to_database(db_path=DB_PATH)

# TODO: remove value_cols and idx_cols (or start using them)
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
cost_plot = create_stacked_bar_plot(
    source=cost_source,
    x_col="period",  # dynamically update this or add scenario?
    title="Cost by Component",
    category_label="Cost Component",
    y_label="Cost (million USD)"  # TODO: link to units
    # TODO:set width and height to resp. (600, 300)
)
energy_plot = create_stacked_bar_plot(
    source=energy_source,
    x_col="period",  # dynamically update this or add scenario?
    title="Energy by Technology",
    category_label="Technology",
    y_label="Energy (MWh)"  # TODO: link to units
)
cap_plot = create_stacked_bar_plot(
    source=capacity_source,
    x_col="period",  # dynamically update this or add scenario?
    title="Capacity by Technology",
    category_label="Technology",
    y_label="Capacity (MW)"  # TODO: link to units
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
