# Copyright 2016-2020 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This operational type is the same as the *gen_commit_bin* operational type,
but the commitment decisions are declared as continuous (with bounds of 0 to
1) instead of binary, so 'partial' generators can be committed. This
linear relaxation treatment can be helpful in situations when mixed-integer
problem run-times are long and is similar to loosening the MIP gap (but can
target specific generators). Please refer to the *gen_commit_bin* module for
more information on the formulation.
"""

from __future__ import division

import csv
import os.path
from pyomo.environ import Var, Set, Param, Constraint, NonNegativeReals, \
    PercentFraction, Boolean, Expression, value

from gridpath.auxiliary.auxiliary import subset_init_by_param_value
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.operations.operational_types.common_functions import \
    determine_relevant_timepoints, update_dispatch_results_table, \
    load_optype_module_specific_data, load_startup_chars, \
    check_for_tmps_to_link, validate_opchars
from gridpath.project.common_functions import \
    check_if_boundary_type_and_first_timepoint, check_if_last_timepoint, \
    check_boundary_type
import gridpath.project.operations.operational_types.gen_commit_unit_common \
    as gen_commit_unit_common


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_COMMIT_LIN`                                                |
    |                                                                         |
    | The set of generators of the :code:`gen_commit_lin` operational type.   |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_LIN_STARTUP_BY_ST_PRJS`                             |
    | | *within*: :code:`GEN_COMMIT_LIN`                                      |
    |                                                                         |
    | The set of generators of the :code:`gen_commit_lin` operational type    |
    | that also have startup ramp rates specified.                            |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_LIN_STARTUP_BY_ST_PRJS_TYPES`                       |
    |                                                                         |
    | Two-dimensional set of generators of the the :code:`gen_commit_lin`     |
    | and their startup types (if the project is in                           |
    | :code:`GEN_COMMIT_LIN_STARTUP_BY_ST_PRJS`). Startup types are ordered   |
    | from hottest to coldest, e.g. if there are 3 startup types the hottest  |
    | start is indicated by 1, and the coldest start is indicated by 3.       |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_LIN_OPR_TMPS`                                       |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_commit_lin`       |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_LIN_OPR_TMPS_STR_TYPES`                             |
    |                                                                         |
    | Three-dimensional set with generators of the :code:`gen_commit_lin`     |
    | operational type, their operational timepoints, and their startup       |
    | types (if the project is in :code:`GEN_COMMIT_LIN_STARTUP_BY_ST_PRJS`). |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_LIN_STR_TYPES_BY_PRJ`                               |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    |                                                                         |
    | Indexed set that describes the startup types for each project of the    |
    | :code:`gen_commit_lin` operational type.                                |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_LIN_LINKED_TMPS`                                    |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_commit_lin`       |
    | operational type and their linked timepoints.                           |
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
    | | :code:`gen_commit_lin_startup_plus_ramp_up_rate_by_st`                |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_STARTUP_BY_ST_PRJS_TYPES`       |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's upward ramp rate limit during startup for a given         |
    | startup type, defined as a fraction of its capacity per minute. If,     |
    | after adjusting for timepoint duration, this is smaller than the        |
    | minimum stable level, the project will have a startup trajectory across |
    | multiple timepoints.                                                    |
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
    | | :code:`gen_commit_lin_min_up_time_hours`                              |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The project's minimum up time in hours.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_min_down_time_hours`                            |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The project's minimum down time in hours.                               |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_aux_consumption_frac_capacity`                  |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | Auxiliary consumption as a fraction of committed capacity.              |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_aux_consumption_frac_power`                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | Auxiliary consumption as a fraction of gross power output.              |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_down_time_cutoff_hours`                         |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_STARTUP_BY_ST_PRJS_TYPES`       |
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
    | Derived Params                                                          |
    +=========================================================================+
    | | :code:`gen_commit_lin_allow_ramp_up_violation`                        |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`Boolean`                                             |
    |                                                                         |
    | Determines whether the ramp up constraint can be violated. It is 1 if a |
    | ramp_up_violation_penalty is specified for the project.                 |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_allow_ramp_down_violation`                      |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`Boolean`                                             |
    |                                                                         |
    | Determines whether the ramp down constraint can be violated. It is 1 if |
    | a ramp_down_violation_penalty is specified for the project.             |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_allow_min_up_time_violation`                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`Boolean`                                             |
    |                                                                         |
    | Determines whether the min up time constraint can be violated. It is 1  |
    | if a min_up_time_violation_penalty is specified for the project.        |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_allow_min_down_time_violation`                  |
    | | *Defined over*: :code:`GEN_COMMIT_LIN`                                |
    | | *Within*: :code:`Boolean`                                             |
    |                                                                         |
    | Determines whether the min down time constraint can be violated. It is  |
    | 1 if a min_down_time_violation_penalty is specified for the project.    |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Linked Input Params                                                     |
    +=========================================================================+
    | | :code:`gen_commit_lin_linked_commit`                                  |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_LINKED_TMPS`                    |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The project's commitment status in the linked timepoints.               |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_linked_startup`                                 |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_LINKED_TMPS`                    |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The project's startup status in the linked timepoints.                  |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_linked_shutdown`                                |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_LINKED_TMPS`                    |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The project's shutdown status in the linked timepoints.                 |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_linked_power_above_pmin`                        |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_LINKED_TMPS`                    |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's power provision above Pmin in the linked timepoints.      |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_linked_upwards_reserves`                        |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_LINKED_TMPS`                    |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's upward reserve provision in the linked timepoints.        |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_linked_downwards_reserves`                      |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_LINKED_TMPS`                    |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's downward reserve provision in the linked timepoints.      |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_linked_ramp_up_rate_mw_per_tmp`                 |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_LINKED_TMPS`                    |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's upward ramp rate in MW in the linked timepoints           |
    | (depends on timepoint duration.)                                        |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_linked_ramp_down_rate_mw_per_tmp`               |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_LINKED_TMPS`                    |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's downward ramp rate in MW in the linked timepoints         |
    | (depends on timepoint duration.)                                        |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_linked_provide_power_startup_by_st_mw`          |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_LINKED_TMPS_STR_TYPES`          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's startup power provision by startup type for each linked   |
    | timepoint.                                                              |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_linked_startup_ramp_rate_by_st_mw_per_tmp`      |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_LINKED_TMPS_STR_TYPES`          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's startup ramp rate in MW by startup type in the linked     |
    | timepoints (depends on timepoint duration.)                             |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_linked_provide_power_shutdown_mw`               |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_LINKED_TMPS`                    |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's shutdown power provision for each linked timepoint.       |
    +-------------------------------------------------------------------------+
    | | :code:`gen_commit_lin_linked_shutdown_ramp_rate_mw_per_tmp`           |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_LINKED_TMPS`                    |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's shutdown ramp rate in MW in the linked timepointsvvv      |
    | (depends on timepoint duration.)                                        |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`GenCommitLin_Commit`                                           |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Continuous variable which represents the commitment decision in each    |
    | operational timepoint. It is one if the unit is committed and zero      |
    | otherwise (including during a startup and shutdown trajectory).         |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Startup`                                          |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Continuous variable which is one if the unit starts up and zero         |
    | otherwise. A startup is defined as changing commitment from zero to one.|
    | Note: this variable is zero throughout a startup trajectory!            |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Startup_Type`                                     |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | Continuous variable which is one if the unit starts up for the given    |
    | startup type and zero otherwise. A startup is defined as changing       |
    | commitment from zero to one, whereas the startup type indicates the     |
    | hotness/coldness of the start. Note: this variable is zero throughout   |
    | a startup trajectory!                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Shutdown`                                         |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Continuous variable which is one if the unit shuts down and zero        |
    | otherwise. A shutdown is defined as changing commitment from one to     |
    | zero. Note: this variable is zero throughout a shutdown trajectory!     |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Synced`                                           |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Continuous variable which is one if the project is providing *any* power|
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
    | | :code:`GenCommitLin_Provide_Power_Startup_By_ST_MW`                   |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | Power provision during startup in each timepoint in which the project   |
    | is starting up, for each startup type (zero if project is committed or  |
    | not starting up).                                                       |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Provide_Power_Shutdown_MW`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Power provision during shutdown in each timepoint in which the project  |
    | is shutting down (zero if project is committed or not shutting down).   |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Ramp_Up_Violation_MW`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Violation of the project's ramp up constraint in each operational       |
    | timepoint.                                                              |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Ramp_Down_Violation_MW`                           |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Violation of the project's ramp down constraint in each operational     |
    | timepoint.                                                              |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Min_Up_Time_Violation`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Violation of the project's min up time constraint in each operational   |
    | timepoint.                                                              |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Min_Down_Time_Violation`                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Violation of the project's min down time constraint in each operational |
    | timepoint.                                                              |
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
    | | :code:`GenCommitLin_Provide_Power_Startup_MW`                         |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Power provision during startup in each timepoint in which the project   |
    | is starting up (zero if project is committed or not starting up).       |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Provide_Power_MW`                                 |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's total power output (in MW) in each operational timepoint, |
    | including power from a startup or shutdown trajectory. If modeling      |
    | auxiliary consumption, this is the gross power output.                  |
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
    | | :code:`GenCommitLin_Startup_Ramp_Rate_By_ST_MW_Per_Tmp`               |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | The project's upward ramp-able capacity (in MW) during startup in each  |
    | operational timepoint. Depends on the                                   |
    | :code:`gen_commit_lin_startup_plus_ramp_up_rate_by_st`                  |
    | availability and capacity in the timepoint, and the timepoint's         |
    | duration.                                                               |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Shutdown_Ramp_Rate_MW_Per_Tmp`                    |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's downward ramp-able capacity (in MW) during shutdown in    |
    | each operational timepoint. Depends on the                              |
    | :code:`gen_commit_lin_shutdown_plus_ramp_down_rate`, the availability   |
    | and capacity in the timepoint, and the timepoint's duration.            |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Active_Startup_Type`                              |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's active startup type in each operational timepoint,        |
    | described as an integer. If no startup type is active (the project is   |
    | not starting up in this timepoint), this expression returns zero.       |
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
    | | :code:`GenCommitLin_Auxiliary_Consumption_MW`                         |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | The project's auxiliary consumption (power consumed on-site and not     |
    | sent to the grid) in each timepoint.                                    |
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
    | Defines the relationship between the linear commitment, startup, and    |
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
    | :code:`gen_commit_lin_min_up_time_hours`.                               |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Min_Down_Time_Constraint`                         |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Requires that when the project is shut down, it stays off for at least  |
    | :code:`gen_commit_lin_min_up_time_hours`.                               |
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
    | | :code:`GenCommitLin_Unique_Startup_Type_Constraint`                   |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Ensures that only one startup type can be active at the same time.      |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Active_Startup_Type_Constraint`                   |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | Ensures that a startup type can only be active if the unit has been     |
    | down for the appropriate interval.                                      |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Max_Startup_Power_Constraint`                     |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS`                       |
    |                                                                         |
    | Limits startup power to zero when the project is committed and to the   |
    | minimum stable level when it is not committed.                          |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Ramp_During_Startup_By_ST_Constraint`             |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | Limits the allowed project upward startup power ramp based on the       |
    | :code:`gen_commit_lin_startup_plus_ramp_up_rate_by_st`.                 |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Increasing_Startup_Power_By_ST_Constraint`        |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | Requires that the startup power always increases, except for the        |
    | startup timepoint (when :code:`GenCommitLin_Startup` is one).           |
    +-------------------------------------------------------------------------+
    | | :code:`GenCommitLin_Power_During_Startup_By_ST_Constraint`            |
    | | *Defined over*: :code:`GEN_COMMIT_LIN_OPR_TMPS_STR_TYPES`             |
    |                                                                         |
    | Limits the difference between the power provision in the startup        |
    | timepoint and the startup power in the previous timepoint based on the  |
    | :code:`gen_commit_lin_startup_plus_ramp_up_rate_by_st`.                 |
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

    """

    gen_commit_unit_common.add_model_components(
        m=m, d=d,
        scenario_directory=scenario_directory,
        subproblem=subproblem, stage=stage,
        bin_or_lin_optype="gen_commit_lin"
    )
    

# Operational Type Methods
###############################################################################

def power_provision_rule(mod, g, tmp):
    """
    Power provision for gen_commit_lin generators is a variable constrained
    constrained to be between the generator's minimum stable level and its
    capacity if the generator is committed and 0 otherwise.
    """
    return gen_commit_unit_common.power_provision_rule(
        mod, g, tmp, "Lin"
    )


def commitment_rule(mod, g, tmp):
    """
    Commitment decision in each timepoint
    """
    return gen_commit_unit_common.commitment_rule(
        mod, g, tmp, "Lin"
    )


def online_capacity_rule(mod, g, tmp):
    """
    Capacity online in each timepoint.
    """
    return gen_commit_unit_common.online_capacity_rule(
        mod, g, tmp, "Lin"
    )


def variable_om_cost_rule(mod, g, tmp):
    """
    Variable O&M cost has two components which are additive:
    1. A fixed variable O&M rate (cost/MWh) that doesn't change with loading
       levels: :code:`variable_om_cost_per_mwh`.
    2. A variable variable O&M rate that changes with the loading level,
       similar to the heat rates. The idea is to represent higher variable cost
       rates at lower loading levels. This is captured in the
       :code:`GenCommitLin_Variable_OM_Cost_By_LL` decision variable. If no
       variable O&M curve inputs are provided, this component will be zero.

    Most users will only use the first component, which is specified in the
    operational characteristics table.  Only operational types with
    commitment decisions can have the second component.

    We need to explicitly have the op type method here because of auxiliary
    consumption. The default method takes Power_Provision_MW multiplied by
    the variable cost, and Power_Provision_MW is equal to Provide_Power_MW
    minus the auxiliary consumption. The variable cost should be applied to
    the gross power.
    """
    return gen_commit_unit_common.variable_om_cost_rule(
        mod, g, tmp, "Lin"
    )


def variable_om_cost_by_ll_rule(mod, g, tmp, s):
    """
    Variable O&M cost has two components which are additive:
    1. A fixed variable O&M rate (cost/MWh) that doesn't change with loading
       levels: :code:`variable_om_cost_per_mwh`.
    2. A variable variable O&M rate that changes with the loading level,
       similar to the heat rates. The idea is to represent higher variable cost
       rates at lower loading levels. This is captured in the
       :code:`GenCommitLin_Variable_OM_Cost_By_LL` decision variable. If no
       variable O&M curve inputs are provided, this component will be zero.

    Most users will only use the first component, which is specified in the
    operational characteristics table.  Only operational types with
    commitment decisions can have the second component.
    """
    return gen_commit_unit_common.variable_om_cost_by_ll_rule(
        mod, g, tmp, s, "Lin"
    )


def startup_cost_simple_rule(mod, g, tmp):
    """
    Simple startup costs are applied in each timepoint based on the amount of
    capacity (in MW) that is started up in that timepoint and the startup cost
    parameter.
    """
    return gen_commit_unit_common.startup_cost_simple_rule(
        mod, g, tmp, "Lin"
    )


def startup_cost_by_st_rule(mod, g, tmp):
    """
    Startup costs are applied in each timepoint based on the amount of capacity
    (in MW) that is started up in that timepoint for a given startup type and
    the startup cost parameter for that startup type. We take the sum across
    all startup types since only one startup type is active at the same time.
    """
    return gen_commit_unit_common.startup_cost_by_st_rule(
        mod, g, tmp, "LIN", "Lin"
    )


def shutdown_cost_rule(mod, g, tmp):
    """
    Shutdown costs are applied in each timepoint based on the amount of
    capacity (in Mw) that is shut down in that timepoint and the shutdown
    cost parameter.
    """
    return gen_commit_unit_common.shutdown_cost_rule(
        mod, g, tmp, "Lin"
    )


def fuel_burn_by_ll_rule(mod, g, tmp, s):
    """
    """
    return gen_commit_unit_common.fuel_burn_by_ll_rule(
        mod, g, tmp, s, "Lin"
    )


def startup_fuel_burn_rule(mod, g, tmp):
    """
    Startup fuel burn is applied in each timepoint based on the amount of
    capacity (in MW) that is started up in that timepoint and the startup
    fuel parameter. This does not vary by startup type.
    """
    return gen_commit_unit_common.startup_fuel_burn_rule(
        mod, g, tmp, "Lin"
    )


def power_delta_rule(mod, g, tmp):
    """
    Ramp between this timepoint and the previous timepoint.
    Actual ramp rate in MW/hr depends on the duration of the timepoints.
    This is only used in tuning costs, so fine to skip for linked horizon's
    first timepoint.
    """
    return gen_commit_unit_common.power_delta_rule(
        mod, g, tmp, "Lin"
    )


def fix_commitment(mod, g, tmp):
    """
    """
    return gen_commit_unit_common.fix_commitment(
        mod, g, tmp, "Lin"
    )


def operational_violation_cost_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return gen_commit_unit_common.operational_violation_cost_rule(
        mod, g, tmp, "lin", "Lin"
    )


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

    gen_commit_unit_common.load_module_specific_data(
        mod=mod, data_portal=data_portal,
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, bin_or_lin_optype="gen_commit_lin", bin_or_lin="lin",
        BIN_OR_LIN="LIN"
    )


def export_module_specific_results(
    mod, d, scenario_directory, subproblem, stage
):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    gen_commit_unit_common.export_module_specific_results(
        mod=mod, d=d, scenario_directory=scenario_directory,
        subproblem=subproblem, stage=stage, BIN_OR_LIN="LIN",
        Bin_or_Lin="Lin", bin_or_lin="lin",
        results_filename="dispatch_continuous_commit.csv"
    )



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

def validate_module_specific_inputs(
    scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and validate the inputs

    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Validate operational chars table inputs
    opchar_df = validate_opchars(
        scenario_id, subscenarios, subproblem, stage, conn, "gen_commit_lin"
    )
