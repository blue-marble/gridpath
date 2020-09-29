#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

import os.path
from pyomo.environ import Param, NonNegativeReals


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    """
    # Price by market hub and timepoint
    # If not specified for a hub-timepoint combination, will default to 0
    m.market_price = Param(
        m.MARKET_HUB, m.TMPS,
        within=NonNegativeReals,
        default=0
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
