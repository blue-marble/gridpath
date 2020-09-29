#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.


from pyomo.environ import Set, Expression


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    """

    m.MARKET_HUB_PRJS_OPRTNL_IN_TMP = Set(
        m.TMPS,
        initialize=lambda mod, tmp:
        mod.MARKET_HUB_PRJS & mod.OPR_PRJS_IN_TMP[tmp]
    )

    def total_market_sales_rule(mod, hub, tmp):
        sum(mod.Sell_Power[prj, tmp]
            for prj in mod.MARKET_HUB_PRJS_OPRTNL_IN_TMP[tmp]
            if mod.market_hub[prj] == hub
            )

    m.Total_Market_Sales = Expression(
        m.MARKET_HUBS, m.TMPS,
        initialize=total_market_sales_rule
    )

    def total_market_purchases_rule(mod, hub, tmp):
        sum(mod.Buy_Power[prj, tmp]
            for prj in mod.MARKET_HUB_PRJS_OPRTNL_IN_TMP[tmp]
            if mod.market_hub[prj] == hub
            )

    m.Total_Market_Purchases = Expression(
        m.MARKET_HUBS, m.TMPS,
        initialize=total_market_purchases_rule
    )
