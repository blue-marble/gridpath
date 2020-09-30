#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.


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
