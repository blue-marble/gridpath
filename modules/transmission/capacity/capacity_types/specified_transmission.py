#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, Reals


def add_module_specific_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS = Set(dimen=2)
    m.tx_capacity_type_operational_period_sets.append(
        "SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS"
    )

    m.specified_tx_min_mw = \
        Param(m.SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS, within=Reals)
    m.specified_tx_max_mw = \
        Param(m.SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS, within=Reals)


def min_transmission_capacity_rule(mod, tx, p):
    return mod.specified_tx_min_mw[tx, p]


def max_transmission_capacity_rule(mod, tx, p):
    return mod.specified_tx_max_mw[tx, p]


# TODO: should there be a fixed cost for keeping transmission around
def tx_capacity_cost_rule(mod, g, p):
    """
    None for now
    :param mod:
    :return:
    """
    return 0


def load_module_specific_data(m, data_portal, scenario_directory,
                              horizon, stage):
    data_portal.load(filename=
                     os.path.join(
                         scenario_directory, "inputs",
                         "specified_transmission_line_capacities.tab"),
                     select=("transmission_line", "period",
                             "specified_tx_min_mw", "specified_tx_max_mw"),
                     index=m.SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS,
                     param=(m.specified_tx_min_mw,
                            m.specified_tx_max_mw)
                     )
