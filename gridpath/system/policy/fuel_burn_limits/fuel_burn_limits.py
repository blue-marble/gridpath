# Copyright 2016-2022 Blue Marble Analytics LLC.
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
Fuel burn limit for each fuel and fuel burn balancing area.
"""

import csv
import os.path


from pyomo.environ import Set, Param, NonNegativeReals, Any

Infinity = float("inf")


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT = Set(
        dimen=4, within=m.FUEL_BURN_LIMIT_BAS * m.BLN_TYPE_HRZS
    )
    m.fuel_burn_limit_unit = Param(
        m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT,
        within=NonNegativeReals,
        default=Infinity,
    )
    m.relative_fuel_burn_limit_fuel = Param(
        m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT,
        within=Any,
        default="undefined",
    )
    m.relative_fuel_burn_limit_ba = Param(
        m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT,
        within=Any,
        default="undefined",
    )

    m.fraction_of_relative_fuel_burn_limit_fuel_ba = Param(
        m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT,
        within=NonNegativeReals,
        default=Infinity,
    )

    m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_ABS_LIMIT = Set(
        dimen=4,
        initialize=lambda mod: [
            (f, ba, bt, h)
            for (f, ba, bt, h) in mod.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT
            if mod.fuel_burn_limit_unit[f, ba, bt, h] != Infinity
        ],
    )

    m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_REL_LIMIT = Set(
        dimen=4,
        initialize=lambda mod: [
            (f, ba, bt, h)
            for (f, ba, bt, h) in mod.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT
            if (
                mod.relative_fuel_burn_limit_fuel[f, ba, bt, h] != "undefined"
                and mod.relative_fuel_burn_limit_ba[f, ba, bt, h] != "undefined"
                and mod.fraction_of_relative_fuel_burn_limit_fuel_ba[f, ba, bt, h]
                != Infinity
            )
        ],
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
            "fuel_burn_limits.tab",
        ),
        index=m.FUEL_FUEL_BA_BLN_TYPE_HRZS_WITH_FUEL_BURN_LIMIT,
        param=(
            m.fuel_burn_limit_unit,
            m.relative_fuel_burn_limit_fuel,
            m.relative_fuel_burn_limit_ba,
            m.fraction_of_relative_fuel_burn_limit_fuel_ba,
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
    fuel_burn_limits = c.execute(
        """SELECT fuel, fuel_burn_limit_ba, balancing_type_horizon, horizon, 
        fuel_burn_limit_unit, relative_fuel_burn_limit_fuel, 
        relative_fuel_burn_limit_ba, fraction_of_relative_fuel_burn_limit_fuel_ba
        FROM inputs_system_fuel_burn_limits
        JOIN
        (SELECT balancing_type_horizon, horizon
        FROM inputs_temporal_horizons
        WHERE temporal_scenario_id = {temporal_scenario_id}) as relevant_horizons
        USING (balancing_type_horizon, horizon)
        JOIN
        (SELECT fuel, fuel_burn_limit_ba
        FROM inputs_geography_fuel_burn_limit_balancing_areas
        WHERE fuel_burn_limit_ba_scenario_id = {fuel_burn_limit_ba_scenario_id}) as 
        relevant_zones
        USING (fuel, fuel_burn_limit_ba)
        WHERE fuel_burn_limit_scenario_id = {fuel_burn_limit_scenario_id}
        AND subproblem_id = {subproblem_id}
        AND stage_id = {stage_id};
        """.format(
            temporal_scenario_id=subscenarios.TEMPORAL_SCENARIO_ID,
            fuel_burn_limit_ba_scenario_id=subscenarios.FUEL_BURN_LIMIT_BA_SCENARIO_ID,
            fuel_burn_limit_scenario_id=subscenarios.FUEL_BURN_LIMIT_SCENARIO_ID,
            subproblem_id=subproblem,
            stage_id=stage,
        )
    )

    return fuel_burn_limits


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
    # Validation to be added
    # carbon_cap_targets = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    carbon_cap.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    fuel_burn_limits = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "fuel_burn_limits.tab",
        ),
        "w",
        newline="",
    ) as carbon_cap_file:
        writer = csv.writer(carbon_cap_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "fuel",
                "fuel_burn_limit_ba",
                "balancing_type_horizon",
                "horizon",
                "fuel_burn_limit_unit",
                "relative_fuel_burn_limit_fuel",
                "relative_fuel_burn_limit_ba",
                "fraction_of_relative_fuel_burn_limit_fuel_ba",
            ]
        )

        for row in fuel_burn_limits:
            row = ["." if i is None else i for i in row]
            writer.writerow(row)
