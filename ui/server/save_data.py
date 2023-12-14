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
Functions to save data from the UI to CSVs.
"""

import csv
from importlib import import_module
import pandas as pd

from db.common_functions import connect_to_database
from ui.server.api.view_data import get_table_data as get_results_table_data
from ui.server.api.scenario_inputs import (
    create_input_data_table_api as get_inputs_table_data,
)


def save_table_data_to_csv(
    db_path,
    download_path,
    scenario_id,
    other_scenarios,
    table,
    table_type,
    ui_table_name_in_db,
    ui_row_name_in_db,
):
    """

    :param db_path:
    :param download_path:
    :param scenario_id:
    :param other_scenarios:
    :param table:
    :param table_type:
    :param ui_table_name_in_db:
    :param ui_row_name_in_db:
    :return:
    """
    print(table)

    print(table_type)

    if table_type in ["subscenario", "input"]:
        table_data = get_inputs_table_data(
            scenario_id=scenario_id,
            db_path=db_path,
            table_type=table_type,
            ui_table_name_in_db=ui_table_name_in_db,
            ui_row_name_in_db=ui_row_name_in_db,
        )
    else:
        table_data = get_results_table_data(
            scenario_id=scenario_id,
            other_scenarios=other_scenarios,
            table=table,
            db_path=db_path,
        )

    with open(download_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow(table_data["columns"])
        for row in table_data["rowsData"]:
            values = [row[column] for column in table_data["columns"]]
            writer.writerow(values)


def save_plot_data_to_csv(
    db_path,
    download_path,
    scenario_id_list,
    plot_type,
    load_zone,
    carbon_cap_zone,
    energy_target_zone,
    period,
    horizon,
    start_timepoint,
    end_timepoint,
    subproblem,
    stage,
    project,
):
    """
    :param db_path: string, the path to the database
    :param download_path: string, the CSV file path
    :param scenario_id_list: list of integers, the scenario_ids to get data for
    :param plot_type: string, which plot
    :param load_zone: string, load zone parameter for the plot
    :param carbon_cap_zone: string, carbon cap zone parameter for the plot
    :param energy_target_zone: string, RPS zone parameter for the plot
    :param period: integer, period parameter for the plot
    :param horizon: integer, horizon parameter for the plot
    :param start_timepoint: integer, start timepoint parameter for the plot
    :param end_timepoint: integer, end timepoint parameter for the plot
    :param subproblem: integer, subproblem parameter for the plot
    :param stage: integer, stage parameter for the plot
    :param project: string, project parameter for the plot
    :return:

    Save plot data to CSV.
    """
    # Assume 1 for "default" subproblem and stage
    subproblem = 1 if subproblem == "default" else subproblem
    stage = 1 if stage == "default" else subproblem

    # Assume None for "default" other params
    load_zone = None if load_zone == "default" else load_zone
    carbon_cap_zone = None if carbon_cap_zone == "default" else carbon_cap_zone
    energy_target_zone = None if energy_target_zone == "default" else energy_target_zone
    period = None if period == "default" else period
    horizon = None if horizon == "default" else horizon
    start_timepoint = None if start_timepoint == "default" else start_timepoint
    end_timepoint = None if end_timepoint == "default" else end_timepoint
    project = None if project == "default" else project

    # Connect to the database
    conn = connect_to_database(db_path=db_path)

    # Import viz module, get the dataframes for all scenarios, and add them to
    # a list
    df_list = []
    try:
        imp_m = import_module("." + plot_type, package="viz")
        for scenario_id in scenario_id_list:
            df = imp_m.get_plotting_data(
                conn=conn,
                scenario_id=scenario_id,
                load_zone=load_zone,
                carbon_cap_zone=carbon_cap_zone,
                energy_target_zone=energy_target_zone,
                period=period,
                horizon=horizon,
                starting_tmp=start_timepoint,
                ending_tmp=end_timepoint,
                subproblem=subproblem,
                stage=stage,
                project=project,
            )
            df.insert(
                0,
                "scenario_name",
                conn.cursor()
                .execute(
                    """
                      SELECT scenario_name
                      FROM scenarios
                      WHERE scenario_id = {};
                      """.format(
                        scenario_id
                    )
                )
                .fetchone()[0],
            )
            df_list.append(df)
    except ImportError:
        print("ERROR! Visualization module " + plot_type + " not found.")

    export_df = pd.concat(df_list)
    export_df.to_csv(download_path, index=False)
