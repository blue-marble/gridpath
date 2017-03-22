#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate carbon emissions from the project-timepoint level to
the carbon cap zone - period level.
"""

import csv
import os.path
from pyomo.environ import Param, Set, Expression, value

from gridpath.auxiliary.dynamic_components import \
    required_operational_modules, carbon_cap_balance_emission_components
from gridpath.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    def total_carbon_emissions_rule(mod, z, p):
        """
        Calculate total emissions from all carbonaceous generators in carbon
        cap zone
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(mod.Carbon_Emissions_Tons[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   for (g, tmp) in
                   mod.CARBONACEOUS_PROJECT_OPERATIONAL_TIMEPOINTS
                   if g in mod.CARBONACEOUS_PROJECTS_BY_CARBON_CAP_ZONE[z]
                   and tmp in mod.TIMEPOINTS_IN_PERIOD[p]
                   )

    m.Total_Carbon_Emissions_Tons = Expression(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
        rule=total_carbon_emissions_rule
    )

    # Add to emission imports to carbon balance
    getattr(d, carbon_cap_balance_emission_components).append(
        "Total_Carbon_Emissions_Tons"
    )
