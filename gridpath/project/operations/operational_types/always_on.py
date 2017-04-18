#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of always-on generators. These are generators that area always 
committed but can ramp up and down between a minimum stable level above 0 and 
full output.
"""

import os.path
import pandas as pd
from pyomo.environ import Param, Set, Var, NonNegativeReals, \
    PercentFraction, Constraint, Expression

from gridpath.auxiliary.auxiliary import generator_subset_init


def add_module_specific_components(m, d):
    """

    :param m:
    :return:
    """    
    m.ALWAYS_ON_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=generator_subset_init(
            "operational_type", "always_on"
        )
    )
    m.always_on_min_stable_level_fraction = \
        Param(m.ALWAYS_ON_GENERATORS, within=PercentFraction)
    m.always_on_unit_size_mw = \
        Param(m.ALWAYS_ON_GENERATORS, within=NonNegativeReals)
    
    # Ramp rates can be optionally specified and will default to 1 if not
    m.always_on_ramp_up_rate = \
        Param(m.ALWAYS_ON_GENERATORS, within=PercentFraction,
              default=1)
    m.always_on_ramp_down_rate = \
        Param(m.ALWAYS_ON_GENERATORS, within=PercentFraction,
              default=1)

    # Operational timepoints
    m.ALWAYS_ON_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.ALWAYS_ON_GENERATORS))

    # Variables
    m.Provide_Power_AlwaysOn_MW = Var(
        m.ALWAYS_ON_GENERATOR_OPERATIONAL_TIMEPOINTS, within=NonNegativeReals
    )

    # Optional ramp constraints
    # Constrain ramps
    m.Always_On_Ramp_MW = Expression(
        m.ALWAYS_ON_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_rule
    )

    def ramp_up_rule(mod, g, tmp):
        """

        :param mod: 
        :param g: 
        :param tmp: 
        :return: 
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        elif mod.always_on_ramp_up_rate[g] == 1:
            return Constraint.Skip
        else:
            return mod.Always_On_Ramp_MW[g, tmp] \
                   <= \
                   mod.always_on_ramp_up_rate[g] \
                   * mod.Capacity_MW[g, mod.period[tmp]]

    m.Always_On_Ramp_Up_Constraint = \
        Constraint(
            m.ALWAYS_ON_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=ramp_up_rule
        )

    def ramp_down_rule(mod, g, tmp):
        """

        :param mod: 
        :param g: 
        :param tmp: 
        :return: 
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        elif mod.always_on_ramp_down_rate[g] == 1:
            return Constraint.Skip
        else:
            return mod.Always_On_Ramp_MW[g, tmp] \
                   >= \
                   - mod.always_on_ramp_down_rate[g] \
                   * mod.Capacity_MW[g, mod.period[tmp]]

    m.Always_On_Ramp_Down_Constraint = \
        Constraint(
            m.ALWAYS_ON_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=ramp_down_rule
        )


def power_provision_rule(mod, g, tmp):
    """
    
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_AlwaysOn_MW[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Committed all the time, so all capacity assumed online
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Capacity_MW[g, mod.period[tmp]]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision for must-run generators, if eligible, is their power output.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_AlwaysOn_MW[g, tmp]


# TODO: ignore curtailment for now, but might need to revisit if for example
#  RPS-eligible technologies are modeled as always-on (e.g. geothermal) -- 
# it may make more sense to model them as 'variable' with constant cap factor
def scheduled_curtailment_rule(mod, g, tmp):
    """
    
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_curtailment_rule(mod, g, tmp):
    """
    
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def fuel_burn_rule(mod, g, tmp, error_message):
    """
    
    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        return (mod.Capacity_MW[g, mod.period[tmp]] /
                mod.always_on_unit_size_mw[g]) \
            * mod.minimum_input_mmbtu_per_hr[g] \
            + (mod.Provide_Power_AlwaysOn_MW[g, tmp] -
                (mod.Capacity_MW[g, mod.period[tmp]]
                 * mod.always_on_min_stable_level_fraction[g])
               ) * mod.inc_heat_rate_mmbtu_per_mwh[g]
    else:
        raise ValueError(error_message)


def startup_shutdown_rule(mod, g, tmp):
    """
    Must-run generators are never started up or shut down
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! Always-on generators should not incur startup/shutdown "
        "costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup/shutdown costs to '.' (no value).")
    )


def ramp_rule(mod, g, tmp):
    """

    :param mod: 
    :param g: 
    :param tmp: 
    :return: 
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        pass
    else:
        return mod.Provide_Power_AlwaysOn_MW[g, tmp] - \
               mod.Provide_Power_AlwaysOn_MW[
                   g, mod.previous_timepoint[tmp]
               ]


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

    unit_size_mw = dict()
    min_stable_fraction = dict()
    # Ramp rate limits are optional, will default to 1 if not specified
    ramp_up_rate = dict()
    ramp_down_rate = dict()
    header = pd.read_csv(os.path.join(scenario_directory, "inputs",
                                      "projects.tab"),
                         sep="\t", header=None, nrows=1).values[0]

    optional_columns = ["ramp_up_when_on_rate",
                        "ramp_down_when_on_rate"]
    used_columns = [c for c in optional_columns if c in header]

    dynamic_components = \
        pd.read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t",
            usecols=["project", "operational_type", "unit_size_mw",
                     "min_stable_level_fraction"] + used_columns
            )

    # Get unit size and minimum stable level
    for row in zip(dynamic_components["project"],
                   dynamic_components["operational_type"],
                   dynamic_components["unit_size_mw"],
                   dynamic_components["min_stable_level_fraction"]):
        if row[1] == "always_on":
            unit_size_mw[row[0]] = float(row[2])
            min_stable_fraction[row[0]] = float(row[3])
        else:
            pass

    data_portal.data()["always_on_unit_size_mw"] = unit_size_mw
    data_portal.data()["always_on_min_stable_level_fraction"] = \
        min_stable_fraction
    
    # Optional ramp rates
    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components[
                           "ramp_up_when_on_rate"]
                       ):
            if row[1] == "always_on" and row[2] != ".":
                ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "always_on_ramp_up_rate"] = \
            ramp_up_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components[
                           "ramp_down_when_on_rate"]
                       ):
            if row[1] == "always_on" and row[2] != ".":
                ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "always_on_ramp_down_rate"] = \
            ramp_down_rate
