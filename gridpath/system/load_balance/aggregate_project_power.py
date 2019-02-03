#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate project dispatch for load balance
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Expression, value

from gridpath.auxiliary.dynamic_components import \
    required_operational_modules, load_balance_production_components
from gridpath.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Add power generation to load balance constraint
    def total_power_production_rule(mod, z, tmp):
        return sum(mod.Power_Provision_MW[g, tmp]
                   for g in mod.OPERATIONAL_PROJECTS_IN_TIMEPOINT[tmp]
                   if mod.load_zone[g] == z)
    m.Power_Production_in_Zone_MW = \
        Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                   rule=total_power_production_rule)
    getattr(d, load_balance_production_components).append(
        "Power_Production_in_Zone_MW")
