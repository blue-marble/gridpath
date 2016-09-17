#!/usr/bin/env python

import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, Expression, NonNegativeReals, value


def add_module_specific_components(m):
    """

    """
    m.NEW_BUILD_TRANSMISSION_VINTAGES = Set(dimen=2)
    m.tx_lifetime_yrs_by_new_build_vintage = \
        Param(m.NEW_BUILD_TRANSMISSION_VINTAGES, within=NonNegativeReals)
    m.tx_annualized_real_cost_per_mw_yr = \
        Param(m.NEW_BUILD_TRANSMISSION_VINTAGES, within=NonNegativeReals)

    m.Build_Transmission_MW = \
        Var(m.NEW_BUILD_TRANSMISSION_VINTAGES, within=NonNegativeReals)

    def operational_periods_by_new_build_transmission_vintage(mod, g, v):
        operational_periods = list()
        for p in mod.PERIODS:
            if v <= p < v + mod.tx_lifetime_yrs_by_new_build_vintage[g, v]:
                operational_periods.append(p)
            else:
                pass
        return operational_periods

    m.OPERATIONAL_PERIODS_BY_NEW_BUILD_TRANSMISSION_VINTAGE = \
        Set(m.NEW_BUILD_TRANSMISSION_VINTAGES,
            initialize=operational_periods_by_new_build_transmission_vintage)

    def new_build_transmission_operational_periods(mod):
        return \
            set((g, p) for (g, v) in mod.NEW_BUILD_TRANSMISSION_VINTAGES
                for p in mod.
                OPERATIONAL_PERIODS_BY_NEW_BUILD_TRANSMISSION_VINTAGE[g, v]
                )

    m.NEW_BUILD_TRANSMISSION_OPERATIONAL_PERIODS = \
        Set(dimen=2, initialize=new_build_transmission_operational_periods)

    m.tx_capacity_type_operational_period_sets.append(
        "NEW_BUILD_TRANSMISSION_OPERATIONAL_PERIODS",
    )

    def new_build_transmission_vintages_operational_in_period(mod, p):
        build_vintages_by_period = list()
        for (g, v) in mod.NEW_BUILD_TRANSMISSION_VINTAGES:
            if p in mod.\
                    OPERATIONAL_PERIODS_BY_NEW_BUILD_TRANSMISSION_VINTAGE[g, v]:
                build_vintages_by_period.append((g, v))
            else:
                pass
        return build_vintages_by_period

    m.NEW_BUILD_TRANSMISSION_VINTAGES_OPERATIONAL_IN_PERIOD = \
        Set(m.PERIODS, dimen=2,
            initialize=new_build_transmission_vintages_operational_in_period)

    def new_build_tx_capacity_rule(mod, g, p):
        """
        Sum all builds of vintages operational in the current period
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return sum(mod.Build_Transmission_MW[g, v] for (gen, v)
                   in mod.NEW_BUILD_TRANSMISSION_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                   if gen == g)

    m.New_Build_Transmission_Capacity_MW = \
        Expression(m.NEW_BUILD_TRANSMISSION_OPERATIONAL_PERIODS,
                   rule=new_build_tx_capacity_rule)


def min_transmission_capacity_rule(mod, g, p):
    """

    :param mod:
    :param g:
    :param p:
    :return:
    """
    return mod.New_Build_Transmission_Capacity_MW[g, p]


def max_transmission_capacity_rule(mod, g, p):
    """

    :param mod:
    :param g:
    :param p:
    :return:
    """
    return mod.New_Build_Transmission_Capacity_MW[g, p]


def tx_capacity_cost_rule(mod, g, p):
    """
    Capacity cost for new builds in each period (sum over all vintages
    operational in current period)
    :param mod:
    :return:
    """
    return sum(mod.Build_Transmission_MW[g, v]
               * mod.tx_annualized_real_cost_per_mw_yr[g, v]
               for (gen, v)
               in mod.NEW_BUILD_TRANSMISSION_VINTAGES_OPERATIONAL_IN_PERIOD[p]
               if gen == g)


def load_module_specific_data(m,
                              data_portal, scenario_directory, horizon, stage):

    # TODO: throw an error when a line of the 'new_build_transmission' capacity
    # type is not found in new_build_transmission_vintage_costs.tab
    data_portal.load(filename=
                     os.path.join(scenario_directory,
                                  "inputs",
                                  "new_build_transmission_vintage_costs.tab"),
                     index=
                     m.NEW_BUILD_TRANSMISSION_VINTAGES,
                     select=("transmission_line", "vintage",
                             "tx_lifetime_yrs",
                             "tx_annualized_real_cost_per_mw_yr"),
                     param=(m.tx_lifetime_yrs_by_new_build_vintage,
                            m.tx_annualized_real_cost_per_mw_yr)
                     )


def export_module_specific_results(m):
    """

    :param m:
    :return:
    """

    new_tx_cap_df = \
        make_tx_time_var_df(
            m,
            "NEW_BUILD_TRANSMISSION_VINTAGES",
            "Build_Transmission_MW",
            ["transmission_line", "period"],
            "transmission_new_capacity_mw"
        )

    m.tx_module_specific_df.append(new_tx_cap_df)


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
