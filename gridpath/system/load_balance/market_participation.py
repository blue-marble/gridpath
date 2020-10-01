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

    m.LZ_MARKET_HUBS = Set(dimen=2, within=m.LOAD_ZONES*m.MARKET_HUBS)

    m.MARKET_HUB_LZS = Set(
        within=m.LOAD_ZONES,
        initialize=lambda mod: set([lz for (lz, hub) in mod.LZ_MARKET_HUBS])
    )

    m.MARKET_HUBS_BY_LZ = Set(
        m.MARKET_HUB_LZS,
        within=m.MARKET_HUBS,
        initialize=lambda mod, lz:
        [hub for (zone, hub) in mod.LZ_MARKET_HUBS if zone == lz]
    )

    m.Sell_Power = Var(m.LZ_MARKET_HUBS, m.TMPS, within=NonNegativeReals)

    m.Buy_Power = Var(m.LZ_MARKET_HUBS, m.TMPS, within=NonNegativeReals)

    def total_power_sold_from_zone_rule(mod, z, tmp):
        if z in mod.MARKET_HUB_LZS:
            return sum(
                mod.Sell_Power[z, hub, tmp]
                for hub in mod.MARKET_HUBS_BY_LZ[z]
            )
        else:
            return 0

    m.Total_Power_Sold = Expression(
        m.LOAD_ZONES, m.TMPS,
        initialize=total_power_sold_from_zone_rule
    )

    def total_power_sold_to_zone_rule(mod, z, tmp):
        if z in mod.MARKET_HUB_LZS:
            return sum(
                mod.Buy_Power[z, hub, tmp]
                for hub in mod.MARKET_HUBS_BY_LZ[z]
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
            "load_zone_market_hubs.tab"
        ),
        set=m.LZ_MARKET_HUBS
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

    # Get load zones and their market hubs; only include load zones that are
    # in the load_zone_scenario_id and market hubs that are in the
    # market_hub_scenario_id
    load_zone_market_hubs = c.execute(
        """
        SELECT load_zone, market_hub
        FROM
        -- Get included load_zones only
        (SELECT load_zone
            FROM inputs_geography_load_zones
            WHERE load_zone_scenario_id = ?
        ) as lz_tbl
        LEFT OUTER JOIN 
        -- Get market hubs for those load zones
        (SELECT load_zone, market_hub
            FROM inputs_load_zone_market_hubs
            WHERE load_zone_market_hub_scenario_id = ?
        ) as lz_mh_tbl
        USING (load_zone)
        -- Filter out load zones whose market hub is not included in our 
        -- market_hub_scenario_id
        WHERE market_hub in (
            SELECT market_hub
                FROM inputs_geography_market_hubs
                WHERE market_hub_scenario_id = ?
        );
        """,
        (subscenarios.LOAD_SCENARIO_ID,
         subscenarios.LOAD_ZONE_MARKET_HUB_SCENARIO_ID,
         subscenarios.MARKET_HUB_SCENARIO_ID)
    )

    return load_zone_market_hubs


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection

    Get inputs from database and write out the model input
    load_zone_market_hubs.tab file.
    """

    load_zone_market_hubs = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(
            os.path.join(
                scenario_directory, str(subproblem), str(stage), "inputs",
                "load_zone_market_hubs.tab"
            ), "w", newline=""
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        writer.writerows(["load_zone", "market_hub"])
        for row in load_zone_market_hubs:
            writer.writerow(row)
