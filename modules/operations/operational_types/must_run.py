#!/usr/bin/env python

"""
Operations of must-run generators. Can't provide reserves.
"""

import os

from pyomo.environ import *


def add_model_components(m):
    """

    :param m:
    :return:
    """
    def power_provision_rule(mod, g, tmp):
        return mod.capacity[g]
    m.Must_Run_Power = Expression(m.MUST_RUN_GENERATORS,
                                  m.TIMEPOINTS,
                                  rule=power_provision_rule
                                  )

    def max_power_rule(mod, g, tmp):
        """
        No variables to constraint for must-run generators.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return Constraint.Skip

    def min_power_rule(mod, g, tmp):
        """
        No variables to constraint for must-run generators.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return Constraint.Skip
