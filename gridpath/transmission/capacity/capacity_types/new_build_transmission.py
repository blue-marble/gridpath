#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Set, Param, Var, Expression, NonNegativeReals, value


# TODO: can we have different capacities depending on the direction
def add_module_specific_components(m, d):
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
        return sum(
            mod.Build_Transmission_MW[g, v] for (gen, v)
            in mod.NEW_BUILD_TRANSMISSION_VINTAGES_OPERATIONAL_IN_PERIOD[p]
            if gen == g
        )

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
    #   type is not found in new_build_transmission_vintage_costs.tab
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


def export_module_specific_results(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :return:
    """

    # Export transmission capacity
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "transmission_new_capacity.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["tx_line", "period", "load_zone_from", "load_zone_to",
                         "new_build_transmission_capacity_mw"])
        for (tx_line, p) in m.TRANSMISSION_OPERATIONAL_PERIODS:
            writer.writerow([
                tx_line,
                p,
                m.load_zone_from[tx_line],
                m.load_zone_to[tx_line],
                value(m.Build_Transmission_MW[tx_line, p])
            ])
