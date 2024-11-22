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

import csv
import os.path
from pyomo.environ import Param, Reals

from gridpath.auxiliary.db_interface import directories_to_db_values


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
    """ """
    # Price by market and timepoint
    # Prices are allowed to be negative
    m.market_price = Param(m.MARKETS, m.TMPS, within=Reals)


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
    """ """

    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "market_prices.tab",
        ),
        param=m.market_price,
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

    (varies_by_weather_iteration, varies_by_hydro_iteration) = c.execute(
        f"""
        SELECT varies_by_weather_iteration, varies_by_hydro_iteration
        FROM inputs_market_prices
        WHERE market_price_scenario_id = {subscenarios.MARKET_PRICE_SCENARIO_ID} 
        """
    ).fetchone()

    weather_iteration_to_use = weather_iteration if varies_by_weather_iteration else 0
    hydro_iteration_to_use = hydro_iteration if varies_by_hydro_iteration else 0

    c1 = conn.cursor()
    prices = c1.execute(
        f"""
        SELECT market, timepoint, market_price
        -- Get prices for included markets only
        FROM (
            SELECT market
            FROM inputs_geography_markets
            WHERE market_scenario_id = {subscenarios.MARKET_SCENARIO_ID}
        ) as market_tbl
        -- Get prices for included timepoints only
        CROSS JOIN (
            SELECT stage_id, timepoint from inputs_temporal
            WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
            AND subproblem_id = {subproblem}
            AND stage_id = {stage}
        ) as tmp_tbl
        LEFT OUTER JOIN (
            SELECT market, stage_id, timepoint, market_price
            FROM inputs_market_price_profiles
            WHERE market_price_profile_scenario_id = (
            SELECT market_price_profile_scenario_id
            FROM inputs_market_prices
            WHERE market_price_scenario_id = {subscenarios.MARKET_PRICE_SCENARIO_ID}
            AND hydro_iteration = {hydro_iteration_to_use}
            AND weather_iteration = {weather_iteration_to_use}
            ) 
        ) as price_tbl
        USING (market, stage_id, timepoint)
        ;
        """
    )

    return prices


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
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection

    Get inputs from database and write out the model input
    market_prices.tab file.
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

    prices = get_inputs_from_database(
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
            "market_prices.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        writer.writerow(["market", "timepoint", "price"])
        for row in prices:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
