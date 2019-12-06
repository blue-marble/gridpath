#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This is a line-level module that adds to the formulation components that
describe the amount of power flowing on each line.
"""

from __future__ import print_function

from pyomo.environ import Set, Var, Constraint, Reals


def add_module_specific_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Set: Simple transmission lines
    m.TRANSMISSION_LINES_SIMPLE = Set(
        within=m.TRANSMISSION_LINES,
        rule=lambda mod: set(l for l in mod.TRANSMISSION_LINES if
                             mod.tx_operational_type[l] ==
                             "tx_simple")
    )

    # Set: Operational timepoints
    m.TX_SIMPLE_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2, within=m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
            set((l, tmp) for (l, tmp) in mod.TRANSMISSION_OPERATIONAL_TIMEPOINTS
                if l in mod.TRANSMISSION_LINES_SIMPLE))

    # Decision variable: transmitted power flow
    m.Transmit_Power_Simple_MW = Var(m.TX_SIMPLE_OPERATIONAL_TIMEPOINTS,
                                     within=Reals)

    # TODO: should these move to operations.py since all transmission op_types
    #  have this constraint?
    def min_transmit_rule(mod, l, tmp):
        """

        :param mod:
        :param l:
        :param tmp:
        :return:
        """
        return mod.Transmit_Power_Simple_MW[l, tmp] \
               >= mod.Transmission_Min_Capacity_MW[l, mod.period[tmp]]

    m.Min_Transmit_Constraint = \
        Constraint(m.TX_SIMPLE_OPERATIONAL_TIMEPOINTS,
                   rule=min_transmit_rule)

    def max_transmit_rule(mod, l, tmp):
        """

        :param mod:
        :param l:
        :param tmp:
        :return:
        """
        return mod.Transmit_Power_Simple_MW[l, tmp] \
               <= mod.Transmission_Max_Capacity_MW[l, mod.period[tmp]]

    m.Max_Transmit_Constraint = \
        Constraint(m.TX_SIMPLE_OPERATIONAL_TIMEPOINTS,
                   rule=max_transmit_rule)


def transmit_power_rule(mod, l, tmp):
    """

    :param mod:
    :param l:
    :param tmp:
    :return:
    """
    return mod.Transmit_Power_Simple_MW[l, tmp]
