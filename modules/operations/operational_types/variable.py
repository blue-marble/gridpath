#!/usr/bin/env python

"""
Operations of variable generators. Can't provide reserves.
No curtailment variable by individual generator.
"""

import os

from pyomo.environ import *


def add_module_specific_components(m):
    """
    Variable generators require a capacity factor for each timepoint.
    :param m:
    :return:
    """

    m.cap_factor = Param(m.VARIABLE_GENERATORS, m.TIMEPOINTS,
                         within=PercentFraction)


# Operations
def power_provision_rule(mod, g, tmp):
    """
    Power provision from variable generators is their capacity times the
    capacity factor in each timepoint.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.capacity[g] * mod.cap_factor[g, tmp]


def max_power_rule(mod, g, tmp):
    """
    No variables to constrain for variable generators.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return Constraint.Skip


def min_power_rule(mod, g, tmp):
    """
    No variables to constrain for variable generators.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return Constraint.Skip


def load_module_specific_data(mod, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory,
                                           "variable_generator_profiles.tab"),
                     index=(mod.VARIABLE_GENERATORS, mod.TIMEPOINTS),
                     param=mod.cap_factor
                     )
