#!/usr/bin/env python

"""
Operations of generic storage
"""

import os.path

from pandas import read_csv
from pyomo.environ import Var, Set, Constraint, Param, BuildAction, \
    NonNegativeReals, PercentFraction

from modules.operations.generation.auxiliary import generator_subset_init, \
    make_gen_tmp_var_df


def add_module_specific_components(m, scenario_directory):
    """
    Add a capacity commit variable to represent the amount of capacity that is
    on.
    :param m:
    :param scenario_directory:
    :return:
    """

    m.STORAGE_GENERIC_PROJECTS = Set(
        within=m.GENERATORS,
        initialize=
        generator_subset_init("operational_type",
                              "storage_generic")
    )

    m.STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.STORAGE_GENERIC_PROJECTS))

    m.storage_generic_charging_efficiency = \
        Param(m.STORAGE_GENERIC_PROJECTS,
              within=PercentFraction, mutable=True, initialize={})
    m.storage_generic_discharging_efficiency = \
        Param(m.STORAGE_GENERIC_PROJECTS,
              within=PercentFraction, mutable=True, initialize={})

    def determine_efficiencies(mod):
        """

        :param mod:
        :return:
        """
        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "generators.tab"),
                sep="\t", usecols=["GENERATORS", "operational_type",
                                   "charging_efficiency",
                                   "discharging_efficiency"]
            )
        for row in zip(dynamic_components["GENERATORS"],
                       dynamic_components["operational_type"],
                       dynamic_components["charging_efficiency"],
                       dynamic_components["discharging_efficiency"]):
            if row[1] == "storage_generic":
                mod.storage_generic_charging_efficiency[row[0]] \
                    = float(row[2])
                mod.storage_generic_discharging_efficiency[row[0]] \
                    = float(row[3])
            else:
                pass

    m.EfficienciesBuild = BuildAction(rule=determine_efficiencies)

    m.Generic_Storage_Discharge_MW = \
        Var(m.STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)
    m.Generic_Storage_Charge_MW = \
        Var(m.STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals
            )
    m.Starting_Energy_in_Generic_Storage_MWh = \
        Var(m.STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals
            )

    def energy_tracking_rule(mod, s, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        else:
            return \
                mod.Starting_Energy_in_Generic_Storage_MWh[s, tmp] \
                == mod.Starting_Energy_in_Generic_Storage_MWh[
                    s, mod.previous_timepoint[tmp]] \
                + mod.Generic_Storage_Charge_MW[
                      s, mod.previous_timepoint[tmp]] \
                * mod.number_of_hours_in_timepoint[tmp] \
                * mod.storage_generic_charging_efficiency[s] \
                - mod.Generic_Storage_Discharge_MW[
                      s, mod.previous_timepoint[tmp]] \
                * mod.number_of_hours_in_timepoint[tmp] \
                / mod.storage_generic_discharging_efficiency[s]

    m.Storage_Generic_Energy_Tracking_Constraint = \
        Constraint(m.STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS,
                   rule=energy_tracking_rule)

    def max_energy_in_storage_rule(mod, s, tmp):
        """

        :param mod:
        :param s:
        :param tmp:
        :return:
        """
        return mod.Starting_Energy_in_Generic_Storage_MWh[s, tmp] \
            <= mod.storage_specified_energy_capacity_mwh[s, mod.period[tmp]]
    m.Max_Energy_in_Generic_Storage_Constraint = \
        Constraint(m.STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS,
                   rule=max_energy_in_storage_rule)


def power_provision_rule(mod, s, tmp):
    """
    Power provision from storage
    :param mod:
    :param s:
    :param tmp:
    :return:
    """
    return mod.Generic_Storage_Discharge_MW[s, tmp] \
        - mod.Generic_Storage_Charge_MW[s, tmp]


def max_power_rule(mod, s, tmp):
    """

    :param mod:
    :param s:
    :param tmp:
    :return:
    """
    return mod.Generic_Storage_Discharge_MW[s, tmp] + \
        mod.Headroom_Provision_MW[s, tmp] \
        <= mod.Generic_Storage_Charge_MW[s, tmp] \
        + mod.Capacity_MW[s, mod.period[tmp]]


def min_power_rule(mod, s, tmp):
    """

    :param mod:
    :param s:
    :param tmp:
    :return:
    """
    return mod.Generic_Storage_Charge_MW[s, tmp] + \
        mod.Footroom_Provision_MW[s, tmp] \
        <= mod.Generic_Storage_Discharge_MW[s, tmp] \
        + mod.Capacity_MW[s, mod.period[tmp]]


def fuel_cost_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def startup_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def shutdown_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def export_module_specific_results(mod):
    """

    :param mod:
    :return:
    """
    generic_storage_df = \
        make_gen_tmp_var_df(
            mod,
            "STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS",
            "Starting_Energy_in_Generic_Storage_MWh",
            "starting_energy_in_generic_storage_mwh")

    mod.module_specific_df.append(generic_storage_df)
