#!/usr/bin/env python

"""
Operations of dispatchable generators with 'capacity commitment,' i.e.
commit some level of capacity below the total capacity. This approach can
be good for modeling 'fleets' of generators, e.g. a total 2000 MW of 500-MW
units, so if 2000 MW are committed 4 generators (x 500 MW) are committed.
"""

import os.path

from pandas import read_csv
from pyomo.environ import Var, Constraint, Param, BuildAction, NonNegativeReals

from modules.operations.generation.auxiliary import make_gen_tmp_var_df


def add_module_specific_components(m, scenario_directory):
    """
    Add a continuous commit variable to represent the fraction of fleet
    capacity that is on.
    :param m:
    :return:
    """

    m.Commit_Capacity_MW = Var(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
                               m.TIMEPOINTS, within=NonNegativeReals
                               )

    def commit_capacity_constraint_rule(mod, g, tmp):
        """
        Can't commit more capacity than available in each timepoint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Commit_Capacity_MW[g, tmp] \
            <= mod.Capacity_MW[g, mod.period[tmp]]
    m.Commit_Capacity_Constraint = \
        Constraint(
            m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=commit_capacity_constraint_rule)

    def determine_unit_size(mod):
        """
        If numeric values greater than 0 for startup costs are specified
        for some generators, add those generators to the
        STARTUP_COST_GENERATORS subset and initialize the respective startup
        cost param value
        :param mod:
        :return:
        """
        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "generators.tab"),
                sep="\t", usecols=["GENERATORS", "operational_type",
                                   "unit_size_mw"]
                )
        for row in zip(dynamic_components["GENERATORS"],
                       dynamic_components["operational_type"],
                       dynamic_components["unit_size_mw"]):
            if row[1] == "dispatchable_capacity_commit":
                mod.unit_size_mw[row[0]] = float(row[2])
            else:
                pass

    # Generators that incur startup/shutdown costs
    m.unit_size_mw = Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
                           within=NonNegativeReals, mutable=True,
                           initialize={})
    m.UnitSizeBuild = BuildAction(
        rule=determine_unit_size)


def power_provision_rule(mod, g, tmp):
    """
    Power provision from dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_MW[g, tmp]


def commitment_rule(mod, g, tmp):
    """
    Number of units committed is the committed capacity divided by the unit
    size
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Commit_Capacity_MW[g, tmp]


def max_power_rule(mod, g, tmp):
    """
    Power plus upward services cannot exceed capacity.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_MW[g, tmp] + \
        mod.Headroom_Provision_MW[g, tmp] \
        <= mod.Commit_Capacity_MW[g, tmp]


def min_power_rule(mod, g, tmp):
    """
    Power minus downward services cannot be below a minimum stable level.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_MW[g, tmp] - \
        mod.Footroom_Provision_MW[g, tmp] \
        >= mod.Commit_Capacity_MW[g, tmp] \
        * mod.min_stable_level_fraction[g]


# TODO: figure out how this should work with fleets (unit size here or in data)
def fuel_cost_rule(mod, g, tmp):
    """
    Fuel use in terms of an IO curve with an incremental heat rate above
    the minimum stable level, i.e. a minimum MMBtu input to have the generator
    on plus incremental fuel use for each MWh above the minimum stable level of
    the generator.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return ((mod.Commit_Capacity_MW[g, tmp]/mod.unit_size_mw[g])
            * mod.minimum_input_mmbtu_per_hr[g]
            + (mod.Provide_Power_MW[g, tmp] -
               (mod.Commit_Capacity_MW[g, tmp]
                * mod.min_stable_level_fraction[g])
               ) * mod.inc_heat_rate_mmbtu_per_mwh[g]
            ) * mod.fuel_price_per_mmbtu[mod.fuel[g].value]


# TODO: startup/shutdown cost per unit won't work without additional info
# about unit size vs total fleet size if modeling a fleet with this module
def startup_rule(mod, g, tmp):
    """
    Will be positive when there are more generators committed in the current
    timepoint that there were in the previous timepoint.
    If horizon is circular, the last timepoint of the horizon is the
    previous_timepoint for the first timepoint if the horizon;
    if the horizon is linear, no previous_timepoint is defined for the first
    timepoint of the horizon, so return 'None' here
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        return None
    else:
        return (mod.Commit_Capacity_MW[g, tmp]
                - mod.Commit_Capacity_MW[g, mod.previous_timepoint[tmp]]
                ) \
               / mod.unit_size_mw[g]


def shutdown_rule(mod, g, tmp):
    """
    Will be positive when there were more generators committed in the previous
    timepoint that there are in the current timepoint.
    If horizon is circular, the last timepoint of the horizon is the
    previous_timepoint for the first timepoint if the horizon;
    if the horizon is linear, no previous_timepoint is defined for the first
    timepoint of the horizon, so return 'None' here
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        return None
    else:
        return (mod.Commit_Capacity_MW[g, mod.previous_timepoint[tmp]]
                - mod.Commit_Capacity_MW[g, tmp]) \
               / mod.unit_size_mw[g]


def fix_commitment(mod, g, tmp):
    """
    Fix committed capacity based on number of committed units and unit size
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    mod.Commit_Capacity_MW[g, tmp] = mod.fixed_commitment[g, tmp].value
    mod.Commit_Capacity_MW[g, tmp].fixed = True


def export_module_specific_results(mod):
    """
    Export commitment decisions.
    :param mod:
    :return:
    """

    commit_capacity_df = \
        make_gen_tmp_var_df(
            mod,
            "DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS",
            "Commit_Capacity_MW",
            "commit_capacity_mw")

    mod.module_specific_df.append(commit_capacity_df)
