#!/usr/bin/env python

"""
Operations of generic storage
"""

import os.path
from pandas import read_csv
from pyomo.environ import Var, Set, Constraint, Param, NonNegativeReals, \
    PercentFraction

from modules.auxiliary.auxiliary import generator_subset_init, \
    make_project_time_var_df


def add_module_specific_components(m, d):
    """
    Add a capacity commit variable to represent the amount of capacity that is
    on.
    :param m:
    :return:
    """

    m.STORAGE_GENERIC_PROJECTS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type",
                              "storage_generic")
    )

    m.STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.STORAGE_GENERIC_PROJECTS))

    m.storage_generic_charging_efficiency = \
        Param(m.STORAGE_GENERIC_PROJECTS, within=PercentFraction)
    m.storage_generic_discharging_efficiency = \
        Param(m.STORAGE_GENERIC_PROJECTS, within=PercentFraction)

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
            <= mod.Energy_Capacity_MWh[s, mod.period[tmp]]
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


def curtailment_rule(mod, g, tmp):
    """
    Curtailment not allowed
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


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


def load_module_specific_data(mod, data_portal, scenario_directory,
                              horizon, stage):
    """

    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    def determine_efficiencies():
        """

        :param mod:
        :return:
        """
        storage_generic_charging_efficiency = dict()
        storage_generic_discharging_efficiency = dict()

        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project", "operational_type",
                                   "charging_efficiency",
                                   "discharging_efficiency"]
            )
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["charging_efficiency"],
                       dynamic_components["discharging_efficiency"]):
            if row[1] == "storage_generic":
                storage_generic_charging_efficiency[row[0]] \
                    = float(row[2])
                storage_generic_discharging_efficiency[row[0]] \
                    = float(row[3])
            else:
                pass

        return storage_generic_charging_efficiency, \
               storage_generic_discharging_efficiency

    data_portal.data()["storage_generic_charging_efficiency"] = \
        determine_efficiencies()[0]
    data_portal.data()["storage_generic_discharging_efficiency"] = \
        determine_efficiencies()[1]


def export_module_specific_results(mod, d):
    """

    :param mod:
    :param d:
    :return:
    """
    generic_storage_df = \
        make_project_time_var_df(
            mod,
            "STORAGE_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS",
            "Starting_Energy_in_Generic_Storage_MWh",
            ["project", "timepoint"],
            "starting_energy_in_generic_storage_mwh")

    d.module_specific_df.append(generic_storage_df)
