#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, Var, Expression, NonNegativeReals


def add_module_specific_components(m):
    """

    """
    m.NEW_BUILD_STORAGE_VINTAGES = Set(dimen=2)
    m.lifetime_yrs_by_new_build_storage_vintage = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES, within=NonNegativeReals)
    m.new_build_storage_annualized_real_cost_per_mw_yr = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES, within=NonNegativeReals)
    m.new_build_storage_annualized_real_cost_per_mwh_yr = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES, within=NonNegativeReals)

    m.Build_Storage_Power_MW = Var(m.NEW_BUILD_STORAGE_VINTAGES,
                             within=NonNegativeReals)
    m.Build_Storage_Energy_MWh = Var(m.NEW_BUILD_STORAGE_VINTAGES,
                              within=NonNegativeReals)

    # TODO: if vintage is 2020 and lifetime is 30, is the project available in
    # 2050 or not -- maybe have options for how this should be treated?
    def operational_periods_by_new_build_storage_vintage(mod, g, v):
        operational_periods = list()
        for p in mod.PERIODS:
            if v <= p < v + mod.lifetime_yrs_by_new_build_storage_vintage[g, v]:
                operational_periods.append(p)
            else:
                pass
        return operational_periods

    m.OPERATIONAL_PERIODS_BY_NEW_BUILD_STORAGE_VINTAGE = \
        Set(m.NEW_BUILD_STORAGE_VINTAGES,
            initialize=operational_periods_by_new_build_storage_vintage)

    def new_build_storage_operational_periods(mod):
        return set((g, p)
                   for (g, v) in mod.NEW_BUILD_STORAGE_VINTAGES
                   for p
                   in mod.OPERATIONAL_PERIODS_BY_NEW_BUILD_STORAGE_VINTAGE[g, v]
                   )

    m.NEW_BUILD_STORAGE_OPERATIONAL_PERIODS = \
        Set(dimen=2, initialize=new_build_storage_operational_periods)

    m.capacity_type_operational_period_sets.append(
        "NEW_BUILD_STORAGE_OPERATIONAL_PERIODS",
    )
    m.storage_only_capacity_type_operational_period_sets.append(
        "NEW_BUILD_STORAGE_OPERATIONAL_PERIODS",
    )

    def new_build_storage_vintages_operational_in_period(mod, p):
        build_vintages_by_period = list()
        for (g, v) in mod.NEW_BUILD_STORAGE_VINTAGES:
            if p in mod.OPERATIONAL_PERIODS_BY_NEW_BUILD_STORAGE_VINTAGE[g, v]:
                build_vintages_by_period.append((g, v))
            else:
                pass
        return build_vintages_by_period

    m.NEW_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD = \
        Set(m.PERIODS, dimen=2,
            initialize=new_build_storage_vintages_operational_in_period)

    def new_build_storage_power_capacity_rule(mod, g, p):
        """
        Sum all builds of vintages operational in the current period
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return sum(mod.Build_Storage_Power_MW[g, v] for (gen, v)
                   in mod.NEW_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                   if gen == g)

    m.New_Build_Storage_Power_Capacity_MW = \
        Expression(m.NEW_BUILD_STORAGE_OPERATIONAL_PERIODS,
                   rule=new_build_storage_power_capacity_rule)

    def new_build_storage_energy_capacity_rule(mod, g, p):
        """
        Sum all builds of vintages operational in the current period
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return sum(mod.Build_Storage_Energy_MWh[g, v] for (gen, v)
                   in mod.NEW_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                   if gen == g)

    m.New_Build_Storage_Energy_Capacity_MWh = \
        Expression(m.NEW_BUILD_STORAGE_OPERATIONAL_PERIODS,
                   rule=new_build_storage_energy_capacity_rule)


def capacity_rule(mod, g, p):
    """

    :param mod:
    :param g:
    :param p:
    :return:
    """
    return mod.New_Build_Storage_Power_Capacity_MW[g, p]


def energy_capacity_rule(mod, g, p):
    """

    :param mod:
    :param g:
    :param p:
    :return:
    """
    return mod.New_Build_Storage_Energy_Capacity_MWh[g, p]


def capacity_cost_rule(mod, g, p):
    """
    Capacity cost for new builds in each period (sum over all vintages
    operational in current period)
    :param mod:
    :return:
    """
    return sum(mod.Build_Storage_Power_MW[g, v]
               * mod.new_build_storage_annualized_real_cost_per_mw_yr[g, v]
               + mod.Build_Storage_Energy_MWh[g, v]
               * mod.new_build_storage_annualized_real_cost_per_mwh_yr[g, v]
               for (gen, v)
               in mod.NEW_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD[p]
               if gen == g)


def load_module_specific_data(m,
                              data_portal, scenario_directory, horizon, stage):

    # TODO: throw an error when a generator of the 'new_build_storage' capacity
    # type is not found in new_build_storage_vintage_costs.tab
    data_portal.load(filename=
                     os.path.join(scenario_directory,
                                  "inputs",
                                  "new_build_storage_vintage_costs.tab"),
                     index=
                     m.NEW_BUILD_STORAGE_VINTAGES,
                     select=("new_build_storage", "vintage",
                             "lifetime_yrs", "annualized_real_cost_per_mw_yr",
                             "annualized_real_cost_per_mwh_yr"),
                     param=(m.lifetime_yrs_by_new_build_storage_vintage,
                            m.new_build_storage_annualized_real_cost_per_mw_yr,
                            m.new_build_storage_annualized_real_cost_per_mwh_yr
                            )
                     )


def export_module_specific_results(m):
    for (g, v) in getattr(m, "NEW_BUILD_STORAGE_VINTAGES"):
        print (g, v), m.Build_Storage_Power_MW[g,v].value
