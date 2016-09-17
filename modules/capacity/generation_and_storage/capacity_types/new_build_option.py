#!/usr/bin/env python

import os.path

from pyomo.environ import Set, Param, Var, Expression, NonNegativeReals

from modules.capacity.generation_and_storage.auxiliary import make_gen_period_var_df


def add_module_specific_components(m):
    """

    """
    m.NEW_BUILD_OPTION_VINTAGES = Set(dimen=2)
    m.lifetime_yrs_by_new_build_vintage = \
        Param(m.NEW_BUILD_OPTION_VINTAGES, within=NonNegativeReals)
    m.annualized_real_cost_per_mw_yr = \
        Param(m.NEW_BUILD_OPTION_VINTAGES, within=NonNegativeReals)

    m.Build_MW = Var(m.NEW_BUILD_OPTION_VINTAGES, within=NonNegativeReals)

    # TODO: if vintage is 2020 and lifetime is 30, is the project available in
    # 2050 or not -- maybe have options for how this should be treated?
    def operational_periods_by_new_build_option_vintage(mod, g, v):
        operational_periods = list()
        for p in mod.PERIODS:
            if v <= p < v + mod.lifetime_yrs_by_new_build_vintage[g, v]:
                operational_periods.append(p)
            else:
                pass
        return operational_periods

    m.OPERATIONAL_PERIODS_BY_NEW_BUILD_OPTION_VINTAGE = \
        Set(m.NEW_BUILD_OPTION_VINTAGES,
            initialize=operational_periods_by_new_build_option_vintage)

    def new_build_option_operational_periods(mod):
        return set((g, p)
                   for (g, v) in mod.NEW_BUILD_OPTION_VINTAGES
                   for p
                   in mod.OPERATIONAL_PERIODS_BY_NEW_BUILD_OPTION_VINTAGE[g, v]
                   )

    m.NEW_BUILD_OPTION_OPERATIONAL_PERIODS = \
        Set(dimen=2, initialize=new_build_option_operational_periods)

    m.capacity_type_operational_period_sets.append(
        "NEW_BUILD_OPTION_OPERATIONAL_PERIODS",
    )

    def new_build_option_vintages_operational_in_period(mod, p):
        build_vintages_by_period = list()
        for (g, v) in mod.NEW_BUILD_OPTION_VINTAGES:
            if p in mod.OPERATIONAL_PERIODS_BY_NEW_BUILD_OPTION_VINTAGE[g, v]:
                build_vintages_by_period.append((g, v))
            else:
                pass
        return build_vintages_by_period

    m.NEW_BUILD_OPTION_VINTAGES_OPERATIONAL_IN_PERIOD = \
        Set(m.PERIODS, dimen=2,
            initialize=new_build_option_vintages_operational_in_period)

    def new_build_capacity_rule(mod, g, p):
        """
        Sum all builds of vintages operational in the current period
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return sum(mod.Build_MW[g, v] for (gen, v)
                   in mod.NEW_BUILD_OPTION_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                   if gen == g)

    m.New_Build_Option_Capacity_MW = \
        Expression(m.NEW_BUILD_OPTION_OPERATIONAL_PERIODS,
                   rule=new_build_capacity_rule)


def capacity_rule(mod, g, p):
    """

    :param mod:
    :param g:
    :param p:
    :return:
    """
    return mod.New_Build_Option_Capacity_MW[g, p]


def capacity_cost_rule(mod, g, p):
    """
    Capacity cost for new builds in each period (sum over all vintages
    operational in current period)
    :param mod:
    :return:
    """
    return sum(mod.Build_MW[g, v]
               * mod.annualized_real_cost_per_mw_yr[g, v]
               for (gen, v)
               in mod.NEW_BUILD_OPTION_VINTAGES_OPERATIONAL_IN_PERIOD[p]
               if gen == g)


def load_module_specific_data(m,
                              data_portal, scenario_directory, horizon, stage):

    # TODO: throw an error when a generator of the 'new_build_option' capacity
    # type is not found in new_build_option_vintage_costs.tab
    data_portal.load(filename=
                     os.path.join(scenario_directory,
                                  "inputs",
                                  "new_build_option_vintage_costs.tab"),
                     index=
                     m.NEW_BUILD_OPTION_VINTAGES,
                     select=("new_build_generator", "vintage",
                             "lifetime_yrs", "annualized_real_cost_per_mw_yr"),
                     param=(m.lifetime_yrs_by_new_build_vintage,
                            m.annualized_real_cost_per_mw_yr)
                     )


def export_module_specific_results(m):
    build_option_df = \
        make_gen_period_var_df(
            m,
            "NEW_BUILD_OPTION_VINTAGES",
            "Build_MW",
            "new_build_option_mw")

    m.module_specific_df.append(build_option_df)