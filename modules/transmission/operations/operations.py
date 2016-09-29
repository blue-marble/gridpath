#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Var, Constraint, Expression, Reals

from modules.auxiliary.dynamic_components import \
    load_balance_production_components, load_balance_consumption_components
from modules.auxiliary.auxiliary import make_project_time_var_df


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # Define various sets to be used in transmission operations module
    m.OPERATIONAL_PERIODS_BY_TRANSMISSION_LINE = \
        Set(m.TRANSMISSION_LINES,
            rule=lambda mod, tx: set(
                p for (l, p) in mod.TRANSMISSION_OPERATIONAL_PERIODS if
                l == tx)
            )

    def tx_op_tmps_init(mod):
        tx_tmps = set()
        for tx in mod.TRANSMISSION_LINES:
            for p in mod.OPERATIONAL_PERIODS_BY_TRANSMISSION_LINE[tx]:
                for tmp in mod.TIMEPOINTS_IN_PERIOD[p]:
                    tx_tmps.add((tx, tmp))
        return tx_tmps
    m.TRANSMISSION_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, rule=tx_op_tmps_init)

    m.Transmit_Power_MW = Var(m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
                              within=Reals)

    def min_transmit_rule(mod, l, tmp):
        """

        :param mod:
        :param l:
        :param tmp:
        :return:
        """
        return mod.Transmit_Power_MW[l, tmp] \
            >= mod.Transmission_Min_Capacity_MW[l, mod.period[tmp]]

    m.Min_Transmit_Constraint = \
        Constraint(m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
                   rule=min_transmit_rule)

    def max_transmit_rule(mod, l, tmp):
        """

        :param mod:
        :param l:
        :param tmp:
        :return:
        """
        return mod.Transmit_Power_MW[l, tmp] \
            <= mod.Transmission_Max_Capacity_MW[l, mod.period[tmp]]

    m.Max_Transmit_Constraint = \
        Constraint(m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
                   rule=max_transmit_rule)

    # Add to load balance
    def total_transmission_to_rule(mod, z, tmp):
        return sum(mod.Transmit_Power_MW[tx, tmp]
                   for tx in mod.TRANSMISSION_LINES
                   if mod.load_zone_to[tx] == z)
    m.Transmission_to_Zone_MW = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                           rule=total_transmission_to_rule)
    getattr(d, load_balance_production_components).append(
        "Transmission_to_Zone_MW")

    def total_transmission_from_rule(mod, z, tmp):
        return sum(mod.Transmit_Power_MW[tx, tmp]
                   for tx in mod.TRANSMISSION_LINES
                   if mod.load_zone_from[tx] == z)
    m.Transmission_from_Zone_MW = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                             rule=total_transmission_from_rule)
    getattr(d, load_balance_consumption_components).append(
        "Transmission_from_Zone_MW")


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export transmission operations
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    op_df = \
        make_project_time_var_df(
            m,
            "TRANSMISSION_OPERATIONAL_PERIODS",
            "Transmission_Max_Capacity_MW",
            ["transmission_line", "timepoint"],
            "transmission_max_capacity_mw"
        )

    op_df.to_csv(
        os.path.join(scenario_directory, horizon, stage, "results",
                     "transmission_operations.csv"),
        header=True, index=True)
