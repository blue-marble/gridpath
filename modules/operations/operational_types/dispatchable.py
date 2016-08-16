#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""

import os
import csv

from pyomo.environ import *


def add_model_components(m):
    """

    :param m:
    :return:
    """

    def power_provision_rule(mod, g, tmp):
        return mod.Provide_Power[g, tmp]

    m.Dispatchable_Power = Expression(
        m.DISPATCHABLE_GENERATORS,
        m.TIMEPOINTS,
        rule=power_provision_rule)

    def max_power_rule(mod, g, tmp):
        """
        Components can include power, upward reserves, upward regulation
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power[g, tmp] + \
            sum(getattr(mod, c)[g, tmp]
                for c in mod.headroom_variables[g]) \
            <= mod.capacity[g]

    m.Max_Headroom_Constraint = Constraint(m.DISPATCHABLE_GENERATORS,
                                           m.TIMEPOINTS,
                                           rule=max_power_rule)

    # TODO: add min stable level
    def min_power_rule(mod, g, tmp):
        """
        The lower bound of services a dispatchable generator can provide.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power[g, tmp] - \
            sum(getattr(mod, c)[g, tmp]
                for c in mod.footroom_variables[g]) \
            >= 0
    m.Max_Footroom_Constraint = Constraint(m.DISPATCHABLE_GENERATORS,
                                           m.TIMEPOINTS,
                                           rule=min_power_rule)


