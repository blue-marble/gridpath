#!/usr/bin/env python

import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, Expression, NonNegativeReals

from modules.auxiliary.auxiliary import make_project_time_var_df
from modules.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets
from modules.project.capacity.capacity_types.common_methods import \
    operational_periods_by_project_vintage, project_operational_periods, \
    project_vintages_operational_in_period


def add_module_specific_components(m, d):
    """

    """
    m.NEW_BUILD_GENERATOR_VINTAGES = Set(dimen=2)
    m.lifetime_yrs_by_new_build_vintage = \
        Param(m.NEW_BUILD_GENERATOR_VINTAGES, within=NonNegativeReals)
    m.annualized_real_cost_per_mw_yr = \
        Param(m.NEW_BUILD_GENERATOR_VINTAGES, within=NonNegativeReals)

    m.Build_MW = Var(m.NEW_BUILD_GENERATOR_VINTAGES, within=NonNegativeReals)

    m.OPERATIONAL_PERIODS_BY_NEW_BUILD_GENERATOR_VINTAGE = \
        Set(m.NEW_BUILD_GENERATOR_VINTAGES,
            initialize=operational_periods_by_generator_vintage)

    m.NEW_BUILD_GENERATOR_OPERATIONAL_PERIODS = \
        Set(dimen=2, initialize=new_build_option_operational_periods)

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "NEW_BUILD_GENERATOR_OPERATIONAL_PERIODS",
    )

    m.NEW_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD = \
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
                   in mod.NEW_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                   if gen == g)

    m.New_Build_Option_Capacity_MW = \
        Expression(m.NEW_BUILD_GENERATOR_OPERATIONAL_PERIODS,
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
               in mod.NEW_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD[p]
               if gen == g)


def load_module_specific_data(m,
                              data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # TODO: throw an error when a generator of the 'new_build_option' capacity
    # type is not found in new_build_option_vintage_costs.tab
    data_portal.load(filename=
                     os.path.join(scenario_directory,
                                  "inputs",
                                  "new_build_generator_vintage_costs.tab"),
                     index=
                     m.NEW_BUILD_GENERATOR_VINTAGES,
                     select=("new_build_generator", "vintage",
                             "lifetime_yrs", "annualized_real_cost_per_mw_yr"),
                     param=(m.lifetime_yrs_by_new_build_vintage,
                            m.annualized_real_cost_per_mw_yr)
                     )


def export_module_specific_results(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    build_option_df = \
        make_project_time_var_df(
            m,
            "NEW_BUILD_GENERATOR_VINTAGES",
            "Build_MW",
            ["project", "period"],
            "new_build_option_mw"
        )

    d.module_specific_df.append(build_option_df)


def operational_periods_by_generator_vintage(mod, prj, v):
    return operational_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"), vintage=v,
        lifetime=mod.lifetime_yrs_by_new_build_vintage[prj, v]
    )


def new_build_option_operational_periods(mod):
    return project_operational_periods(
        project_vintages_set=mod.NEW_BUILD_GENERATOR_VINTAGES,
        operational_periods_by_project_vintage_set=
        mod.OPERATIONAL_PERIODS_BY_NEW_BUILD_GENERATOR_VINTAGE
    )


def new_build_option_vintages_operational_in_period(mod, p):
    return project_vintages_operational_in_period(
        project_vintage_set=mod.NEW_BUILD_GENERATOR_VINTAGES,
        operational_periods_by_project_vintage_set=
        mod.OPERATIONAL_PERIODS_BY_NEW_BUILD_GENERATOR_VINTAGE,
        period=p
    )


def summarize_results(capacity_results_agg_df):
    """
    Summarize new build generation capacity results.
    :param capacity_results_agg_df:
    :return:
    """
    print("\n--> New Generation Capacity <--")
    # Set the formatting of float to be readable
    pd.options.display.float_format = "{:,.0f}".format

    # Get all technologies with the new build capacity
    new_build_option_df = pd.DataFrame(
        capacity_results_agg_df[
            capacity_results_agg_df["new_build_option_mw"] > 0
        ]["new_build_option_mw"]
    )

    new_build_option_df.columns = ["New Capacity (MW)"]
    if new_build_option_df.empty:
        print("No new storage was built.")
    else:
        print new_build_option_df
