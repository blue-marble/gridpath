#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, Var, Expression, Reals


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    m.TRANSMISSION_LINES = Set()
    m.load_zone_from = Param(m.TRANSMISSION_LINES)
    m.load_zone_to = Param(m.TRANSMISSION_LINES)
    m.tx_min_mw = Param(m.TRANSMISSION_LINES, within=Reals)
    m.tx_max_mw = Param(m.TRANSMISSION_LINES, within=Reals)

    m.Transmit_Power_MW = Var(m.TRANSMISSION_LINES, m.TIMEPOINTS,
                              within=Reals)

    # Add to load balance
    def total_transmission_to_rule(mod, z, tmp):
        return sum(mod.Transmit_Power_MW[tx, tmp]
                   for tx in mod.TRANSMISSION_LINES
                   if mod.load_zone_to[tx] == z)
    m.Transmission_to_Zone_MW = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                           rule=total_transmission_to_rule)
    d.load_balance_production_components.append("Transmission_to_Zone_MW")

    def total_transmission_from_rule(mod, z, tmp):
        return sum(mod.Transmit_Power_MW[tx, tmp]
                   for tx in mod.TRANSMISSION_LINES
                   if mod.load_zone_from[tx] == z)
    m.Transmission_from_Zone_MW = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                             rule=total_transmission_from_rule)
    d.load_balance_consumption_components.append("Transmission_from_Zone_MW")


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory, "inputs",
                                           "transmission_lines.tab"),
                     select=("TRANSMISSION_LINES", "load_zone_from",
                             "load_zone_to", "tx_min_mw", "tx_max_mw"),
                     index=m.TRANSMISSION_LINES,
                     param=(m.load_zone_from, m.load_zone_to,
                            m.tx_min_mw, m.tx_max_mw)
                     )


def export_results(scenario_directory, horizon, stage, m):
    for tx in getattr(m, "TRANSMISSION_LINES"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Transmit_Power_MW[" + str(tx) + ", " + str(tmp) + "]: "
                  + str(m.Transmit_Power_MW[tx, tmp].value)
                  )