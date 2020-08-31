#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
To run: navigate ./viz/ folder and run:
"bokeh serve dashboard --show"

TODO:
 - hover tools break when multi-level x_col is reordered; update if reordering
 - make sure energy and and cost etc. work with multiple scenarios
 - re-arrange scenarios and periods
 - LATEST: deal with updating x-axis dynamically (doesn't change when CDS
   changes) + also fix energy and cost chart to be similar to capacity
    (deal with multiple scenarios and periods)
 - NEW: allow multiple zones
 - NEW: link capacity plots and energy plot to real data
 - NEW: link summary plot to real data
 - replace dummy data with real sql scripts pulling data
     also requires adding database connection and parsers
 - add a PreText title that summaries everything
   (which load_zones selected etc.)
 - allow "all zones" option
 - what to do with subproblems? --> sum across them?
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
    DataTable, TableColumn, MultiSelect
from bokeh.io import curdoc
from bokeh.layouts import column, row

import pandas as pd

# GridPath modules
from db.common_functions import connect_to_database
from gridpath.auxiliary.auxiliary import get_scenario_id_and_name
from viz.common_functions import create_stacked_bar_plot, order_cols_by_nunique

# TODO: base on actual data
CAP_OPTIONS = ["new_build_capacity", "retired_capacity", "total_capacity",
               "cumulative_new_build_capacity", "cumulative_retired_capacity"]
SCENARIO = "test"
scenario_id = 42
DB_PATH = "../db/test.db"  # TODO: link to UI or parsed arg?


def get_scenario_options(conn):
    scenario_options = [sc[0] for sc in conn.execute(
        """SELECT scenario_name FROM scenarios
        WHERE run_status_id = 2  --scenarios that have finished;"""
    ).fetchall()]
    return scenario_options


def get_zone_options(conn, scenarios):
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    # TODO: refactor with ui.server.api.scenario_results
    load_zone_options = [z[0] for z in conn.execute(
        """SELECT DISTINCT load_zone FROM inputs_geography_load_zones
        WHERE load_zone_scenario_id in (
            SELECT load_zone_scenario_id
            FROM scenarios
            WHERE scenario_name in ({})
        );""".format(",".join("?" * len(scenarios)))
        , scenarios
    ).fetchall()]

    return load_zone_options


def get_period_options(conn, scenarios):
    # TODO: refactor with ui.server.api.scenario_results
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    period_options = [str(p[0]) for p in conn.execute(
        """SELECT DISTINCT period FROM inputs_temporal_periods
        WHERE temporal_scenario_id in (
            SELECT temporal_scenario_id
            FROM scenarios
            WHERE scenario_name in ({})
        );""".format(",".join("?" * len(scenarios)))
        , scenarios
      ).fetchall()]

    return period_options


def get_stage_options(conn, scenario_id):
    stage_options = [h[0] for h in conn.execute(
        """SELECT DISTINCT stage_id
        FROM inputs_temporal_subproblems_stages
        WHERE temporal_scenario_id = (
        SELECT temporal_scenario_id
        FROM scenarios
        WHERE scenario_id = {});""".format(scenario_id)
    ).fetchall()]

    return stage_options


def get_all_cost_data(conn, scenario_id):
    # get data for all zones and periods

    # TODO: add tx deliverability costs, but those aren't by zone!
    #  might just keep zone NULL and make sure filter can deal with it
    # TODO: filter for multiple scenarios
    # TODO: filter for subproblem/stage (?)
    sql = """SELECT period, load_zone,
        capacity_cost, variable_om_cost, fuel_cost, startup_cost, 
        shutdown_cost, tx_capacity_cost, tx_hurdle_cost
        FROM results_costs_by_period_load_zone
        WHERE scenario_id = ?;
        """

    df = pd.read_sql(sql, conn, params=(scenario_id,)).fillna(0)

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh
    return df


def get_all_capacity_data(conn, scenarios):
    # TODO: filter for subproblem/stage (?)
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    sql = """SELECT scenario_name as scenario, period, load_zone, technology, 
        SUM(new_build_mw) AS new_build_capacity, 
        SUM(retired_mw) AS retired_capacity, 
        SUM(capacity_mw) AS total_capacity
        FROM results_project_capacity
        INNER JOIN 
        (SELECT scenario_name, scenario_id FROM scenarios
         WHERE scenario_name in ({}) ) as scen_table
        USING (scenario_id)
        GROUP BY scenario, period, load_zone, technology;
        """.format(",".join(["?"] * len(scenarios)))
    df = pd.read_sql(sql, conn, params=scenarios).fillna(0)

    df["cumulative_new_build_capacity"] = df.groupby(
        ["scenario", "load_zone", "technology"]
    )["new_build_capacity"].transform(pd.Series.cumsum)
    df["cumulative_retired_capacity"] = df.groupby(
        ["scenario", "load_zone", "technology"]
    )["retired_capacity"].transform(pd.Series.cumsum)

    # 'Unpivot' capacity metrics from wide to long format
    df = pd.melt(
        df,
        id_vars=['scenario', 'period', 'load_zone', 'technology'],
        var_name='capacity_metric',
        value_name='capacity'
    )

    # Pivot technologies to wide format (for stack chart)
    # Note: df.pivot does not work with multi-index as of pandas 1.0.5
    df = pd.pivot_table(
        df,
        index=['scenario', 'period', 'load_zone', 'capacity_metric'],
        columns='technology',
        values='capacity'
    ).fillna(0).reset_index()

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh
    return df


def get_all_energy_data(conn, scenario_id):
    # TODO: filter/aggregate for subproblem/stage (?)
    # TODO: don't return value and idx cols (?)
    sql = """SELECT period, load_zone, technology, 
        SUM(energy_mwh) AS energy
        FROM results_project_dispatch_by_technology_period
        WHERE scenario_id = ?
        GROUP BY period, load_zone, technology
        ;"""
    df = pd.read_sql(sql, conn, params=(scenario_id,)).fillna(0)

    # df = pd.DataFrame(
    #     columns=['period', 'load_zone', 'technology', 'energy'],
    #     data=[[2020, 'Zone1', 'Solar', 10],
    #           [2030, 'Zone1', 'Solar', 10],
    #           [2040, 'Zone1', 'Solar', 10],
    #           [2020, 'Zone1', 'Wind', 20],
    #           [2030, 'Zone1', 'Wind', 20],
    #           [2040, 'Zone1', 'Wind', 20],
    #           [2020, 'Zone2', 'Solar', 0],
    #           [2030, 'Zone2', 'Solar', 10],
    #           [2040, 'Zone2', 'Solar', 20],
    #           [2020, 'Zone2', 'Wind', 20],
    #           [2030, 'Zone2', 'Wind', 30],
    #           [2040, 'Zone2', 'Wind', 40]
    #           ]
    # )

    # Pivot technologies to wide format (for stack chart)
    # Note: df.pivot does not work with multi-index as of pandas 1.0.5
    # value_cols = list(df['technology'].unique())
    df = pd.pivot_table(
        df,
        index=['period', 'load_zone'],
        columns='technology',
        values='energy'
    ).fillna(0).reset_index()

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh

    return df


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


# Define callbacks
def scenario_change(attr, old, new):
    """
    When the selected scenario changes, update the cost, energy and capacity.
    """
    # TODO: update cost, energy
    src, x_factors = update_capacity_data(scenario=new,
                         period=period_select.value,
                         zone=zone_select.value,
                         capacity_metric=capacity_select.value)
    # Need to update x-axis separately (factors need to be list, not array!)
    # cap_plot.x_range.factors = list(capacity_source.data["period_scenario"])
    # cap_plot.x_range.factors = x_factors[1]

    cap_plot = create_stacked_bar_plot(
        source=src,
        x_col=x_factors[0],
        title="Capacity by Technology",
        category_label="Technology",
        y_label="Capacity (MW)"
    )

    # TODO: completely re-draw plot instead of updating data
    middle_row.children[0] = cap_plot


def period_change(attr, old, new):
    """
    When the selected period changes, update the cost, energy and capacity.
    """
    # TODO: update cost, energy
    src, x_factors = update_capacity_data(scenario=scenario_select.value,
                         period=new,
                         zone=zone_select.value,
                         capacity_metric=capacity_select.value)
    # Need to update x-axis separately (factors need to be list, not array!)
    # cap_plot.x_range.factors = list(capacity_source.data["period_scenario"])
    # cap_plot.x_range.factors = x_factors[1]

    cap_plot = create_stacked_bar_plot(
        source=src,
        x_col=x_factors[0],
        title="Capacity by Technology",
        category_label="Technology",
        y_label="Capacity (MW)"
    )

    # TODO: completely re-draw plot instead of updating data
    middle_row.children[0] = cap_plot


def zone_change(attr, old, new):
    """
    When the selected load zone changes, update the cost, energy and capacity.
    """
    update_summary_data(zone=new)
    update_cost_data(zone=new)
    update_energy_data(zone=new)
    update_capacity_data(scenario=scenario_select.value,
                         period=period_select.value,
                         zone=new,
                         capacity_metric=capacity_select.value)


def capacity_change(attr, old, new):
    """
    When the selected capacity metric changes, update the capacity.
    """
    update_capacity_data(scenario=scenario_select.value,
                         period=period_select.value,
                         zone=zone_select.value,
                         capacity_metric=new)


# TODO: Update summary table when zone changes!
def update_summary_data(zone):
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
def update_cost_data(zone):
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


def update_energy_data(zone):
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


def update_capacity_data(scenario, period, zone, capacity_metric):
    """
    Update the ColumnDataSource object 'cost_source' with the appropriate
    load_zone slice of the data, and with the appropriate capacity metric.
    :param zone:
    :param capacity_metric:
    :return:
    """
    # TODO: allow for multiple load zones (sum across zones)
    scenario = scenario if isinstance(scenario, list) else [scenario]
    period = period if isinstance(period, list) else [period]
    df = capacity.copy()

    scenario_filter = df["scenario"].isin(scenario)
    period_filter = df["period"].isin(period)
    zone_filter = (df["load_zone"] == zone)
    cap_metric_filter = (df["capacity_metric"] == capacity_metric)

    slice = df[period_filter & scenario_filter & zone_filter &
               cap_metric_filter]
    slice = slice.drop(["load_zone", "capacity_metric"], axis=1)  # drop because not stacked

    x_col = ["period", "scenario"]
    slice = slice.set_index(x_col)
    # x_col_reordered = order_cols_by_nunique(slice, x_col)
    # slice = slice.set_index(x_col_reordered)
    new_src = ColumnDataSource(slice)
    # capacity_source.data.update(new_src.data)

    # if x_col_reordered != x_col:
    #     capacity_source.remove("_".join(x_col))
    # x_factors = ("_".join(x_col_reordered),
    #              list(capacity_source.data["_".join(x_col_reordered)]))
    x_factors = ("_".join(x_col),
                 list(new_src.data["_".join(x_col)]))
    return new_src, x_factors

    # Can't do this here because update_capacity_data is called before
    # cap plot is created. Perhaps look into different way to initalize data?
    # cap_plot.x_range.factors = list(capacity_source.data["period_scenario"])


# Get the data (make sure we do this in global scope vs. in callbacks)
conn = connect_to_database(db_path=DB_PATH)
scenario_options = get_scenario_options(conn)
period_options = get_period_options(conn, scenario_options)
zone_options = get_zone_options(conn, scenario_options)
# TODO: ideally dynamically update zone_options based on selected scenarios

# Set up widgets
scenario_select = MultiSelect(title="Select Scenario(s):",
                              value=scenario_options,
                              options=scenario_options)
period_select = MultiSelect(title="Select Period(s):",
                            value=period_options,
                            options=period_options)
zone_select = Select(title="Select Load Zone:", value=zone_options[0],
                     options=zone_options)
capacity_select = Select(title="Select Capacity Metric:", value=CAP_OPTIONS[2],
                         options=CAP_OPTIONS)

# Get Data
summary = get_all_summary_data(conn, scenario_id)
cost = get_all_cost_data(conn, scenario_id)
capacity = get_all_capacity_data(conn, scenario_options)
energy = get_all_energy_data(conn, scenario_id)

# Iniitialize CDSs
summary_source = ColumnDataSource()
cost_source = ColumnDataSource()
energy_source = ColumnDataSource()
capacity_source = ColumnDataSource()
# Update CDSs with initial values
update_summary_data(zone=zone_select.value)
update_cost_data(zone=zone_select.value)
src, x_factors = update_capacity_data(scenario=scenario_select.value,
                     period=period_select.value,
                     zone=zone_select.value,
                     capacity_metric=capacity_select.value)
update_energy_data(zone=zone_select.value)

# TODO: figure out initial order of x_cols here

# Set up Title
# TODO: somehow update zone (changing global var in callback doensn't work)
title = PreText(text="title goes here specifying active zone: {} "
                     "etc.".format('Zone1'))

# Set up Bokeh DataTable for summary
cols_to_use = [c for c in summary.columns if c not in ['load_zone', 'stage']]
columns = [TableColumn(field=c, title=c) for c in cols_to_use]
summary_table = DataTable(columns=columns, source=summary_source, height=250)

# Set up plots
cost_plot = create_stacked_bar_plot(
    source=cost_source,
    x_col="period",
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
    source=src,
    x_col=x_factors[0],  # TODO: dynamically update based on x_col order
    title="Capacity by Technology",
    category_label="Technology",
    y_label="Capacity (MW)"  # TODO: link to units
)

# Set up layout
top_row = row(summary_table, column(scenario_select,
                                    period_select,
                                    zone_select,
                                    capacity_select))
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

# Set up callback behavior
scenario_select.on_change('value', scenario_change)
period_select.on_change('value', period_change)
zone_select.on_change('value', zone_change)
capacity_select.on_change('value', capacity_change)

# Set up curdoc
curdoc().add_root(tabs)
curdoc().title = "Dashboard"
