# Copyright 2022 (c) Crown Copyright, GC.
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
Performance standard for each performance_standard zone
"""

import csv
import os.path
import pandas as pd

from pyomo.environ import Set, Param, NonNegativeReals, value

from gridpath.common_functions import create_results_df
from gridpath.system.policy.performance_standard import PERFORMANCE_STANDARD_Z_PRD_DF


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD = Set(
        dimen=2, within=m.PERFORMANCE_STANDARD_ZONES * m.PERIODS
    )
    m.performance_standard = Param(
        m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD,
        within=NonNegativeReals,
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
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
            str(subproblem),
            str(stage),
            "inputs",
            "performance_standard.tab",
        ),
        index=m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD,
        param=m.performance_standard,
        select=(
            "performance_standard_zone",
            "period",
            "performance_standard_tco2_per_mwh",
        ),
    )


def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()
    performance_standard = c.execute(
        """SELECT performance_standard_zone, period, performance_standard_tco2_per_mwh
        FROM inputs_system_performance_standard
        JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        USING (period)
        JOIN
        (SELECT performance_standard_zone
        FROM inputs_geography_performance_standard_zones
        WHERE performance_standard_zone_scenario_id = {}) as relevant_zones
        using (performance_standard_zone)
        WHERE performance_standard_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PERFORMANCE_STANDARD_ZONE_SCENARIO_ID,
            subscenarios.PERFORMANCE_STANDARD_SCENARIO_ID,
            subproblem,
            stage,
        )
    )

    return performance_standard


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    performance_standard.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    performance_standard = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "performance_standard.tab",
        ),
        "w",
        newline="",
    ) as performance_standard_file:
        writer = csv.writer(
            performance_standard_file, delimiter="\t", lineterminator="\n"
        )

        # Write header
        writer.writerow(
            ["performance_standard_zone", "period", "performance_standard_tco2_per_mwh"]
        )

        for row in performance_standard:
            writer.writerow(row)


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    results_columns = [
        "performance_standard_tco2_per_mwh",
    ]
    data = [
        [
            z,
            p,
            float(m.performance_standard[z, p]),
        ]
        for (z, p) in m.PERFORMANCE_STANDARD_ZONE_PERIODS_WITH_PERFORMANCE_STANDARD
    ]
    results_df = create_results_df(
        index_columns=["performance_standard_zone", "period"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, PERFORMANCE_STANDARD_Z_PRD_DF)[c] = None
    getattr(d, PERFORMANCE_STANDARD_Z_PRD_DF).update(results_df)
