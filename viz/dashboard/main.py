# Copyright 2016-2020 Blue Marble Analytics LLC.
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
To run: navigate ./viz/ folder and run:
"bokeh serve dashboard --show --args --database DB_PATH"
Note: -- args can be used at as the last argument to add additional command
line arguments to the script, see here:
https://docs.bokeh.org/en/latest/docs/reference/command/subcommands/serve.html

TODO:
 - split out transmission costs from data by load zone (should be separate
   update that also updates database schema).
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
from bokeh.models import Tabs, Panel, PreText, Select, MultiSelect, DataTable, \
    TableColumn
from bokeh.plotting import figure
from bokeh.io import curdoc
from bokeh.layouts import column, row
import sys

from db.common_functions import connect_to_database
from viz.common_functions import create_stacked_bar_plot
from viz.dashboard.data import DataProvider


def create_parser():
    parser = ArgumentParser(add_help=True)
    parser.add_argument("--database",
                        default="../../db/io.db",
                        help="The database file path relative to the current "
                             "working directory. Defaults to ../db/io.db")
    return parser


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


# Define callbacks
# (<attr, old, new> function args are Bokeh standard)
def update_plots(attr, old, new):
    # TODO: could separate out updating the data sources from re-drawing the
    #  plots. Data source could be a DataProvier attribute that gets updated
    #  whenever user selections change.

    # Get the current selection values
    scenario = scenario_select.value
    stage = stage_select.value
    period = period_select.value
    zone = zone_select.value
    capacity_metric = capacity_select.value

    # Get data sources
    cap_src, cap_x_col = data.get_cap_src(
        scenario=scenario,
        stage=stage,
        period=period,
        zone=zone,
        capacity_metric=capacity_metric
    )
    energy_src, energy_x_col = data.get_energy_src(
        scenario=scenario,
        stage=stage,
        period=period,
        zone=zone
    )
    cost_src, cost_x_col = data.get_cost_src(
        scenario=scenario,
        stage=stage,
        period=period,
        zone=zone
    )
    summary_src = data.get_summary_src(
        scenario=scenario,
        stage=stage,
        period=period,
        zone=zone
    )
    objective_src = data.get_objective_src(
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


# Parse arguments and connect to db
parser = create_parser()
args = sys.argv[1:]
parsed_args = parser.parse_args(args=args)
conn = connect_to_database(db_path=parsed_args.database)

# Set Up Data
data = DataProvider(conn)

# Set up selection widgets
scenario_select = MultiSelect(title="Select Scenario(s):",
                              value=data.scenario_options,
                              # width=600,
                              options=data.scenario_options)
period_select = MultiSelect(title="Select Period(s):",
                            value=data.period_options,
                            options=data.period_options)
stage_select = Select(title="Select Stage:",
                      value=data.stage_options[0],
                      options=data.stage_options)
zone_select = Select(title="Select Load Zone:",
                     value=data.zone_options[0],
                     options=data.zone_options)
capacity_select = Select(title="Select Capacity Metric:",
                         value=data.cap_options[2],
                         options=data.cap_options)

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
tab1 = Panel(child=layout, title='General')
storage_dummy = PreText(text='storage summary here, incl. duration', width=600)
policy_dummy = PreText(text='policy summary here, including duals', width=600)
inputs_dummy = PreText(text='inputs summary here, e.g. loads (profile charts, min, max, avg), costs',
                       width=600)
tab2 = Panel(child=storage_dummy, title='Storage')
tab3 = Panel(child=policy_dummy, title='Policy Targets')
tab4 = Panel(child=inputs_dummy, title='Inputs')
tabs = Tabs(tabs=[tab1, tab2, tab3, tab4])  # Put all tabs in one application

# Update Plots based on selected values
update_plots(attr="", old="", new="")

# Set up callback behavior (update plots if user changes selection)
scenario_select.on_change('value', update_plots)
period_select.on_change('value', update_plots)
stage_select.on_change('value', update_plots)
zone_select.on_change('value', update_plots)
capacity_select.on_change('value', update_plots)

# Set up curdoc
curdoc().add_root(tabs)
curdoc().title = "Dashboard"
