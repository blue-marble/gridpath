#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This operational types describes generation projects that can be turned on and
off, i.e. that have binary commitment variables associated with them. This is
particularly useful for production cost modeling approaches where capturing
the unit commitment decisions is important, e.g. when modeling a slow-starting
coal plant. This operational type is not compatible with new-build capacity
types (e.g. gen_new_lin) where the available capacity is an endogenous decision
variable.

The optimization makes commitment and power output decisions in every
timepoint. If the project is not committed (or starting up / shutting down),
power output is zero. If it is committed, power output can vary between a
pre-specified minimum stable level (greater than zero) and the project's
available capacity. Heat rate degradation below full load is considered.
These projects can be allowed to provide upward and/or downward reserves.

Startup and/or shutdown trajectories can be optionally modeled by specifying a
low startup and/or shutdown ramp rate.  Ramp rate limits as well us minimum up
and down time constraints are implemented. Starts and stops -- and the
associated cost and emissions -- can be tracked and constrained.

Costs for this operational type include fuel costs, variable O&M costs, and
startup and shutdown costs.

Interesting background papers:
- "Hidden power system inflexibilities imposed by traditional unit commitment
formulations", Morales-Espana et al. (2017).
- "Tight and compact MILP formulation for the thermal unit commitment problem",
Morales-Espana et al. (2013).

"""


from __future__ import division

from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Param, Constraint, NonNegativeReals, \
    Binary, PercentFraction, Expression, value

from gridpath.auxiliary.auxiliary import generator_subset_init, \
    check_req_prj_columns, write_validation_to_database,\
    validate_startup_shutdown_rate_inputs
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints, update_dispatch_results_table
from gridpath.project.common_functions import \
    check_if_linear_horizon_first_timepoint,\
    check_if_linear_horizon_last_timepoint


def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_COMMIT_BIN`                                                |
    |                                                                         |
    | The set of generators of the :code:`gen_commit_bin` operational type.   |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_BIN_STR_RMP_PRJS`                                   |
    | | *within*: :code:`GEN_COMMIT_BIN`                                      |
    |                                                                         |
    | The set of generators of the :code:`gen_commit_bin` operational type    |
    | that also have startup ramp rates specified.                            |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_BIN_STR_RMP_PRJS_TYPES`                             |
    |                                                                         |
    | Two-dimensional set of generators of the the :code:`gen_commit_bin`     |
    | and their startup types (if the project is in                           |
    | :code:`GEN_COMMIT_BIN_STR_RMP_PRJS`). Startup types are ordered from    |
    | hottest to coldest, e.g. if there are 3 startup types the hottest start |
    | is indicated by 1, and the coldest start is indicated by 3.             |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_BIN_OPR_TMPS`                                       |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_commit_bin`       |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_BIN_OPR_TMPS_FUEL_SEG`                              |
    |                                                                         |
    | Three-dimensional set with generators of the :code:`gen_commit_bin`     |
    | operational type, their operational timepoints, and their fuel          |
    | segments (if the project is in :code:`FUEL_PROJECTS`).                  |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES`                             |
    |                                                                         |
    | Three-dimensional set with generators of the :code:`gen_commit_bin`     |
    | operational type, their operational timepoints, and their startup       |
    | types (if the project is in :code:`GEN_COMMIT_BIN_STR_RMP_PRJS`).       |
    +-------------------------------------------------------------------------+
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_BIN_STR_TYPES_BY_PRJ  `                             |
    | | *Defined over*: :code:`GEN_COMMIT_BIN`                                |
    |                                                                         |
    | Indexed set that describes the startup types for each project of the    |
    | :code:`gen_commit_bin`operational type.                                 |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_commit_bin_min_stable_level_fraction`                      |
    | | *Defined over*: :code:`GEN_COMMIT_BIN`                                |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The minimum stable level of this project as a fraction of its capacity. |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_commit_bin_ramp_up_when_on_rate`                           |
    | | *Defined over*: :code:`GEN_COMMIT_BIN`                                |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's upward ramp rate limit during operations, defined as a    |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_bin_ramp_down_when_on_rate`                         |
    | | *Defined over*: :code:`GEN_COMMIT_BIN`                                |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's downward ramp rate limit during operations, defined as a  |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_bin_startup_plus_ramp_up_rate`                      |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_STR_RMP_PRJS_TYPES`             |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's upward ramp rate limit during startup for a given         |
    | startup type, defined as a fraction of its capacity per minute. If,     |
    | after adjusting for timepoint duration, this is smaller than the        |
    | minimum stable level, the project will have a startup trajectory across |
    | multiple timepoints.                                                    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_bin_shutdown_plus_ramp_down_rate`                   |
    | | *Defined over*: :code:`GEN_COMMIT_BIN`                                |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's downward ramp rate limit during startup, defined as a     |
    | fraction of its capacity per minute. If, after adjusting for timepoint  |
    | duration, this is smaller than the minimum stable level, the project    |
    | will have a shutdown trajectory across multiple timepoitns.             |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_bin_min_up_time_hrs`                                |
    | | *Defined over*: :code:`GEN_COMMIT_BIN`                                |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The project's minimum up time in hours.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_bin_min_down_time_hrs`                              |
    | | *Defined over*: :code:`GEN_COMMIT_BIN`                                |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The project's minimum down time in hours.                               |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_bin_startup_cost_per_mw`                            |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_STR_RMP_PRJS_TYPES`             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The project's startup cost per MW of capacity that is started up for a  |
    | for a given startup type.                                               |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_bin_shutdown_cost_per_mw`                           |
    | | *Defined over*: :code:`GEN_COMMIT_BIN`                                |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The project's shutdown cost per MW of capacity that is shut down.       |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_bin_startup_fuel_mmbtu_per_mw`                      |
    | | *Defined over*: :code:`GEN_COMMIT_BIN`                                |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The project's startup fuel burn in MMBtu per MW of capacity that is     |
    | started up.                                                             |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_bin_down_time_cutoff_hours`                         |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_STR_RMP_PRJS_TYPES`             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's minimum down time cutoff to activate a given startup      |
    | type. If the unit has been down for more hours than this cutoff, the    |
    | relevant startup type will be activated. E.g. if a unit has 2 startup   |
    | types (hot and cold) with respective cutoffs of 4 hours and 8 hours, it |
    | means that startup type 1 (the hot start) will be activated if the unit |
    | starts after a down time between 4-8 hours, and startup type 2 (the     |
    | cold start) will be activated if the unit starts after a down time of   |
    | over 8 hours. The cutoff for the hottest start must match the unit's    |
    | minimum down time. If the unit is fast-start without a minimum down     |
    | time, the user should input zero (rather than NULL)                     |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`GenCommitBin_Commit`                                           |
    | | *Within*: :code:`Binary`                                              |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Binary variable which represents the commitment decision in each        |
    | operational timepoint. It is one if the unit is committed and zero      |
    | otherwise (including during a startup and shutdown trajectory).         |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Startup`                                          |
    | | *Within*: :code:`Binary`                                              |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Binary variable which is one if the unit starts up and zero otherwise.  |
    | A startup is defined as changing commitment from zero to one.           |
    | Note: this variable is zero throughout a startup trajectory!            |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Startup_Type`                                     |
    | | *Within*: :code:`Binary`                                              |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | Binary variable which is one if the unit starts up for the given        |
    | startup type and zero otherwise. A startup is defined as changing       |
    | commitment from zero to one, whereas the startup type indicates the     |
    | hotness/coldness of the start. Note: this variable is zero throughout   |
    | a startup trajectory!                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Shutdown`                                         |
    | | *Within*: :code:`Binary`                                              |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Binary variable which is one if the unit shuts down and zero otherwise. |
    | A shutdown is defined as changing commitment from one to zero.          |
    | Note: this variable is zero throughout a shutdown trajectory!           |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Synced`                                           |
    | | *Within*: :code:`Binary`                                              |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Binary variable which is one if the project is providing *any* power (  |
    | either because it is committed or because it is in a startup or shutdown|
    | trajectory), and zero otherwise.                                        |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Provide_Power_Above_Pmin_MW`                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Power provision above the minimum stable level in MW from this project  |
    | in each timepoint in which the project is committed.                    |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Provide_Power_Startup_MW`                         |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | Power provision during startup in each timepoint in which the project   |
    | is starting up, for each startup type (zero if project is committed or  |
    | not starting up).                                                       |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Provide_Power_Shutdown_MW`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Power provision during shutdown in each timepoint in which the project  |
    | is shutting down (zero if project is committed or not shutting down).   |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Fuel_Burn_MMBTU`                                  |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_FUEL_PRJ_OPR_TMPS`              |
    |                                                                         |
    | Fuel burn in MMBTU by this project in each operational timepoint.       |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`GenCommitBin_Pmax_MW`                                          |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's maximum power output (in MW) if the unit was committed.   |
    | Depends on the project's availability and capacity in the timepoint.    |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Pmin_MW`                                          |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's minimum power output (in MW) if the unit was committed.   |
    | Depends on the project's availability and capacity in the timepoint,    |
    | and the minimum stable level.                                           |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Provide_Power_MW`                                 |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's total power output (in MW) in each operational timepoint, |
    | including power from a startup or shutdown trajectory.                  |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Ramp_Up_Rate_MW_Per_Tmp`                          |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's upward ramp-able capacity (in MW) in each operational     |
    | timepoint. Depends on the :code:`gen_commit_bin_ramp_up_when_on_rate`,  |
    | the availability and capacity in the timepoint, and the timepoint's     |
    | duration.                                                               |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Ramp_Down_Rate_MW_Per_Tmp`                        |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's downward ramp-able capacity (in MW) in each operationa    |
    | timepoint. Depends on the :code:`gen_commit_bin_ramp_down_when_on_rate` |
    | , the availability and capacity in the timepoint, and the timepoint's   |
    | duration.                                                               |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Startup_Ramp_Rate_MW_Per_Tmp`                     |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | The project's upward ramp-able capacity (in MW) during startup in each  |
    | operational timepoint. Depends on the                                   |
    | :code:`gen_commit_bin_startup_plus_ramp_up_rate`, the availability and  |
    | capacity in the timepoint, and the timepoint's duration.                |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Shutdown_Ramp_Rate_MW_Per_Tmp`                    |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's downward ramp-able capacity (in MW) during shutdown in    |
    | each operational timepoint. Depends on the                              |
    | :code:`gen_commit_bin_shutdown_plus_ramp_down_rate`, the availability   |
    | and capacity in the timepoint, and the timepoint's duration.            |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Active_Startup_Type          `                    |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's active startup type in each operational timepoint,        |
    | described as an integer. If no startup type is active (the project is   |
    | not starting up in this timepoint), this expression returns zero.       |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Upwards_Reserves_MW`                              |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's total upward reserves offered (in MW) in each timepoint.  |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Downwards_Reserves_MW`                            |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's total downward reserves offered (in MW) in each timepoint.|
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | Commitment                                                              |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Binary_Logic_Constraint`                          |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Defines the relationship between the binary commitment, startup, and    |
    | shutdown variables. When the commitment changes from zero to one, the   |
    | startup variable is one, when it changes from one to zero, the shutdown |
    | variable is one.                                                        |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Synced_Constraint`                                |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Sets the GenCommitBin_Synced variable to one if the project is          |
    | providing  *any* power (either because it is committed or because it is |
    | in a startup or shutdown trajectory), and zero otherwise.               |
    +-------------------------------------------------------------------------+
    | Power                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Max_Power_Constraint`                             |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits the power plus upward reserves to the available capacity.        |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Min_Power_Constraint`                             |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Power provision minus downward reserves should exceed the minimum       |
    | stable level for the project.                                           |
    +-------------------------------------------------------------------------+
    | Minimum Up and Down Time                                                |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Min_Up_Time_Constraint`                           |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Requires that when the project is started, it stays on for at least     |
    | :code:`gen_commit_bin_min_up_time_hrs`.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Min_Down_Time_Constraint`                         |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Requires that when the project is shut down, it stays off for at least  |
    | :code:`gen_commit_bin_min_up_time_hrs`.                                 |
    +-------------------------------------------------------------------------+
    | Ramps                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Ramp_Up_Constraint`                               |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project upward ramp during operations based on the   |
    | :code:`gen_commit_bin_ramp_up_when_on_rate`.                            |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Ramp_Down_Constraint`                             |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project downward ramp during operations based on the |
    | :code:`gen_commit_bin_ramp_down_when_on_rate`.                          |
    +-------------------------------------------------------------------------+
    | Startup Power                                                           |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Unique_Startup_Type_Constraint`                   |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Ensures that only one startup type can be active at the same time.      |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Active_Startup_Type_Constraint`                   |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | Ensures that a startup type can only be active if the unit has been     |
    | down for the appropriate interval.                                      |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Max_Startup_Power_Constraint`                     |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits startup power to zero when the project is committed and to the   |
    | minimum stable level when it is not committed.                          |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Ramp_During_Startup_Constraint`                   |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | Limits the allowed project upward startup power ramp based on the       |
    | :code:`gen_commit_bin_startup_plus_ramp_up_rate`.                       |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Increasing_Startup_Power_Constraint`              |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | Requires that the startup power always increases, except for the        |
    | startup timepoint (when :code:`GenCommitBin_Startup` is one).           |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Power_During_Startup_Constraint`                  |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | Limits the difference between the power provision in the startup        |
    | timepoint and the startup power in the previous timepoint based on the  |
    | :code:`gen_commit_bin_startup_plus_ramp_up_rate`.                       |
    +-------------------------------------------------------------------------+
    | Shutdown Power                                                          |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Max_Shutdown_Power_Constraint`                    |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits shutdown power to zero when the project is committed and to the  |
    | minimum stable level when it is not committed.                          |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Ramp_During_Shutdown_Constraint`                  |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project downward shutdown power ramp based on the    |
    | :code:`gen_commit_bin_shutdown_plus_ramp_down_rate`.                    |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Decreasing_Shutdown_Power_Constraint`             |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Requires that the shutdown power always decreases, except for the       |
    | shutdown timepoint (when :code:`GenCommitBin_Shutdown` is one).         |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Power_During_Shutdown_Constraint`                 |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits the difference between the power provision in the shutdown       |
    | timepoint and the shutdown power in the next timepoint based on the     |
    | :code:`gen_commit_bin_shutdown_plus_ramp_down_rate`.                    |
    +-------------------------------------------------------------------------+
    | Fuel Burn                                                               |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitBin_Fuel_Burn_Constraint`                             |
    | | *Defined over*: :code:`GEN_COMMIT_BIN_OPR_TMPS_FUEL_SEG`              |
    |                                                                         |
    | Determines fuel burn from the project in each timepoint based on its    |
    | heat rate curve.                                                        |
    +-------------------------------------------------------------------------+
    """

    # Sets
    ###########################################################################

    m.GEN_COMMIT_BIN = Set(
        within=m.PROJECTS,
        initialize=generator_subset_init("operational_type", "gen_commit_bin")
    )

    m.GEN_COMMIT_BIN_OPR_TMPS = Set(
        dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            if g in mod.GEN_COMMIT_BIN)
    )

    m.GEN_COMMIT_BIN_OPR_TMPS_FUEL_SEG = Set(
        dimen=3,
        within=m.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
        set((g, tmp, s) for (g, tmp, s)
            in mod.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS
            if g in mod.GEN_COMMIT_BIN)
    )

    m.GEN_COMMIT_BIN_STR_RMP_PRJS = Set(
        within=m.GEN_COMMIT_BIN
    )

    m.GEN_COMMIT_BIN_STR_RMP_PRJS_TYPES = Set(
        dimen=2,
        ordered=True
    )

    m.GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES = Set(
        dimen=3,
        rule=lambda mod:
        set((g, tmp, s) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            for _g, s in mod.GEN_COMMIT_BIN_STR_RMP_PRJS_TYPES
            if g == _g)
    )

    m.GEN_COMMIT_BIN_STR_TYPES_BY_PRJ = Set(
        m.GEN_COMMIT_BIN,
        initialize=get_startup_types_by_project,
        ordered=True
    )

    # Required Params
    ###########################################################################
    m.gen_commit_bin_min_stable_level_fraction = Param(
        m.GEN_COMMIT_BIN,
        within=PercentFraction
    )

    # Optional Params
    ###########################################################################

    m.gen_commit_bin_ramp_up_when_on_rate = Param(
        m.GEN_COMMIT_BIN,
        within=PercentFraction, default=1
    )
    m.gen_commit_bin_ramp_down_when_on_rate = Param(
        m.GEN_COMMIT_BIN,
        within=PercentFraction, default=1
    )
    m.gen_commit_bin_startup_plus_ramp_up_rate = Param(
        m.GEN_COMMIT_BIN_STR_RMP_PRJS_TYPES,
        within=PercentFraction, default=1
    )
    m.gen_commit_bin_shutdown_plus_ramp_down_rate = Param(
        m.GEN_COMMIT_BIN,
        within=PercentFraction, default=1
    )

    m.gen_commit_bin_min_up_time_hrs = Param(
        m.GEN_COMMIT_BIN,
        within=NonNegativeReals, default=0
    )
    m.gen_commit_bin_min_down_time_hrs = Param(
        m.GEN_COMMIT_BIN,
        within=NonNegativeReals, default=0
    )

    m.gen_commit_bin_startup_cost_per_mw = Param(
        m.GEN_COMMIT_BIN_STR_RMP_PRJS_TYPES,
        within=NonNegativeReals,
        default=0
    )
    m.gen_commit_bin_shutdown_cost_per_mw = Param(
        m.GEN_COMMIT_BIN,
        within=NonNegativeReals,
        default=0
    )
    m.gen_commit_bin_startup_fuel_mmbtu_per_mw = Param(
        m.GEN_COMMIT_BIN,
        within=NonNegativeReals,
        default=0
    )

    m.gen_commit_bin_down_time_cutoff_hours = Param(
        m.GEN_COMMIT_BIN_STR_RMP_PRJS_TYPES,
        within=NonNegativeReals
    )

    # Variables
    ###########################################################################

    m.GenCommitBin_Commit = Var(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        within=Binary
    )

    m.GenCommitBin_Startup = Var(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        within=Binary
    )

    m.GenCommitBin_Startup_Type = Var(
        m.GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES,
        within=Binary
    )

    m.GenCommitBin_Shutdown = Var(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        within=Binary
    )

    m.GenCommitBin_Synced = Var(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        within=Binary
    )

    m.GenCommitBin_Provide_Power_Above_Pmin_MW = Var(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        within=NonNegativeReals
    )

    m.GenCommitBin_Provide_Power_Startup_MW = Var(
        m.GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES,
        within=NonNegativeReals
    )

    m.GenCommitBin_Provide_Power_Shutdown_MW = Var(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        within=NonNegativeReals
    )

    m.GenCommitBin_Fuel_Burn_MMBTU = Var(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        within=NonNegativeReals
    )

    # Expressions
    ###########################################################################

    m.GenCommitBin_Pmax_MW = Expression(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=pmax_rule
    )

    m.GenCommitBin_Pmin_MW = Expression(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=pmin_rule
    )

    m.GenCommitBin_Provide_Power_MW = Expression(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=provide_power_rule
    )

    m.GenCommitBin_Ramp_Up_Rate_MW_Per_Tmp = Expression(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=ramp_up_rate_rule
    )

    m.GenCommitBin_Ramp_Down_Rate_MW_Per_Tmp = Expression(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=ramp_down_rate_rule
    )

    m.GenCommitBin_Startup_Ramp_Rate_MW_Per_Tmp = Expression(
        m.GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES,
        rule=startup_ramp_rate_rule
    )

    m.GenCommitBin_Shutdown_Ramp_Rate_MW_Per_Tmp = Expression(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=shutdown_ramp_rate_rule
    )

    m.GenCommitBin_Active_Startup_Type = Expression(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=active_startup_rule
    )

    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])
    m.GenCommitBin_Upwards_Reserves_MW = Expression(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=upwards_reserve_rule
    )

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])
    m.GenCommitBin_Downwards_Reserves_MW = Expression(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=downwards_reserve_rule
    )

    # Constraints
    ###########################################################################

    # Commitment
    m.GenCommitBin_Binary_Logic_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=binary_logic_constraint_rule
    )

    m.GenCommitBin_Synced_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=synced_constraint_rule
    )

    # Power
    m.GenCommitBin_Max_Power_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=max_power_constraint_rule
    )

    m.GenCommitBin_Min_Power_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=min_power_constraint_rule
    )

    # Minimum Up and Down Time
    m.GenCommitBin_Min_Up_Time_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=min_up_time_constraint_rule
    )

    m.GenCommitBin_Min_Down_Time_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=min_down_time_constraint_rule
    )

    # Ramps
    m.GenCommitBin_Ramp_Up_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=ramp_up_constraint_rule
    )

    m.GenCommitBin_Ramp_Down_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=ramp_down_constraint_rule
    )

    # Startup Power
    m.GenCommitBin_Unique_Startup_Type_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=unique_startup_type_constraint_rule
    )

    m.GenCommitBin_Active_Startup_Type_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES,
        rule=active_startup_type_constraint_rule
    )

    m.GenCommitBin_Max_Startup_Power_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=max_startup_power_constraint_rule
    )

    m.GenCommitBin_Ramp_During_Startup_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES,
        rule=ramp_during_startup_constraint_rule
    )

    m.GenCommitBin_Increasing_Startup_Power_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES,
        rule=increasing_startup_power_constraint_rule
    )

    m.GenCommitBin_Power_During_Startup_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES,
        rule=power_during_startup_constraint_rule
    )

    # Shutdown Power
    m.GenCommitBin_Max_Shutdown_Power_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=max_shutdown_power_constraint_rule
    )

    m.GenCommitBin_Ramp_During_Shutdown_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=ramp_during_shutdown_constraint_rule
    )

    m.GenCommitBin_Decreasing_Shutdown_Power_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=decreasing_shutdown_power_constraint_rule
    )

    m.GenCommitBin_Power_During_Shutdown_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS,
        rule=power_during_shutdown_constraint_rule
    )

    # Fuel Burn
    m.GenCommitBin_Fuel_Burn_Constraint = Constraint(
        m.GEN_COMMIT_BIN_OPR_TMPS_FUEL_SEG,
        rule=fuel_burn_constraint_rule
    )


# Set Rules
###############################################################################

def get_startup_types_by_project(mod, g):
    """
    Get indexed set of startup types by project, ordered from hottest to
    coldest.
    """
    types = [s for (_g, s) in mod.GEN_COMMIT_BIN_STR_RMP_PRJS_TYPES
             if g == _g]
    return types


# Expression Rules
###############################################################################

def pmax_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitBin_Pmax_MW
    **Defined Over**: GEN_COMMIT_BIN_OPR_TMPS
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def pmin_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitBin_Pmin_MW
    **Defined Over**: GEN_COMMIT_BIN_OPR_TMPS
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp] \
        * mod.gen_commit_bin_min_stable_level_fraction[g]


def provide_power_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitBin_Provide_Power_MW
    **Defined Over**: GEN_COMMIT_BIN_OPR_TMPS
    """
    return mod.GenCommitBin_Provide_Power_Above_Pmin_MW[g, tmp] \
        + mod.GenCommitBin_Pmin_MW[g, tmp] \
        * mod.GenCommitBin_Commit[g, tmp] \
        + sum(mod.GenCommitBin_Provide_Power_Startup_MW[g, tmp, s]
              for s in mod.GEN_COMMIT_BIN_STR_TYPES_BY_PRJ[g]) \
        + mod.GenCommitBin_Provide_Power_Shutdown_MW[g, tmp]


def ramp_up_rate_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitBin_Ramp_Up_Rate_MW_Per_Tmp
    **Defined Over**: GEN_COMMIT_BIN_OPR_TMPS

    Ramp up rate limit in MW per timepoint, derived from input ramp rate
    which is given in fraction of installed capacity per minute. Longer
    timepoints will lead to a larger ramp up rate limit, since ramping
    can take place over a longer duration.
    Unit check:
        capacity [MW]
        * availability [unit-less]
        * ramp up rate [1/min]
        * hours in timepoint [hours/timepoint]
        * minutes per hour [min/hour]
        = ramp up rate [MW/timepoint]
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp] \
        * mod.gen_commit_bin_ramp_up_when_on_rate[g] \
        * mod.number_of_hours_in_timepoint[tmp] \
        * 60  # convert min to hours


def ramp_down_rate_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitBin_Ramp_Down_Rate_MW_Per_Tmp
    **Defined Over**: GEN_COMMIT_BIN_OPR_TMPS

    Ramp down rate limit in MW per timepoint, derived from input ramp rate
    which is given in fraction of installed capacity per minute. Longer
    timepoints will lead to a larger ramp down rate limit, since ramping
    can take place over a longer duration.
    Unit check:
        capacity [MW]
        * availability [unit-less]
        * ramp down rate [1/min]
        * hours in timepoint [hours/timepoint]
        * minutes per hour [min/hour]
        = ramp down rate [MW/timepoint]
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp] \
        * mod.gen_commit_bin_ramp_down_when_on_rate[g] \
        * mod.number_of_hours_in_timepoint[tmp] \
        * 60  # convert min to hours


def startup_ramp_rate_rule(mod, g, tmp, s):
    """
    **Expression Name**: GenCommitBin_Startup_Ramp_Rate_MW_Per_Tmp
    **Defined Over**: GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp] \
        * min(mod.gen_commit_bin_startup_plus_ramp_up_rate[g, s]
              * mod.number_of_hours_in_timepoint[tmp]
              * 60, 1)


def shutdown_ramp_rate_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitBin_Shutdown_Ramp_Rate_MW_Per_Tmp
    **Defined Over**: GEN_COMMIT_BIN_OPR_TMPS
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp] \
        * min(mod.gen_commit_bin_shutdown_plus_ramp_down_rate[g]
              * mod.number_of_hours_in_timepoint[tmp]
              * 60, 1)


def active_startup_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitBin_Active_Startup_Type
    **Defined Over**: GEN_COMMIT_BIN_OPR_TMPS
    """
    return (sum(mod.GenCommitBin_Startup_Type[g, tmp, s] * s
                for s in mod.GEN_COMMIT_BIN_STR_TYPES_BY_PRJ[g])
            if g in mod.GEN_COMMIT_BIN_STR_RMP_PRJS else 0)

# Constraint Formulation Rules
###############################################################################

# Commitment
def binary_logic_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Binary_Logic_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    If commit status changes, unit is turning on or shutting down.
    The *GenCommitBin_Startup* variable is 1 for the first timepoint the unit
    is committed after being offline; it will be able to provide power in that
    timepoint. The *GenCommitBin_Shutdown* variable is 1 for the first
    timepoint the unit is not committed after being online; it will not be
    able to provide power in that timepoint.

    Constraint (8) in Morales-Espana et al. (2013)
    """

    # TODO: if we can link horizons, input commit from previous horizon's
    #  last timepoint rather than skipping the constraint
    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    else:
       return mod.GenCommitBin_Commit[g, tmp] \
              - mod.GenCommitBin_Commit[
                  g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]] \
              == mod.GenCommitBin_Startup[g, tmp] - mod.GenCommitBin_Shutdown[g, tmp]


def synced_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Synced_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    Synced is 1 if the unit is committed, starting, or stopping and zero
    otherwise.
    """
    return mod.GenCommitBin_Synced[g, tmp] \
        >= mod.GenCommitBin_Commit[g, tmp] \
        + (sum(mod.GenCommitBin_Provide_Power_Startup_MW[g, tmp, s]
               for s in mod.GEN_COMMIT_BIN_STR_TYPES_BY_PRJ[g])
           + mod.GenCommitBin_Provide_Power_Shutdown_MW[g, tmp]) \
        / mod.GenCommitBin_Pmin_MW[g, tmp]


# Power
def max_power_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Max_Power_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    Power provision plus upward reserves shall not exceed maximum power.
    """
    return \
        (mod.GenCommitBin_Provide_Power_Above_Pmin_MW[g, tmp]
         + mod.GenCommitBin_Upwards_Reserves_MW[g, tmp]) \
        <= \
        (mod.GenCommitBin_Pmax_MW[g, tmp]
         - mod.GenCommitBin_Pmin_MW[g, tmp]) \
        * mod.GenCommitBin_Commit[g, tmp]


def min_power_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Min_Power_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    Power minus downward services cannot be below minimum stable level.
    This constraint is not in Morales-Espana et al. (2013) because they
    don't look at downward reserves. In that case, enforcing
    provide_power_above_pmin to be within NonNegativeReals is sufficient.
    """
    return mod.GenCommitBin_Provide_Power_Above_Pmin_MW[g, tmp] - \
        mod.GenCommitBin_Downwards_Reserves_MW[g, tmp] \
        >= 0


# Minimum Up and Down Time
def min_up_time_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Min_Up_Time_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    When units are started, they have to stay on for a minimum number
    of hours described by the gen_commit_bin_min_up_time_hrs parameter.
    The constraint is enforced by ensuring that the binary commitment
    is at least as large as the number of unit starts within min up time
    hours.

    We ensure a unit turned on less than the minimum up time ago is
    still on in the current timepoint *tmp* by checking how much units
    were turned on in each 'relevant' timepoint (i.e. a timepoint that
    begins more than or equal to gen_commit_bin_min_up_time_hrs ago
    relative to the start of timepoint *tmp*) and then summing those
    starts.

    If using linear horizon boundaries, the constraint is skipped for all
    timepoints less than min up time hours from the start of the timepoint's
    horizon because the constraint for the first included timepoint
    will sufficiently constrain the binary start variables of all the
    timepoints before it.

    Constraint (6) in Morales-Espana et al. (2013)

    Example 1:
      min_up_time = 4; tmps = [0,1,2,3];
      hours_in_tmps = [1,3,1,1];
      tmp = 2; relevant_tmps = [1,2]
      --> if there is a start in tmp 1, you have to be committed in tmp 2
      --> starts in all other tmps (incl. tmp 0) don't affect tmp 2
    Example 2:
      min_up_time = 4; tmps = [0,1,2,3];
      hours_in_tmps = [1,4,1,1];
      tmp = 2; relevant_tmps = [2]
      --> start in t1 does not affect state of t2; tmp 1 is 4 hrs long
      --> so even if you start in tmp 1 you can stop again in tmp 2
      --> The constraint simply ensures that the unit is committed if
      --> it is turned on.
    Example 3:
      min_up_time = 4; tmps = [0,1,2,3];
      hours_in_tmps = [1,1,1,1];
      tmp = 2; relevant_tmps = [0,1,2,3]
      --> if there is a start in tmp 0, 1, 2, or 3, you have to be committed
      --> in tmp 2. The unit either has to be on for all timepoints, or off
      --> for all timepoints
    """

    relevant_tmps = determine_relevant_timepoints(
        mod, g, tmp, mod.gen_commit_bin_min_up_time_hrs[g]
    )

    number_of_starts_min_up_time_or_less_hours_ago = \
        sum(mod.GenCommitBin_Startup[g, tp] for tp in relevant_tmps)

    # If we've reached the first timepoint in linear boundary mode and
    # the total duration of the relevant timepoints (which includes *tmp*)
    # is less than the minimum up time, skip the constraint since the next
    # timepoint's constraint will already cover these same timepoints.
    # Don't skip if this timepoint is the last timepoint of the horizon
    # (since there will be no next timepoint).
    if (mod.boundary[
        mod.balancing_type_project[g],
        mod.horizon[tmp, mod.balancing_type_project[g]]
    ] == "linear"
            and
            relevant_tmps[-1]
            == mod.first_horizon_timepoint[
                mod.balancing_type_project[g],
                mod.horizon[tmp, mod.balancing_type_project[g]]
            ]
            and
            sum(mod.number_of_hours_in_timepoint[t] for t in relevant_tmps)
            < mod.gen_commit_bin_min_up_time_hrs[g]
            and
            tmp != mod.last_horizon_timepoint[
                mod.balancing_type_project[g],
                mod.horizon[tmp, mod.balancing_type_project[g]]
            ]):
        return Constraint.Skip
    # Otherwise, if there was a start min_up_time or less ago, the unit has
    # to remain committed.
    else:
        return mod.GenCommitBin_Commit[g, tmp] \
            >= number_of_starts_min_up_time_or_less_hours_ago


def min_down_time_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Min_Down_Time_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    When units are shut down, they have to stay off for a minimum number
    of hours described by the gen_commit_bin_min_down_time_hrs parameter.
    The constraint is enforced by ensuring that (1-binary commitment)
    is at least as large as the number of unit shutdowns within min down
    time hours.

    We ensure a unit shut down less than the minimum up time ago is
    still off in the current timepoint *tmp* by checking how much units
    were shut down in each 'relevant' timepoint (i.e. a timepoint that
    begins more than or equal to gen_commit_bin_min_down_time_hrs ago
    relative to the start of timepoint *tmp*) and then summing those
    shutdowns.

    If using linear horizon boundaries, the constraint is skipped for all
    timepoints less than min down time hours from the start of the
    timepoint's horizon because the constraint for the first included
    timepoint will sufficiently constrain the binary stop variables of all
    the timepoints before it.

    Constraint (7) in Morales-Espana et al. (2013)
    """

    relevant_tmps = determine_relevant_timepoints(
        mod, g, tmp, mod.gen_commit_bin_min_down_time_hrs[g]
    )

    number_of_stops_min_down_time_or_less_hours_ago = \
        sum(mod.GenCommitBin_Shutdown[g, tp] for tp in relevant_tmps)

    # If we've reached the first timepoint in linear boundary mode and
    # the total duration of the relevant timepoints (which includes *tmp*)
    # is less than the minimum down time, skip the constraint since the
    # next timepoint's constraint will already cover these same timepoints.
    # Don't skip if this timepoint is the last timepoint of the horizon
    # (since there will be no next timepoint).
    if (mod.boundary[
        mod.balancing_type_project[g],
        mod.horizon[tmp, mod.balancing_type_project[g]]
    ] == "linear"
            and
            relevant_tmps[-1]
            == mod.first_horizon_timepoint[
                mod.balancing_type_project[g],
                mod.horizon[tmp, mod.balancing_type_project[g]]
            ]
            and
            sum(mod.number_of_hours_in_timepoint[t] for t in relevant_tmps)
            < mod.gen_commit_bin_min_down_time_hrs[g]
            and
            tmp != mod.last_horizon_timepoint[
                mod.balancing_type_project[g],
                mod.horizon[tmp, mod.balancing_type_project[g]]
            ]):
        return Constraint.Skip
    # Otherwise, if there was a shutdown min_down_time or less ago, the unit
    # has to remain shut down.
    else:
        return 1 - mod.GenCommitBin_Commit[g, tmp] \
            >= number_of_stops_min_down_time_or_less_hours_ago


# Ramps
def ramp_up_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Ramp_Up_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    Difference between power generation of consecutive timepoints has to
    obey ramp up rates.

    We assume that a unit has to reach its setpoint at the start of the
    timepoint; as such, the ramping between 2 timepoints is assumed to
    take place during the duration of the first timepoint, and the
    ramp rate is adjusted for the duration of the first timepoint.
    Constraint (12) in Morales-Espana et al. (2013)
    """
    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    # If ramp rate limits, adjusted for timepoint duration, allow you to
    # ramp up the full operable range between timepoints, constraint
    # won't bind, so skip
    elif (mod.gen_commit_bin_ramp_up_when_on_rate[g] * 60
          * mod.number_of_hours_in_timepoint[
              mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
          >= (1 - mod.gen_commit_bin_min_stable_level_fraction[g])):
        return Constraint.Skip
    else:
        return \
            (mod.GenCommitBin_Provide_Power_Above_Pmin_MW[g, tmp]
             + mod.GenCommitBin_Upwards_Reserves_MW[g, tmp]) \
            - \
            (mod.GenCommitBin_Provide_Power_Above_Pmin_MW[
                 g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
             - mod.GenCommitBin_Downwards_Reserves_MW[
                 g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]) \
            <= \
            mod.GenCommitBin_Ramp_Up_Rate_MW_Per_Tmp[
                g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]


def ramp_down_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Ramp_Down_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    Difference between power generation of consecutive timepoints has to
    obey ramp down rates.
    We assume that a unit has to reach its setpoint at the start of the
    timepoint; as such, the ramping between 2 timepoints is assumed to
    take place during the duration of the first timepoint, and the
    ramp rate is adjusted for the duration of the first timepoint.
    Constraint (13) in Morales-Espana et al. (2013)
    """
    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    # If ramp rate limits, adjusted for timepoint duration, allow you to
    # ramp down the full operable range between timepoints, constraint
    # won't bind, so skip
    elif (mod.gen_commit_bin_ramp_down_when_on_rate[g] * 60
          * mod.number_of_hours_in_timepoint[
              mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
          >= (1 - mod.gen_commit_bin_min_stable_level_fraction[g])):
        return Constraint.Skip
    else:
        return \
            (mod.GenCommitBin_Provide_Power_Above_Pmin_MW[
                 g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
             + mod.GenCommitBin_Upwards_Reserves_MW[
                 g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]) \
            - \
            (mod.GenCommitBin_Provide_Power_Above_Pmin_MW[g, tmp]
             - mod.GenCommitBin_Downwards_Reserves_MW[g, tmp]) \
            <= mod.GenCommitBin_Ramp_Down_Rate_MW_Per_Tmp[
                g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]


# Startup Power
def unique_startup_type_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Unique_Startup_Type_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    Only one startup type can be active (>= 1) at the same time.
    """

    if g not in mod.GEN_COMMIT_BIN_STR_RMP_PRJS:
        return Constraint.Skip

    sum_startup_types = sum(
        mod.GenCommitBin_Startup_Type[g, tmp, s]
        for s in mod.GEN_COMMIT_BIN_STR_TYPES_BY_PRJ[g]
    )

    return sum_startup_types == mod.GenCommitBin_Startup[g, tmp]


def active_startup_type_constraint_rule(mod, g, tmp, s):
    """
    **Constraint Name**: GenCommitBin_Active_Startup_Type_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES

    Startup_type s can only be activated (startup_type >= 1) if the unit has
    previously been down within the appropriate interval. The interval for
    startup type s is defined by the user specified boundary parameters
    mod.gen_commit_bin_down_time_cutoff_hours[s] and
    mod.gen_commit_bin_down_time_cutoff_hours[s+1]. Note that the down time
    interval includes any timepoints during which the unit is starting up.

    For the coldest (last) startup type, there is no s+1 and the
    constraint is skipped. This is okay because the model will select a
    hotter, cheaper startup type if it can and there can only be one
    startup_type active at once (see unique_startup_type_constraint_rule).
    This also means the constraint will be skipped if there is only one
    startup type.

    The constraint works by first determining the relevant timepoints, i.e.
    the timepoints within [TSU,s ; TSU,s+1) hours from *tmp*. If the unit
    has been down in any of these timepoints, we can activate the startup
    variable of the associated startup type for timepoint *tmp* (but only if
    the unit is actually starting in timepoint *tmp*).

    Example: we are in timepoint 7 (hourly resolution) and the down time
    interval is 2-4 hours for a hot start and >=4 hours for a cold start.
    This means timepoints 4 and 5 will be the relevant timepoints (resp. 2
    and 3 hours from *tmp*). A shutdown in any of those timepoints means
    that a start in timepoint 7 would be a hot start.

    See constraint (7) in Morales-Espana et al. (2017).
    """

    # Coldest startup type is un-constrained
    if s == mod.GEN_COMMIT_BIN_STR_TYPES_BY_PRJ[g][-1]:
        return Constraint.Skip

    # Get the timepoints within [TSU,s; TSU,s+1) hours from *tmp*
    relevant_tmps1 = determine_relevant_timepoints(
        mod, g, tmp, mod.gen_commit_bin_down_time_cutoff_hours[g, s])
    relevant_tmps2 = determine_relevant_timepoints(
        mod, g, tmp, mod.gen_commit_bin_down_time_cutoff_hours[g, s+1])
    relevant_tmps = set(relevant_tmps2) - set(relevant_tmps1)

    # Skip constraint if we are within TSU,s hours from the start of the
    # horizon (linear horizon boundary) or from the current tmp (circular
    # horizon boundary). We have no way to know whether unit was down
    # [TSU,s; TSU,s+1) hours ago so we can't know if this start type could
    # be active.
    if len(relevant_tmps) == 0:
        return Constraint.Skip

    # Equal to 1 if unit has been down within interval [TSU,s; TSU,s+1)
    # before hour t. This "activates" this particular startup type
    shutdown_within_interval = \
        sum(mod.GenCommitBin_Shutdown[g, tp] for tp in relevant_tmps)

    return mod.GenCommitBin_Startup_Type[g, tmp, s] <= shutdown_within_interval


def max_startup_power_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Max_Startup_Power_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    Startup power is 0 when the unit is committed and must be less than or
    equal to the minimum stable level when not committed.
    """

    # TODO: make this expression since used in many places?
    total_startup_power = sum(
        mod.GenCommitBin_Provide_Power_Startup_MW[g, tmp, s]
        for s in mod.GEN_COMMIT_BIN_STR_TYPES_BY_PRJ[g]
    )

    return total_startup_power \
        <= (1 - mod.GenCommitBin_Commit[g, tmp]) \
        * mod.GenCommitBin_Pmin_MW[g, tmp]


def ramp_during_startup_constraint_rule(mod, g, tmp, s):
    """
    **Constraint Name**: GenCommitBin_Ramp_During_Startup_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES

    The difference between startup power of consecutive timepoints has to
    obey startup ramp up rates.

    We assume that a unit has to reach its setpoint at the start of the
    timepoint; as such, the ramping between 2 timepoints is assumed to
    take place during the duration of the first timepoint, and the
    ramp rate is adjusted for the duration of the first timepoint.
    """

    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    else:
        return \
            mod.GenCommitBin_Provide_Power_Startup_MW[g, tmp, s] - \
            mod.GenCommitBin_Provide_Power_Startup_MW[g,
                          mod.previous_timepoint[tmp,
                                                 mod
                                                 .balancing_type_project[g]
                                                 ], s
                          ] \
            <= mod.GenCommitBin_Startup_Ramp_Rate_MW_Per_Tmp[
                g, mod.previous_timepoint[tmp,
                                          mod.balancing_type_project[g]], s
            ]


def increasing_startup_power_constraint_rule(mod, g, tmp, s):
    """
    **Constraint Name**: GenCommitBin_Increasing_Startup_Power_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES

    GenCommitBin_Provide_Power_Startup_MW[t] can only be less than
    GenCommitBin_Provide_Power_Startup_MW[t-1] in the starting timepoint (when
    it is is back at 0). In other words, GenCommitBin_Provide_Power_Startup_MW
    can only decrease in the starting timepoint; in all other timepoints it
    should increase or stay constant. This prevents situations in which the
    model can abuse this by providing starting power in some timepoints and
    then reducing power back to 0 without ever committing the unit.
    """
    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    else:
        return \
            mod.GenCommitBin_Provide_Power_Startup_MW[g, tmp, s] - \
            mod.GenCommitBin_Provide_Power_Startup_MW[g,
                          mod.previous_timepoint[tmp,
                                                 mod
                                                 .balancing_type_project[g]
                                                 ], s
                          ] \
            >= - mod.GenCommitBin_Startup_Type[g, tmp, s] \
            * mod.GenCommitBin_Pmin_MW[g, tmp]


def power_during_startup_constraint_rule(mod, g, tmp, s):
    """
    **Constraint Name**: GenCommitBin_Power_During_Startup_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS_STR_TYPES

    Power provision in the start timepoint (i.e. the timepoint when the unit
    is first committed) is constrained by the startup ramp rate (adjusted
    for timepoint duration).

    In other words, to provide 'committed' power in the start timepoint, we
    need to have provided startup power in the previous timepoint, which
    will in turn set the whole startup trajectory based on the previous
    constraints.

    When we are not in the start timepoint, simply constrain power provision
    by the capacity, which may not bind. To elaborate, when we are not in a
    start timepoint, t-1 could have had:
    1) the unit committed, meaning Pstarting[t-1]=0, resulting in
    power provision <= capacity, or
    2) the unit not committed, meaning that we are also not committed in t,
    i.e. power provision[t]=0, resulting in -Pstarting[t-1] <= capacity

    (Commit[t] x Pmin + P_above_Pmin[t]) - Pstarting[t-1]
    <=
    (1 - Start[t]) x Pmax + Start[t] x Startup_Ramp_Rate x Pmax
    """

    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    else:
        return (mod.GenCommitBin_Commit[g, tmp]
                * mod.GenCommitBin_Pmin_MW[g, tmp]
                + mod.GenCommitBin_Provide_Power_Above_Pmin_MW[g, tmp]
                ) \
            + mod.GenCommitBin_Upwards_Reserves_MW[g, tmp] \
            - mod.GenCommitBin_Provide_Power_Startup_MW[g, mod.previous_timepoint[
                tmp, mod.balancing_type_project[g]], s] \
            <= \
            (1 - mod.GenCommitBin_Startup_Type[g, tmp, s]) \
            * mod.GenCommitBin_Pmax_MW[g, tmp] \
            + mod.GenCommitBin_Startup[g, tmp] \
            * mod.GenCommitBin_Startup_Ramp_Rate_MW_Per_Tmp[
                g, mod.previous_timepoint[tmp,
                                          mod.balancing_type_project[g]], s
            ]


# Shutdown Power
def max_shutdown_power_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Max_Shutdown_Power_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    Shutdown power is 0 when the unit is committed and must be less than or
    equal to the minimum stable level when not committed
    """

    return mod.GenCommitBin_Provide_Power_Shutdown_MW[g, tmp] \
        <= (1 - mod.GenCommitBin_Commit[g, tmp]) \
        * mod.GenCommitBin_Pmin_MW[g, tmp]


def ramp_during_shutdown_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Ramp_During_Shutdown_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    The difference between shutdown power of consecutive timepoints has to
    obey shutdown ramp up rates.

    We assume that a unit has to reach its setpoint at the start of the
    timepoint; as such, the ramping between 2 timepoints is assumed to
    take place during the duration of the first timepoint, and the
    ramp rate is adjusted for the duration of the first timepoint.
    """

    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    else:
        return mod.GenCommitBin_Provide_Power_Shutdown_MW[g, mod.previous_timepoint[
            tmp, mod.balancing_type_project[g]]] \
            - mod.GenCommitBin_Provide_Power_Shutdown_MW[g, tmp] \
            <= mod.GenCommitBin_Shutdown_Ramp_Rate_MW_Per_Tmp[
                g, mod.previous_timepoint[tmp,
                                          mod.balancing_type_project[g]]
            ]


def decreasing_shutdown_power_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Decreasing_Shutdown_Power_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    GenCommitBin_Provide_Power_Shutdown_MW[t] can only be less than
    GenCommitBin_Provide_Power_Shutdown_MW[t+1] if the unit stops in t+1 (when
    it is back above 0). In other words, GenCommitBin_Provide_Power_Shutdown_MW
    can only increase in the stopping timepoint; in all other timepoints it
    should decrease or stay constant. This prevents situations in which the
    model can abuse this by providing stopping power in some timepoints without
    previously having committed the unit.
    """
    if check_if_linear_horizon_last_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    else:
        return \
            mod.GenCommitBin_Provide_Power_Shutdown_MW[g, tmp] - \
            mod.GenCommitBin_Provide_Power_Shutdown_MW[g,
                          mod.next_timepoint[tmp,
                                             mod
                                             .balancing_type_project[g]
                                             ]
                          ] \
            >= \
            - mod.GenCommitBin_Shutdown[g,
                              mod.next_timepoint[tmp,
                                                 mod
                                                 .balancing_type_project[g]
                                                 ]
                              ] * \
            mod.GenCommitBin_Pmin_MW[g, tmp]


def power_during_shutdown_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitBin_Power_During_Shutdown_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    Power provision in the stop timepoint (i.e. the first timepoint the unit
    is not committed after having been committed) is constrained by the
    shutdown ramp rate (adjusted for timepoint duration).

    In other words, to provide 'committed' power in the stop timepoint, we
    need to provide shutdown power in the next timepoint, which will in turn
    set the whole shutdown trajectory based on the previous constraints.

    When we are not in the stop timepoint, simply constrain power provision
    by the capacity, which may not bind. To elaborate, when we are not in a
    stop timepoint, t+1 could have:
    1) the unit committed, meaning Pstopping[t+1]=0, resulting in
    power provision <= capacity, or
    2) the unit not committed, meaning that we are also not committed in t
    i.e. power provision[t]=0, resulting in -Pstopping[t+1] <= capacity

    (Commit[t] x Pmin + P_above_Pmin[t]) - Pstopping[t+1]
    <=
    (1 - Stop[t+1]) x Pmax + Stop[t+1] x Shutdown_Ramp_Rate x Pmax
    """

    if check_if_linear_horizon_last_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    else:
        return (mod.GenCommitBin_Commit[g, tmp]
                * mod.GenCommitBin_Pmin_MW[g, tmp]
                + mod.GenCommitBin_Provide_Power_Above_Pmin_MW[g,
                                                                   tmp]) \
            + mod.GenCommitBin_Upwards_Reserves_MW[g, tmp] \
            - mod.GenCommitBin_Provide_Power_Shutdown_MW[g, mod.next_timepoint[
                tmp, mod.balancing_type_project[g]]] \
            <= \
            (1 - mod.GenCommitBin_Shutdown[g, mod.next_timepoint[
                tmp, mod.balancing_type_project[g]]]) \
            * mod.GenCommitBin_Pmax_MW[
                g, mod.next_timepoint[tmp, mod.balancing_type_project[g]]] \
            + mod.GenCommitBin_Shutdown[
                g, mod.next_timepoint[tmp, mod.balancing_type_project[g]]] \
            * mod.GenCommitBin_Shutdown_Ramp_Rate_MW_Per_Tmp[g, tmp]


def fuel_burn_constraint_rule(mod, g, tmp, s):
    """
    **Constraint Name**: GenCommitBin_Fuel_Burn_Constraint
    **Enforced Over**: GEN_COMMIT_BIN_OPR_TMPS

    Fuel burn is set by piecewise linear representation of input/output
    curve.

    Note: we assume that when projects are derated for availability, the
    input/output curve is derated by the same amount. The implicit
    assumption is that when a generator is de-rated, some of its units
    are out rather than it being forced to run below minimum stable level
    at very inefficient operating points.
    """
    return \
        mod.GenCommitBin_Fuel_Burn_MMBTU[g, tmp] \
        >= \
        mod.fuel_burn_slope_mmbtu_per_mwh[g, s] \
        * mod.GenCommitBin_Provide_Power_MW[g, tmp] \
        + mod.fuel_burn_intercept_mmbtu_per_hr[g, s] \
        * mod.Availability_Derate[g, tmp] \
        * mod.GenCommitBin_Synced[g, tmp]


# Operational Type Methods
###############################################################################

def power_provision_rule(mod, g, tmp):
    """
    Power provision for gen_commit_bin generators is a variable constrained
    constrained to be between the generator's minimum stable level and its
    capacity if the generator is committed and 0 otherwise.
    """
    return mod.GenCommitBin_Provide_Power_MW[g, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision of dispatchable generators is an endogenous variable.
    """
    return mod.GenCommitBin_Provide_Power_MW[g, tmp]


def commitment_rule(mod, g, tmp):
    """
    Commitment decision in each timepoint
    """
    # TODO: shouldn't we return MW here to make this consistent w
    #  gen_commit_cap?
    return mod.GenCommitBin_Commit[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Capacity online in each timepoint.
    """
    return mod.GenCommitBin_Pmax_MW[g, tmp] \
        * mod.GenCommitBin_Commit[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    No 'curtailment' -- simply dispatch down
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
        return mod.GenCommitBin_Fuel_Burn_MMBTU[g, tmp]
    else:
        raise ValueError(error_message)


def startup_cost_rule(mod, g, tmp):
    """
    Startup costs are applied in each timepoint based on the amount of capacity
    (in MW) that is started up in that timepoint for a given startup type and
    the startup cost parameter for that startup type. We take the sum across
    all startup types since only one startup type is active at the same time.
    """
    return sum(
        mod.gen_commit_bin_startup_cost_per_mw[g, s]
        * mod.GenCommitBin_Startup_Type[g, tmp, s]
        for s in mod.GEN_COMMIT_BIN_STR_TYPES_BY_PRJ[g]
    ) * mod.GenCommitBin_Pmax_MW[g, tmp]


def shutdown_cost_rule(mod, g, tmp):
    """
    Shutdown costs are applied in each timepoint based on the amount of
    capacity (in Mw) that is shut down in that timepoint and the shutdown
    cost parameter.
    """
    return mod.GenCommitBin_Shutdown[g, tmp] \
        * mod.GenCommitBin_Pmax_MW[g, tmp] \
        * mod.gen_commit_bin_shutdown_cost_per_mw[g]


def startup_fuel_burn_rule(mod, g, tmp):
    """
    Startup fuel burn is applied in each timepoint based on the amount of
    capacity (in MW) that is started up in that timepoint and the startup
    fuel parameter.
    """
    return mod.GenCommitBin_Startup[g, tmp] \
        * mod.GenCommitBin_Pmax_MW[g, tmp] \
        * mod.gen_commit_bin_startup_fuel_mmbtu_per_mw[g]


def power_delta_rule(mod, g, tmp):
    """
    Ramp between this timepoint and the previous timepoint
    Actual ramp rate in MW/hr depends on the duration of the timepoints.
    """
    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        pass
    else:
        return mod.GenCommitBin_Provide_Power_Above_Pmin_MW[g, tmp] \
            - mod.GenCommitBin_Provide_Power_Above_Pmin_MW[
                g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]


def fix_commitment(mod, g, tmp):
    """
    """
    mod.GenCommitBin_Commit[g, tmp] = \
        mod.fixed_commitment[g, mod.previous_stage_timepoint_map[tmp]]
    mod.GenCommitBin_Commit[g, tmp].fixed = True


# Input-Output
###############################################################################

def load_module_specific_data(mod, data_portal,
                              scenario_directory, subproblem, stage):
    """
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    min_stable_fraction = dict()
    shutdown_plus_ramp_down_rate = dict()
    ramp_up_when_on_rate = dict()
    ramp_down_when_on_rate = dict()
    min_up_time = dict()
    min_down_time = dict()
    shutdown_cost = dict()
    startup_fuel = dict()

    header = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t", header=None, nrows=1
    ).values[0]

    optional_columns = ["shutdown_plus_ramp_down_rate",
                        "ramp_up_when_on_rate",
                        "ramp_down_when_on_rate",
                        "min_up_time_hours",
                        "min_down_time_hours",
                        "shutdown_cost_per_mw",
                        "startup_fuel_mmbtu_per_mw"
                        ]
    used_columns = [c for c in optional_columns if c in header]

    dynamic_components = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "operational_type",
                 "min_stable_level_fraction"] + used_columns

    )
    for row in zip(dynamic_components["project"],
                   dynamic_components["operational_type"],
                   dynamic_components["min_stable_level_fraction"]):
        if row[1] == "gen_commit_bin":
            min_stable_fraction[row[0]] = float(row[2])
        else:
            pass
    data_portal.data()["gen_commit_bin_min_stable_level_fraction"] = \
        min_stable_fraction
    gen_commit_bin_projects = min_stable_fraction.keys()

    # Ramp rate limits are optional, will default to 1 if not specified
    # (startup plus ramp up rate is read in separately because different
    #  startup types, e.g. hot/cold).
    if "shutdown_plus_ramp_down_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["shutdown_plus_ramp_down_rate"]):
            if row[1] == "gen_commit_bin" and row[2] != ".":
                shutdown_plus_ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_bin_shutdown_plus_ramp_down_rate"] = \
            shutdown_plus_ramp_down_rate

    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_up_when_on_rate"]):
            if row[1] == "gen_commit_bin" and row[2] != ".":
                ramp_up_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_bin_ramp_up_when_on_rate"] = \
            ramp_up_when_on_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_down_when_on_rate"]):
            if row[1] == "gen_commit_bin" and row[2] != ".":
                ramp_down_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_bin_ramp_down_when_on_rate"] = \
            ramp_down_when_on_rate

    # Up and down time limits are optional, will default to 1 if not specified
    if "min_up_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["min_up_time_hours"]):
            if row[1] == "gen_commit_bin" and row[2] != ".":
                min_up_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_bin_min_up_time_hrs"] = min_up_time

    if "min_down_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["min_down_time_hours"]):
            if row[1] == "gen_commit_bin" and row[2] != ".":
                min_down_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_bin_min_down_time_hrs"] = min_down_time

    # Shutdown costs are optional, will default to 0 if not specified
    if "shutdown_cost_per_mw" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["shutdown_cost_per_mw"]
                       ):
            if row[1] == "gen_commit_bin" and row[2] != ".":
                shutdown_cost[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_bin_shutdown_cost_per_mw"] = \
            shutdown_cost

    # Startup fuel is optional, will default to 0 if not specified
    if "startup_fuel_mmbtu_per_mw" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["startup_fuel_mmbtu_per_mw"]
                       ):
            if row[1] == "gen_commit_bin" and row[2] != ".":
                startup_fuel[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_bin_startup_fuel_mmbtu_per_mw"] = \
            startup_fuel

    # Startup characteristics
    df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "startup_chars.tab"),
        sep="\t"
    )

    # Note: the rank function requires at least one numeric input in the
    # down_time_cutoff_hours column (can't be all NULL/None).
    if len(df) > 0:
        df["startup_type_id"] = df.groupby("project")[
            "down_time_cutoff_hours"].rank()

    startup_ramp_projects = set()
    startup_ramp_projects_types = list()
    down_time_cutoff_hours_dict = dict()
    startup_plus_ramp_up_rate_dict = dict()
    startup_cost_dict = dict()

    for i, row in df.iterrows():
        project = row["project"]
        startup_type_id = row["startup_type_id"]
        down_time_cutoff_hours = row["down_time_cutoff_hours"]
        startup_plus_ramp_up_rate = row["startup_plus_ramp_up_rate"]
        startup_cost = row["startup_cost_per_mw"]

        if down_time_cutoff_hours != "." and startup_plus_ramp_up_rate != "." \
                and project in gen_commit_bin_projects:
            startup_ramp_projects.add(project)
            startup_ramp_projects_types.append((project, startup_type_id))
            down_time_cutoff_hours_dict[(project, startup_type_id)] = \
                float(down_time_cutoff_hours)
            startup_plus_ramp_up_rate_dict[(project, startup_type_id)] = \
                float(startup_plus_ramp_up_rate)
            startup_cost_dict[(project, startup_type_id)] = \
                float(startup_cost)

    if startup_ramp_projects:
        data_portal.data()["GEN_COMMIT_BIN_STR_RMP_PRJS"] = \
            {None: startup_ramp_projects}
        data_portal.data()["GEN_COMMIT_BIN_STR_RMP_PRJS_TYPES"] = \
            {None: startup_ramp_projects_types}
        data_portal.data()["gen_commit_bin_down_time_cutoff_hours"] = \
            down_time_cutoff_hours_dict
        data_portal.data()["gen_commit_bin_startup_plus_ramp_up_rate"] = \
            startup_plus_ramp_up_rate_dict
        data_portal.data()["gen_commit_bin_startup_cost_per_mw"] = \
            startup_cost_dict


def export_module_specific_results(mod, d,
                                   scenario_directory, subproblem, stage):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "dispatch_binary_commit.csv"), "w", newline="") \
            as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "balancing_type_project",
                         "horizon", "timepoint", "timepoint_weight",
                         "number_of_hours_in_timepoint", "technology",
                         "load_zone", "power_mw", "committed_mw",
                         "committed_units", "started_units", "stopped_units",
                         "synced_units", "active_startup_type"
                         ])

        for (p, tmp) in mod.GEN_COMMIT_BIN_OPR_TMPS:
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
                value(mod.GenCommitBin_Provide_Power_MW[p, tmp]),
                value(mod.GenCommitBin_Pmax_MW[p, tmp])
                * value(mod.GenCommitBin_Commit[p, tmp]),
                value(mod.GenCommitBin_Commit[p, tmp]),
                value(mod.GenCommitBin_Startup[p, tmp]),
                value(mod.GenCommitBin_Shutdown[p, tmp]),
                value(mod.GenCommitBin_Synced[p, tmp]),
                value(mod.GenCommitBin_Active_Startup_Type[p, tmp])
            ])


# Database
###############################################################################

def import_module_specific_results_to_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """
    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    if not quiet:
        print("project dispatch binary commit")

    update_dispatch_results_table(
        db=db, c=c, results_directory=results_directory,
        scenario_id=scenario_id, subproblem=subproblem, stage=stage,
        results_file="dispatch_binary_commit.csv"
    )


def get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()
    # TODO: should we align this better with heat rates (queries and input
    #  validations are slightly different).
    startup_chars = c.execute(
        """
        SELECT project, 
        down_time_cutoff_hours, startup_plus_ramp_up_rate, startup_cost_per_mw
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, startup_chars_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = '{}') AS op_char
        USING(project)
        INNER JOIN
        inputs_project_startup_chars
        USING(project, startup_chars_scenario_id)
        WHERE project_portfolio_scenario_id = {}
        AND startup_chars_scenario_id is not Null
        """.format(subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                   "gen_commit_bin",
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID)
    )

    return startup_chars


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    startup_chars.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    startup_chars = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # If startup_chars.tab file already exists, append rows to it
    if os.path.isfile(os.path.join(inputs_directory, "startup_chars.tab")):
        with open(os.path.join(inputs_directory, "startup_chars.tab"),
                  "a") as startup_chars_file:
            writer = csv.writer(startup_chars_file,
                                delimiter="\t", lineterminator="\n")
            for row in startup_chars:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)
    # If startup_chars.tab does not exist, write header first, then add data
    else:
        with open(os.path.join(inputs_directory, "startup_chars.tab"),
                  "w", newline="") as startup_chars_file:
            writer = csv.writer(startup_chars_file,
                                delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(["project",
                             "down_time_cutoff_hours",
                             "startup_plus_ramp_up_rate",
                             "startup_cost_per_mw"])

            for row in startup_chars:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)


# Validation
###############################################################################

def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs

    TODO: could add data type checking here
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    validation_results = []

    # Get startup chars and project inputs
    startup_chars = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    c1 = conn.cursor()
    projects = c1.execute(
        """SELECT project, operational_type,
        min_stable_level, unit_size_mw,
        shutdown_cost_per_mw,
        startup_fuel_mmbtu_per_mw,
        startup_plus_ramp_up_rate,
        shutdown_plus_ramp_down_rate,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, operational_type,
        min_stable_level, unit_size_mw,
        shutdown_cost_per_mw,
        startup_fuel_mmbtu_per_mw,
        startup_plus_ramp_up_rate,
        shutdown_plus_ramp_down_rate,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}) as prj_chars
        USING (project)
        WHERE project_portfolio_scenario_id = {}
        AND operational_type = '{}'""".format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            "gen_commit_bin"
        )
    )

    # Convert input data to DataFrame
    prj_df = pd.DataFrame(
        data=projects.fetchall(),
        columns=[s[0] for s in projects.description]
    )
    su_df = pd.DataFrame(
        data=startup_chars.fetchall(),
        columns=[s[0] for s in startup_chars.description]
    )

    # Get the number of hours in the timepoint (take min if it varies)
    c2 = conn.cursor()
    tmp_durations = c2.execute(
        """SELECT number_of_hours_in_timepoint
           FROM inputs_temporal_timepoints
           WHERE temporal_scenario_id = {}
           AND subproblem_id = {}
           AND stage_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage
        )
    ).fetchall()
    hrs_in_tmp = min(tmp_durations)

    # Check that min stable level is specified
    # (not all operational types require this input)
    req_columns = [
        "min_stable_level",
    ]
    validation_errors = check_req_prj_columns(prj_df, req_columns, True,
                                              "gen_commit_bin")
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
        "unit_size_mw",
        "charging_efficiency", "discharging_efficiency",
        "minimum_duration_hours"
    ]
    validation_errors = check_req_prj_columns(prj_df, expected_na_columns,
                                              False,
                                              "gen_commit_bin")
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "Low",
             "Unexpected inputs",
             error
             )
        )

    # Check startup shutdown rate inputs
    validation_errors = validate_startup_shutdown_rate_inputs(prj_df,
                                                              su_df,
                                                              hrs_in_tmp)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS, PROJECT_STARTUP_CHARS",
             "inputs_project_operational_chars, inputs_project_startup_chars",
             "High",
             "Invalid startup/shutdown ramp inputs",
             error
             )
        )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)
