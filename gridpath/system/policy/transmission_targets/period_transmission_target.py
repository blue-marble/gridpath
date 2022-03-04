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
Simplest implementation with a MWh target
"""

import csv
import os.path
from pyomo.environ import Set, Param, NonNegativeReals, PercentFraction, Expression


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET = Set(
        dimen=2, within=m.TRANSMISSION_TARGET_ZONES * m.PERIODS
    )

    # Transmission target specified in energy terms for the positive direction of the tx line
    m.period_transmission_target_pos_dir_mwh = Param(
        m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET,
        within=NonNegativeReals,
        default=0,
    )

    # Transmission target specified in energy terms for the negative direction of the tx line
    m.period_transmission_target_neg_dir_mwh = Param(
        m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET,
        within=NonNegativeReals,
        default=0,
    )

    def transmission_target_pos_dir_rule(mod, transmission_target_zone, period):
        """
        """

        return mod.period_transmission_target_pos_dir_mwh[transmission_target_zone, period]

    m.Period_Transmission_Target_Pos_Dir = Expression(
        m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET, rule=transmission_target_pos_dir_rule
    )

    def transmission_target_neg_dir_rule(mod, transmission_target_zone, period):
        """
        """

        return mod.period_transmission_target_neg_dir_mwh[transmission_target_zone, period]

    m.Period_Transmission_Target_Neg_Dir = Expression(
        m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET, rule=transmission_target_neg_dir_rule
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
    # Load the targets
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "period_transmission_targets.tab",
        ),
        index=m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET,
        param=(
            m.period_transmission_target_pos_dir_mwh,
            m.period_transmission_target_neg_dir_mwh,
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

    # Get the transmission flow and percent targets
    c = conn.cursor()
    transmission_targets = c.execute(
        """SELECT transmission_target_zone, period, transmission_target_positive_direction_mwh, 
        transmission_target_negative_direction_mwh
        FROM inputs_system_period_transmission_targets
        JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        USING (period)
        JOIN
        (SELECT transmission_target_zone
        FROM inputs_geography_transmission_target_zones
        WHERE transmission_target_zone_scenario_id = {}) as relevant_zones
        USING (transmission_target_zone)
        WHERE period_transmission_target_scenario_id = {}
        AND subproblem_id = {}
        AND stage_ID = {};
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.TRANSMISSION_TARGET_ZONE_SCENARIO_ID,
            subscenarios.PERIOD_TRANSMISSION_TARGET_SCENARIO_ID,
            subproblem,
            stage,
        )
    )

    return transmission_targets


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
    period_transmission_targets.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    transmission_targets = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "period_transmission_targets.tab",
        ),
        "w",
        newline="",
    ) as transmission_targets_tab_file:
        writer = csv.writer(
            transmission_targets_tab_file, delimiter="\t", lineterminator="\n"
        )

        # Write header
        writer.writerow(
            [
                "transmission_target_zone",
                "period",
                "transmission_target_positive_direction_mwh",
                "transmission_target_negative_direction_mwh",
            ]
        )

        for row in transmission_targets:
            # It's OK if targets are not specified; they default to 0
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
