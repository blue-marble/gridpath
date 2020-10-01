#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Set, Var, Expression, NonNegativeReals

from gridpath.auxiliary.dynamic_components import \
    load_balance_production_components, load_balance_consumption_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    """

    m.LZ_MARKETS = Set(dimen=2, within=m.LOAD_ZONES*m.MARKETS)

    m.MARKET_LZS = Set(
        within=m.LOAD_ZONES,
        initialize=lambda mod: set([lz for (lz, hub) in mod.LZ_MARKETS])
    )

    m.MARKETS_BY_LZ = Set(
        m.MARKET_LZS,
        within=m.MARKETS,
        initialize=lambda mod, lz:
        [hub for (zone, hub) in mod.LZ_MARKETS if zone == lz]
    )

    m.Sell_Power = Var(m.LZ_MARKETS, m.TMPS, within=NonNegativeReals)

    m.Buy_Power = Var(m.LZ_MARKETS, m.TMPS, within=NonNegativeReals)

    def total_power_sold_from_zone_rule(mod, z, tmp):
        if z in mod.MARKET_LZS:
            return sum(
                mod.Sell_Power[z, hub, tmp]
                for hub in mod.MARKETS_BY_LZ[z]
            )
        else:
            return 0

    m.Total_Power_Sold = Expression(
        m.LOAD_ZONES, m.TMPS,
        initialize=total_power_sold_from_zone_rule
    )

    def total_power_sold_to_zone_rule(mod, z, tmp):
        if z in mod.MARKET_LZS:
            return sum(
                mod.Buy_Power[z, hub, tmp]
                for hub in mod.MARKETS_BY_LZ[z]
            )
        else:
            return 0

    m.Total_Power_Bought = Expression(
        m.LOAD_ZONES, m.TMPS,
        initialize=total_power_sold_to_zone_rule
    )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:
    :return:

    """
    getattr(dynamic_components, load_balance_consumption_components).append(
        "Total_Power_Sold"
    )
    getattr(dynamic_components, load_balance_production_components).append(
        "Total_Power_Bought"
    )


def load_model_data(
    m, d, data_portal, scenario_directory, subproblem, stage
):
    data_portal.load(
        filename=os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs",
            "load_zone_markets.tab"
        ),
        set=m.LZ_MARKETS
    )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
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
    load_zone_markets = c.execute(
        """
        SELECT load_zone, market
        FROM
        -- Get included load_zones only
        (SELECT load_zone
            FROM inputs_geography_load_zones
            WHERE load_zone_scenario_id = ?
        ) as lz_tbl
        LEFT OUTER JOIN 
        -- Get markets for those load zones
        (SELECT load_zone, market
            FROM inputs_load_zone_markets
            WHERE load_zone_market_scenario_id = ?
        ) as lz_mh_tbl
        USING (load_zone)
        -- Filter out load zones whose market is not included in our 
        -- market_scenario_id
        WHERE market in (
            SELECT market
                FROM inputs_geography_markets
                WHERE market_scenario_id = ?
        );
        """,
        (subscenarios.LOAD_SCENARIO_ID,
         subscenarios.LOAD_ZONE_MARKET_SCENARIO_ID,
         subscenarios.MARKET_SCENARIO_ID)
    )

    return load_zone_markets


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection

    Get inputs from database and write out the model input
    load_zone_markets.tab file.
    """

    load_zone_markets = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(
            os.path.join(
                scenario_directory, str(subproblem), str(stage), "inputs",
                "load_zone_markets.tab"
            ), "w", newline=""
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        writer.writerows(["load_zone", "market"])
        for row in load_zone_markets:
            writer.writerow(row)
