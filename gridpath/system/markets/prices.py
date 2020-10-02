#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Param, Reals


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    """
    # Price by market and timepoint
    # Prices are allowed to be negative
    m.market_price = Param(
        m.MARKETS, m.TMPS,
        within=Reals
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    """

    data_portal.load(
        filename=os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs",
            "market_prices.tab"
        ),
        param=m.market_price
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

    prices = c.execute(
        """
        SELECT market, timepoint, market_price
        -- Get prices for included markets only
        FROM (
            SELECT market
            FROM inputs_geography_markets
            WHERE market_scenario_id = ?
        ) as market_tbl
        -- Get prices for included timepoints only
        CROSS JOIN (
            SELECT timepoint from inputs_temporal
            WHERE temporal_scenario_id = ?
        ) as tmp_tbl
        LEFT OUTER JOIN (
            SELECT market, timepoint, market_price
            FROM inputs_market_prices
            WHERE market_price_scenario_id = ?
        ) as price_tbl
        USING (market, timepoint)
        ;
        """,
        (subscenarios.MARKET_SCENARIO_ID,
         subscenarios.TEMPORAL_SCENARIO_ID,
         subscenarios.MARKET_PRICE_SCENARIO_ID)
    )

    return prices


def write_model_inputs(scenario_directory, scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection

    Get inputs from database and write out the model input
    market_prices.tab file.
    """

    prices = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
            os.path.join(
                scenario_directory, str(subproblem), str(stage), "inputs",
                "market_prices.tab"
            ), "w", newline=""
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        writer.writerow(["market", "timepoint", "price"])
        for row in prices:
            writer.writerow(row)
