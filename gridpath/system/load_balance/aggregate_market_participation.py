#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.


from pyomo.environ import Set, Expression

from gridpath.auxiliary.dynamic_components import \
    load_balance_production_components, load_balance_consumption_components


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    """
    def total_power_sold_from_zone_rule(mod, z, tmp):
        sum(mod.Sell_Power[prj, tmp]
            for prj in mod.MARKET_HUB_PRJS_OPRTNL_IN_TMP[tmp]
            if mod.load_zone[prj] == z
            )

    m.Total_Power_Sold_From_Zone = Expression(
        m.LOAD_ZONES, m.TMPS,
        initialize=total_power_sold_from_zone_rule
    )

    def total_power_sold_to_zone_rule(mod, z, tmp):
        sum(mod.Buy_Power[prj, tmp]
            for prj in mod.MARKET_HUB_PRJS_OPRTNL_IN_TMP[tmp]
            if mod.load_zone[prj] == z
            )

    m.Total_Power_Sold_To_Zone = Expression(
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
        "Total_Power_Sold_From_Zone")
    getattr(dynamic_components, load_balance_production_components).append(
        "Total_Power_Sold_To_Zone")
