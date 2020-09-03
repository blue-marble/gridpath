#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
To run: navigate ./viz/ folder and run:
"bokeh serve dashboard --show --args --database DB_PATH"
Note: -- args can be used at as the last argument to add additional command
line arguments to the script, see here:
https://docs.bokeh.org/en/latest/docs/reference/command/subcommands/serve.html

TODO:
 - don't include spinup/lookahead when summing across subproblems (and add
   some notes on dashboard to explain this?)
 - formatting of data tables, titles, etc.
 - bring in dynamic units into datatable headers
 - add tabs with more info:
    - storage (on duration and charge/discharge behavior + losses?)
    - transmission
    - policy
    - duals
 - download data button(s) - requires customJS:
 https://stackoverflow.com/questions/59950849/bokeh-chart-download-as-csv

"""

from argparse import ArgumentParser
from bokeh.models import Tabs, Panel, PreText, Select, MultiSelect, \
    ColumnDataSource, DataTable, TableColumn
from bokeh.plotting import figure
from bokeh.io import curdoc
from bokeh.layouts import column, row
import pandas as pd
import sys

from db.common_functions import connect_to_database
from viz.common_functions import create_stacked_bar_plot, order_cols_by_nunique


def create_parser():
    parser = ArgumentParser(add_help=True)
    parser.add_argument("--database",
                        default="../../db/io.db",
                        help="The database file path relative to the current "
                             "working directory. Defaults to ../db/io.db")
    return parser


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


def get_stage_options(conn, scenarios):
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    stage_options = [str(s[0]) for s in conn.execute(
        """SELECT DISTINCT stage_id
        FROM inputs_temporal_subproblems_stages
        WHERE temporal_scenario_id in (
            SELECT temporal_scenario_id
            FROM scenarios
            WHERE scenario_name in ({})
        );""".format(",".join("?" * len(scenarios)))
        , scenarios
    ).fetchall()]

    return stage_options


def get_objective_metrics(conn):
    data = conn.execute("""SELECT * FROM results_system_costs WHERE 0 = 1;""")
    cols = [s[0] for s in data.description]
    cols = cols[3:]  # remove scenario_id, subproblem_id, stage_id
    return cols


def get_all_cost_data(conn, scenarios):
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    # TODO: add tx deliverability costs, but those aren't by zone!?
    #  might just keep zone NULL and make sure filter can deal with it
    sql = """SELECT scenario_name AS scenario, stage_id, period, load_zone,
        SUM(capacity_cost) AS capacity_cost, 
        SUM(variable_om_cost) AS variable_om_cost, 
        SUM(fuel_cost) AS fuel_cost, 
        SUM(startup_cost) AS startup_cost, 
        SUM(shutdown_cost) AS shutdown_cost, 
        SUM(tx_capacity_cost) AS tx_capacity_cost, 
        SUM(tx_hurdle_cost) AS tx_hurdle_cost
        FROM results_costs_by_period_load_zone
        INNER JOIN 
        (SELECT scenario_name, scenario_id FROM scenarios
         WHERE scenario_name in ({}) ) as scen_table
        USING (scenario_id)
        GROUP BY scenario, stage_id, period, load_zone
        ;""".format(",".join(["?"] * len(scenarios)))
    df = pd.read_sql(sql, conn, params=scenarios).fillna(0)
    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh
    return df


def get_all_capacity_data(conn, scenarios):
    # Note: this averages capacity across subproblems within one period
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    sql = """SELECT scenario_name AS scenario, stage_id, period, load_zone, 
        technology, 
        AVG(new_build_mw) AS new_build_capacity, 
        AVG(retired_mw) AS retired_capacity, 
        AVG(capacity_mw) AS total_capacity
        FROM results_project_capacity
        INNER JOIN 
        (SELECT scenario_name, scenario_id FROM scenarios
         WHERE scenario_name in ({}) ) as scen_table
        USING (scenario_id)
        GROUP BY scenario, stage_id, period, load_zone, technology;
        """.format(",".join(["?"] * len(scenarios)))
    df = pd.read_sql(sql, conn, params=scenarios).fillna(0)

    df["cumulative_new_build_capacity"] = df.groupby(
        ["scenario", "stage_id", "load_zone", "technology"]
    )["new_build_capacity"].transform(pd.Series.cumsum)
    df["cumulative_retired_capacity"] = df.groupby(
        ["scenario", "stage_id", "load_zone", "technology"]
    )["retired_capacity"].transform(pd.Series.cumsum)

    # 'Unpivot' capacity metrics from wide to long format
    df = pd.melt(
        df,
        id_vars=['scenario', 'stage_id', 'period', 'load_zone', 'technology'],
        var_name='capacity_metric',
        value_name='capacity'
    )

    # Pivot technologies to wide format (for stack chart)
    # Note: df.pivot does not work with multi-index as of pandas 1.0.5
    df = pd.pivot_table(
        df,
        index=['scenario', 'stage_id', 'period', 'load_zone', 'capacity_metric'],
        columns='technology',
        values='capacity'
    ).fillna(0).reset_index()

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh
    return df


def get_all_energy_data(conn, scenarios):
    # note: this will aggregate across subproblems
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    sql = """SELECT scenario_name AS scenario, stage_id, period, load_zone, 
        technology, 
        SUM(energy_mwh) AS energy
        FROM results_project_dispatch_by_technology_period
        INNER JOIN 
        (SELECT scenario_name, scenario_id FROM scenarios
         WHERE scenario_name in ({}) ) as scen_table
        USING (scenario_id)
        GROUP BY scenario, stage_id, period, load_zone, technology;
        """.format(",".join(["?"] * len(scenarios)))
    df = pd.read_sql(sql, conn, params=scenarios).fillna(0)
    # Pivot technologies to wide format (for stack chart)
    # Note: df.pivot does not work with multi-index as of pandas 1.0.5
    df = pd.pivot_table(
        df,
        index=['scenario', 'stage_id', 'period', 'load_zone'],
        columns='technology',
        values='energy'
    ).fillna(0).reset_index()

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh
    return df


# Data gathering functions
def get_objective_cost_data(conn, scenarios):
    # note: this will include costs that are part of spinup/lookahead tmps!
    # note: this will aggregate across subproblems
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    objective_metrics = get_objective_metrics(conn)
    sql1 = """SELECT scenario_name AS scenario, stage_id, """
    sql2 = ",".join(["SUM({}) AS {} ".format(c, c) for c in objective_metrics])
    sql3 = """FROM results_system_costs
        INNER JOIN
        (SELECT scenario_name, scenario_id FROM scenarios
        WHERE scenario_name in ({}) ) AS scen_table
        USING (scenario_id)
        
        GROUP BY scenario, stage_id
        ;""".format(",".join(["?"] * len(scenarios)))
    sql = sql1 + sql2 + sql3

    df = pd.read_sql(sql, conn, params=scenarios).fillna(0)

    return df


def get_all_summary_data(conn, scenarios):
    # TODO: could link summary columns to a python variable which can then be
    #  reused when creating the categorical column
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    sql = """
    SELECT scenario_name AS scenario, stage_id, period, load_zone, 
    capacity_cost, operational_cost, transmission_cost,
    (ifnull(capacity_cost, 0) 
     + ifnull(operational_cost, 0) 
     + ifnull(transmission_cost, 0)) AS total_cost, 
    load, 
    (ifnull(capacity_cost, 0) 
     + ifnull(operational_cost, 0) 
     + ifnull(transmission_cost, 0))
    /ifnull(load,0) AS average_cost, 
    overgeneration, unserved_energy, carbon_emissions
    
    FROM (
        SELECT scenario_id, stage_id, period, load_zone, 
        SUM(capacity_cost) AS capacity_cost,
        SUM(variable_om_cost + fuel_cost + startup_cost + shutdown_cost) AS 
        operational_cost,  
        SUM(tx_capacity_cost + tx_hurdle_cost) AS transmission_cost
        FROM results_costs_by_period_load_zone
        GROUP BY scenario_id, stage_id, period, load_zone
        ) AS cost_table
        
    INNER JOIN 
    (SELECT scenario_id, stage_id, period, load_zone, 
    SUM(timepoint_weight * number_of_hours_in_timepoint * load_mw) AS load,
    SUM(timepoint_weight * number_of_hours_in_timepoint * overgeneration_mw) 
    AS overgeneration,
    SUM(timepoint_weight * number_of_hours_in_timepoint * unserved_energy_mw) 
    AS unserved_energy
    FROM results_system_load_balance
    GROUP BY scenario_id, stage_id, period, load_zone
    ) AS load_table
    USING (scenario_id, stage_id, period, load_zone)
    
    INNER JOIN
    (SELECT scenario_id, stage_id, period, load_zone,
    SUM(carbon_emission_tons) AS carbon_emissions
    FROM results_project_carbon_emissions_by_technology_period
    GROUP BY scenario_id, stage_id, period, load_zone
    ) AS carbon_table
    USING(scenario_id, stage_id, period, load_zone)
    
    INNER JOIN
    (SELECT scenario_name, scenario_id FROM scenarios
    WHERE scenario_name in ({}) ) AS scen_table
    USING (scenario_id)
    ;""".format(",".join(["?"] * len(scenarios)))

    df = pd.read_sql(sql, conn, params=scenarios).fillna(0)
    df['period'] = df['period'].astype(str)  # Bokeh CDS needs string columns

    return df


def get_objective_src(objective_df, scenario, stage):
    """
    Update the ColumnDataSource object 'objective_source' with the appropriate
    scenario slice of the data.
    :param objective_df:
    :param scenario:
    :return:
    """
    scenario = scenario if isinstance(scenario, list) else [scenario]
    df = objective_df.copy()

    scenario_filter = df["scenario"].isin(scenario)
    stage_filter = (df["stage_id"] == int(stage))
    df = df[scenario_filter & stage_filter]

    # 'Unpivot' from wide to long format (move metrics into a col)
    df = pd.melt(
        df,
        id_vars=['scenario', 'stage_id'],
        var_name='objective_metric',
        value_name='value'
    )
    # # Pivot scenarios into columms
    df = pd.pivot_table(
        df,
        index=['stage_id', 'objective_metric'],
        columns='scenario',
        values='value'
    ).reset_index().fillna(0)

    # Convert to categorical for sorting
    objective_metrics = get_objective_metrics(conn)
    df['objective_metric'] = pd.Categorical(
        values=df['objective_metric'],
        categories=objective_metrics
    )
    df = df.sort_values(by=["objective_metric"])

    src = ColumnDataSource(df)
    return src


def get_summary_src(summary_df, scenario, stage, period, zone):
    """
    Update the ColumnDataSource object 'summary_source' with the appropriate
    slice of the data.
    :param summary_df:
    :param zone:
    :return:
    """
    scenario = scenario if isinstance(scenario, list) else [scenario]
    period = period if isinstance(period, list) else [period]
    df = summary_df.copy()

    scenario_filter = df["scenario"].isin(scenario)
    period_filter = df["period"].isin(period)
    stage_filter = (df["stage_id"] == int(stage))
    zone_filter = (df["load_zone"] == zone)

    df = df[period_filter & stage_filter & scenario_filter & zone_filter]

    # 'Unpivot' from wide to long format (move metrics into a col)
    df = pd.melt(
        df,
        id_vars=['scenario', 'stage_id', 'period', 'load_zone'],
        var_name='summary_metric',
        value_name='value'
    )
    # Pivot scenarios into columms
    df = pd.pivot_table(
        df,
        index=['load_zone', 'stage_id', 'period', 'summary_metric'],
        columns='scenario',
        values='value'
    ).reset_index().fillna(0)

    # Convert to categorical for sorting
    df['summary_metric'] = pd.Categorical(
        values=df['summary_metric'],
        categories=["capacity_cost", "operational_cost", "transmission_cost",
                    "total_cost", "load", "average_cost", "overgeneration",
                    "unserved_energy", "carbon_emissions"]
    )
    df = df.sort_values(by=["load_zone", "period", "summary_metric"])

    src = ColumnDataSource(df)
    return src


def get_cost_src(cost_df, scenario, stage, period, zone):
    """
    Create a Bokeh ColumnDataSource object with the appropriate sliced out data.
    :return:
    """
    scenario = scenario if isinstance(scenario, list) else [scenario]
    period = period if isinstance(period, list) else [period]
    df = cost_df.copy()

    scenario_filter = df["scenario"].isin(scenario)
    stage_filter = (df["stage_id"] == int(stage))
    period_filter = df["period"].isin(period)
    zone_filter = (df["load_zone"] == zone)

    df = df[scenario_filter & stage_filter & period_filter & zone_filter]
    df = df.drop(["load_zone", "stage_id"], axis=1)  # drop bc not stacked

    x_col = ["period", "scenario"]
    x_col_reordered = order_cols_by_nunique(df, x_col)
    df = df.set_index(x_col_reordered)

    src = ColumnDataSource(df)
    x_col_src = "_".join(x_col_reordered)
    return src, x_col_src


def get_energy_src(energy_df, scenario, stage, period, zone):
    """
    Create a Bokeh ColumnDataSource object with the appropriate sliced out data.
    :return:
    """
    scenario = scenario if isinstance(scenario, list) else [scenario]
    period = period if isinstance(period, list) else [period]
    df = energy_df.copy()

    scenario_filter = df["scenario"].isin(scenario)
    period_filter = df["period"].isin(period)
    stage_filter = (df["stage_id"] == int(stage))
    zone_filter = (df["load_zone"] == zone)

    df = df[scenario_filter & period_filter & stage_filter & zone_filter]
    df = df.drop(["load_zone", "stage_id"], axis=1)  # drop bc not stacked

    x_col = ["period", "scenario"]
    x_col_reordered = order_cols_by_nunique(df, x_col)
    df = df.set_index(x_col_reordered)

    src = ColumnDataSource(df)
    x_col_src = "_".join(x_col_reordered)
    return src, x_col_src


def get_cap_src(capacity_df, scenario, stage, period, zone, capacity_metric):
    """
    Create a Bokeh ColumnDataSource object with the appropriate sliced out data.
    :return:
    """
    # TODO: allow for multiple load zones (sum across zones)
    scenario = scenario if isinstance(scenario, list) else [scenario]
    period = period if isinstance(period, list) else [period]
    df = capacity_df.copy()

    scenario_filter = df["scenario"].isin(scenario)
    period_filter = df["period"].isin(period)
    stage_filter = (df["stage_id"] == int(stage))
    zone_filter = (df["load_zone"] == zone)
    cap_metric_filter = (df["capacity_metric"] == capacity_metric)

    df = df[scenario_filter & period_filter & stage_filter & zone_filter &
               cap_metric_filter]
    df = df.drop(["load_zone", "stage_id", "capacity_metric"], axis=1)

    x_col = ["period", "scenario"]
    x_col_reordered = order_cols_by_nunique(df, x_col)
    df = df.set_index(x_col_reordered)

    src = ColumnDataSource(df)
    x_col_src = "_".join(x_col_reordered)
    return src, x_col_src


def create_datatable(src):
    # TODO: use Bokeh NumberFormatter on number columns
    # TableColumn(field=, title=, formatter=NumberFormatter(format='0,0[.]00')
    cols_to_use = [c for c in src.data.keys()
                   if c not in ['stage_id', 'index']]
    columns = [TableColumn(field=c, title=c) for c in cols_to_use]
    summary_table = DataTable(
        columns=columns, source=src,
        index_position=None,
        fit_columns=True,
        # width=800,
        height=300
    )
    return summary_table


def draw_plots(scenario, stage, period, zone, capacity_metric):
    """
    (Re)draw plots: slice out appropriate data, convert to Bokeh CDS, and
    create Bokeh plots.

    Note that this requires that you have loaded all data (capacity, costs,
    etc) into global variables, and have set up the layout as well with
    global variables.
    :param scenario:
    :param stage:
    :param period:
    :param zone:
    :param capacity_metric:
    :return:
    """
    # Get data sources
    cap_src, cap_x_col = get_cap_src(
        capacity_df=capacity,
        scenario=scenario,
        stage=stage,
        period=period,
        zone=zone,
        capacity_metric=capacity_metric
    )
    energy_src, energy_x_col = get_energy_src(
        energy_df=energy,
        scenario=scenario,
        stage=stage,
        period=period,
        zone=zone
    )
    cost_src, cost_x_col = get_cost_src(
        cost_df=cost,
        scenario=scenario,
        stage=stage,
        period=period,
        zone=zone
    )
    summary_src = get_summary_src(
        summary_df=summary,
        scenario=scenario,
        stage=stage,
        period=period,
        zone=zone
    )
    objective_src = get_objective_src(
        objective_df=objective,
        scenario=scenario,
        stage=stage
    )

    # Create Bokeh Plots and Tables
    title = PreText(text="Results: {} - {} - {}".format(scenario, period, zone))
    summary_table = create_datatable(summary_src)
    objective_table = create_datatable(objective_src)
    cap_plot = create_stacked_bar_plot(
        source=cap_src,
        x_col=cap_x_col,
        title="Capacity by Technology",
        category_label="Technology",
        y_label="Capacity (MW)"
    )
    energy_plot = create_stacked_bar_plot(
        source=energy_src,
        x_col=energy_x_col,
        title="Energy by Technology",
        category_label="Technology",
        y_label="Energy (MWh)"  # TODO: link to units
    )
    cost_plot = create_stacked_bar_plot(
        source=cost_src,
        x_col=cost_x_col,
        title="Cost by Component",
        category_label="Cost Component",
        y_label="Cost (million USD)"  # TODO: link to units
    )

    # Update layout with new plots
    layout.children[0] = title
    top_row.children[1] = summary_table
    top_row.children[2] = objective_table
    middle_row.children[0] = cap_plot
    middle_row.children[1] = energy_plot
    bottom_row.children[0] = cost_plot


# Define callbacks
def scenario_change(attr, old, new):
    """
    When the selected scenario changes, get the appropriate data slice and
    and re-draw the plots.
    """
    draw_plots(scenario_select.value, stage_select.value, period_select.value,
               zone_select.value, capacity_select.value)


def period_change(attr, old, new):
    """
    When the selected period changes, get the appropriate data slice and
    re-draw the plots.
    """
    draw_plots(scenario_select.value, stage_select.value, period_select.value,
               zone_select.value, capacity_select.value)


def stage_change(attr, old, new):
    """
    When the selected stage changes, get the appropriate data slice and
    re-draw the plots.
    """
    draw_plots(scenario_select.value, stage_select.value, period_select.value,
               zone_select.value, capacity_select.value)


def zone_change(attr, old, new):
    """
    When the selected load zone changes, get the appropriate data slice and
    re-draw the plots.
    """
    draw_plots(scenario_select.value, stage_select.value, period_select.value,
               zone_select.value, capacity_select.value)


def capacity_change(attr, old, new):
    """
    When the selected capacity metric changes, get the appropriate data slice
    and re-draw the plots.
    """
    draw_plots(scenario_select.value, stage_select.value, period_select.value,
               zone_select.value, capacity_select.value)


CAP_OPTIONS = ["new_build_capacity", "retired_capacity", "total_capacity",
               "cumulative_new_build_capacity", "cumulative_retired_capacity"]

# Parse arguments and connect to db
parser = create_parser()
args = sys.argv[1:]
parsed_args = parser.parse_args(args=args)
conn = connect_to_database(db_path=parsed_args.database)

# Get drop down options
scenario_options = get_scenario_options(conn)
period_options = get_period_options(conn, scenario_options)
stage_options = get_stage_options(conn, scenario_options)
zone_options = get_zone_options(conn, scenario_options)
# TODO: ideally dynamically update zone_options based on selected scenarios

# Set up widgets
scenario_select = MultiSelect(title="Select Scenario(s):",
                              value=scenario_options,
                              # width=600,
                              options=scenario_options)
period_select = MultiSelect(title="Select Period(s):",
                            value=period_options,
                            options=period_options)
stage_select = Select(title="Select Stage:",
                      value=stage_options[0],
                      options=stage_options)
zone_select = Select(title="Select Load Zone:",
                     value=zone_options[0],
                     options=zone_options)
capacity_select = Select(title="Select Capacity Metric:",
                         value=CAP_OPTIONS[2],
                         options=CAP_OPTIONS)

# Get data for all scenarios/periods/... (note: global var, done once)
summary = get_all_summary_data(conn, scenario_options)
cost = get_all_cost_data(conn, scenario_options)
capacity = get_all_capacity_data(conn, scenario_options)
energy = get_all_energy_data(conn, scenario_options)
objective = get_objective_cost_data(conn, scenario_options)

# Set up Bokeh Layout with placeholders
title = PreText()
summary_table = DataTable()
objective_table = DataTable()
cost_plot = figure()
energy_plot = figure()
cap_plot = figure()
selectors = column(scenario_select, period_select,
                   stage_select, zone_select, capacity_select)
top_row = row(selectors, summary_table, objective_table)
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
tabs = Tabs(tabs=[tab1, tab2, tab3, tab4])  # Put all tabs in one application

# Draw Plots based on selected values
draw_plots(scenario_select.value, stage_select.value, period_select.value,
           zone_select.value, capacity_select.value)

# Set up callback behavior (redraw plots)
scenario_select.on_change('value', scenario_change)
period_select.on_change('value', period_change)
stage_select.on_change('value', stage_change)
zone_select.on_change('value', zone_change)
capacity_select.on_change('value', capacity_change)

# Set up curdoc
curdoc().add_root(tabs)
curdoc().title = "Dashboard"
