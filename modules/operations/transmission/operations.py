#!/usr/bin/env python

import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, Constraint, Expression, Reals, value


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
    d.load_balance_production_components.append("Transmission_to_Zone_MW")

    def total_transmission_from_rule(mod, z, tmp):
        return sum(mod.Transmit_Power_MW[tx, tmp]
                   for tx in mod.TRANSMISSION_LINES
                   if mod.load_zone_from[tx] == z)
    m.Transmission_from_Zone_MW = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                             rule=total_transmission_from_rule)
    d.load_balance_consumption_components.append("Transmission_from_Zone_MW")


def export_results(scenario_directory, horizon, stage, m):
    """
    Export transmission operations
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :return:
    """
    op_df = \
        make_tx_time_var_df(
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


# TODO: consolidate with similar function in capacity and operations modules
def make_tx_time_var_df(m, tx_time_set, x, df_index_names, header):
    """

    :param m:
    :param tx_time_set:
    :param df_index_names:
    :param x:
    :param header:
    :return:
    """
    # Created nested dictionary for each generator-timepoint
    dict_for_tx_df = {}
    for (g, p) in getattr(m, tx_time_set):
        if g not in dict_for_tx_df.keys():
            dict_for_tx_df[g] = {}
            try:
                dict_for_tx_df[g][p] = value(getattr(m, x)[g, p])
            except ValueError:
                dict_for_tx_df[g][p] = None
        else:
            try:
                dict_for_tx_df[g][p] = value(getattr(m, x)[g, p])
            except ValueError:
                dict_for_tx_df[g][p] = None

    # For each generator, create a dataframe with its x values
    # Create two lists, the generators and dictionaries with the timepoints as
    # keys and the values -- it is critical that the order of generators and
    # of the dictionaries with their values match
    generators = []
    periods = []
    for g, tmp in dict_for_tx_df.iteritems():
        generators.append(g)
        periods.append(pd.DataFrame.from_dict(tmp, orient='index'))

    # Concatenate all the individual generator dataframes into a final one
    final_df = pd.DataFrame(pd.concat(periods, keys=generators))
    final_df.index.names = df_index_names
    final_df.columns = [header]

    return final_df
