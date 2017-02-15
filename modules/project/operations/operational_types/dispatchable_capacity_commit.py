#!/usr/bin/env python

"""
Operations of dispatchable generators with 'capacity commitment,' i.e.
commit some level of capacity below the total capacity. This approach can
be good for modeling 'fleets' of generators, e.g. a total 2000 MW of 500-MW
units, so if 2000 MW are committed 4 generators (x 500 MW) are committed.
Integer commitment is not enforced as capacity commitment with this approach is
continuous.
"""

import os.path

from pandas import read_csv
from pyomo.environ import Var, Set, Constraint, Param, NonNegativeReals, \
    PercentFraction

from modules.auxiliary.auxiliary import generator_subset_init, \
    make_project_time_var_df
from modules.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables


def add_module_specific_components(m, d):
    """
    Add a capacity commit variable to represent the amount of capacity that is
    on.
    :param m:
    :param d:
    :return:
    """

    # Sets and params
    m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type",
                              "dispatchable_capacity_commit")
    )

    m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS))
    
    m.unit_size_mw = Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
                           within=NonNegativeReals)
    m.disp_cap_commit_min_stable_level_fraction = \
        Param(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATORS,
              within=PercentFraction)

    # Variables
    m.Provide_Power_DispCapacityCommit_MW = \
        Var(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)
    m.Commit_Capacity_MW = \
        Var(m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals
            )

    # Operational constraints
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

    def max_power_rule(mod, g, tmp):
        """
        Power plus upward services cannot exceed capacity.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_DispCapacityCommit_MW[g, tmp] + \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, headroom_variables)[g]) \
            <= mod.Commit_Capacity_MW[g, tmp]
    m.DispCapCommit_Max_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=max_power_rule
        )

    def min_power_rule(mod, g, tmp):
        """
        Power minus downward services cannot be below a minimum stable level.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_DispCapacityCommit_MW[g, tmp] - \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, footroom_variables)[g]) \
            >= mod.Commit_Capacity_MW[g, tmp] \
            * mod.disp_cap_commit_min_stable_level_fraction[g]
    m.DispCapCommit_Min_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_power_rule
        )


def power_provision_rule(mod, g, tmp):
    """
    Power provision from dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispCapacityCommit_MW[g, tmp]


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


def scheduled_curtailment_rule(mod, g, tmp):
    """
    No 'curtailment' -- simply dispatch down
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


# TODO: ignoring subhourly behavior for dispatchable gens for now
def subhourly_curtailment_rule(mod, g, tmp):
    """
    Can't provide reserves
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    Can't provide reserves
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


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
            + (mod.Provide_Power_DispCapacityCommit_MW[g, tmp] -
               (mod.Commit_Capacity_MW[g, tmp]
                * mod.disp_cap_commit_min_stable_level_fraction[g])
               ) * mod.inc_heat_rate_mmbtu_per_mwh[g]
            ) * mod.fuel_price_per_mmbtu[mod.fuel[g]]


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
    mod.Commit_Capacity_MW[g, tmp] = mod.fixed_commitment[g, tmp]
    mod.Commit_Capacity_MW[g, tmp].fixed = True


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
    dynamic_components = \
        read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t", usecols=["project", "operational_type",
                               "unit_size_mw", "min_stable_level_fraction"]
            )
    for row in zip(dynamic_components["project"],
                   dynamic_components["operational_type"],
                   dynamic_components["unit_size_mw"],
                   dynamic_components["min_stable_level_fraction"]):
        if row[1] == "dispatchable_capacity_commit":
            unit_size_mw[row[0]] = float(row[2])
            min_stable_fraction[row[0]] = float(row[3])
        else:
            pass

    data_portal.data()["unit_size_mw"] = unit_size_mw
    data_portal.data()["disp_cap_commit_min_stable_level_fraction"] = \
        min_stable_fraction


def export_module_specific_results(mod, d):
    """
    Export commitment decisions.
    :param mod:
    :param d:
    :return:
    """

    commit_capacity_df = \
        make_project_time_var_df(
            mod,
            "DISPATCHABLE_CAPACITY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS",
            "Commit_Capacity_MW",
            ["project", "timepoint"],
            "commit_capacity_mw"
        )

    d.module_specific_df.append(commit_capacity_df)
