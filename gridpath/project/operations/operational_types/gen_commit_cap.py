#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module describes the operations of generation projects with 'capacity
commitment' operational decisions, i.e. continuous variables to commit some
level of capacity below the total capacity of the project. This operational
type is particularly well suited for application to 'fleets' of generators
with the same characteristics. For example, we could have a GridPath project
with a total capacity of 2000 MW, which actually consists of four 500-MW
units. The optimization decides how much total capacity to commit (i.e. turn
on), e.g. if 2000 MW are committed, then four generators (x 500 MW) are on
and if 500 MW are committed, then one generator is on, etc.

The capacity commitment decision variables are continuous. This approach
makes it possible to reduce problem size by grouping similar generators
together and linearizing the commitment decisions.

The optimization makes the capacity-commitment and dispatch decisions in
every timepoint. Project power output can vary between a minimum loading level
(specified as a fraction of committed capacity) and the committed capacity
in each timepoint when the project is available. Heat rate degradation below
full load is considered. These projects can be allowed to provide upward
and/or downward reserves.

No standard approach exists for applying ramp rate and minimum up and down
time constraints to this operational type. GridPath does include
experimental functionality for doing so. Starts and stops -- and the
associated cost and emissions -- can also be tracked and constrained for
this operational type.

Costs for this operational type include fuel costs, variable O&M costs, and
startup and shutdown costs.

"""

from __future__ import division
from __future__ import print_function

from builtins import next
from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Constraint, Param, NonNegativeReals, \
    NonPositiveReals, PercentFraction, Reals, value, Expression

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import generator_subset_init, \
    write_validation_to_database, check_req_prj_columns, setup_results_import
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints


def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_COMMIT_CAP`                                                |
    |                                                                         |
    | The set of generators of the `gen_commit_cap` operational type          |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_CAP_OPR_TMPS`                                       |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_commit_cap`       |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_CAP_OPR_TMPS_FUEL_SEG`                              |
    |                                                                         |
    | Three-dimensional set with generators of the :code:`gen_commit_cap`     |
    | operational type, their operational timepoints, and their fuel          |
    | segments (if the project is in :code:`FUEL_PROJECTS`).                  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_commit_cap_unit_size_mw`                                   |
    | | *Defined over*: :code:`GEN_COMMIT_CAP`                                |
    |                                                                         |
    | The MW size of a unit in this project (projects of the                  |
    | :code:`gen_commit_cap` type can represent a fleet of similar units).    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_cap_min_stable_level_fraction`                      |
    | | *Defined over*: :code:`GEN_COMMIT_CAP`                                |
    |                                                                         |
    | The minimum stable level of this project as a fraction of its capacity. |
    | This can also be interpreted as the minimum stable level of a unit      |
    | within this project (as the project itself can represent multiple       |
    | units with similar characteristics.                                     |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_commit_cap_startup_plus_ramp_up_rate`                      |
    | | *Defined over*: :code:`GEN_COMMIT_CAP`                                |
    |                                                                         |
    | The project's ramp rate when starting up as percent of project capacity |
    | per minute (defaults to 1 if not specified).                            |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_cap_shutdown_plus_ramp_down_rate`                   |
    | | *Defined over*: :code:`GEN_COMMIT_CAP`                                |
    |                                                                         |
    | The project's ramp rate when shutting down as percent of project        |
    | capacity per minute (defaults to 1 if not specified).                   |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_cap_ramp_up_when_on_rate`                           |
    | | *Defined over*: :code:`GEN_COMMIT_CAP`                                |
    |                                                                         |
    | The project's upward ramp rate limit during operations, defined as a    |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_cap_ramp_down_when_on_rate`                         |
    | | *Defined over*: :code:`GEN_COMMIT_CAP`                                |
    |                                                                         |
    | The project's downward ramp rate limit during operations, defined as a  |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_cap_min_up_time_hours`                              |
    | | *Defined over*: :code:`GEN_COMMIT_CAP`                                |
    |                                                                         |
    | The project's minimum up time in hours.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_cap_min_down_time_hours`                            |
    | | *Defined over*: :code:`GEN_COMMIT_CAP`                                |
    |                                                                         |
    | The project's minimum down time in hours.                               |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`GenCommitCap_Provide_Power_MW`                                 |
    | | *Within*: :code:`NonNegativeReals`)                                   |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Power provision in MW from this project in each timepoint in which the  |
    | project is operational (capacity exists and the project is available).  |
    +-------------------------------------------------------------------------+
    | | :code:`Commit_Capacity_MW`                                            |
    | | *Within*: :code:`NonNegativeReals`)                                   |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | A continuous variable that represents the commitment state of the       |
    | (i.e. of the units represented by this project).                        |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitCap_Fuel_Burn_MMBTU`                                  |
    | | *Within*: :code:`NonNegativeReals`)                                   |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Fuel burn by this project in each operational timepoint.                |
    +-------------------------------------------------------------------------+
    | | :code:`Ramp_Up_Startup_MW`                                            |
    | | *Within*: :code:`Reals`)                                              |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | The upward ramp of the project when capacity is started up.             |
    +-------------------------------------------------------------------------+
    | | :code:`Ramp_Down_Startup_MW`                                          |
    | | *Within*: :code:`Reals`)                                              |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | The downward ramp of the project when capacity is shutting down.        |
    +-------------------------------------------------------------------------+
    | | :code:`Ramp_Up_When_On_MW`                                            |
    | | *Within*: :code:`Reals`)                                              |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | The upward ramp of the project when capacity on.                        |
    +-------------------------------------------------------------------------+
    | | :code:`Ramp_Down_When_On_MW`                                          |
    | | *Within*: :code:`Reals`)                                              |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | The downward ramp of the project when capacity is on.                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitCap_Startup_MW`                                       |
    | | *Within*: :code:`NonNegativeReals`)                                   |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | The amount of capacity started up.                                      |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitCap_Shutdown_MW`                                      |
    | | *Within*: :code:`NonNegativeReals`)                                   |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | The amount of capacity shut down.                                       |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | Commitment and Power                                                    |
    +-------------------------------------------------------------------------+
    | | :code:`Commit_Capacity_Constraint`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits committed capacity to the available capacity.                    |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitCap_Max_Power_Constraint`                             |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits the power plus upward reserves to the committed capacity.        |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitCap_Min_Power_Constraint`                             |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits the power provision minus downward reserves to the minimum       |
    | stable level for the project.                                           |
    +-------------------------------------------------------------------------+
    | Ramps                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`Ramp_Up_Off_to_On_Constraint`                                  |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project upward ramp when turning capacity on based   |
    | on the :code:`gen_commit_cap_startup_plus_ramp_up_rate`.                |
    +-------------------------------------------------------------------------+
    | | :code:`Ramp_Up_When_On_Constraint`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project upward ramp when capacity is on based on     |
    | the :code:`gen_commit_cap_ramp_up_when_on_rate`.                        |
    +-------------------------------------------------------------------------+
    | | :code:`Ramp_Up_When_On_Headroom_Constraint`                           |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project upward ramp based on the headroom available  |
    | in the previous timepoint.                                              |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitCap_Ramp_Up_Constraint`                               |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project upward ramp (regardless of commitment state).|
    +-------------------------------------------------------------------------+
    | | :code:`Ramp_Down_On_to_Off_Constraint`                                |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project downward ramp when turning capacity on based |
    | on the :code:`gen_commit_cap_shutdown_plus_ramp_down_rate`.             |
    +-------------------------------------------------------------------------+
    | | :code:`Ramp_Down_When_On_Constraint`                                  |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project downward ramp when capacity is on based on   |
    | the :code:`gen_commit_cap_ramp_down_when_on_rate`.                      |
    +-------------------------------------------------------------------------+
    | | :code:`Ramp_Down_When_On_Headroom_Constraint`                         |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project downward ramp based on the headroom          |
    | available in the current timepoint.                                     |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitCap_Ramp_Down_Constraint`                             |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project downward ramp (regardless of commitment      |
    | state).                                                                 |
    +-------------------------------------------------------------------------+
    | Minimum Up and Down Time                                                |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitCap_Startup_Constraint`                               |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits the capacity started up to the difference in commitment between  |
    | the current and previous timepoint.                                     |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitCap_Shutdown_Constraint`                              |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Limits the capacity shut down to the difference in commitment between   |
    | the current and previous timepoint.                                     |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitCap_Min_Up_Time_Constraint`                           |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Requires that when units within this project are started, they stay on  |
    | for at least :code:`gen_commit_cap_min_up_time_hours`.                  |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitCap_Min_Down_Time_Constraint`                         |
    | | *Defined over*: :code:`GEN_COMMIT_CAP_OPR_TMPS`                       |
    |                                                                         |
    | Requires that when units within this project are stopped, they stay off |
    | for at least :code:`gen_commit_cap_min_down_time_hours`.                |
    +-------------------------------------------------------------------------+




    """

    # Sets
    ###########################################################################
    m.GEN_COMMIT_CAP = Set(
        within=m.PROJECTS,
        initialize=generator_subset_init("operational_type", "gen_commit_cap")
    )

    m.GEN_COMMIT_CAP_OPR_TMPS = Set(
        dimen=2,
        within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod: set((g, tmp) for (g, tmp) in
                             mod.PROJECT_OPERATIONAL_TIMEPOINTS if g in
                             mod.GEN_COMMIT_CAP)
    )

    m.GEN_COMMIT_CAP_OPR_TMPS_FUEL_SEG = Set(
        dimen=3,
        within=m.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
        set((g, tmp, s) for (g, tmp, s)
            in mod.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS
            if g in mod.GEN_COMMIT_CAP)
    )

    # Required Params
    ###########################################################################
    m.gen_commit_cap_unit_size_mw = Param(
        m.GEN_COMMIT_CAP,
        within=NonNegativeReals
    )
    m.gen_commit_cap_min_stable_level_fraction = Param(
        m.GEN_COMMIT_CAP,
        within=PercentFraction
    )

    # Optional Params
    ###########################################################################
    m.gen_commit_cap_startup_plus_ramp_up_rate = Param(
        m.GEN_COMMIT_CAP,
        within=PercentFraction, default=1
    )
    m.gen_commit_cap_shutdown_plus_ramp_down_rate = Param(
        m.GEN_COMMIT_CAP,
        within=PercentFraction, default=1
    )
    m.gen_commit_cap_ramp_up_when_on_rate = Param(
        m.GEN_COMMIT_CAP,
        within=PercentFraction, default=1
    )
    m.gen_commit_cap_ramp_down_when_on_rate = Param(
        m.GEN_COMMIT_CAP,
        within=PercentFraction, default=1
    )
    m.gen_commit_cap_min_up_time_hours = Param(
        m.GEN_COMMIT_CAP,
        within=NonNegativeReals, default=1
    )
    m.gen_commit_cap_min_down_time_hours = Param(
        m.GEN_COMMIT_CAP,
        within=NonNegativeReals, default=1
    )

    # Variables
    ###########################################################################
    m.GenCommitCap_Provide_Power_MW = Var(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        within=NonNegativeReals
    )
    m.Commit_Capacity_MW = Var(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        within=NonNegativeReals
    )
    m.GenCommitCap_Fuel_Burn_MMBTU = Var(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        within=NonNegativeReals
    )

    # Variables for optional ramp constraints
    # We'll have separate treatment of ramps of:
    # generation that is online in both the current and the previous timepoint
    # and of
    # generation that is either started up or shut down since the previous
    # timepoint

    # Ramp_Up_Startup_MW and Ramp_Down_Shutdown_MW must be able to take
    # either positive  or negative values, as they are both constrained by
    # a product of a positive number and the difference committed capacity
    # between the current and previous timepoints (which needs to be able to
    # take on both positive values when turning units on and negative values
    # when turning units off)
    # They also need to be separate variables, as if they were combined,
    # the only solution would be for there to be no startups/shutdowns
    m.Ramp_Up_Startup_MW = Var(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        within=Reals
    )
    m.Ramp_Down_Shutdown_MW = Var(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        within=Reals
    )

    m.Ramp_Up_When_On_MW = Var(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        within=NonNegativeReals
    )
    m.Ramp_Down_When_On_MW = Var(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        within=NonPositiveReals
    )

    # Variables for constraining up and down time
    # Startup and shutdown variables, must be non-negative
    m.GenCommitCap_Startup_MW = Var(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        within=NonNegativeReals
    )
    m.GenCommitCap_Shutdown_MW = Var(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        within=NonNegativeReals
    )

    # Expressions
    ###########################################################################
    # TODO: the reserve rules are the same in all modules, so should be
    #  consolidated
    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])
    m.GenCommitCap_Upwards_Reserves_MW = Expression(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=upwards_reserve_rule
    )

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])
    m.GenCommitCap_Downwards_Reserves_MW = Expression(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=downwards_reserve_rule
    )

    # Constraints
    ###########################################################################

    # Commitment and power
    m.Commit_Capacity_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=commit_capacity_constraint_rule
    )

    m.GenCommitCap_Max_Power_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=max_power_rule
    )

    m.GenCommitCap_Min_Power_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=min_power_rule
    )

    # Ramping
    m.Ramp_Up_Off_to_On_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=ramp_up_off_to_on_constraint_rule
    )

    m.Ramp_Up_When_On_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=ramp_up_on_to_on_constraint_rule
    )

    m.Ramp_Up_When_On_Headroom_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=ramp_up_on_to_on_headroom_constraint_rule
    )

    m.GenCommitCap_Ramp_Up_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=ramp_up_constraint_rule
    )

    m.Ramp_Down_On_to_Off_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=ramp_down_on_to_off_constraint_rule
    )

    m.Ramp_Down_When_On_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=ramp_down_on_to_on_constraint_rule
    )

    m.Ramp_Down_When_On_Headroom_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=ramp_down_on_to_on_headroom_constraint_rule
    )

    m.GenCommitCap_Ramp_Down_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=ramp_down_constraint_rule
    )

    # Min up and down time
    m.GenCommitCap_Startup_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=startup_constraint_rule
    )

    m.GenCommitCap_Shutdown_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=shutdown_constraint_rule
    )

    m.GenCommitCap_Min_Up_Time_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=min_up_time_constraint_rule
    )

    m.GenCommitCap_Min_Down_Time_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS,
        rule=min_down_time_constraint_rule
    )

    # Fuel burn
    m.Fuel_Burn_GenCommitCap_Constraint = Constraint(
        m.GEN_COMMIT_CAP_OPR_TMPS_FUEL_SEG,
        rule=fuel_burn_constraint_rule
    )


# Constraint Formulation Rules
###############################################################################

# Commitment and power
def commit_capacity_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: Commit_Capacity_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

    Can't commit more capacity than available in each timepoint.
    """
    return mod.Commit_Capacity_MW[g, tmp] \
        <= mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def max_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitCap_Max_Power_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

    Power plus upward services cannot exceed capacity.
    """
    return mod.GenCommitCap_Provide_Power_MW[g, tmp] \
        + mod.GenCommitCap_Upwards_Reserves_MW[g, tmp] \
        <= mod.Commit_Capacity_MW[g, tmp]


def min_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitCap_Min_Power_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

    Power minus downward services cannot be below a minimum stable level.
    """
    return mod.GenCommitCap_Provide_Power_MW[g, tmp] \
        - mod.GenCommitCap_Downwards_Reserves_MW[g, tmp] \
        >= mod.Commit_Capacity_MW[g, tmp] \
        * mod.gen_commit_cap_min_stable_level_fraction[g]


# Ramping
def ramp_up_off_to_on_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: Ramp_Up_Off_to_On_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

    When turning on, generators can ramp up to a certain fraction of
    started up capacity. This fraction must be greater than or equal to
    the minimum stable level for the generator to be able to turn on.

    We assume that a unit has to reach its setpoint at the start of the
    timepoint; as such, the ramping between 2 timepoints is assumed to
    take place during the duration of the first timepoint, and the
    ramp rate limit is adjusted for the duration of the first timepoint.
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        return Constraint.Skip
    else:
        return mod.Ramp_Up_Startup_MW[g, tmp] \
            <= \
            (mod.Commit_Capacity_MW[g, tmp]
             - mod.Commit_Capacity_MW[
                 g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]) \
            * mod.gen_commit_cap_startup_plus_ramp_up_rate[g] * 60 \
            * mod.number_of_hours_in_timepoint[
                   mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]


def ramp_up_on_to_on_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: Ramp_Up_When_On_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

    Generators online in the last timepoint, if still online, could have
    ramped up at a rate at or below the online capacity times a
    pre-specified ramp rate fraction. The max on to on ramp up
    allowed is if they all stayed online. Startups are treated separately.
    There are limitations to this approach. For example, if online
    capacity was producing at full power at t-2 and t-1, some additional
    capacity was turned on at t-1 and ramped to some level above its
    Pmin but not full output, this constraint would allow for the total
    committed capacity in t-1 to be ramped up, even though in reality
    only the started up capacity can be ramped as the capacity from t-2
    is already producing at full power. In reality, this situation is
    unlikely to be an issue, as most generators can ramp from Pmin to
    Pmax fully in an hour, so the fact that this constraint is too lax
    in this situation does not matter when modeling fleets at an hourly
    or coarser resolution.

    We assume that a unit has to reach its setpoint at the start of the
    timepoint; as such, the ramping between 2 timepoints is assumed to
    take place during the duration of the first timepoint, and the
    ramp rate limit is adjusted for the duration of the first timepoint.
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        return Constraint.Skip
    else:
        return mod.Ramp_Up_When_On_MW[g, tmp] \
            <= \
            mod.Commit_Capacity_MW[
                   g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]] \
            * mod.gen_commit_cap_ramp_up_when_on_rate[g] * 60 \
            * mod.number_of_hours_in_timepoint[
                   mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]


def ramp_up_on_to_on_headroom_constraint_rule(mod, g, tmp):
        """
        **Constraint Name**: Ramp_Up_When_On_Headroom_Constraint
        **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

        Generators online in the previous timepoint that are still online
        could not have ramped up above their total online capacity, i.e. not
        more than their available headroom in the previous timepoint.
        The maximum possible headroom in the previous timepoint is equal to
        the difference between committed capacity and (power provided minus
        downward reserves).
        """
        # TODO: check behavior more carefully (same for ramp down)
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return mod.Ramp_Up_When_On_MW[g, tmp] \
                <= \
                mod.Commit_Capacity_MW[
                       g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]] \
                - (mod.GenCommitCap_Provide_Power_MW[
                    g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
                   - mod.GenCommitCap_Downwards_Reserves_MW[
                    g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]])


def ramp_up_constraint_rule(mod, g, tmp):
        """
        **Constraint Name**: GenCommitCap_Ramp_Up_Constraint
        **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

        The ramp up (power provided in the current timepoint minus power
        provided in the previous timepoint), adjusted for any reserve provision
        in the current and previous timepoint, cannot exceed a prespecified
        ramp rate (expressed as fraction of capacity)
        Two components:
        1) Ramp_Up_Startup_MW (see Ramp_Up_Off_to_On_Constraint above):
        If we are turning generators on since the previous timepoint, we will
        allow the ramp of going from 0 to minimum stable level + some
        additional ramping : the gen_commit_cap_startup_plus_ramp_up_rate
        parameter
        2) Ramp_Up_When_On_MW (see Ramp_Up_When_On_Constraint and
        Ramp_Up_When_On_Headroom_Constraint above):
        Units committed in both the current timepoint and the previous
        timepoint could have ramped up at a certain rate since the previous
        timepoint
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # start up the full capacity and ramp up the full operable range
        # between timepoints, constraint won't bind, so skip
        elif (mod.gen_commit_cap_startup_plus_ramp_up_rate[g] * 60
              * mod.number_of_hours_in_timepoint[
                  mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
              >= 1
              and
              mod.gen_commit_cap_ramp_up_when_on_rate[g] * 60
              * mod.number_of_hours_in_timepoint[
                  mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
              >= (1 - mod.gen_commit_cap_min_stable_level_fraction[g])
              ):
            return Constraint.Skip
        else:
            return (mod.GenCommitCap_Provide_Power_MW[g, tmp]
                    + mod.GenCommitCap_Upwards_Reserves_MW[g, tmp]) \
                - (mod.GenCommitCap_Provide_Power_MW[
                        g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
                   - mod.GenCommitCap_Downwards_Reserves_MW[
                        g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
                   ) \
                <= \
                mod.Ramp_Up_Startup_MW[g, tmp] \
                + mod.Ramp_Up_When_On_MW[g, tmp]


def ramp_down_on_to_off_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: Ramp_Down_On_to_Off_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

    When turning off, generators can ramp down from a certain
    fraction of the capacity to be shut down to 0. This fraction must be
    greater than or equal to the minimum stable level for the generator
    to be able to turn off.

    We assume that a unit has to reach its setpoint at the start of the
    timepoint; as such, the ramping between 2 timepoints is assumed to
    take place during the duration of the first timepoint, and the
    ramp rate limit is adjusted for the duration of the first timepoint.
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        return Constraint.Skip
    else:
        return mod.Ramp_Down_Shutdown_MW[g, tmp] \
               >= \
               (mod.Commit_Capacity_MW[g, tmp]
                - mod.Commit_Capacity_MW[
                    g, mod.previous_timepoint[
                        tmp, mod.balancing_type_project[g]]]) \
               * mod.gen_commit_cap_shutdown_plus_ramp_down_rate[g] * 60 \
               * mod.number_of_hours_in_timepoint[
                   mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]


def ramp_down_on_to_on_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: Ramp_Down_When_On_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

    Generators still online in the current timepoint could have ramped
    down at a rate at or below the online capacity times a pre-specified
    ramp rate fraction. Shutdowns are treated separately.
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        return Constraint.Skip
    else:
        return mod.Ramp_Down_When_On_MW[g, tmp] \
               >= \
               mod.Commit_Capacity_MW[g, tmp] \
               * (-mod.gen_commit_cap_ramp_down_when_on_rate[g]) * 60 \
               * mod.number_of_hours_in_timepoint[
                   mod.previous_timepoint[
                       tmp, mod.balancing_type_project[g]]]


def ramp_down_on_to_on_headroom_constraint_rule(mod, g, tmp):
        """
        **Constraint Name**: Ramp_Down_When_On_Headroom_Constraint
        **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

        Generators still online in the current timepoint could not have ramped
        down more than their current headroom. The maximum possible headroom is
        equal to the difference between committed capacity and (power provided
        minus downward reserves).
        Note: Ramp_Down_When_On_MW is negative when a unit is ramping down, so
        we add a negative sign before it the constraint.
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                and mod.boundary[
            mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        else:
            return -mod.Ramp_Down_When_On_MW[g, tmp] \
                   <= \
                   mod.Commit_Capacity_MW[g, tmp] \
                   - (mod.GenCommitCap_Provide_Power_MW[g, tmp]
                      - mod.GenCommitCap_Downwards_Reserves_MW[g, tmp])


def ramp_down_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitCap_Ramp_Down_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

    The ramp down (power provided in the current timepoint minus power
    provided in the previous timepoint), adjusted for any reserve provision
    in the current and previous timepoint, cannot exceed a prespecified
    ramp rate (expressed as fraction of capacity)
    Two components:
    1) Ramp_Down_Shutdown_MW (see Ramp_Down_On_to_Off_Constraint above):
    If we are turning generators off, we will allow the ramp of
    going from minimum stable level to 0 + some additional ramping from
    above minimum stable level
    2) Ramp_Down_When_On_MW (see Ramp_Down_When_On_Constraint and
    Ramp_Down_When_On_Headroom_Constraint above):
    Units still committed in the current timepoint could have ramped down
    at a certain rate since the previous timepoint
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        return Constraint.Skip
    # If ramp rate limits, adjusted for timepoint duration, allow you to
    # shut down the full capacity and ramp down the full operable range
    # between timepoints, constraint won't bind, so skip
    elif (mod.gen_commit_cap_shutdown_plus_ramp_down_rate[g] * 60
          * mod.number_of_hours_in_timepoint[
              mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
          >= 1
          and
          mod.gen_commit_cap_ramp_down_when_on_rate[g] * 60
          * mod.number_of_hours_in_timepoint[
              mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
          >= (1 - mod.gen_commit_cap_min_stable_level_fraction[g])
    ):
        return Constraint.Skip
    else:
        return (mod.GenCommitCap_Provide_Power_MW[g, tmp]
                - mod.GenCommitCap_Downwards_Reserves_MW[g, tmp]) \
               - (mod.GenCommitCap_Provide_Power_MW[
                      g, mod.previous_timepoint[
                          tmp, mod.balancing_type_project[g]]]
                  + mod.GenCommitCap_Upwards_Reserves_MW[
                      g, mod.previous_timepoint[
                          tmp, mod.balancing_type_project[g]]]
                  ) \
               >= \
               mod.Ramp_Down_Shutdown_MW[g, tmp] \
               + mod.Ramp_Down_When_On_MW[g, tmp]


def startup_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitCap_Startup_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

    When units are shut off, GenCommitCap_Startup_MW will be 0 (as it
    has to be non-negative)
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        return Constraint.Skip
    else:
        return mod.GenCommitCap_Startup_MW[g, tmp] \
               >= mod.Commit_Capacity_MW[g, tmp] \
               - mod.Commit_Capacity_MW[
                   g, mod.previous_timepoint[
                       tmp, mod.balancing_type_project[g]]]


def shutdown_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitCap_Shutdown_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

    When units are turned on, GenCommitCap_Shutdown_MW will be 0 (as it
    has to be non-negative)
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        return Constraint.Skip
    else:
        return mod.GenCommitCap_Shutdown_MW[g, tmp] \
               >= mod.Commit_Capacity_MW[
                   g, mod.previous_timepoint[
                       tmp, mod.balancing_type_project[g]]] \
               - mod.Commit_Capacity_MW[g, tmp]


def min_up_time_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitCap_Min_Up_Time_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

    When units are started, they have to stay on for a minimum number
    of hours described by the gen_commit_cap_min_up_time_hours parameter.
    The constraint is enforced by ensuring that the online capacity
    (committed capacity) is at least as large as the amount of capacity
    that was started within min down time hours.

    We ensure capacity turned on less than the minimum up time ago is
    still on in the current timepoint *tmp* by checking how much capacity
    was turned on in each 'relevant' timepoint (i.e. a timepoint that
    begins more than or equal to gen_commit_cap_min_up_time_hours ago
    relative to the start of timepoint *tmp*) and then summing those
    capacities.
    """
    relevant_tmps = determine_relevant_timepoints(
        mod, g, tmp, mod.gen_commit_cap_min_up_time_hours[g]
    )

    # If only the current timepoint is determined to be relevant,
    # this constraint is redundant (it will simplify to
    # Commit_Capacity_MW[g, previous_timepoint[tmp]} >= 0)
    # This also takes care of the first timepoint in a linear horizon
    # setting, which has only *tmp* in the list of relevant timepoints
    if relevant_tmps == [tmp]:
        return Constraint.Skip
    # Otherwise, we must have at least as much capacity committed as was
    # started up in the relevant timepoints
    else:
        capacity_turned_on_min_up_time_or_less_hours_ago = \
            sum(mod.GenCommitCap_Startup_MW[g, tp]
                for tp in relevant_tmps)

        return mod.Commit_Capacity_MW[g, tmp] \
               >= capacity_turned_on_min_up_time_or_less_hours_ago


def min_down_time_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitCap_Min_Down_Time_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS

    When units are stopped, they have to stay off for a minimum number
    of hours described by the gen_commit_cap_min_down_time_hours parameter.
    The constraint is enforced by ensuring that the offline capacity
    (available capacity minus committed capacity) is at least as large
    as the amount of capacity that was stopped within min down time hours.

    We ensure capacity turned off less than the minimum down time ago is
    still off in the current timepoint *tmp* by checking how much capacity
    was turned off in each 'relevant' timepoint (i.e. a timepoint that
    begins more than or equal to gen_commit_cap_min_down_time_hours ago
    relative to the start of timepoint *tmp*) and then summing those
    capacities.
    """

    relevant_tmps = determine_relevant_timepoints(
        mod, g, tmp, mod.gen_commit_cap_min_down_time_hours[g]
    )

    capacity_turned_off_min_down_time_or_less_hours_ago = \
        sum(mod.GenCommitCap_Shutdown_MW[g, tp]
            for tp in relevant_tmps)

    # If only the current timepoint is determined to be relevant,
    # this constraint is redundant (it will simplify to
    # Commit_Capacity_MW[g, previous_timepoint[tmp]} >= 0)
    # This also takes care of the first timepoint in a linear horizon
    # setting, which has only *tmp* in the list of relevant timepoints
    if relevant_tmps == [tmp]:
        return Constraint.Skip
    # Otherwise, we must have at least as much capacity off as was shut
    # down in the relevant timepoints
    else:
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.Availability_Derate[g, tmp] \
            - mod.Commit_Capacity_MW[g, tmp] \
            >= capacity_turned_off_min_down_time_or_less_hours_ago


def fuel_burn_constraint_rule(mod, g, tmp, s):
    """
    **Constraint Name**: Fuel_Burn_GenCommitCap_Constraint
    **Enforced Over**: GEN_COMMIT_CAP_OPR_TMPS_FUEL_SEG

    Fuel burn is set by piecewise linear representation of input/output
    curve.

    Note: The availability de-rate is already accounted for in
    Commit_Capacity_MW so we don't need to multiply the intercept
    by the Availability_Derate like we do for gen_always_on generators.
    """
    return \
        mod.GenCommitCap_Fuel_Burn_MMBTU[g, tmp] \
        >= \
        mod.fuel_burn_slope_mmbtu_per_mwh[g, s] \
        * mod.GenCommitCap_Provide_Power_MW[g, tmp] \
        + mod.fuel_burn_intercept_mmbtu_per_hr[g, s] \
        * (mod.Commit_Capacity_MW[g, tmp] / mod.gen_commit_cap_unit_size_mw[g])


# Operational Type Methods
###############################################################################
def power_provision_rule(mod, g, tmp):
    """
    Power provision for dispatchable-capacity-commit generators is a
    variable constrained to be between the minimum stable level (defined as
    a fraction of committed capacity) and the committed capacity.
    """
    return mod.GenCommitCap_Provide_Power_MW[g, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision from dispatchable generators is an endogenous variable.
    """
    return mod.GenCommitCap_Provide_Power_MW[g, tmp]


def commitment_rule(mod, g, tmp):
    """
    Number of units committed is the committed capacity divided by the unit
    size
    """
    return mod.Commit_Capacity_MW[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Capacity online in each timepoint
    """
    return mod.Commit_Capacity_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    No 'curtailment' -- simply dispatch down and use energy (fuel) later
    """
    return 0


# TODO: ignoring subhourly behavior for dispatchable gens for now
def subhourly_curtailment_rule(mod, g, tmp):
    """
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    """
    return 0


def fuel_burn_rule(mod, g, tmp, error_message):
    """
    """
    if g in mod.FUEL_PROJECTS:
        return mod.GenCommitCap_Fuel_Burn_MMBTU[g, tmp]
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
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        return None
    else:
        return mod.Commit_Capacity_MW[g, tmp] \
         - mod.Commit_Capacity_MW[
                   g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]


def power_delta_rule(mod, g, tmp):
    """
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        pass
    else:
        return mod.GenCommitCap_Provide_Power_MW[g, tmp] - \
               mod.GenCommitCap_Provide_Power_MW[
                   g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]
               ]


def fix_commitment(mod, g, tmp):
    """
    Fix committed capacity based on number of committed units and unit size
    """
    mod.Commit_Capacity_MW[g, tmp] = \
        mod.fixed_commitment[g, mod.previous_stage_timepoint_map[tmp]]
    mod.Commit_Capacity_MW[g, tmp].fixed = True


# Input-Output
###############################################################################
def load_module_specific_data(mod, data_portal, scenario_directory,
                              subproblem, stage):
    """

    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    unit_size_mw = dict()
    min_stable_fraction = dict()
    startup_plus_ramp_up_rate = dict()
    shutdown_plus_ramp_down_rate = dict()
    ramp_up_when_on_rate = dict()
    ramp_down_when_on_rate = dict()
    min_up_time = dict()
    min_down_time = dict()

    header = pd.read_csv(os.path.join(scenario_directory, subproblem, stage,
                                      "inputs", "projects.tab"),
                         sep="\t", header=None, nrows=1).values[0]

    optional_columns = ["startup_plus_ramp_up_rate",
                        "shutdown_plus_ramp_down_rate",
                        "ramp_up_when_on_rate",
                        "ramp_down_when_on_rate",
                        "min_up_time_hours", "min_down_time_hours"]
    used_columns = [c for c in optional_columns if c in header]

    dynamic_components = \
        pd.read_csv(
            os.path.join(scenario_directory, subproblem, stage, "inputs", "projects.tab"),
            sep="\t",
            usecols=["project", "operational_type", "unit_size_mw",
                     "min_stable_level_fraction"] + used_columns
            )

    for row in zip(dynamic_components["project"],
                   dynamic_components["operational_type"],
                   dynamic_components["unit_size_mw"],
                   dynamic_components["min_stable_level_fraction"]):
        if row[1] == "gen_commit_cap":
            unit_size_mw[row[0]] = float(row[2])
            min_stable_fraction[row[0]] = float(row[3])
        else:
            pass

    data_portal.data()["gen_commit_cap_unit_size_mw"] = unit_size_mw
    data_portal.data()["gen_commit_cap_min_stable_level_fraction"] = \
        min_stable_fraction

    # Ramp rate limits are optional; will default to 1 if not specified
    if "startup_plus_ramp_up_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["startup_plus_ramp_up_rate"]
                       ):
            if row[1] == "gen_commit_cap" and row[2] != ".":
                startup_plus_ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "gen_commit_cap_startup_plus_ramp_up_rate"] = \
            startup_plus_ramp_up_rate

    if "shutdown_plus_ramp_down_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["shutdown_plus_ramp_down_rate"]
                       ):
            if row[1] == "gen_commit_cap" and row[2] != ".":
                shutdown_plus_ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "gen_commit_cap_shutdown_plus_ramp_down_rate"] = \
            shutdown_plus_ramp_down_rate

    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_up_when_on_rate"]
                       ):
            if row[1] == "gen_commit_cap" and row[2] != ".":
                ramp_up_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "gen_commit_cap_ramp_up_when_on_rate"] = \
            ramp_up_when_on_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_down_when_on_rate"]
                       ):
            if row[1] == "gen_commit_cap" and row[2] != ".":
                ramp_down_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "gen_commit_cap_ramp_down_when_on_rate"] = \
            ramp_down_when_on_rate

    # Up and down time limits are optional, will default to 1 if not specified
    if "min_up_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components[
                           "min_up_time_hours"]
                       ):
            if row[1] == "gen_commit_cap" and row[2] != ".":
                min_up_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "gen_commit_cap_min_up_time_hours"] = \
            min_up_time

    if "min_down_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components[
                           "min_down_time_hours"]
                       ):
            if row[1] == "gen_commit_cap" and row[2] != ".":
                min_down_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "gen_commit_cap_min_down_time_hours"] = \
            min_down_time


def export_module_specific_results(mod, d, scenario_directory, subproblem, stage):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "dispatch_capacity_commit.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "balancing_type_project",
                         "horizon", "timepoint", "timepoint_weight",
                         "number_of_hours_in_timepoint",
                         "technology", "load_zone",
                         "power_mw", "committed_mw", "committed_units"
                         ])

        for (p, tmp) \
                in mod. \
                GEN_COMMIT_CAP_OPR_TMPS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.balancing_type_project[p],
                mod.horizon[tmp, mod.balancing_type_project[p]],
                tmp,
                mod.timepoint_weight[tmp],
                mod.number_of_hours_in_timepoint[tmp],
                mod.technology[p],
                mod.load_zone[p],
                value(mod.GenCommitCap_Provide_Power_MW[p, tmp]),
                value(mod.Commit_Capacity_MW[p, tmp]),
                value(mod.Commit_Capacity_MW[p, tmp]) /
                mod.gen_commit_cap_unit_size_mw[p]
            ])


# Database
###############################################################################
def import_module_specific_results_to_database(
        scenario_id, subproblem, stage, c, db, results_directory
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c: 
    :param db: 
    :param results_directory: 
    :return: 
    """
    print("project dispatch capacity commit")

    # dispatch_capacity_commit.csv
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_dispatch_capacity_commit",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(
            results_directory, "dispatch_capacity_commit.csv"), "r") \
            as cc_dispatch_file:
        reader = csv.reader(cc_dispatch_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            balancing_type_project = row[2]
            horizon = row[3]
            timepoint = row[4]
            timepoint_weight = row[5]
            number_of_hours_in_timepoint = row[6]
            load_zone = row[8]
            technology = row[7]
            power_mw = row[9]
            committed_mw = row[10]
            committed_units = row[11]
            results.append(
                (scenario_id, project, period, subproblem, stage,
                    balancing_type_project, horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology,
                    power_mw, committed_mw, committed_units)
            )
    insert_temp_sql = """
        INSERT INTO temp_results_project_dispatch_capacity_commit{}
        (scenario_id, project, period, subproblem_id, stage_id, 
        balancing_type_project, horizon, timepoint,
        timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, technology, power_mw, committed_mw, 
        committed_units)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_dispatch_capacity_commit
        (scenario_id, project, period, subproblem_id, stage_id,
        balancing_type_project, horizon, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint, load_zone, technology, power_mw, 
        committed_mw, committed_units)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        balancing_type_project, horizon, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint, load_zone, technology, power_mw, 
        committed_mw, committed_units
        FROM temp_results_project_dispatch_capacity_commit{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


# Validation
###############################################################################
def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    validation_results = []

    c = conn.cursor()
    projects = c.execute(
        """SELECT project, operational_type,
        min_stable_level, unit_size_mw,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, operational_type,
        min_stable_level, unit_size_mw,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}) as prj_chars
        USING (project)
        WHERE project_portfolio_scenario_id = {}
        AND operational_type = '{}'""".format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            "gen_commit_cap"
        )
    )

    df = pd.DataFrame(
        data=projects.fetchall(),
        columns=[s[0] for s in projects.description]
    )

    # Check that unit size and min stable level are specified
    # (not all operational types require this input)
    req_columns = [
        "min_stable_level",
        "unit_size_mw"
    ]
    validation_errors = check_req_prj_columns(df, req_columns, True,
                                          "Dispatchable_capacity_commit")
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "Missing inputs",
             error
             )
        )

    # Check that there are no unexpected operational inputs
    expected_na_columns = [
        "charging_efficiency", "discharging_efficiency",
        "minimum_duration_hours"
    ]
    validation_errors = check_req_prj_columns(df, expected_na_columns, False,
                                          "Dispatchable_capacity_commit")
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "Unexpected inputs",
             error
             )
        )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)
