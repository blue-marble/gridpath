#!/usr/bin/env python

import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, Expression, NonNegativeReals, \
    Constraint

from modules.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets, \
    storage_only_capacity_type_operational_period_sets
from modules.auxiliary.auxiliary import make_project_time_var_df
from modules.project.capacity.capacity_types.common_methods import \
    operational_periods_by_project_vintage, project_operational_periods, \
    project_vintages_operational_in_period


def add_module_specific_components(m, d):
    """

    """
    m.NEW_BUILD_STORAGE_PROJECTS = Set()
    m.minimum_duration_hours = \
        Param(m.NEW_BUILD_STORAGE_PROJECTS, within=NonNegativeReals)
    m.NEW_BUILD_STORAGE_VINTAGES = \
        Set(dimen=2, within=m.NEW_BUILD_STORAGE_PROJECTS*m.PERIODS)
    m.lifetime_yrs_by_new_build_storage_vintage = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES, within=NonNegativeReals)
    m.new_build_storage_annualized_real_cost_per_mw_yr = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES, within=NonNegativeReals)
    m.new_build_storage_annualized_real_cost_per_mwh_yr = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES, within=NonNegativeReals)

    m.Build_Storage_Power_MW = \
        Var(m.NEW_BUILD_STORAGE_VINTAGES,
            within=NonNegativeReals)
    m.Build_Storage_Energy_MWh = \
        Var(m.NEW_BUILD_STORAGE_VINTAGES,
            within=NonNegativeReals)

    m.OPERATIONAL_PERIODS_BY_NEW_BUILD_STORAGE_VINTAGE = \
        Set(m.NEW_BUILD_STORAGE_VINTAGES,
            initialize=operational_periods_by_storage_vintage)

    m.NEW_BUILD_STORAGE_OPERATIONAL_PERIODS = \
        Set(dimen=2, initialize=new_build_storage_operational_periods)

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "NEW_BUILD_STORAGE_OPERATIONAL_PERIODS",
    )
    # Add to list of sets we'll join to get the final
    # STORAGE_OPERATIONAL_PERIODS set
    getattr(d, storage_only_capacity_type_operational_period_sets).append(
        "NEW_BUILD_STORAGE_OPERATIONAL_PERIODS",
    )

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

    def minimum_duration_constraint_rule(mod, g, p):
        """
        Storage duration must be above a pre-specified requirement
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return mod.New_Build_Storage_Energy_Capacity_MWh[g, p] >= \
            mod.New_Build_Storage_Power_Capacity_MW[g, p] * \
            mod.minimum_duration_hours[g]
    m.New_Build_Storage_Minimum_Duration_Constraint = \
        Constraint(m.NEW_BUILD_STORAGE_OPERATIONAL_PERIODS,
                   rule=minimum_duration_constraint_rule)


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
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    def determine_minimum_duration():
        """
        :return:
        """
        new_build_storage_projects = list()
        storage_min_duration = dict()

        dynamic_components = \
            pd.read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project", "capacity_type",
                                   "minimum_duration_hours"]
            )
        for row in zip(dynamic_components["project"],
                       dynamic_components["capacity_type"],
                       dynamic_components["minimum_duration_hours"]):
            if row[1] == "new_build_storage":
                new_build_storage_projects.append(row[0])
                storage_min_duration[row[0]] \
                    = float(row[2])
            else:
                pass

        return new_build_storage_projects, storage_min_duration

    data_portal.data()["NEW_BUILD_STORAGE_PROJECTS"] = {
        None: determine_minimum_duration()[0]
    }
    data_portal.data()["minimum_duration_hours"] = \
        determine_minimum_duration()[1]

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


def export_module_specific_results(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    build_storage_capacity_df = \
        make_project_time_var_df(
            m,
            "NEW_BUILD_STORAGE_VINTAGES",
            "Build_Storage_Power_MW",
            ["project", "period"],
            "new_build_storage_mw"
        )

    build_storage_energy_df = \
        make_project_time_var_df(
            m,
            "NEW_BUILD_STORAGE_VINTAGES",
            "Build_Storage_Energy_MWh",
            ["project", "period"],
            "new_build_storage_mwh"
        )

    d.module_specific_df.append(build_storage_capacity_df)
    d.module_specific_df.append(build_storage_energy_df)


def operational_periods_by_storage_vintage(mod, prj, v):
    return operational_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"), vintage=v,
        lifetime=mod.lifetime_yrs_by_new_build_storage_vintage[prj, v])


def new_build_storage_operational_periods(mod):
    return project_operational_periods(
        project_vintages_set=mod.NEW_BUILD_STORAGE_VINTAGES,
        operational_periods_by_project_vintage_set=
        mod.OPERATIONAL_PERIODS_BY_NEW_BUILD_STORAGE_VINTAGE
    )


def new_build_storage_vintages_operational_in_period(mod, p):
    return project_vintages_operational_in_period(
        project_vintage_set=mod.NEW_BUILD_STORAGE_VINTAGES,
        operational_periods_by_project_vintage_set=
        mod.OPERATIONAL_PERIODS_BY_NEW_BUILD_STORAGE_VINTAGE,
        period=p
    )


def summarize_module_specific_results(capacity_results_agg_df,
                                      summary_results_file):
    """
    Summarize new build storage results.
    :param capacity_results_agg_df:
    :param summary_results_file:
    :return:
    """
    # Set the formatting of float to be readable
    pd.options.display.float_format = "{:,.0f}".format
    # Get all technologies with new build storage power OR energy capacity
    new_build_storage_df = pd.DataFrame(
        capacity_results_agg_df[
            (capacity_results_agg_df["new_build_storage_mw"] > 0) |
            (capacity_results_agg_df["new_build_storage_mwh"] > 0)
        ][["new_build_storage_mw", "new_build_storage_mwh"]]
    )
    new_build_storage_df.columns =["New Storage Power Capacity (MW)",
                                   "New Storage Energy Capacity (MWh)"]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> New Storage Capacity <--\n")
        if new_build_storage_df.empty:
            outfile.write("No new storage was built.\n")
        else:
            new_build_storage_df.to_string(outfile)
            outfile.write("\n")
