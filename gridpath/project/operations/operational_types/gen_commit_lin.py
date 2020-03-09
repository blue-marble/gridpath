#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This operational type is the same as the *gen_commit_bin* operational type,
but the commitment decisions are declared as continuous (with bounds of 0 to
1) instead of binary, so 'partial' generators can be committed. This
linear relaxation treatment can be helpful in situations when mixed-integer
problem run-times are long and is similar to loosening the MIP gap (but can
target specific generators). Please refer to the *gen_commit_bin* module for
more information on the formulation.

.. Note:: Some of the more complex constraints in this module such as the
startup trajectories might show weird behavior in the linearized version, e.g.
different fractions of the unit might be starting up and shutting down in the
same timepoint. We don't recommend using this linearized version in combination
with these complex constraints.
"""

from __future__ import division

from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Param, Constraint, NonNegativeReals, \
    PercentFraction, Expression, value

from gridpath.auxiliary.auxiliary import generator_subset_init, \
    check_req_prj_columns, write_validation_to_database,\
    validate_startup_shutdown_rate_inputs
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints, update_dispatch_results_table
from gridpath.project.common_functions import \
    check_if_linear_horizon_first_timepoint, \
    check_if_linear_horizon_last_timepoint


def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_COMMIT_LIN`                                                |
    |                                                                         |
    | The set of generators of the :code:`gen_commit_lin` operational type.   |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_LIN_OPR_TMPS`                                       |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_commit_lin`       |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_LIN_OPR_TMPS_FUEL_SEG`                              |
    |                                                                         |
    | Three-dimensional set with generators of the :code:`gen_commit_lin`     |
    | operational type, their operational timepoints, and their fuel          |
    | segments (if the project is in :code:`FUEL_PROJECTS`).                  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_commit_lin_min_stable_level_fraction`                      |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The minimum stable level of this project as a fraction of its capacity. |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_commit_lin_ramp_up_when_on_rate`                           |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's upward ramp rate limit during operations, defined as a    |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_ramp_down_when_on_rate`                         |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's downward ramp rate limit during operations, defined as a  |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_startup_plus_ramp_up_rate`                      |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's upward ramp rate limit during startup, defined as a       |
    | fraction of its capacity per minute. If, after adjusting for timepoint  |
    | duration, this is smaller than the minimum stable level, the project    |
    | will have a startup trajectory across multiple timepoitns.              |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_shutdown_plus_ramp_down_rate`                   |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's downward ramp rate limit during startup, defined as a     |
    | fraction of its capacity per minute. If, after adjusting for timepoint  |
    | duration, this is smaller than the minimum stable level, the project    |
    | will have a shutdown trajectory across multiple timepoitns.             |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_min_up_time_hrs`                                |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The project's minimum up time in hours.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_min_down_time_hrs`                              |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The project's minimum down time in hours.                               |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_startup_cost_per_mw`                            |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The project's startup cost per MW of capacity that is started up.       |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_shutdown_cost_per_mw`                           |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The project's shutdown cost per MW of capacity that is shut down.       |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_startup_fuel_mmbtu_per_mw`                      |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The project's startup fuel burn in MMBtu per MW of capacity that is     |
    | started up.                                                             |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`GenCommitLin_Commit`                                           |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Continuous variable which represents the commitment decision in each        |
    | operational timepoint. It is one if the unit is committed and zero      |
    | otherwise (including during a startup and shutdown trajectory).         |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Startup`                                          |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Continuous variable which is one of the unit starts up and zero otherwise.  |
    | A startup is defined as changing commitment from zero to one.           |
    | Note: this variable is zero throughout a startup trajectory!            |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Shutdown`                                         |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Continuous variable which is one of the unit shuts down and zero otherwise. |
    | A shutdown is defined as changing commitment from one to zero.          |
    | Note: this variable is zero throughout a shutdown trajectory!           |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Synced`                                           |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Continuous variable which is one if the project is providing *any* power (  |
    | either because it is committed or because it is in a startup or shutdown|
    | trajectory), and zero otherwise.                                        |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Provide_Power_Above_Pmin_MW`                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Power provision above the minimum stable level in MW from this project  |
    | in each timepoint in which the project is committed.                    |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Provide_Power_Startup_MW`                         |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Power provision during startup in each timepoint in which the project   |
    | is starting up (zero if project is committed or not starting up).       |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Provide_Power_Shutdown_MW`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Power provision during shutdown in each timepoint in which the project  |
    | is shutting down (zero if project is committed or not shutting down).   |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Fuel_Burn_MMBTU`                                  |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_FUEL_PRJ_OPR_TMPS`              |
    |                                                                         |
    | Fuel burn in MMBTU by this project in each operational timepoint.       |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`GenCommitLin_Pmax_MW`                                          |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's maximum power output (in MW) if the unit was committed.   |
    | Depends on the project's availability and capacity in the timepoint.    |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Pmin_MW`                                          |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's minimum power output (in MW) if the unit was committed.   |
    | Depends on the project's availability and capacity in the timepoint,    |
    | and the minimum stable level.                                           |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Provide_Power_MW`                                 |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's total power output (in MW) in each operational timepoint, |
    | including power from a startup or shutdown trajectory.                  |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Ramp_Up_Rate_MW_Per_Tmp`                          |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's upward ramp-able capacity (in MW) in each operational     |
    | timepoint. Depends on the :code:`gen_commit_lin_ramp_up_when_on_rate`,  |
    | the availability and capacity in the timepoint, and the timepoint's     |
    | duration.                                                               |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Ramp_Down_Rate_MW_Per_Tmp`                        |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's downward ramp-able capacity (in MW) in each operationa    |
    | timepoint. Depends on the :code:`gen_commit_lin_ramp_down_when_on_rate` |
    | , the availability and capacity in the timepoint, and the timepoint's   |
    | duration.                                                               |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Startup_Ramp_Rate_MW_Per_Tmp`                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's upward ramp-able capacity (in MW) during startup in each  |
    | operational timepoint. Depends on the                                   |
    | :code:`gen_commit_lin_startup_plus_ramp_up_rate`, the availability and  |
    | capacity in the timepoint, and the timepoint's duration.                |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Shutdown_Ramp_Rate_MW_Per_Tmp`                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's downward ramp-able capacity (in MW) during shutdown in    |
    | each operational timepoint. Depends on the                              |
    | :code:`gen_commit_lin_shutdown_plus_ramp_down_rate`, the availability   |
    | and capacity in the timepoint, and the timepoint's duration.            |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Upwards_Reserves_MW`                              |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's total upward reserves offered (in MW) in each timepoint.  |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Downwards_Reserves_MW`                            |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's total downward reserves offered (in MW) in each timepoint.|
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | Commitment                                                              |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Binary_Logic_Constraint`                          |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Defines the relationship between the binary commitment, startup, and    |
    | shutdown variables. When the commitment changes from zero to one, the   |
    | startup variable is one, when it changes from one to zero, the shutdown |
    | variable is one.                                                        |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Synced_Constraint`                                |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Sets the GenCommitLin_Synced variable to one if the project is          |
    | providing  *any* power (either because it is committed or because it is |
    | in a startup or shutdown trajectory), and zero otherwise.               |
    +-------------------------------------------------------------------------+
    | Power                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Max_Power_Constraint`                             |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits the power plus upward reserves to the available capacity.        |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Min_Power_Constraint`                             |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Power provision minus downward reserves should exceed the minimum       |
    | stable level for the project.                                           |
    +-------------------------------------------------------------------------+
    | Minimum Up and Down Time                                                |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Min_Up_Time_Constraint`                           |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Requires that when the project is started, it stays on for at least     |
    | :code:`gen_commit_lin_min_up_time_hrs`.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Min_Down_Time_Constraint`                         |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Requires that when the project is shut down, it stays off for at least  |
    | :code:`gen_commit_lin_min_up_time_hrs`.                                 |
    +-------------------------------------------------------------------------+
    | Ramps                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Ramp_Up_Constraint`                               |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project upward ramp during operations based on the   |
    | :code:`gen_commit_lin_ramp_up_when_on_rate`.                            |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Ramp_Down_Constraint`                             |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project downward ramp during operations based on the |
    | :code:`gen_commit_lin_ramp_down_when_on_rate`.                          |
    +-------------------------------------------------------------------------+
    | Startup Power                                                           |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Max_Startup_Power_Constraint`                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits startup power to zero when the project is committed and to the   |
    | minimum stable level when it is not committed.                          |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Ramp_During_Startup_Constraint`                   |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project upward startup power ramp based on the       |
    | :code:`gen_commit_lin_startup_plus_ramp_up_rate`.                       |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Increasing_Startup_Power_Constraint`              |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Requires that the startup power always increases, except for the        |
    | startup timepoint (when :code:`GenCommitLin_Startup` is one).           |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Power_During_Startup_Constraint`                  |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits the difference between the power provision in the startup        |
    | timepoint and the startup power in the previous timepoint based on the  |
    | :code:`gen_commit_lin_startup_plus_ramp_up_rate`.                       |
    +-------------------------------------------------------------------------+
    | Shutdown Power                                                          |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Max_Shutdown_Power_Constraint`                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits shutdown power to zero when the project is committed and to the  |
    | minimum stable level when it is not committed.                          |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Ramp_During_Shutdown_Constraint`                  |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits the allowed project downward shutdown power ramp based on the    |
    | :code:`gen_commit_lin_shutdown_plus_ramp_down_rate`.                    |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Decreasing_Shutdown_Power_Constraint`             |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Requires that the shutdown power always decreases, except for the       |
    | shutdown timepoint (when :code:`GenCommitLin_Shutdown` is one).         |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Power_During_Shutdown_Constraint`                 |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits the difference between the power provision in the shutdown       |
    | timepoint and the shutdown power in the next timepoint based on the     |
    | :code:`gen_commit_lin_shutdown_plus_ramp_down_rate`.                    |
    +-------------------------------------------------------------------------+
    | Fuel Burn                                                               |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Fuel_Burn_Constraint`                             |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS_FUEL_SEG`              |
    |                                                                         |
    | Determines fuel burn from the project in each timepoint based on its    |
    | heat rate curve.                                                        |
    +-------------------------------------------------------------------------+
    """

    # Sets
    ###########################################################################

    m.GEN_COMMIT_LIN = Set(
        within=m.PROJECTS,
        initialize=generator_subset_init("operational_type", "gen_commit_lin")
    )

    m.GEN_COMMIT_LIN_OPR_TMPS = Set(
        dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            if g in mod.GEN_COMMIT_LIN)
    )

    m.GEN_COMMIT_LIN_OPR_TMPS_FUEL_SEG = Set(
        dimen=3,
        within=m.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
        set((g, tmp, s) for (g, tmp, s)
            in mod.FUEL_PROJECT_SEGMENTS_OPERATIONAL_TIMEPOINTS
            if g in mod.GEN_COMMIT_LIN)
    )

    # Required Params
    ###########################################################################
    m.gen_commit_lin_min_stable_level_fraction = Param(
        m.GEN_COMMIT_LIN,
        within=PercentFraction
    )

    # Optional Params
    ###########################################################################

    m.gen_commit_lin_ramp_up_when_on_rate = Param(
        m.GEN_COMMIT_LIN,
        within=PercentFraction, default=1
    )
    m.gen_commit_lin_ramp_down_when_on_rate = Param(
        m.GEN_COMMIT_LIN,
        within=PercentFraction, default=1
    )
    m.gen_commit_lin_startup_plus_ramp_up_rate = Param(
        m.GEN_COMMIT_LIN,
        within=PercentFraction, default=1
    )
    m.gen_commit_lin_shutdown_plus_ramp_down_rate = Param(
        m.GEN_COMMIT_LIN,
        within=PercentFraction, default=1
    )

    m.gen_commit_lin_min_up_time_hrs = Param(
        m.GEN_COMMIT_LIN,
        within=NonNegativeReals, default=0
    )
    m.gen_commit_lin_min_down_time_hrs = Param(
        m.GEN_COMMIT_LIN,
        within=NonNegativeReals, default=0
    )

    m.gen_commit_lin_startup_cost_per_mw = Param(
        m.GEN_COMMIT_LIN,
        within=NonNegativeReals,
        default=0
    )
    m.gen_commit_lin_shutdown_cost_per_mw = Param(
        m.GEN_COMMIT_LIN,
        within=NonNegativeReals,
        default=0
    )
    m.gen_commit_lin_startup_fuel_mmbtu_per_mw = Param(
        m.GEN_COMMIT_LIN,
        within=NonNegativeReals,
        default=0
    )

    # Variables
    ###########################################################################

    m.GenCommitLin_Commit = Var(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        within=PercentFraction
    )

    m.GenCommitLin_Startup = Var(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        within=PercentFraction
    )

    m.GenCommitLin_Shutdown = Var(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        within=PercentFraction
    )

    m.GenCommitLin_Synced = Var(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        within=PercentFraction
    )

    m.GenCommitLin_Provide_Power_Above_Pmin_MW = Var(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        within=NonNegativeReals
    )

    m.GenCommitLin_Provide_Power_Startup_MW = Var(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        within=NonNegativeReals
    )

    m.GenCommitLin_Provide_Power_Shutdown_MW = Var(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        within=NonNegativeReals
    )

    m.GenCommitLin_Fuel_Burn_MMBTU = Var(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        within=NonNegativeReals
    )

    # Expressions
    ###########################################################################

    m.GenCommitLin_Pmax_MW = Expression(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=pmax_rule
    )

    m.GenCommitLin_Pmin_MW = Expression(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=pmin_rule
    )

    m.GenCommitLin_Provide_Power_MW = Expression(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=provide_power_rule
    )

    m.GenCommitLin_Ramp_Up_Rate_MW_Per_Tmp = Expression(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=ramp_up_rate_rule
    )

    m.GenCommitLin_Ramp_Down_Rate_MW_Per_Tmp = Expression(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=ramp_down_rate_rule
    )

    m.GenCommitLin_Startup_Ramp_Rate_MW_Per_Tmp = Expression(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=startup_ramp_rate_rule
    )

    m.GenCommitLin_Shutdown_Ramp_Rate_MW_Per_Tmp = Expression(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=shutdown_ramp_rate_rule
    )

    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])

    m.GenCommitLin_Upwards_Reserves_MW = Expression(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=upwards_reserve_rule
    )

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])

    m.GenCommitLin_Downwards_Reserves_MW = Expression(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=downwards_reserve_rule
    )

    # Constraints
    ###########################################################################

    # Commitment
    m.GenCommitLin_Binary_Logic_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=binary_logic_constraint_rule
    )

    m.GenCommitLin_Synced_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=synced_constraint_rule
    )

    # Power
    m.GenCommitLin_Max_Power_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=max_power_constraint_rule
    )

    m.GenCommitLin_Min_Power_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=min_power_constraint_rule
    )

    # Minimum Up and Down Time
    m.GenCommitLin_Min_Up_Time_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=min_up_time_constraint_rule
    )

    m.GenCommitLin_Min_Down_Time_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=min_down_time_constraint_rule
    )

    # Ramps
    m.GenCommitLin_Ramp_Up_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=ramp_up_constraint_rule
    )

    m.GenCommitLin_Ramp_Down_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=ramp_down_constraint_rule
    )

    # Startup Power
    m.GenCommitLin_Max_Startup_Power_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=max_startup_power_constraint_rule
    )

    m.GenCommitLin_Ramp_During_Startup_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=ramp_during_startup_constraint_rule
    )

    m.GenCommitLin_Increasing_Startup_Power_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=increasing_startup_power_constraint_rule
    )

    m.GenCommitLin_Power_During_Startup_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=power_during_startup_constraint_rule
    )

    # Shutdown Power
    m.GenCommitLin_Max_Shutdown_Power_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=max_shutdown_power_constraint_rule
    )

    m.GenCommitLin_Ramp_During_Shutdown_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=ramp_during_shutdown_constraint_rule
    )

    m.GenCommitLin_Decreasing_Shutdown_Power_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=decreasing_shutdown_power_constraint_rule
    )

    m.GenCommitLin_Power_During_Shutdown_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS,
        rule=power_during_shutdown_constraint_rule
    )

    # Fuel Burn
    m.GenCommitLin_Fuel_Burn_Constraint = Constraint(
        m.GEN_COMMIT_LIN_OPR_TMPS_FUEL_SEG,
        rule=fuel_burn_constraint_rule
    )


# Expression Rules
###########################################################################

def pmax_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitLin_Pmax_MW
    **Defined Over**: GEN_COMMIT_LIN_OPR_TMPS
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
           * mod.Availability_Derate[g, tmp]


def pmin_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitLin_Pmin_MW
    **Defined Over**: GEN_COMMIT_LIN_OPR_TMPS
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
           * mod.Availability_Derate[g, tmp] \
           * mod.gen_commit_lin_min_stable_level_fraction[g]


def provide_power_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitLin_Provide_Power_MW
    **Defined Over**: GEN_COMMIT_LIN_OPR_TMPS
    """
    return mod.GenCommitLin_Provide_Power_Above_Pmin_MW[g, tmp] \
           + mod.GenCommitLin_Pmin_MW[g, tmp] \
           * mod.GenCommitLin_Commit[g, tmp] \
           + mod.GenCommitLin_Provide_Power_Startup_MW[g, tmp] \
           + mod.GenCommitLin_Provide_Power_Shutdown_MW[g, tmp]


def ramp_up_rate_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitLin_Ramp_Up_Rate_MW_Per_Tmp
    **Defined Over**: GEN_COMMIT_LIN_OPR_TMPS

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
           * mod.gen_commit_lin_ramp_up_when_on_rate[g] \
           * mod.number_of_hours_in_timepoint[tmp] \
           * 60  # convert min to hours


def ramp_down_rate_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitLin_Ramp_Down_Rate_MW_Per_Tmp
    **Defined Over**: GEN_COMMIT_LIN_OPR_TMPS

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
           * mod.gen_commit_lin_ramp_down_when_on_rate[g] \
           * mod.number_of_hours_in_timepoint[tmp] \
           * 60  # convert min to hours


def startup_ramp_rate_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitLin_Startup_Ramp_Rate_MW_Per_Tmp
    **Defined Over**: GEN_COMMIT_LIN_OPR_TMPS
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
           * mod.Availability_Derate[g, tmp] \
           * min(mod.gen_commit_lin_startup_plus_ramp_up_rate[g]
                 * mod.number_of_hours_in_timepoint[tmp]
                 * 60, 1)


def shutdown_ramp_rate_rule(mod, g, tmp):
    """
    **Expression Name**: GenCommitLin_Shutdown_Ramp_Rate_MW_Per_Tmp
    **Defined Over**: GEN_COMMIT_LIN_OPR_TMPS
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
           * mod.Availability_Derate[g, tmp] \
           * min(mod.gen_commit_lin_shutdown_plus_ramp_down_rate[g]
                 * mod.number_of_hours_in_timepoint[tmp]
                 * 60, 1)


# Constraint Formulation Rules
###############################################################################

# Commitment
def binary_logic_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Binary_Logic_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

    If commit status changes, unit is turning on or shutting down.
    The *GenCommitLin_Startup* variable is 1 for the first timepoint the unit
    is committed after being offline; it will be able to provide power in that
    timepoint. The *GenCommitLin_Shutdown* variable is 1 for the first
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
        return mod.GenCommitLin_Commit[g, tmp] \
               - mod.GenCommitLin_Commit[
                   g, mod.previous_timepoint[
                       tmp, mod.balancing_type_project[g]]] \
               == mod.GenCommitLin_Startup[g, tmp] - mod.GenCommitLin_Shutdown[
                   g, tmp]


def synced_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Synced_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

    Synced is 1 if the unit is committed, starting, or stopping and zero
    otherwise.
    """
    return mod.GenCommitLin_Synced[g, tmp] \
           >= mod.GenCommitLin_Commit[g, tmp] \
           + (mod.GenCommitLin_Provide_Power_Startup_MW[g, tmp]
              + mod.GenCommitLin_Provide_Power_Shutdown_MW[g, tmp]) \
           / mod.GenCommitLin_Pmin_MW[g, tmp]


# Power
def max_power_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Max_Power_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

    Power provision plus upward reserves shall not exceed maximum power.
    """
    return \
        (mod.GenCommitLin_Provide_Power_Above_Pmin_MW[g, tmp]
         + mod.GenCommitLin_Upwards_Reserves_MW[g, tmp]) \
        <= \
        (mod.GenCommitLin_Pmax_MW[g, tmp]
         - mod.GenCommitLin_Pmin_MW[g, tmp]) \
        * mod.GenCommitLin_Commit[g, tmp]


def min_power_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Min_Power_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

    Power minus downward services cannot be below minimum stable level.
    This constraint is not in Morales-Espana et al. (2013) because they
    don't look at downward reserves. In that case, enforcing
    provide_power_above_pmin to be within NonNegativeReals is sufficient.
    """
    return mod.GenCommitLin_Provide_Power_Above_Pmin_MW[g, tmp] \
        - mod.GenCommitLin_Downwards_Reserves_MW[g, tmp] \
        >= 0


# Minimum Up and Down Time
def min_up_time_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Min_Up_Time_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

    When units are started, they have to stay on for a minimum number
    of hours described by the gen_commit_lin_min_up_time_hrs parameter.
    The constraint is enforced by ensuring that the binary commitment
    is at least as large as the number of unit starts within min up time
    hours.

    We ensure a unit turned on less than the minimum up time ago is
    still on in the current timepoint *tmp* by checking how much units
    were turned on in each 'relevant' timepoint (i.e. a timepoint that
    begins more than or equal to gen_commit_lin_min_up_time_hrs ago
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
        mod, g, tmp, mod.gen_commit_lin_min_up_time_hrs[g]
    )

    number_of_starts_min_up_time_or_less_hours_ago = \
        sum(mod.GenCommitLin_Startup[g, tp] for tp in relevant_tmps)

    # If we've reached the first timepoint in linear boundary mode and
    # the total duration of the relevant timepoints (which includes *tmp*)
    # is less than the minimum up time, skip the constraint since the next
    # timepoint's constraint will already cover these same timepoints.
    # Don't skip if this timepoint is the last timepoint of the horizon
    # (since there will be no next timepoint).
    if (mod.boundary[
        mod.horizon[tmp, mod.balancing_type_project[g]]] == "linear"
            and
            relevant_tmps[-1]
            == mod.first_horizon_timepoint[
                mod.horizon[tmp, mod.balancing_type_project[g]]]
            and
            sum(mod.number_of_hours_in_timepoint[t] for t in relevant_tmps)
            < mod.gen_commit_lin_min_up_time_hrs[g]
            and
            tmp != mod.last_horizon_timepoint[
                mod.horizon[tmp, mod.balancing_type_project[g]]]):
        return Constraint.Skip
    # Otherwise, if there was a start min_up_time or less ago, the unit has
    # to remain committed.
    else:
        return mod.GenCommitLin_Commit[g, tmp] \
               >= number_of_starts_min_up_time_or_less_hours_ago


def min_down_time_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Min_Down_Time_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

    When units are shut down, they have to stay off for a minimum number
    of hours described by the gen_commit_lin_min_down_time_hrs parameter.
    The constraint is enforced by ensuring that (1-binary commitment)
    is at least as large as the number of unit shutdowns within min down
    time hours.

    We ensure a unit shut down less than the minimum up time ago is
    still off in the current timepoint *tmp* by checking how much units
    were shut down in each 'relevant' timepoint (i.e. a timepoint that
    begins more than or equal to gen_commit_lin_min_down_time_hrs ago
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
        mod, g, tmp, mod.gen_commit_lin_min_down_time_hrs[g]
    )

    number_of_stops_min_down_time_or_less_hours_ago = \
        sum(mod.GenCommitLin_Shutdown[g, tp] for tp in relevant_tmps)

    # If we've reached the first timepoint in linear boundary mode and
    # the total duration of the relevant timepoints (which includes *tmp*)
    # is less than the minimum down time, skip the constraint since the
    # next timepoint's constraint will already cover these same timepoints.
    # Don't skip if this timepoint is the last timepoint of the horizon
    # (since there will be no next timepoint).
    if (mod.boundary[
        mod.horizon[tmp, mod.balancing_type_project[g]]] == "linear"
            and
            relevant_tmps[-1]
            == mod.first_horizon_timepoint[
                mod.horizon[tmp, mod.balancing_type_project[g]]]
            and
            sum(mod.number_of_hours_in_timepoint[t] for t in relevant_tmps)
            < mod.gen_commit_lin_min_down_time_hrs[g]
            and
            tmp != mod.last_horizon_timepoint[
                mod.horizon[tmp, mod.balancing_type_project[g]]]):
        return Constraint.Skip
    # Otherwise, if there was a shutdown min_down_time or less ago, the unit
    # has to remain shut down.
    else:
        return 1 - mod.GenCommitLin_Commit[g, tmp] \
               >= number_of_stops_min_down_time_or_less_hours_ago


# Ramps
def ramp_up_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Ramp_Up_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

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
    elif (mod.gen_commit_lin_ramp_up_when_on_rate[g] * 60
          * mod.number_of_hours_in_timepoint[
              mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
          >= (1 - mod.gen_commit_lin_min_stable_level_fraction[g])):
        return Constraint.Skip
    else:
        return \
            (mod.GenCommitLin_Provide_Power_Above_Pmin_MW[g, tmp]
             + mod.GenCommitLin_Upwards_Reserves_MW[g, tmp]) \
            - \
            (mod.GenCommitLin_Provide_Power_Above_Pmin_MW[
                 g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
             - mod.GenCommitLin_Downwards_Reserves_MW[
                 g, mod.previous_timepoint[
                     tmp, mod.balancing_type_project[g]]]) \
            <= \
            mod.GenCommitLin_Ramp_Up_Rate_MW_Per_Tmp[
                g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]


def ramp_down_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Ramp_Down_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

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
    elif (mod.gen_commit_lin_ramp_down_when_on_rate[g] * 60
          * mod.number_of_hours_in_timepoint[
              mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
          >= (1 - mod.gen_commit_lin_min_stable_level_fraction[g])):
        return Constraint.Skip
    else:
        return \
            (mod.GenCommitLin_Provide_Power_Above_Pmin_MW[
                 g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
             + mod.GenCommitLin_Upwards_Reserves_MW[
                 g, mod.previous_timepoint[
                     tmp, mod.balancing_type_project[g]]]) \
            - \
            (mod.GenCommitLin_Provide_Power_Above_Pmin_MW[g, tmp]
             - mod.GenCommitLin_Downwards_Reserves_MW[g, tmp]) \
            <= mod.GenCommitLin_Ramp_Down_Rate_MW_Per_Tmp[
                g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]


# Startup Power
def max_startup_power_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Max_Startup_Power_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

    Startup power is 0 when the unit is committed and must be less than or
    equal to the minimum stable level when not committed.
    """

    return mod.GenCommitLin_Provide_Power_Startup_MW[g, tmp] \
           <= (1 - mod.GenCommitLin_Commit[g, tmp]) \
           * mod.GenCommitLin_Pmin_MW[g, tmp]


def ramp_during_startup_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Ramp_During_Startup_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

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
            mod.GenCommitLin_Provide_Power_Startup_MW[g, tmp] - \
            mod.GenCommitLin_Provide_Power_Startup_MW[g,
                                                      mod.previous_timepoint[
                                                          tmp,
                                                          mod
                                                              .balancing_type_project[
                                                              g]
                                                      ]
            ] \
            <= mod.GenCommitLin_Startup_Ramp_Rate_MW_Per_Tmp[
                g, mod.previous_timepoint[tmp,
                                          mod.balancing_type_project[g]]
            ]


def increasing_startup_power_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Increasing_Startup_Power_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

    GenCommitLin_Provide_Power_Startup_MW[t] can only be less than
    GenCommitLin_Provide_Power_Startup_MW[t-1] in the starting timepoint (when
    it is is back at 0). In other words, GenCommitLin_Provide_Power_Startup_MW
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
            mod.GenCommitLin_Provide_Power_Startup_MW[g, tmp] \
            - mod.GenCommitLin_Provide_Power_Startup_MW[
                g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]\
            >= - mod.GenCommitLin_Startup[g, tmp] \
            * mod.GenCommitLin_Pmin_MW[g, tmp]


def power_during_startup_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Power_During_Startup_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

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
    :param mod:
    :param g:
    :param tmp:
    :return:
    """

    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    else:
        return (mod.GenCommitLin_Commit[g, tmp]
                * mod.GenCommitLin_Pmin_MW[g, tmp]
                + mod.GenCommitLin_Provide_Power_Above_Pmin_MW[g, tmp]
                ) \
               + mod.GenCommitLin_Upwards_Reserves_MW[g, tmp] \
               - mod.GenCommitLin_Provide_Power_Startup_MW[
                   g, mod.previous_timepoint[
                       tmp, mod.balancing_type_project[g]]] \
               <= \
               (1 - mod.GenCommitLin_Startup[g, tmp]) \
               * mod.GenCommitLin_Pmax_MW[g, tmp] \
               + mod.GenCommitLin_Startup[g, tmp] \
               * mod.GenCommitLin_Startup_Ramp_Rate_MW_Per_Tmp[
                   g, mod.previous_timepoint[tmp,
                                             mod.balancing_type_project[g]]
               ]


# Shutdown Power
def max_shutdown_power_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Max_Shutdown_Power_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

    Shutdown power is 0 when the unit is committed and must be less than or
    equal to the minimum stable level when not committed
    """

    return mod.GenCommitLin_Provide_Power_Shutdown_MW[g, tmp] \
           <= (1 - mod.GenCommitLin_Commit[g, tmp]) \
           * mod.GenCommitLin_Pmin_MW[g, tmp]


def ramp_during_shutdown_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Ramp_During_Shutdown_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

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
        return mod.GenCommitLin_Provide_Power_Shutdown_MW[
                   g, mod.previous_timepoint[
                       tmp, mod.balancing_type_project[g]]] \
               - mod.GenCommitLin_Provide_Power_Shutdown_MW[g, tmp] \
               <= mod.GenCommitLin_Shutdown_Ramp_Rate_MW_Per_Tmp[
                   g, mod.previous_timepoint[tmp,
                                             mod.balancing_type_project[g]]
               ]


def decreasing_shutdown_power_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Decreasing_Shutdown_Power_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

    GenCommitLin_Provide_Power_Shutdown_MW[t] can only be less than
    GenCommitLin_Provide_Power_Shutdown_MW[t+1] if the unit stops in t+1 (when
    it is back above 0). In other words, GenCommitLin_Provide_Power_Shutdown_MW
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
            mod.GenCommitLin_Provide_Power_Shutdown_MW[g, tmp] - \
            mod.GenCommitLin_Provide_Power_Shutdown_MW[
                g, mod.next_timepoint[tmp, mod.balancing_type_project[g]]] \
            >= - mod.GenCommitLin_Shutdown[
                g, mod.next_timepoint[tmp, mod.balancing_type_project[g]]] \
            * mod.GenCommitLin_Pmin_MW[g, tmp]


def power_during_shutdown_constraint_rule(mod, g, tmp):
    """
    **Constraint Name**: GenCommitLin_Power_During_Shutdown_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

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
        return (mod.GenCommitLin_Commit[g, tmp]
                * mod.GenCommitLin_Pmin_MW[g, tmp]
                + mod.GenCommitLin_Provide_Power_Above_Pmin_MW[g,
                                                               tmp]) \
               + mod.GenCommitLin_Upwards_Reserves_MW[g, tmp] \
               - mod.GenCommitLin_Provide_Power_Shutdown_MW[
                   g, mod.next_timepoint[
                       tmp, mod.balancing_type_project[g]]] \
               <= \
               (1 - mod.GenCommitLin_Shutdown[g, mod.next_timepoint[
                   tmp, mod.balancing_type_project[g]]]) \
               * mod.GenCommitLin_Pmax_MW[
                   g, mod.next_timepoint[tmp, mod.balancing_type_project[g]]] \
               + mod.GenCommitLin_Shutdown[
                   g, mod.next_timepoint[tmp, mod.balancing_type_project[g]]] \
               * mod.GenCommitLin_Shutdown_Ramp_Rate_MW_Per_Tmp[g, tmp]


def fuel_burn_constraint_rule(mod, g, tmp, s):
    """
    **Constraint Name**: GenCommitLin_Fuel_Burn_Constraint
    **Enforced Over**: GEN_COMMIT_LIN_OPR_TMPS

    Fuel burn is set by piecewise linear representation of input/output
    curve.

    Note: we assume that when projects are derated for availability, the
    input/output curve is derated by the same amount. The implicit
    assumption is that when a generator is de-rated, some of its units
    are out rather than it being forced to run below minimum stable level
    at very inefficient operating points.
    """
    return \
        mod.GenCommitLin_Fuel_Burn_MMBTU[g, tmp] \
        >= \
        mod.fuel_burn_slope_mmbtu_per_mwh[g, s] \
        * mod.GenCommitLin_Provide_Power_MW[g, tmp] \
        + mod.fuel_burn_intercept_mmbtu_per_hr[g, s] \
        * mod.Availability_Derate[g, tmp] \
        * mod.GenCommitLin_Synced[g, tmp]


# Operational Type Methods
###############################################################################

def power_provision_rule(mod, g, tmp):
    """
    Power provision for gen_commit_lin generators is a variable constrained
    constrained to be between the generator's minimum stable level and its
    capacity if the generator is committed and 0 otherwise.
    """
    return mod.GenCommitLin_Provide_Power_MW[g, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision of dispatchable generators is an endogenous variable.
    """
    return mod.GenCommitLin_Provide_Power_MW[g, tmp]


def commitment_rule(mod, g, tmp):
    """
    Commitment decision in each timepoint
    """
    # TODO: shouldn't we return MW here to make this consistent w
    #  gen_commit_cap?
    return mod.GenCommitLin_Commit[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Capacity online in each timepoint.
    """
    return mod.GenCommitLin_Pmax_MW[g, tmp] \
           * mod.GenCommitLin_Commit[g, tmp]


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
        return mod.GenCommitLin_Fuel_Burn_MMBTU[g, tmp]
    else:
        raise ValueError(error_message)


def startup_cost_rule(mod, g, tmp):
    """
    Startup costs are applied in each timepoint based on the amount of capacity
    (in MW) that is started up in that timepoint and the startup cost
    parameter.
    """
    return mod.GenCommitLin_Startup[g, tmp] \
        * mod.GenCommitLin_Pmax_MW[g, tmp] \
        * mod.gen_commit_lin_startup_cost_per_mw[g]


def shutdown_cost_rule(mod, g, tmp):
    """
    Shutdown costs are applied in each timepoint based on the amount of
    capacity (in Mw) that is shut down in that timepoint and the shutdown
    cost parameter.
    """
    return mod.GenCommitLin_Shutdown[g, tmp] \
        * mod.GenCommitLin_Pmax_MW[g, tmp] \
        * mod.gen_commit_lin_shutdown_cost_per_mw[g]


def startup_fuel_burn_rule(mod, g, tmp):
    """
    Startup fuel burn is applied in each timepoint based on the amount of
    capacity (in MW) that is started up in that timepoint and the startup
    fuel parameter.
    """
    return mod.GenCommitLin_Startup[g, tmp] \
        * mod.GenCommitLin_Pmax_MW[g, tmp] \
        * mod.gen_commit_lin_startup_fuel_mmbtu_per_mw[g]


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
        return mod.GenCommitLin_Provide_Power_Above_Pmin_MW[g, tmp] \
               - mod.GenCommitLin_Provide_Power_Above_Pmin_MW[
                   g, mod.previous_timepoint[
                       tmp, mod.balancing_type_project[g]]]


def fix_commitment(mod, g, tmp):
    """
    """
    mod.GenCommitLin_Commit[g, tmp] = \
        mod.fixed_commitment[g, mod.previous_stage_timepoint_map[tmp]]
    mod.GenCommitLin_Commit[g, tmp].fixed = True


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
    startup_plus_ramp_up_rate = dict()
    shutdown_plus_ramp_down_rate = dict()
    ramp_up_when_on_rate = dict()
    ramp_down_when_on_rate = dict()
    min_up_time = dict()
    min_down_time = dict()
    startup_cost = dict()
    shutdown_cost = dict()
    startup_fuel = dict()

    header = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t", header=None, nrows=1
    ).values[0]

    optional_columns = ["startup_plus_ramp_up_rate",
                        "shutdown_plus_ramp_down_rate",
                        "ramp_up_when_on_rate",
                        "ramp_down_when_on_rate",
                        "min_up_time_hours",
                        "min_down_time_hours",
                        "startup_cost_per_mw",
                        "shutdown_cost_per_mw",
                        "startup_fuel_mmbtu_per_mw"]
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
        if row[1] == "gen_commit_lin":
            min_stable_fraction[row[0]] = float(row[2])
        else:
            pass
    data_portal.data()["gen_commit_lin_min_stable_level_fraction"] = \
        min_stable_fraction

    # Ramp rate limits are optional, will default to 1 if not specified
    if "startup_plus_ramp_up_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["startup_plus_ramp_up_rate"]):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                startup_plus_ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_lin_startup_plus_ramp_up_rate"] = \
            startup_plus_ramp_up_rate

    if "shutdown_plus_ramp_down_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["shutdown_plus_ramp_down_rate"]):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                shutdown_plus_ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_lin_shutdown_plus_ramp_down_rate"] = \
            shutdown_plus_ramp_down_rate

    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_up_when_on_rate"]):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                ramp_up_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_lin_ramp_up_when_on_rate"] = \
            ramp_up_when_on_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_down_when_on_rate"]):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                ramp_down_when_on_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_lin_ramp_down_when_on_rate"] = \
            ramp_down_when_on_rate

    # Up and down time limits are optional, will default to 1 if not specified
    if "min_up_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["min_up_time_hours"]):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                min_up_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_lin_min_up_time_hrs"] = min_up_time

    if "min_down_time_hours" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["min_down_time_hours"]):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                min_down_time[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_lin_min_down_time_hrs"] = min_down_time

    # Startup/shutdown costs are optional, will default to 0 if not specified
    if "startup_cost_per_mw" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["startup_cost_per_mw"]
                       ):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                startup_cost[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_lin_startup_cost_per_mw"] = startup_cost

    if "shutdown_cost_per_mw" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["shutdown_cost_per_mw"]
                       ):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                shutdown_cost[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_lin_shutdown_cost_per_mw"] = \
            shutdown_cost

    # Startup fuel is optional, will default to 0 if not specified
    if "startup_fuel_mmbtu_per_mw" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["startup_fuel_mmbtu_per_mw"]
                       ):
            if row[1] == "gen_commit_lin" and row[2] != ".":
                startup_fuel[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_commit_lin_startup_fuel_mmbtu_per_mw"] = \
            startup_fuel


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
                           "dispatch_continuous_commit.csv"),
              "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "balancing_type_project",
                         "horizon", "timepoint", "timepoint_weight",
                         "number_of_hours_in_timepoint", "technology",
                         "load_zone", "power_mw", "committed_mw",
                         "committed_units", "started_units", "stopped_units",
                         "synced_units"
                         ])

        for (p, tmp) in mod.GEN_COMMIT_LIN_OPR_TMPS:
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
                value(mod.GenCommitLin_Provide_Power_MW[p, tmp]),
                value(mod.GenCommitLin_Pmax_MW[p, tmp])
                * value(mod.GenCommitLin_Commit[p, tmp]),
                value(mod.GenCommitLin_Commit[p, tmp]),
                value(mod.GenCommitLin_Startup[p, tmp]),
                value(mod.GenCommitLin_Shutdown[p, tmp]),
                value(mod.GenCommitLin_Synced[p, tmp])
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
        print("project dispatch continuous commit")

    update_dispatch_results_table(
        db=db, c=c, results_directory=results_directory,
        scenario_id=scenario_id, subproblem=subproblem, stage=stage,
        results_file="dispatch_continuous_commit.csv"
    )


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

    # Get project inputs
    c1 = conn.cursor()
    projects = c1.execute(
        """SELECT project, operational_type,
        min_stable_level, unit_size_mw,
        startup_cost_per_mw, shutdown_cost_per_mw,
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
        startup_cost_per_mw, shutdown_cost_per_mw,
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
            "gen_commit_lin"
        )
    )

    df = pd.DataFrame(
        data=projects.fetchall(),
        columns=[s[0] for s in projects.description]
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
    validation_errors = check_req_prj_columns(df, req_columns, True,
                                              "gen_commit_lin")
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
    validation_errors = check_req_prj_columns(df, expected_na_columns, False,
                                              "gen_commit_lin")
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

    # Check startup shutdown rate inputs
    validation_errors = validate_startup_shutdown_rate_inputs(df, hrs_in_tmp)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "Invalid startup/shutdown ramp inputs",
             error
             )
        )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)

