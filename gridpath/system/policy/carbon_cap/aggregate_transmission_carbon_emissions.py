#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate carbon emissions from the transmission-line-timepoint level to
the carbon cap zone - period level.
"""

import csv
import os.path
from pyomo.environ import Param, Set, Var, Constraint, Expression, \
    NonNegativeReals, value

from gridpath.auxiliary.dynamic_components import \
    carbon_cap_balance_emission_components


def add_model_components(m, d):
    """
    Aggregate total imports of emissions and add to carbon balance constraint
    :param m:
    :param d:
    :return:
    """
    def total_carbon_emissions_imports_rule(mod, z, p):
        """
        Calculate total emissions from all carbonaceous transmission lines
        imported into the carbon cap zone
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(mod.Import_Carbon_Emissions_Tons[tx, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   for (tx, tmp) in
                   mod.CARBONACEOUS_TRANSMISSION_OPERATIONAL_TIMEPOINTS
                   if tx in
                   mod.CARBONACEOUS_TRANSMISSION_LINES_BY_CARBON_CAP_ZONE[z]
                   and tmp in mod.TIMEPOINTS_IN_PERIOD[p]
                   )

    m.Total_Carbon_Emission_Imports_Tons = Expression(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
        rule=total_carbon_emissions_imports_rule
    )

    # Add to emission imports to carbon balance
    getattr(d, carbon_cap_balance_emission_components).append(
        "Total_Carbon_Emission_Imports_Tons"
    )
