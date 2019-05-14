#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module describes the operations of 'binary-commit' generators,
i.e. generators with on/off commitment decisions.
"""

from __future__ import division

from builtins import zip
import csv
import os.path
from pandas import read_csv
from pyomo.environ import Var, Set, Param, Constraint, NonNegativeReals, \
    Binary, PercentFraction, Integers, Expression, value

from gridpath.auxiliary.auxiliary import generator_subset_init
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables


# TODO: ramp rate limits, min up and down time, startups/shutdowns
def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    First, we determine the project subset with 'dispatchable_binary_commit'
    as operational type. This is the *DISPATCHABLE_BINARY_COMMIT_GENERATORS*
    set, which we also designate with :math:`BCG\subset R` and index
    :math:`bcg`.

    We define the minimum stable level parameters over :math:`AGO`: \n
    *disp_binary_commit_min_stable_level_fraction* \ :sub:`aog`\ -- the
    minimum stable level of the dispatchable-binary-commit generator, defined
    as a fraction its capacity \n

    *DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS* (
    :math:`BCG\_OT\subset RT`) is a two-dimensional set that
    defines all project-timepoint combinations when a
    'dispatchable_binary_commit' project can be operational.

    Commit_Binary is the binary commit variable to represent 'on' or 'off'
    state of a generator. It is defined over over
    *DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS*.

    Provide_Power_DispBinaryCommit_MW is the power provision variable for
    the generator. It is defined over is defined over
    *DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS*.

    The main constraints on dispatchable-binary-commit generator power
    provision are as follows:

    For :math:`(bcg, tmp) \in BCG\_OT`: \n
    :math:`Provide\_Power\_DispBinaryCommit\_MW_{bcg, tmp} \geq
    Commit\_MW_{bcg, tmp} \\times disp\_binary\_commit\_min\_stable\_level
    \_fraction \\times Capacity\_MW_{bcg,p}` \n
    :math:`Provide\_Power\_DispBinaryCommit\_MW_{bcg, tmp} \leq
    Commit\_MW_{bcg, tmp} \\times Capacity\_MW_{bcg,p}`

    """
    # Sets and params
    m.DISPATCHABLE_BINARY_COMMIT_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type", "dispatchable_binary_commit")
    )

    m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_BINARY_COMMIT_GENERATORS))

    m.dispbincommit_min_stable_level_fraction = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=PercentFraction)
    # Assume this is the start up ramp rate as defined in Knueven 2018?
    m.dispbincommit_startup_plus_ramp_up_rate = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispbincommit_shutdown_plus_ramp_down_rate = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispbincommit_ramp_up_when_on_rate = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispbincommit_ramp_down_when_on_rate = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=PercentFraction, default=1)
    m.dispbincommit_min_up_time_hours = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=Integers, default=1)
    m.dispbincommit_min_down_time_hours = \
        Param(m.DISPATCHABLE_BINARY_COMMIT_GENERATORS,
              within=Integers, default=1)

    # Variables
    m.Provide_Power_DispBinaryCommit_MW = \
        Var(m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    # New Variables - Binary
    m.Commit_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=Binary)

    m.Start_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=Binary)

    m.Stop_Binary = Var(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=Binary)

    # New Variables - Continuous
    m.Provide_Power_Above_Pmin_DispBinaryCommit_MW = \
        Var(m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    m.Available_Power_Above_Pmin_DispBinaryCommit_MW = \
        Var(m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    # Expressions
    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])
    m.DispBinCommit_Upwards_Reserves_MW = Expression(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=upwards_reserve_rule)

    def pmax_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]]
    m.DispBinCommit_Pmax_MW = Expression(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=pmax_rule)

    def pmin_rule(mod, g, tmp):
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * mod.disp_binary_commit_min_stable_level_fraction[g]
    m.DispBinCommit_Pmin_MW = Expression(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=pmin_rule)

    # constraints from Knueven
    # 17, 23 - DONE
    # 38 40, 41 - gen, part 2, very complex
    # 35, 36 - ramps
    # ??? - piecewise liner - Just use piecewise linear fuel burn separately?
    # 57, 58, 59 - startup costs
    # 60 shutdown costs

    # SU / SD - shut down rate and start-up rate (MW/hr)
    # RU / RD - ramp up rate and ramp down rate
    # TC - time after which generator goes totally cold
    # DT - min down time
    # UT - min runtime
    # TRU
    # C - cost (can be many things depending on subscript)
    # delta_s - startup in category s
    # x - feasible intervals of non-operation (see (57) and nomenclature sets)
    #    --> takes into account minimum down times, e.g. could be 1-4, 1-5,
    #    1-6, 2-5, etc. if min down time is 3 hours

    # T_btm dash = time offline after which you can start up again (min up time)
    # T = set of timesteps, 1-24 generally
    # U = number of hours generator is required to be on at t = 1
    #     presumably depends on previous day. Can assume for it to be zero?
    # UT = minimum up time


    # New Constraints
    def binary_variables_rule(mod, g, tmp):
        """
        If commit status changes, unit is starting or stopping
        Constraint (2) in Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        return (mod.Commit_Binary[g, tmp] -
                mod.Commit_Binary[g, mod.mod.previous_timepoint[tmp]]) \
            == mod.Start_Binary[g, tmp] - mod.Stop_Binary[g, tmp]
    m.DispBinCommit_Binary_Variables_Constraint = \
        Constraint(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=binary_variables_rule
        )

    def min_up_time_rule(mod, g, tmp):
        """
        When units are started, they have to stay on for a minimum number
        of hours described by the dispbincommit_min_up_time_hours parameter
        Constraint (4) from Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        # TODO: should skip constraint for the first "min up time" hours
        #   rather than just the first hour
        #   could add another derived param that is hours_elapsed[tmp] which
        #   returns hours elapsed since start of horizon for each tmp
        # TODO: this constraint assumes that hours per timepoint stays
        #   constant, but timepoints.py does not state this
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        # TODO: enforce subhourly?
        elif mod.dispbincommit_min_up_time_hours[g] <= 1:
            return Constraint.Skip
        else:
            relevant_tmps = list()
            relevant_tmp = tmp
            n_timepoints_in_min_up_time = \
                int(mod.dispbincommit_min_up_time_hours[g]
                    / mod.number_of_hours_in_timepoint[tmp]) + 1

            # build list of relevant tmps: start at relevant tmp and go down to
            # min_up_time_hours before the relevant tmp.
            for n in range(1, n_timepoints_in_min_up_time):
                relevant_tmps.append(relevant_tmp)
                # If horizon is 'linear' and we reach the first timepoint,
                # skip the constraint
                if relevant_tmp == mod.first_horizon_timepoint[mod.horizon[
                    tmp]] \
                        and mod.boundary[mod.horizon[tmp]] == "linear":
                    return Constraint.Skip
                else:
                    relevant_tmp = mod.previous_timepoint[relevant_tmp]

            units_started_min_up_time_or_less_hours_ago = \
                sum(mod.Start_Binary[g, tp] for tp in relevant_tmps)

            return mod.Commit_Binary[g, tmp] \
                >= units_started_min_up_time_or_less_hours_ago
    m.DispBinCommit_Min_Up_Time_Constraint = \
        Constraint(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_up_time_rule
        )

    def min_down_time_rule(mod, g, tmp):
        """
        When units are stopped, they have to stay off for a minimum number
        of hours described by the dispbincommit_min_down_time_hours parameter
        Constraint (5) from Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """

        # TODO: should skip constraint for the first "min up time" hours
        #   rather than just the first hour
        #   could add another derived param that is hours_elapsed[tmp] which
        #   returns hours elapsed since start of horizon for each tmp
        # TODO: this constraint assumes that hours per timepoint stays
        #   constant, but timepoints.py does not state this
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        # TODO: enforce subhourly?
        elif mod.dispbincommit_min_up_time_hours[g] <= 1:
            return Constraint.Skip
        else:
            relevant_tmps = list()
            relevant_tmp = tmp
            n_timepoints_in_min_up_time = \
                int(mod.dispbincommit_min_up_time_hours[g]
                    / mod.number_of_hours_in_timepoint[tmp]) + 1

            # build list of relevant tmps: start at relevant tmp and go down to
            # min_up_time_hours before the relevant tmp.
            for n in range(1, n_timepoints_in_min_up_time):
                relevant_tmps.append(relevant_tmp)
                # If horizon is 'linear' and we reach the first timepoint,
                # skip the constraint
                if relevant_tmp == mod.first_horizon_timepoint[mod.horizon[
                    tmp]] \
                        and mod.boundary[mod.horizon[tmp]] == "linear":
                    return Constraint.Skip
                else:
                    relevant_tmp = mod.previous_timepoint[relevant_tmp]

            units_stopped_min_up_time_or_less_hours_ago = \
                sum(mod.Stop_Binary[g, tp] for tp in relevant_tmps)

            return 1 - mod.Commit_Binary[g, tmp] \
                >= units_stopped_min_up_time_or_less_hours_ago
    m.DispBinCommit_Min_Down_Time_Constraint = \
        Constraint(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_down_time_rule
        )

    # TODO: when module is done, double check this rule is really necessary
    def max_power_rule(mod, g, tmp):
        """
        Can't provide more power than is available
        Constraint (17) in Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_Above_Pmin_DispBinaryCommit[g, tmp] \
            <= mod.Available_Power_Above_Pmin_DispBinaryCommit[g, tmp]
    m.Max_Power_Constraint_DispBinaryCommit = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=max_power_rule
    )

    def max_power_rule_extended_a(mod, g, tmp):
        """
        Total power provision can't be above generator's maximum power output
        Also ensure total capacity is not above shutdown ramp rate if unit
        is shutting down the next timepoint
        Constraint (23a) in Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return \
            (mod.Provide_Power_Above_Pmin_DispBinaryCommit[g, tmp]
                + mod.DispBinCommit_Upwards_Reserves_MW[g, tmp]) \
            <= \
            (mod.DispBinCommit_Pmax_MW[g, tmp]
                - mod.DispBinCommit_Pmin_MW[g, tmp]) \
            * mod.Commit_Binary[g, tmp] \
            - (mod.DispBinCommit_Pmax_MW[g, tmp]
                - mod.dispbincommit_startup_plus_ramp_up_rate[g]) \
            * mod.Start_Binary[g, tmp] \
            - max(mod.dispbincommit_startup_plus_ramp_up_rate[g]
                  - mod.dispbincommit_shutdown_plus_ramp_up_rate[g], 0) \
            * mod.Stop_Binary[g, mod.next_timepoint[tmp]]
    m.Max_Power_Extended_Constraint_A_DispBinaryCommit = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=max_power_rule_extended_a
    )

    def max_power_rule_extended_b(mod, g, tmp):
        """
        Total power provision can't be above generator's maximum power output
        Also ensure total capacity is not above shutdown ramp rate if unit
        is shutting down the next timepoint
        Constraint (23b) in Knueven et al. (2018)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return \
            (mod.Provide_Power_Above_Pmin_DispBinaryCommit[g, tmp]
                + mod.DispBinCommit_Upwards_Reserves_MW[g, tmp]) \
            <= \
            (mod.DispBinCommit_Pmax_MW[g, tmp]
                - mod.DispBinCommit_Pmin_MW[g, tmp]) \
            * mod.Commit_Binary[g, tmp] \
            - (mod.DispBinCommit_Pmax_MW[g, tmp]
                - mod.dispbincommit_shutdown_plus_ramp_up_rate[g]) \
            * mod.Stop_Binary[g, mod.next_timepoint[tmp]] \
            - max(mod.dispbincommit_shutdown_plus_ramp_up_rate[g]
                  - mod.dispbincommit_startup_plus_ramp_up_rate[g], 0) \
            * mod.Start_Binary[g, tmp]
    m.Max_Power_Extended_Constraint_B_DispBinaryCommit = Constraint(
        m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=max_power_rule_extended_b
    )


    # Operational constraints - OLD
    def max_power_rule(mod, g, tmp):
        """
        Power plus upward services cannot exceed capacity.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_DispBinaryCommit_MW[g, tmp] + \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, headroom_variables)[g]) \
            <= mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * mod.Commit_Binary[g, tmp]
    m.DispBinCommit_Max_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
        return mod.Provide_Power_DispBinaryCommit_MW[g, tmp] - \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, footroom_variables)[g]) \
            >= mod.Commit_Binary[g, tmp] \
            * mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * mod.disp_binary_commit_min_stable_level_fraction[g]
    m.DispBinCommit_Min_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_power_rule
        )


def power_provision_rule(mod, g, tmp):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param tmp: the operational timepoint
    :return: expression for power provision by dispatchable-binary-commit
     generators

    Power provision for dispatchable-binary-commit generators is a
    variable constrained to be between the generator's minimum stable level
    and its capacity, if the generator is committed and 0 otherwise.
    """
    return mod.Provide_Power_DispBinaryCommit_MW[g, tmp]


# RPS
def rec_provision_rule(mod, g, tmp):
    """
    REC provision dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """

    return mod.Provide_Power_DispBinaryCommit_MW[g, tmp]


def commitment_rule(mod, g, tmp):
    return mod.Commit_Binary[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Capacity online in each timepoint
    :param mod: 
    :param g: 
    :param tmp: 
    :return: 
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.availability_derate[g, mod.horizon[tmp]] \
        * mod.Commit_Binary[g, tmp]


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
    Fuel use in terms of an IO curve with an incremental heat rate above
    the minimum stable level, i.e. a minimum MMBtu input to have the generator
    on plus incremental fuel use for each MWh above the minimum stable level of
    the generator.
    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        return mod.Commit_Binary[g, tmp] \
            * mod.minimum_input_mmbtu_per_hr[g] \
            + (mod.Provide_Power_DispBinaryCommit_MW[g, tmp] -
               (mod.Commit_Binary[g, tmp]
                * mod.Capacity_MW[g, mod.period[tmp]]
                * mod.availability_derate[g, mod.horizon[tmp]]
                * mod.disp_binary_commit_min_stable_level_fraction[g])
               ) * mod.inc_heat_rate_mmbtu_per_mwh[g]
    else:
        raise ValueError(error_message)


def startup_shutdown_rule(mod, g, tmp):
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
        return (mod.Commit_Binary[g, tmp]
                - mod.Commit_Binary[g, mod.previous_timepoint[tmp]]) * \
               mod.Capacity_MW[g, mod.period[tmp]] \
               * mod.availability_derate[g, mod.horizon[tmp]]


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
        return mod.Provide_Power_DispBinaryCommit_MW[g, tmp] - \
               mod.Provide_Power_DispBinaryCommit_MW[
                    g, mod.previous_timepoint[tmp]
                ]


def fix_commitment(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    mod.Commit_Binary[g, tmp] = mod.fixed_commitment[g, tmp]
    mod.Commit_Binary[g, tmp].fixed = True


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
    min_stable_fraction = dict()
    dynamic_components = \
        read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t", usecols=["project", "operational_type",
                               "min_stable_level_fraction"]
            )
    for row in zip(dynamic_components["project"],
                   dynamic_components["operational_type"],
                   dynamic_components["min_stable_level_fraction"]):
        if row[1] == "dispatchable_binary_commit":
            min_stable_fraction[row[0]] = float(row[2])
        else:
            pass

    data_portal.data()["disp_binary_commit_min_stable_level_fraction"] = \
        min_stable_fraction


def export_module_specific_results(mod, d, scenario_directory, horizon, stage):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "dispatch_binary_commit.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "horizon_weight", "number_of_hours_in_timepoint",
                         "technology", "load_zone",
                         "power_mw", "committed_mw", "committed_units"
                         ])

        for (p, tmp) \
                in mod. \
                DISPATCHABLE_BINARY_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.horizon[tmp],
                tmp,
                mod.horizon_weight[mod.horizon[tmp]],
                mod.number_of_hours_in_timepoint[tmp],
                mod.technology[p],
                mod.load_zone[p],
                value(mod.Provide_Power_DispBinaryCommit_MW[p, tmp]),
                value(mod.Provide_Power_DispBinaryCommit_MW[p, tmp])
                * value(mod.Commit_Binary[p, tmp]),
                value(mod.Provide_Power_DispBinaryCommit_MW[p, tmp])
            ])
