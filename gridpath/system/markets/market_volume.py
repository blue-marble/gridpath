#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.


from pyomo.environ import Set, Expression, Param, Constraint
Infinity = float('inf')


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    """

    m.MARKET_PRJS_OPRTNL_IN_TMP = Set(
        m.TMPS,
        initialize=lambda mod, tmp:
        mod.MARKET_PRJS & mod.OPR_PRJS_IN_TMP[tmp]
    )

    m.max_market_sales = Param(
        m.MARKETS, m.TMPS,
        default=Infinity
    )

    m.max_market_purchases = Param(
        m.MARKETS, m.TMPS,
        default=Infinity
    )

    def total_market_sales_rule(mod, hub, tmp):
        sum(mod.Sell_Power[prj, tmp]
            for prj in mod.MARKET_PRJS_OPRTNL_IN_TMP[tmp]
            if mod.market[prj] == hub
            )

    m.Total_Market_Sales = Expression(
        m.MARKETS, m.TMPS,
        initialize=total_market_sales_rule
    )

    def total_market_purchases_rule(mod, hub, tmp):
        sum(mod.Buy_Power[prj, tmp]
            for prj in mod.MARKET_PRJS_OPRTNL_IN_TMP[tmp]
            if mod.market[prj] == hub
            )

    m.Total_Market_Purchases = Expression(
        m.MARKETS, m.TMPS,
        initialize=total_market_purchases_rule
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
