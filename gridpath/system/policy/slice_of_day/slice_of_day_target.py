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
Slice-of-day target (MW) for each zone, period, month, and hour.
"""

import csv
import os.path

from pyomo.environ import Set, Param, NonNegativeReals

from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.common_functions import create_results_df
from gridpath.system.policy.slice_of_day import SLICE_OF_DAY_ZONE_PRD_MONTH_HOUR_DF


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param m:
    :param d:
    :return:
    """

    m.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS = Set(dimen=4)
    m.slice_of_day_target_mw = Param(
        m.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS, within=NonNegativeReals
    )


def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "slice_of_day_targets.tab",
        ),
        index=m.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS,
        param=m.slice_of_day_target_mw,
        select=(
            "slice_of_day_zone",
            "period",
            "month",
            "hour",
            "slice_of_day_target_mw",
        ),
    )


def get_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()
    slice_of_day_targets = c.execute(
        """SELECT slice_of_day_zone, period, month, hour, slice_of_day_target_mw
        FROM inputs_system_slice_of_day_targets
        JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {temporal}) as relevant_periods
        USING (period)
        JOIN
        (SELECT slice_of_day_zone
        FROM inputs_geography_slice_of_day_zones
        WHERE slice_of_day_zone_scenario_id = {sod_zone}) as relevant_zones
        USING (slice_of_day_zone)
        WHERE slice_of_day_target_scenario_id = {sod_target};
        """.format(
            temporal=subscenarios.TEMPORAL_SCENARIO_ID,
            sod_zone=subscenarios.SLICE_OF_DAY_ZONE_SCENARIO_ID,
            sod_target=subscenarios.SLICE_OF_DAY_TARGET_SCENARIO_ID,
        )
    )

    return slice_of_day_targets


def validate_inputs(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass
    # Validation to be added
    # slice_of_day_targets = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    Get inputs from database and write out the model input
    slice_of_day_targets.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    slice_of_day_targets = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "slice_of_day_targets.tab",
        ),
        "w",
        newline="",
    ) as slice_of_day_targets_tab_file:
        writer = csv.writer(
            slice_of_day_targets_tab_file, delimiter="\t", lineterminator="\n"
        )

        # Write header
        writer.writerow(
            [
                "slice_of_day_zone",
                "period",
                "month",
                "hour",
                "slice_of_day_target_mw",
            ]
        )

        for row in slice_of_day_targets:
            writer.writerow(row)


def export_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
    d,
):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    results_columns = [
        "slice_of_day_target_mw",
    ]
    data = [
        [
            z,
            p,
            mn,
            hr,
            float(m.slice_of_day_target_mw[z, p, mn, hr]),
        ]
        for (z, p, mn, hr) in m.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
    ]
    results_df = create_results_df(
        index_columns=["slice_of_day_zone", "period", "month", "hour"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, SLICE_OF_DAY_ZONE_PRD_MONTH_HOUR_DF)[c] = None
    getattr(d, SLICE_OF_DAY_ZONE_PRD_MONTH_HOUR_DF).update(results_df)
