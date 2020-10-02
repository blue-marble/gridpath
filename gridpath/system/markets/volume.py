#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Expression, Param, Constraint
Infinity = float('inf')


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    """
    m.max_market_sales = Param(
        m.MARKETS, m.TMPS,
        default=Infinity
    )

    m.max_market_purchases = Param(
        m.MARKETS, m.TMPS,
        default=Infinity
    )

    def total_market_sales_rule(mod, market, tmp):
        return sum(mod.Sell_Power[lz, mrkt, tmp]
            for (lz, mrkt) in mod.LZ_MARKETS
            if mrkt == market
            )

    m.Total_Market_Sales = Expression(
        m.MARKETS, m.TMPS,
        rule=total_market_sales_rule
    )

    def total_market_purchases_rule(mod, market, tmp):
        return sum(mod.Buy_Power[lz, mrkt, tmp]
            for (lz, mrkt) in mod.LZ_MARKETS
            if mrkt == market
            )

    m.Total_Market_Purchases = Expression(
        m.MARKETS, m.TMPS,
        rule=total_market_purchases_rule
    )

    def max_market_sales_rule(mod, hub, tmp):
        return mod.Total_Market_Sales[hub, tmp] \
               <= mod.max_market_sales[hub, tmp]

    m.Max_Market_Sales_Constraint = Constraint(
        m.MARKETS, m.TMPS,
        rule=max_market_sales_rule
    )

    def max_market_purchases_rule(mod, hub, tmp):
        return mod.Total_Market_Purchases[hub, tmp] \
               <= mod.max_market_purchases[hub, tmp]

    m.Max_Market_Purchases_Constraint = Constraint(
        m.MARKETS, m.TMPS,
        rule=max_market_purchases_rule
    )


def load_model_data(
    m, d, data_portal, scenario_directory, subproblem, stage
):
    data_portal.load(
        filename=os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs",
            "market_volume.tab"
        ),
        param=(m.max_market_sales, m.max_market_purchases)
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

    # Get load zones and their markets; only include load zones that are
    # in the load_zone_scenario_id and markets that are in the
    # market_scenario_id
    market_limits = c.execute(
        """
        SELECT market, timepoint, max_market_sales, max_market_purchases
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
            SELECT market, timepoint, max_market_sales, max_market_purchases
            FROM inputs_market_volume
            WHERE market_volume_scenario_id = ?
        ) as price_tbl
        USING (market, timepoint)
        ;
        """,
        (subscenarios.MARKET_SCENARIO_ID,
         subscenarios.TEMPORAL_SCENARIO_ID,
         subscenarios.MARKET_VOLUME_SCENARIO_ID)
    )

    return market_limits


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

    market_limits = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
            os.path.join(
                scenario_directory, str(subproblem), str(stage), "inputs",
                "market_volume.tab"
            ), "w", newline=""
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        writer.writerow(["market", "timepoint", "max_market_sales",
                         "max_market_purchases"])
        for row in market_limits:
            writer.writerow(row)
