#!/usr/bin/env python

"""
Operations of variable generators. Can't provide reserves.
No curtailment variable by individual generator.
"""

import os

from pyomo.environ import *


def add_model_components(m):
    """

    :param m:
    :return:
    """

    m.cap_factor = Param(m.VARIABLE_GENERATORS, m.TIMEPOINTS,
                         within=PercentFraction)

    # Operations
    def max_available_power_rule(mod, g, tmp):
        return mod.capacity[g] * mod.cap_factor[g, tmp]

    m.Variable_Power = Expression(m.VARIABLE_GENERATORS,
                                                   m.TIMEPOINTS,
                                                   rule=
                                                   max_available_power_rule)

    def max_power_rule(mod, g, tmp):
        """
        No variables to constraint for variable generators.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return Constraint.Skip

    def min_power_rule(mod, g, tmp):
        """
        No variables to constraint for variable generators.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return Constraint.Skip


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory,
                                           "variable_generator_profiles.tab"),
                     index=(m.VARIABLE_GENERATORS, m.TIMEPOINTS),
                     param=m.cap_factor
                     )