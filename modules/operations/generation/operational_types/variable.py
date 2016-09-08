#!/usr/bin/env python

"""
Operations of variable generators. Can't provide reserves.
No curtailment variable by individual generator.
"""

import os.path
from pyomo.environ import Param, PercentFraction, Constraint, Expression


def add_module_specific_components(m, scenario_directory):
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

    return mod.Capacity_MW[g, mod.period[tmp]] * mod.cap_factor[g, tmp]


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


def fuel_cost_rule(mod, g, tmp):
    """
    Variable generators should not have fuel use
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise (ValueError(
        "ERROR! Variable generators should not use fuel." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its fuel to '.' (no value).")
    )


def startup_rule(mod, g, tmp):
    """
    Variable generators are never started up.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! Variable generators should not incur startup costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup costs to '.' (no value).")
    )


def shutdown_rule(mod, g, tmp):
    """
    Variable generators are never started up.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! Variable generators should not incur shutdown costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its shutdown costs to '.' (no value).")
    )


def load_module_specific_data(mod, data_portal, scenario_directory,
                              horizon, stage):
    """
    Capacity factors vary by horizon and stage, so get inputs from appropriate
    directory
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs",
                                           "variable_generator_profiles.tab"),
                     index=(mod.VARIABLE_GENERATORS, mod.TIMEPOINTS),
                     param=mod.cap_factor
                     )
