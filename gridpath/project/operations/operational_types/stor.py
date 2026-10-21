# Copyright 2016-2023 Blue Marble Analytics LLC.
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
This operational type describes a generic storage resource. It can be
applied to a battery, to a pumped-hydro project or another storage
technology.

The type is associated with three main variables in each timepoint when the
project is available: the charging level, the discharging level, and the
energy available in storage. The first two are constrained to be less than
or equal to the project's power capacity. The third is constrained to be
less than or equal to the project's energy capacity. The model tracks the
stage of charge in each timepoint based on the charging and discharging
decisions in the previous timepoint, with adjustments for charging and
discharging efficiencies. Storage projects can be allowed to provide upward
and/or downward reserves.

Costs for this operational type include variable O&M costs.

**Multi-sample horizons.** The energy in storage is tracked timepoint to
timepoint along each horizon. On a horizon whose timepoints all carry the
same weight (a single sample, e.g. one representative day repeated by its
weight), the chain is the horizon's chronology and nothing else is needed.
A horizon can also hold several samples with different weights, e.g. a
half-month represented by a peak day of weight 1 followed by a median day
of weight 14, so that the project can move energy between the sampled days.
The type then reads the horizon as a sequence of *sample blocks* (maximal
runs of consecutive timepoints with the same weight) and treats each block
of weight greater than 1 as repeated as many times as its weight before the
chronology moves on: the energy carried into the timepoint after the block
is the energy at the end of the block's last repeat
(:code:`Stor_Sample_Block_Repeat_Carryover_MWh` is added in the energy
tracking constraint), and the energy in storage at the last repeat, which
differs from the first repeat's by
:code:`Stor_Last_Repeat_SOC_Offset_MWh`, must satisfy the same bounds as
the first repeat's (the :code:`Stor_Last_Repeat_*` constraints). The energy
across repeats is monotonic, so bounding the first and the last repeat
bounds every repeat, with a storage efficiency below 1 as well (the
offsets then follow a geometric rather than an arithmetic series). The
model's variables describe the first repeat; the results report the
starting energy at the last repeat alongside them. Horizons with a single
sample are unaffected, as are blocks of weight 1 (and weight 0, e.g. spinup
or lookahead timepoints, which do not count as samples). A linked horizon
with several samples is refused, as is an exogenous state of charge inside
a repeated block. The per-horizon losses limit and the state-of-charge
penalties see the first repeat only.

.. note:: Please note that to calculate the duration of the storage project, i.e.,
    how long it can sustain discharging at its maximum output, you must adjust the
    energy capacity by the discharge efficiency. For example, a 1 MW  with 1 MWh energy
    capacity battery with discharging losses of 5% (discharging_loss_factor = 95%) would
    have a duration of 1 MWh / (1 MW/0.95) or 0.95 hours rather than 1 hour.

.. note:: Model construction performance: most components in this module are
    indexed by project-timepoint, so their initialization and constraint/
    expression rules are called once per index -- millions of times in
    production-scale scenarios. Per-index work that only depends on the
    project (or can be looked up once) is therefore deliberately hoisted:

    * :code:`STOR_OPR_BT_HRZ` checks horizon-timepoint membership
      element-by-element with O(1) lookups against :code:`PRJ_OPR_TMPS` and
      iterates only the horizons of the project's energy-budget balancing
      type. (Testing
      with :code:`set(...).issubset(mod.PRJ_OPR_TMPS)` would materialize the
      entire multi-million-element superset into a temporary Python set on
      every check.)
    * The reserve expressions delegate to
      :code:`gridpath.project.operations.reserves.reserve_aggregation`,
      which resolves reserve variable names to component objects once per
      model instance instead of calling :code:`getattr` per index.
    * The tracking/ramp-style rules look up
      :code:`mod.balancing_type_project[prj]` and :code:`mod.prev_tmp[...]`
      once per call and reuse the local, rather than re-indexing the params
      for every term of the returned expression.
    * Derived sets initialized by filtering a superset do not re-declare
      that superset as :code:`within` -- the domain check is redundant with
      the initializer and roughly doubles set construction time. (Sets
      loaded from input data, like :code:`STOR_EXOG_SOC_TMPS`, keep
      :code:`within` since there it validates user input.)

"""

import csv
import os.path
from pyomo.environ import (
    Var,
    Set,
    Constraint,
    Param,
    Expression,
    NonNegativeIntegers,
    NonNegativeReals,
    PercentFraction,
    value,
)
import warnings

from gridpath.auxiliary.auxiliary import (
    subset_init_by_param_value,
    subset_init_by_set_membership,
)
from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.auxiliary.dynamic_components import headroom_variables, footroom_variables
from gridpath.project.operations.reserves.reserve_aggregation import (
    headroom_provision_rule,
    footroom_provision_rule,
)
from gridpath.project.common_functions import (
    check_if_first_timepoint,
    check_if_last_timepoint,
    check_boundary_type,
    get_energy_budget_balancing_type,
)
from gridpath.project.operations.operational_types.common_functions import (
    load_optype_model_data,
    check_for_tmps_to_link,
    validate_opchars,
    write_tab_file_model_inputs,
    get_prj_temporal_index_opr_inputs_from_db,
)
from gridpath.common_functions import create_results_df


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`STOR`                                                          |
    |                                                                         |
    | The set of projects of the :code:`stor` operational type.               |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_OPR_TMPS`                                                 |
    |                                                                         |
    | Two-dimensional set with projects of the :code:`stor`                   |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_LINKED_TMPS`                                              |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`stor`                 |
    | operational type and their linked timepoints.                           |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_OPR_BT_HRZ`                                               |
    |                                                                         |
    | Three-dimensional set with projects of the :code:`stor` operational     |
    | type and the (balancing type, horizon)s of their energy-budget          |
    | balancing type (see :code:`stor_energy_budget_balancing_type`) that     |
    | lie entirely within their operational timepoints; the max-losses        |
    | limit is enforced over these horizons.                                  |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_SAMPLE_BLOCKS`                                            |
    |                                                                         |
    | Two-dimensional set of projects of the :code:`stor` operational type    |
    | and the first timepoint of each repeated sample block of their          |
    | multi-sample horizons (see the module description). Empty when every    |
    | horizon holds a single sample.                                          |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_SAMPLE_BLOCK_TMPS`                                        |
    | | *Defined over*: :code:`STOR_SAMPLE_BLOCKS`                            |
    |                                                                         |
    | Indexed set of the timepoints of each repeated sample block, in         |
    | chronological order.                                                    |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_SAMPLE_BLOCK_OPR_TMPS`                                    |
    |                                                                         |
    | Two-dimensional set of the project-timepoints that lie in a repeated    |
    | sample block.                                                           |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_SAMPLE_BLOCK_TRANSITION_OPR_TMPS`                         |
    |                                                                         |
    | Two-dimensional set of the project-timepoints that follow a repeated    |
    | sample block (the horizon's first timepoint when the block ends a       |
    | circular horizon); their energy tracking constraint adds the block's    |
    | repeat carryover.                                                       |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Derived Params                                                          |
    +-------------------------------------------------------------------------+
    | | :code:`stor_sample_block_weight`                                      |
    | | *Defined over*: :code:`STOR_SAMPLE_BLOCKS`                            |
    |                                                                         |
    | The timepoint weight of the repeated sample block, i.e. the number of   |
    | times it is repeated.                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`stor_sample_block`                                             |
    | | *Defined over*: :code:`STOR_SAMPLE_BLOCK_OPR_TMPS`                    |
    |                                                                         |
    | The first timepoint of the repeated sample block the timepoint lies     |
    | in.                                                                     |
    +-------------------------------------------------------------------------+
    | | :code:`stor_sample_block_position`                                    |
    | | *Defined over*: :code:`STOR_SAMPLE_BLOCK_OPR_TMPS`                    |
    |                                                                         |
    | The timepoint's 0-based position in its repeated sample block.          |
    +-------------------------------------------------------------------------+
    | | :code:`stor_sample_block_before`                                      |
    | | *Defined over*: :code:`STOR_SAMPLE_BLOCK_TRANSITION_OPR_TMPS`         |
    |                                                                         |
    | The first timepoint of the repeated sample block that the timepoint     |
    | follows.                                                                |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`stor_charging_efficiency`                                      |
    | | *Defined over*: :code:`STOR`                                          |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The storage project's charging efficiency (1 = 100% efficient).         |
    +-------------------------------------------------------------------------+
    | | :code:`stor_discharging_efficiency`                                   |
    | | *Defined over*: :code:`STOR`                                          |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The storage project's discharging efficiency (1 = 100% efficient).      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`stor_storage_efficiency`                                       |
    | | *Defined over*: :code:`STOR`                                          |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The storage project's storage efficiency (1 = 100% efficient).          |
    +-------------------------------------------------------------------------+
    | | :code:`stor_losses_factor_in_energy_target`                           |
    | | *Defined over*: :code:`STOR`                                          |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The fraction of storage losses that count against the energy target.    |
    +-------------------------------------------------------------------------+
    | | :code:`stor_max_losses_in_hrz_frac_stor_energy_capacity`              |
    | | *Defined over*: :code:`STOR`                                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`inf`                                                |
    |                                                                         |
    | The maximum losses (charging minus discharging energy) in each          |
    | horizon of the project's energy-budget balancing type, as a fraction    |
    | of the project's energy capacity.                                       |
    +-------------------------------------------------------------------------+
    | | :code:`stor_energy_budget_balancing_type`                             |
    | | *Defined over*: :code:`STOR`                                          |
    | | *Within*: :code:`BLN_TYPES`                                           |
    | | *Default*: the project's :code:`balancing_type_project`               |
    |                                                                         |
    | The balancing type of the horizons over which the max-losses limit      |
    | applies. The project's :code:`balancing_type_project` continues to      |
    | govern chronology (state-of-charge tracking and horizon-boundary        |
    | handling).                                                              |
    +-------------------------------------------------------------------------+
    | | :code:`stor_losses_factor_curtailment`                                |
    | | *Defined over*: :code:`STOR`                                          |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The fraction of storage losses that count against curtailment.          |
    +-------------------------------------------------------------------------+
    | | :code:`stor_charging_capacity_multiplier`                             |
    | | *Defined over*: :code:`STOR`                                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`1.0`                                                |
    |                                                                         |
    | The storage project's charging capacity multiplier to be used if the    |
    | charging capacity is different from the nameplate capacity.             |
    +-------------------------------------------------------------------------+
    | | :code:`stor_discharging_capacity_multiplier`                          |
    | | *Defined over*: :code:`STOR`                                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`1.0`                                                |
    |                                                                         |
    | The storage project's discharging capacity multiplier to be used if the |
    | discharging capacity is different from the nameplate capacity.          |
    +-------------------------------------------------------------------------+
    | | :code:`stor_exogenous_starting_state_of_charge`                       |
    | | *Defined over*: :code:`STOR_EXOG_SOC_TMPS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The storage project's exogenously specified starting state of charge.   |
    | If not specified, the state of charge is endogenously determined by the |
    | optimization subject to the rest of the constraints.                    |
    +-------------------------------------------------------------------------+
    | | :code:`stor_reserves_setpoint_duration_hours`                         |
    | | *Defined over*: :code:`STOR`                                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The number of hours for which the project must be able to sustain the   |
    | new setpoint if its reserves are called, i.e., the duration over which  |
    | the upward (downward) reserves must be backed by energy (room) in       |
    | storage in the headroom (footroom) energy constraints. If not           |
    | specified, the timepoint duration is used, i.e., the new setpoint must  |
    | be sustainable for the full timepoint.                                  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Linked Input Params                                                     |
    +=========================================================================+
    | | :code:`stor_linked_starting_energy_in_storage`                        |
    | | *Defined over*: :code:`STOR_LINKED_TMPS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's starting energy in storage in the linked timepoints.      |
    +-------------------------------------------------------------------------+
    | | :code:`stor_linked_discharge`                                         |
    | | *Defined over*: :code:`STOR_LINKED_TMPS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's dicharging in the linked timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`stor_linked_charge`                                            |
    | | *Defined over*: :code:`STOR_LINKED_TMPS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's charging in the linked timepoints.                        |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`Stor_Charge_MW`                                                |
    | | *Defined over*: :code:`STOR_OPR_TMPS`                                 |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Charging power in MW from this project in each timepoint in which the   |
    | project is operational (capacity exists and the project is available).  |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Discharge_MW`                                             |
    | | *Defined over*: :code:`STOR_OPR_TMPS`                                 |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Discharging power in MW from this project in each timepoint in which the|
    |  project is operational (capacity exists and the project is available). |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Starting_Energy_in_Storage_MWh`                           |
    | | *Defined over*: :code:`STOR_OPR_TMPS`                                 |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The state of charge of the storage project at the start of each         |
    | timepoint, in MWh of energy stored.                                     |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Sample_Block_End_Energy_MWh`                              |
    | | *Defined over*: :code:`STOR_SAMPLE_BLOCKS`                            |
    |                                                                         |
    | The energy in storage at the end of one repeat of the sample block      |
    | that comes from the block's own charging and discharging (each          |
    | timepoint's energy step decayed by the storage efficiency over the      |
    | timepoints that follow it in the block).                                |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Last_Repeat_SOC_Offset_MWh`                               |
    | | *Defined over*: :code:`STOR_SAMPLE_BLOCK_OPR_TMPS`                    |
    |                                                                         |
    | The energy in storage at the timepoint in the last repeat of its        |
    | sample block minus the energy in the first repeat (the model's          |
    | variable).                                                              |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Sample_Block_Repeat_Carryover_MWh`                        |
    | | *Defined over*: :code:`STOR_SAMPLE_BLOCKS`                            |
    |                                                                         |
    | The energy at the end of the block's last repeat minus the energy at    |
    | the end of its first repeat: what the repeats after the first carry     |
    | into the timepoint that follows the block.                              |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | Power and Stage of Charge                                               |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Max_Charge_Constraint`                                    |
    | | *Defined over*: :code:`STOR_OPR_TMPS`                                 |
    |                                                                         |
    | Limits the project's charging power to the available capacity.          |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Max_Discharge_Constraint`                                 |
    | | *Defined over*: :code:`STOR_OPR_TMPS`                                 |
    |                                                                         |
    | Limits the project's discharging power to the available capacity.       |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Energy_Tracking_Constraint`                               |
    | | *Defined over*: :code:`STOR_OPR_TMPS`                                 |
    |                                                                         |
    | Tracks the amount of energy stored in each timepoint based on the       |
    | previous timepoint's energy stored and the charge and discharge         |
    | decisions.                                                              |
    | After a repeated sample block, the block's repeat carryover is added.   |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Max_Energy_in_Storage_Constraint`                         |
    | | *Defined over*: :code:`STOR_OPR_TMPS`                                 |
    |                                                                         |
    | Limits the project's total energy stored to the available energy        |
    | capacity.                                                               |
    +-------------------------------------------------------------------------+
    | Reserves                                                                |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Max_Headroom_Power_Constraint`                            |
    | | *Defined over*: :code:`STOR_OPR_TMPS`                                 |
    |                                                                         |
    | Limits the project's upward reserves based on available headroom.       |
    | Going from charging to non-charging also counts as headroom, doubling   |
    | the maximum amount of potential headroom.                               |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Max_Footroom_Power_Constraint`                            |
    | | *Defined over*: :code:`STOR_OPR_TMPS`                                 |
    |                                                                         |
    | Limits the project's downward reserves based on available footroom.     |
    | Going from non-charging to charging also counts as footroom, doubling   |
    | the maximum amount of potential footroom.                               |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Max_Headroom_Energy_Constraint`                           |
    | | *Defined over*: :code:`STOR_OPR_TMPS`                                 |
    |                                                                         |
    | Can't provide more upward reserves (times the reserves setpoint         |
    | duration, the timepoint duration by default) than available energy in   |
    | storage in that timepoint.                                              |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Max_Footroom_Energy_Constraint`                           |
    | | *Defined over*: :code:`STOR_OPR_TMPS`                                 |
    |                                                                         |
    | Can't provide more downward reserves (times the reserves setpoint       |
    | duration, the timepoint duration by default) than available capacity to |
    | store energy in that timepoint.                                         |
    +-------------------------------------------------------------------------+
    +-------------------------------------------------------------------------+
    | Multi-Sample Horizons                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Last_Repeat_Min_Energy_in_Storage_Constraint`             |
    | | *Defined over*: :code:`STOR_SAMPLE_BLOCK_OPR_TMPS`                    |
    |                                                                         |
    | The energy in storage in the last repeat of the sample block cannot     |
    | be negative.                                                            |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Last_Repeat_Max_Energy_in_Storage_Constraint`             |
    | | *Defined over*: :code:`STOR_SAMPLE_BLOCK_OPR_TMPS`                    |
    |                                                                         |
    | The energy in storage in the last repeat of the sample block cannot     |
    | exceed the available energy capacity.                                   |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Last_Repeat_Max_Headroom_Energy_Constraint`               |
    | | *Defined over*: :code:`STOR_SAMPLE_BLOCK_OPR_TMPS`                    |
    |                                                                         |
    | :code:`Stor_Max_Headroom_Energy_Constraint` at the last repeat of the   |
    | sample block (same skip conditions).                                    |
    +-------------------------------------------------------------------------+
    | | :code:`Stor_Last_Repeat_Max_Footroom_Energy_Constraint`               |
    | | *Defined over*: :code:`STOR_SAMPLE_BLOCK_OPR_TMPS`                    |
    |                                                                         |
    | :code:`Stor_Max_Footroom_Energy_Constraint` at the last repeat of the   |
    | sample block (same skip conditions).                                    |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.STOR = Set(
        within=m.PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod, "PROJECTS", "operational_type", "stor"
        ),
    )

    m.STOR_OPR_TMPS = Set(
        dimen=2,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod, superset="PRJ_OPR_TMPS", index=0, membership_set=mod.STOR
        ),
    )

    m.STOR_LINKED_TMPS = Set(dimen=2)

    m.STOR_EXOG_SOC_TMPS = Set(within=m.STOR_OPR_TMPS)

    # Declared before STOR_OPR_BT_HRZ, whose initializer reads it: Pyomo
    # constructs components in declaration order, and sparse membership in a
    # not-yet-constructed Param is silently False. No default: unspecified
    # means the project's balancing_type_project (see
    # get_energy_budget_balancing_type).
    m.stor_energy_budget_balancing_type = Param(m.STOR, within=m.BLN_TYPES)

    def stor_opr_bt_hrz_set_init(mod):
        prj_bt_hrz = []
        for prj in mod.STOR:
            # The horizons over which the max-losses limit applies
            bt = get_energy_budget_balancing_type(
                mod, prj, mod.stor_energy_budget_balancing_type
            )
            for hrz in mod.HRZS_BY_BLN_TYPE[bt]:
                # Add to the set if all timepoints in the horizon are in
                # the project's operational timepoints
                # Keep the element-by-element membership checks: they are
                # O(1) each and short-circuit, whereas an issubset() test
                # against PRJ_OPR_TMPS would copy that entire set per
                # project-horizon
                if all(
                    (prj, tmp) in mod.PRJ_OPR_TMPS
                    for tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]
                ):
                    prj_bt_hrz.append((prj, bt, hrz))

        return prj_bt_hrz

    m.STOR_OPR_BT_HRZ = Set(
        within=m.STOR * m.BLN_TYPE_HRZS, initialize=stor_opr_bt_hrz_set_init
    )

    # Multi-sample horizons (see the module docstring): the structure is
    # derived once per instance by get_stor_sample_block_structure and
    # read by the initializers below
    m.STOR_SAMPLE_BLOCKS = Set(
        dimen=2,
        initialize=lambda mod: sorted(
            get_stor_sample_block_structure(mod)["blocks"].keys()
        ),
    )

    m.STOR_SAMPLE_BLOCK_TMPS = Set(
        m.STOR_SAMPLE_BLOCKS,
        ordered=True,
        initialize=lambda mod, prj, first_tmp: get_stor_sample_block_structure(mod)[
            "blocks"
        ][prj, first_tmp]["tmps"],
    )

    m.stor_sample_block_weight = Param(
        m.STOR_SAMPLE_BLOCKS,
        within=NonNegativeReals,
        initialize=lambda mod, prj, first_tmp: get_stor_sample_block_structure(mod)[
            "blocks"
        ][prj, first_tmp]["weight"],
    )

    m.STOR_SAMPLE_BLOCK_OPR_TMPS = Set(
        dimen=2,
        initialize=lambda mod: sorted(
            get_stor_sample_block_structure(mod)["tmp_block"].keys()
        ),
    )

    m.stor_sample_block = Param(
        m.STOR_SAMPLE_BLOCK_OPR_TMPS,
        within=m.TMPS,
        initialize=lambda mod, prj, tmp: get_stor_sample_block_structure(mod)[
            "tmp_block"
        ][prj, tmp][0],
    )

    m.stor_sample_block_position = Param(
        m.STOR_SAMPLE_BLOCK_OPR_TMPS,
        within=NonNegativeIntegers,
        initialize=lambda mod, prj, tmp: get_stor_sample_block_structure(mod)[
            "tmp_block"
        ][prj, tmp][1],
    )

    m.STOR_SAMPLE_BLOCK_TRANSITION_OPR_TMPS = Set(
        dimen=2,
        initialize=lambda mod: sorted(
            get_stor_sample_block_structure(mod)["transition"].keys()
        ),
    )

    m.stor_sample_block_before = Param(
        m.STOR_SAMPLE_BLOCK_TRANSITION_OPR_TMPS,
        within=m.TMPS,
        initialize=lambda mod, prj, tmp: get_stor_sample_block_structure(mod)[
            "transition"
        ][prj, tmp],
    )

    # Required Params
    ###########################################################################

    m.stor_charging_efficiency = Param(m.STOR, within=PercentFraction)

    m.stor_discharging_efficiency = Param(m.STOR, within=PercentFraction)

    # Optional Params
    ###########################################################################

    m.stor_storage_efficiency = Param(m.STOR, within=PercentFraction, default=1)

    m.stor_losses_factor_in_energy_target = Param(m.STOR, default=1)

    m.stor_losses_factor_curtailment = Param(m.STOR, default=1)

    m.stor_upward_reserves_to_soc_depletion = Param(m.STOR, default=0)

    m.stor_charging_capacity_multiplier = Param(
        m.STOR, within=NonNegativeReals, default=1.0
    )

    m.stor_discharging_capacity_multiplier = Param(
        m.STOR, within=NonNegativeReals, default=1.0
    )

    m.stor_exogenous_starting_state_of_charge = Param(
        m.STOR_EXOG_SOC_TMPS, within=NonNegativeReals
    )

    # No default: when not specified for a project, the headroom/footroom
    # energy rules fall back to the timepoint duration (see
    # reserves_setpoint_duration_hours below)
    m.stor_reserves_setpoint_duration_hours = Param(m.STOR, within=NonNegativeReals)

    m.stor_max_losses_in_hrz_frac_stor_energy_capacity = Param(
        m.STOR, within=NonNegativeReals, default=float("inf")
    )

    # Linked Params
    ###########################################################################

    m.stor_linked_starting_energy_in_storage = Param(
        m.STOR_LINKED_TMPS, within=NonNegativeReals
    )

    m.stor_linked_discharge = Param(m.STOR_LINKED_TMPS, within=NonNegativeReals)

    m.stor_linked_charge = Param(m.STOR_LINKED_TMPS, within=NonNegativeReals)

    # Variables
    ###########################################################################

    m.Stor_Charge_MW = Var(m.STOR_OPR_TMPS, within=NonNegativeReals)

    m.Stor_Discharge_MW = Var(m.STOR_OPR_TMPS, within=NonNegativeReals)

    m.Stor_Starting_Energy_in_Storage_MWh = Var(
        m.STOR_OPR_TMPS, within=NonNegativeReals
    )

    # Expressions
    ###########################################################################
    def ending_energy_in_storage_expression_rule(mod, prj, tmp):
        return (
            mod.Stor_Starting_Energy_in_Storage_MWh[prj, tmp]
            + mod.Stor_Charge_MW[prj, tmp]
            * mod.hrs_in_tmp[tmp]
            * mod.stor_charging_efficiency[prj]
            - mod.Stor_Discharge_MW[prj, tmp]
            * mod.hrs_in_tmp[tmp]
            / mod.stor_discharging_efficiency[prj]
        )

    m.Stor_Ending_Energy_in_Storage_MWh = Expression(
        m.STOR_OPR_TMPS,
        initialize=ending_energy_in_storage_expression_rule,
    )

    def upward_reserve_rule(mod, g, tmp):
        return headroom_provision_rule(d, mod, g, tmp)

    m.Stor_Upward_Reserves_MW = Expression(m.STOR_OPR_TMPS, rule=upward_reserve_rule)

    def downward_reserve_rule(mod, g, tmp):
        return footroom_provision_rule(d, mod, g, tmp)

    m.Stor_Downward_Reserves_MW = Expression(
        m.STOR_OPR_TMPS, rule=downward_reserve_rule
    )

    # Multi-sample horizons: a block's end-of-block energy from its own
    # charging and discharging, the state-of-charge offset at the block's
    # last repeat, and the energy carried into the next timepoint by the
    # repeats after the first (see the module docstring and the rules)
    m.Stor_Sample_Block_End_Energy_MWh = Expression(
        m.STOR_SAMPLE_BLOCKS, rule=sample_block_end_energy_rule
    )

    m.Stor_Last_Repeat_SOC_Offset_MWh = Expression(
        m.STOR_SAMPLE_BLOCK_OPR_TMPS, rule=last_repeat_soc_offset_rule
    )

    m.Stor_Sample_Block_Repeat_Carryover_MWh = Expression(
        m.STOR_SAMPLE_BLOCKS, rule=sample_block_repeat_carryover_rule
    )

    # Constraints
    ###########################################################################

    # Power and State of Charge
    m.Stor_Max_Charge_Constraint = Constraint(m.STOR_OPR_TMPS, rule=max_charge_rule)

    m.Stor_Max_Discharge_Constraint = Constraint(
        m.STOR_OPR_TMPS, rule=max_discharge_rule
    )

    m.Stor_Energy_Tracking_Constraint = Constraint(
        m.STOR_OPR_TMPS, rule=energy_tracking_rule
    )

    m.Stor_Max_Energy_in_Storage_Constraint = Constraint(
        m.STOR_OPR_TMPS, rule=max_energy_in_storage_rule
    )

    m.Stor_Max_Losses_Constraint = Constraint(
        m.STOR_OPR_BT_HRZ, rule=max_losses_in_hrz_rule
    )

    # Reserves
    # For a project with no reserve variables, each reserve constraint
    # reduces to a bound on charging, discharging or ending energy that
    # the project's other constraints already imply in most timepoints;
    # the constraint is skipped there (see each rule for the exact
    # conditions). Half of a storage project's per-timepoint constraints
    # are reserve constraints, so this roughly halves the storage rows of
    # a model without reserves.
    def max_headroom_power_constraint_rule(mod, s, tmp):
        if (
            not getattr(d, headroom_variables)[s]
            and mod.stor_discharging_capacity_multiplier[s] <= 1
        ):
            return Constraint.Skip
        return max_headroom_power_rule(mod, s, tmp)

    m.Stor_Max_Headroom_Power_Constraint = Constraint(
        m.STOR_OPR_TMPS, rule=max_headroom_power_constraint_rule
    )

    def max_footroom_power_constraint_rule(mod, s, tmp):
        if (
            not getattr(d, footroom_variables)[s]
            and mod.stor_charging_capacity_multiplier[s] <= 1
        ):
            return Constraint.Skip
        return max_footroom_power_rule(mod, s, tmp)

    m.Stor_Max_Footroom_Power_Constraint = Constraint(
        m.STOR_OPR_TMPS, rule=max_footroom_power_constraint_rule
    )

    def max_headroom_energy_constraint_rule(mod, s, tmp):
        if not getattr(d, headroom_variables)[s] and next_tmp_tracks_energy(
            mod, s, tmp
        ):
            return Constraint.Skip
        return max_headroom_energy_rule(mod, s, tmp)

    m.Stor_Max_Headroom_Energy_Constraint = Constraint(
        m.STOR_OPR_TMPS, rule=max_headroom_energy_constraint_rule
    )

    def max_footroom_energy_constraint_rule(mod, s, tmp):
        if (
            not getattr(d, footroom_variables)[s]
            and mod.stor_storage_efficiency[s] == 1
            and next_tmp_tracks_energy(mod, s, tmp)
            and next_tmp_derate_is_no_higher(mod, s, tmp)
        ):
            return Constraint.Skip
        return max_footroom_energy_rule(mod, s, tmp)

    m.Stor_Max_Footroom_Energy_Constraint = Constraint(
        m.STOR_OPR_TMPS, rule=max_footroom_energy_constraint_rule
    )

    # Multi-sample horizons: the state of charge at the last repeat of a
    # sample block must satisfy the same bounds as at the first repeat (it
    # is monotonic across repeats, so the two together cover every repeat)
    m.Stor_Last_Repeat_Min_Energy_in_Storage_Constraint = Constraint(
        m.STOR_SAMPLE_BLOCK_OPR_TMPS, rule=last_repeat_min_energy_in_storage_rule
    )

    m.Stor_Last_Repeat_Max_Energy_in_Storage_Constraint = Constraint(
        m.STOR_SAMPLE_BLOCK_OPR_TMPS, rule=last_repeat_max_energy_in_storage_rule
    )

    def last_repeat_max_headroom_energy_constraint_rule(mod, s, tmp):
        if not getattr(d, headroom_variables)[s] and next_tmp_tracks_energy(
            mod, s, tmp
        ):
            return Constraint.Skip
        return max_headroom_energy_rule(
            mod, s, tmp, soc_offset=mod.Stor_Last_Repeat_SOC_Offset_MWh[s, tmp]
        )

    m.Stor_Last_Repeat_Max_Headroom_Energy_Constraint = Constraint(
        m.STOR_SAMPLE_BLOCK_OPR_TMPS,
        rule=last_repeat_max_headroom_energy_constraint_rule,
    )

    def last_repeat_max_footroom_energy_constraint_rule(mod, s, tmp):
        if (
            not getattr(d, footroom_variables)[s]
            and mod.stor_storage_efficiency[s] == 1
            and next_tmp_tracks_energy(mod, s, tmp)
            and next_tmp_derate_is_no_higher(mod, s, tmp)
        ):
            return Constraint.Skip
        return max_footroom_energy_rule(
            mod, s, tmp, soc_offset=mod.Stor_Last_Repeat_SOC_Offset_MWh[s, tmp]
        )

    m.Stor_Last_Repeat_Max_Footroom_Energy_Constraint = Constraint(
        m.STOR_SAMPLE_BLOCK_OPR_TMPS,
        rule=last_repeat_max_footroom_energy_constraint_rule,
    )


# Multi-Sample Horizons
###############################################################################


def get_stor_sample_block_structure(mod):
    """
    Derive, once per model instance, the sample blocks of every storage
    project's horizons (see the module docstring): a sample block is a
    maximal run of consecutive timepoints of a horizon that share a
    timepoint weight, and a horizon is a multi-sample horizon when it has
    more than one such run (runs of weight 0, e.g. spinup or lookahead
    timepoints, do not count). In a multi-sample horizon every block of
    weight greater than 1 is repeated as many times as its weight before
    the chronology moves on to the next timepoint.

    Returns a dict with three entries, all keyed by (project, timepoint):

    * ``blocks``: first timepoint of a repeated block -> dict of its
      ``tmps`` (in chronological order) and ``weight``;
    * ``tmp_block``: timepoint in a repeated block -> (first timepoint of
      the block, 0-based position in it);
    * ``transition``: timepoint that follows a repeated block (the horizon's
      first timepoint when the block is last in a circular horizon) -> first
      timepoint of that block.

    A linked horizon with sample blocks is refused (the linked timepoint
    params carry the state after the first repeat only), as is an
    exogenous state of charge inside a repeated block (the repeats could not
    all start from it).
    """
    if hasattr(mod, "_stor_sample_block_structure"):
        return mod._stor_sample_block_structure

    blocks, tmp_block, transition = {}, {}, {}
    for prj in mod.STOR:
        bt = mod.balancing_type_project[prj]
        for hrz in mod.HRZS_BY_BLN_TYPE[bt]:
            tmps = list(mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz])
            # Element-by-element membership checks (see STOR_OPR_BT_HRZ)
            if not all((prj, tmp) in mod.STOR_OPR_TMPS for tmp in tmps):
                continue
            runs = []
            for tmp in tmps:
                if runs and mod.tmp_weight[runs[-1][0]] == mod.tmp_weight[tmp]:
                    runs[-1].append(tmp)
                else:
                    runs.append([tmp])
            if sum(1 for run in runs if mod.tmp_weight[run[0]] > 0) < 2:
                continue
            boundary = mod.boundary[bt, hrz]
            if boundary == "linked":
                raise ValueError(
                    f"Storage project {prj} is on horizon {hrz} of balancing "
                    f"type {bt}, which has a linked boundary and timepoints "
                    f"of different weights; the linked timepoint params "
                    f"cannot carry the state of charge across repeated "
                    f"samples. Use a circular or linear boundary."
                )
            for i, run in enumerate(runs):
                weight = mod.tmp_weight[run[0]]
                if weight <= 1:
                    continue
                first_tmp = run[0]
                blocks[prj, first_tmp] = {"tmps": run, "weight": weight}
                for position, tmp in enumerate(run):
                    if (prj, tmp) in mod.STOR_EXOG_SOC_TMPS:
                        raise ValueError(
                            f"Storage project {prj} has an exogenous state of "
                            f"charge in timepoint {tmp}, which lies in a "
                            f"repeated sample (weight {weight}) of horizon "
                            f"{hrz} of balancing type {bt}; the repeats of the "
                            f"sample cannot all start from it."
                        )
                    tmp_block[prj, tmp] = (first_tmp, position)
                if i + 1 < len(runs):
                    transition[prj, runs[i + 1][0]] = first_tmp
                elif boundary == "circular":
                    transition[prj, tmps[0]] = first_tmp

    mod._stor_sample_block_structure = {
        "blocks": blocks,
        "tmp_block": tmp_block,
        "transition": transition,
    }

    return mod._stor_sample_block_structure


def energy_step_rule(mod, s, tmp):
    """
    The change in the energy in storage over timepoint *tmp* from the
    project's charging, discharging and upward-reserve depletion, exactly
    as the energy tracking constraint propagates it to the next timepoint
    (before the storage-efficiency decay of the starting energy).
    """
    hrs_in_tmp = mod.hrs_in_tmp[tmp]
    return (
        mod.Stor_Charge_MW[s, tmp] * hrs_in_tmp * mod.stor_charging_efficiency[s]
        - (
            mod.Stor_Discharge_MW[s, tmp]
            + mod.Stor_Upward_Reserves_MW[s, tmp]
            * mod.stor_upward_reserves_to_soc_depletion[s]
        )
        * hrs_in_tmp
        / mod.stor_discharging_efficiency[s]
    )


def repeat_decay(mod, s, first_tmp):
    """
    The storage-efficiency decay over one repeat of the sample block: the
    storage efficiency to the power of the block's number of timepoints.
    """
    return mod.stor_storage_efficiency[s] ** len(
        mod.STOR_SAMPLE_BLOCK_TMPS[s, first_tmp]
    )


def repeat_decay_series(mod, s, first_tmp, n_repeats):
    """
    1 + r + r^2 + ... + r^(n_repeats - 1) for the block's repeat decay r,
    i.e. the factor on the block's end-of-block energy after *n_repeats*
    repeats; *n_repeats* when the storage efficiency is 1.
    """
    r = repeat_decay(mod, s, first_tmp)
    if r == 1:
        return n_repeats
    return (1 - r**n_repeats) / (1 - r)


def sample_block_end_energy_rule(mod, s, first_tmp):
    """
    **Expression Name**: Stor_Sample_Block_End_Energy_MWh
    **Defined Over**: STOR_SAMPLE_BLOCKS

    The energy in storage at the end of one repeat of the sample block that
    comes from the block's own charging and discharging (each timepoint's
    energy step, decayed by the storage efficiency over the timepoints that
    follow it in the block). With the starting energy of the repeat decayed
    over the block, it gives the energy at the end of the repeat.
    """
    tmps = list(mod.STOR_SAMPLE_BLOCK_TMPS[s, first_tmp])
    n = len(tmps)
    return sum(
        energy_step_rule(mod, s, tmp) * mod.stor_storage_efficiency[s] ** (n - 1 - i)
        for i, tmp in enumerate(tmps)
    )


def last_repeat_soc_offset_rule(mod, s, tmp):
    """
    **Expression Name**: Stor_Last_Repeat_SOC_Offset_MWh
    **Defined Over**: STOR_SAMPLE_BLOCK_OPR_TMPS

    The energy in storage at timepoint *tmp* in the LAST repeat of its sample
    block minus the energy in the first repeat (the model's variable). The
    starting energy of repeat k is r^(k-1) x the first repeat's starting
    energy + (1 + r + ... + r^(k-2)) x the end-of-block energy, where r is
    the repeat decay; within the repeat the difference to the first repeat
    decays by the storage efficiency per timepoint. The offset is monotonic
    across repeats, so bounding the first and the last repeat bounds them
    all.
    """
    first_tmp = mod.stor_sample_block[s, tmp]
    weight = mod.stor_sample_block_weight[s, first_tmp]
    r = repeat_decay(mod, s, first_tmp)
    starting_energy_shift = (
        r ** (weight - 1) - 1
    ) * mod.Stor_Starting_Energy_in_Storage_MWh[s, first_tmp] + repeat_decay_series(
        mod, s, first_tmp, weight - 1
    ) * mod.Stor_Sample_Block_End_Energy_MWh[
        s, first_tmp
    ]
    return (
        mod.stor_storage_efficiency[s] ** mod.stor_sample_block_position[s, tmp]
        * starting_energy_shift
    )


def sample_block_repeat_carryover_rule(mod, s, first_tmp):
    """
    **Expression Name**: Stor_Sample_Block_Repeat_Carryover_MWh
    **Defined Over**: STOR_SAMPLE_BLOCKS

    The energy in storage at the end of the block's last repeat minus the
    energy at the end of its first repeat: what the repeats after the first
    carry into the timepoint that follows the block, added there by the
    energy tracking constraint.
    """
    weight = mod.stor_sample_block_weight[s, first_tmp]
    r = repeat_decay(mod, s, first_tmp)
    return (r**weight - r) * mod.Stor_Starting_Energy_in_Storage_MWh[s, first_tmp] + (
        repeat_decay_series(mod, s, first_tmp, weight) - 1
    ) * mod.Stor_Sample_Block_End_Energy_MWh[s, first_tmp]


def last_repeat_min_energy_in_storage_rule(mod, s, tmp):
    """
    **Constraint Name**: Stor_Last_Repeat_Min_Energy_in_Storage_Constraint
    **Enforced Over**: STOR_SAMPLE_BLOCK_OPR_TMPS

    The energy in storage in the last repeat of the sample block cannot be
    negative (the first repeat's is non-negative by the variable's domain).
    """
    return (
        mod.Stor_Starting_Energy_in_Storage_MWh[s, tmp]
        + mod.Stor_Last_Repeat_SOC_Offset_MWh[s, tmp]
        >= 0
    )


def last_repeat_max_energy_in_storage_rule(mod, s, tmp):
    """
    **Constraint Name**: Stor_Last_Repeat_Max_Energy_in_Storage_Constraint
    **Enforced Over**: STOR_SAMPLE_BLOCK_OPR_TMPS

    The energy in storage in the last repeat of the sample block cannot
    exceed the available energy capacity.
    """
    return max_energy_in_storage_rule(
        mod, s, tmp, soc_offset=mod.Stor_Last_Repeat_SOC_Offset_MWh[s, tmp]
    )


# Constraint Formulation Rules
###############################################################################


# Power and State of Charge
def max_discharge_rule(mod, s, tmp):
    """
    **Constraint Name**: Stor_Max_Discharge_Constraint
    **Enforced Over**: STOR_OPR_TMPS

    Storage discharging power can't exceed available capacity.
    """
    return (
        mod.Stor_Discharge_MW[s, tmp]
        <= mod.Capacity_MW[s, mod.period[tmp]]
        * mod.Availability_Derate[s, tmp]
        * mod.stor_discharging_capacity_multiplier[s]
    )


def max_charge_rule(mod, s, tmp):
    """
    **Constraint Name**: Stor_Max_Charge_Constraint
    **Enforced Over**: STOR_OPR_TMPS

    Storage charging power can't exceed available capacity.
    """
    return (
        mod.Stor_Charge_MW[s, tmp]
        <= mod.Capacity_MW[s, mod.period[tmp]]
        * mod.Availability_Derate[s, tmp]
        * mod.stor_charging_capacity_multiplier[s]
    )


# TODO: also adjust storage energy for downward reserves provided
def energy_tracking_rule(mod, s, tmp):
    """
    **Constraint Name**: Stor_Energy_Tracking_Constraint
    **Enforced Over**: STOR_OPR_TMPS

    The energy stored in each timepoint is equal to the energy stored in the
    previous timepoint minus any discharged power (adjusted for discharging
    efficiency and timepoint duration) plus any charged power (adjusted for
    charging efficiency and timepoint duration).
    """
    if (s, tmp) in mod.STOR_EXOG_SOC_TMPS:
        starting_soc = check_for_soc_infeasibilities(
            mod=mod,
            s=s,
            tmp=tmp,
            starting_soc=mod.stor_exogenous_starting_state_of_charge[s, tmp],
        )
    else:
        bt = mod.balancing_type_project[s]
        is_first_tmp = check_if_first_timepoint(mod=mod, tmp=tmp, balancing_type=bt)
        if is_first_tmp and check_boundary_type(
            mod=mod,
            tmp=tmp,
            balancing_type=bt,
            boundary_type="linear",
        ):
            return Constraint.Skip
        else:
            if is_first_tmp and check_boundary_type(
                mod=mod,
                tmp=tmp,
                balancing_type=bt,
                boundary_type="linked",
            ):
                prev_tmp_hrs_in_tmp = mod.hrs_in_linked_tmp[0]
                prev_tmp_starting_energy_in_storage = (
                    mod.stor_linked_starting_energy_in_storage[s, 0]
                )
                prev_tmp_discharge = mod.stor_linked_discharge[s, 0]
                prev_tmp_charge = mod.stor_linked_charge[s, 0]

                calculated_starting_energy_in_storage = (
                    prev_tmp_starting_energy_in_storage * mod.stor_storage_efficiency[s]
                    + prev_tmp_charge
                    * prev_tmp_hrs_in_tmp
                    * mod.stor_charging_efficiency[s]
                    - prev_tmp_discharge
                    * prev_tmp_hrs_in_tmp
                    / mod.stor_discharging_efficiency[s]
                )

                # Deal with possible precision-related infeasibilities, e.g. if
                # the calculated energy in storage is just below or just above
                # its boundaries of 0 and the energy capacity x availability
                # If no infeasibilities found, just return the calculated value
                starting_soc = check_for_soc_infeasibilities(
                    mod=mod,
                    s=s,
                    tmp=tmp,
                    starting_soc=calculated_starting_energy_in_storage,
                )

            else:
                # Look up the previous timepoint once for all the terms below
                prev = mod.prev_tmp[tmp, bt]
                prev_tmp_hrs_in_tmp = mod.hrs_in_tmp[prev]
                prev_tmp_starting_energy_in_storage = (
                    mod.Stor_Starting_Energy_in_Storage_MWh[s, prev]
                )
                prev_tmp_discharge = mod.Stor_Discharge_MW[s, prev]
                prev_tmp_charge = mod.Stor_Charge_MW[s, prev]
                prev_tmp_upward_reserves = mod.Stor_Upward_Reserves_MW[s, prev]

                starting_soc = (
                    prev_tmp_starting_energy_in_storage * mod.stor_storage_efficiency[s]
                    + prev_tmp_charge
                    * prev_tmp_hrs_in_tmp
                    * mod.stor_charging_efficiency[s]
                    - (
                        prev_tmp_discharge
                        + prev_tmp_upward_reserves
                        * mod.stor_upward_reserves_to_soc_depletion[s]
                    )
                    * prev_tmp_hrs_in_tmp
                    / mod.stor_discharging_efficiency[s]
                )

                # Multi-sample horizons: the previous timepoint ends a
                # repeated sample block, so add what its repeats after the
                # first carry over (zero on single-sample horizons, where
                # the set is empty)
                if (s, tmp) in mod.STOR_SAMPLE_BLOCK_TRANSITION_OPR_TMPS:
                    starting_soc = (
                        starting_soc
                        + mod.Stor_Sample_Block_Repeat_Carryover_MWh[
                            s, mod.stor_sample_block_before[s, tmp]
                        ]
                    )

    return mod.Stor_Starting_Energy_in_Storage_MWh[s, tmp] == starting_soc


def max_energy_in_storage_rule(mod, s, tmp, soc_offset=0):
    """
    **Constraint Name**: Stor_Max_Energy_in_Storage_Constraint
    **Enforced Over**: STOR_OPR_TMPS

    The amount of energy stored in each operational timepoint cannot exceed
    the available energy capacity. *soc_offset* is added to the starting
    energy (the last-repeat constraints of multi-sample horizons pass the
    repeat offset).
    """
    return (
        mod.Stor_Starting_Energy_in_Storage_MWh[s, tmp] + soc_offset
        <= mod.Energy_Storage_Capacity_MWh[s, mod.period[tmp]]
        * mod.Availability_Derate[s, tmp]
    )


# Max losses in horizon (e.g., to limit cycling)
def max_losses_in_hrz_rule(mod, prj, bt, hrz):
    """
    Limit losses in each horizon
    Can be used to constrain cycling or acting as load
    """
    if mod.stor_max_losses_in_hrz_frac_stor_energy_capacity[prj] == float("inf"):
        return Constraint.Skip
    else:
        return (
            sum(
                (mod.Stor_Charge_MW[prj, tmp] - mod.Stor_Discharge_MW[prj, tmp])
                * mod.hrs_in_tmp[tmp]
                for tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, hrz]
            )
            <= mod.stor_max_losses_in_hrz_frac_stor_energy_capacity[prj]
            * mod.Energy_Storage_Capacity_MWh[
                prj, mod.period[mod.first_hrz_tmp[bt, hrz]]
            ]
        )


# Reserves
def next_tmp_tracks_energy(mod, s, tmp):
    """
    Whether the timepoint after *tmp* (in the project's balancing type)
    has an energy tracking constraint that sets its starting energy from
    *tmp*'s charging and discharging: the last timepoint of a linear or
    linked horizon has no next timepoint in this subproblem, and a next
    timepoint with an exogenous state of charge does not look back.
    """
    next_tmp = mod.next_tmp[tmp, mod.balancing_type_project[s]]
    if next_tmp == ".":
        return False
    return (s, next_tmp) not in mod.STOR_EXOG_SOC_TMPS


def next_tmp_derate_is_no_higher(mod, s, tmp):
    """
    Whether the project's availability derate is a known constant (no
    endogenous availability in the model) and is no higher in the next
    timepoint than in *tmp*, so that the next timepoint's maximum energy
    in storage bounds *tmp*'s ending energy at least as tightly as the
    footroom energy constraint would.
    """
    if mod.Availability_Derate.ctype is not Param:
        return False
    next_tmp = mod.next_tmp[tmp, mod.balancing_type_project[s]]
    return mod.Availability_Derate[s, next_tmp] <= mod.Availability_Derate[s, tmp]


def max_headroom_power_rule(mod, s, tmp):
    """
    **Constraint Name**: Stor_Max_Headroom_Power_Constraint
    **Enforced Over**: STOR_OPR_TMPS

    The project's upward reserves cannot exceed the available headroom.
    Going from charging to non-charging also counts as headroom, doubling
    the maximum amount of potential headroom.

    Skipped for a project with no upward reserve variables whose
    discharging capacity multiplier is at most 1: the constraint then
    reduces to a discharge limit that the maximum discharge constraint
    implies.
    """
    return (
        mod.Stor_Upward_Reserves_MW[s, tmp]
        <= mod.Capacity_MW[s, mod.period[tmp]] * mod.Availability_Derate[s, tmp]
        - mod.Stor_Discharge_MW[s, tmp]
        + mod.Stor_Charge_MW[s, tmp]
    )


def max_footroom_power_rule(mod, s, tmp):
    """
    **Constraint Name**: Stor_Max_Footroom_Power_Constraint
    **Enforced Over**: STOR_OPR_TMPS

    The project's downward reserves cannot exceed the available footroom.
    Going from non-charging to charging also counts as footroom, doubling
    the the maximum amount of potential footroom.

    Skipped for a project with no downward reserve variables whose
    charging capacity multiplier is at most 1: the constraint then
    reduces to a charge limit that the maximum charge constraint implies.
    """
    return (
        mod.Stor_Downward_Reserves_MW[s, tmp]
        <= mod.Stor_Discharge_MW[s, tmp]
        + mod.Capacity_MW[s, mod.period[tmp]] * mod.Availability_Derate[s, tmp]
        - mod.Stor_Charge_MW[s, tmp]
    )


# Headroom and footroom energy constraints
# TODO: allow derate of the net energy in the current timepoint in the
#  headroom and footroom energy rules; in reality, reserves could be
#  called at the very beginning or the very end of the timepoint (e.g.
#  hour)
#  If called at the end, we would have all the net energy (or
#  resulting 'room in the tank') available, but if called in the beginning
#  none of it would be available


def reserves_setpoint_duration_hours(mod, s, tmp):
    """
    The number of hours for which the new setpoint must be sustainable if
    reserves are called: the project's
    :code:`stor_reserves_setpoint_duration_hours` if specified, otherwise
    the duration of the timepoint.
    """
    # Sparse membership check: the param has no default, so a project is
    # only "in" it when a value was loaded
    if s in mod.stor_reserves_setpoint_duration_hours:
        return mod.stor_reserves_setpoint_duration_hours[s]
    else:
        return mod.hrs_in_tmp[tmp]


def max_headroom_energy_rule(mod, s, tmp, soc_offset=0):
    """
    **Constraint Name**: Stor_Max_Headroom_Energy_Constraint
    **Enforced Over**: STOR_OPR_TMPS

    Can't provide more reserves (times sustained duration required) than
    available energy in storage in that timepoint. Said differently,
    must have enough energy available to be at the new set point for the
    required setpoint duration (the timepoint duration by default).
    *soc_offset* is added to the starting energy (the last-repeat
    constraints of multi-sample horizons pass the repeat offset).

    Skipped for a project with no upward reserve variables when the next
    timepoint's energy tracking constraint looks back to this one: the
    constraint then reduces to a non-negative ending energy, which the
    next timepoint's non-negative starting energy implies. It is kept in
    the last timepoint of a linear or linked horizon and before a
    timepoint with an exogenous state of charge, where it is the only
    bound on the ending energy.
    """
    hrs_in_tmp = mod.hrs_in_tmp[tmp]
    return (
        mod.Stor_Upward_Reserves_MW[s, tmp]
        * reserves_setpoint_duration_hours(mod, s, tmp)
        / mod.stor_discharging_efficiency[s]
        <= mod.Stor_Starting_Energy_in_Storage_MWh[s, tmp]
        + soc_offset
        + mod.Stor_Charge_MW[s, tmp] * hrs_in_tmp * mod.stor_charging_efficiency[s]
        - mod.Stor_Discharge_MW[s, tmp]
        * hrs_in_tmp
        / mod.stor_discharging_efficiency[s]
    )


def max_footroom_energy_rule(mod, s, tmp, soc_offset=0):
    """
    **Constraint Name**: Stor_Max_Footroom_Energy_Constraint
    **Enforced Over**: STOR_OPR_TMPS

    Can't provide more reserves (times sustained duration required) than
    available capacity to store energy in that timepoint. Said differently,
    must have enough 'room left in the tank' (remaining energy capacity)
    to be at the new set point for the required setpoint duration (the
    timepoint duration by default). *soc_offset* is added to the starting
    energy (the last-repeat constraints of multi-sample horizons pass the
    repeat offset).

    Skipped for a project with no downward reserve variables when the
    constraint reduces to an ending-energy cap that the next timepoint's
    maximum energy in storage implies: the next timepoint's energy
    tracking constraint looks back to this one, the storage efficiency is
    1 and the availability derate is a constant no higher in the next
    timepoint. Otherwise (e.g. in the last timepoint of a linear horizon)
    it is kept, as it is then the only cap on the ending energy.
    """
    hrs_in_tmp = mod.hrs_in_tmp[tmp]
    return (
        mod.Stor_Downward_Reserves_MW[s, tmp]
        * reserves_setpoint_duration_hours(mod, s, tmp)
        * mod.stor_charging_efficiency[s]
        <= mod.Energy_Storage_Capacity_MWh[s, mod.period[tmp]]
        * mod.Availability_Derate[s, tmp]
        - mod.Stor_Starting_Energy_in_Storage_MWh[s, tmp]
        - soc_offset
        - mod.Stor_Charge_MW[s, tmp] * hrs_in_tmp * mod.stor_charging_efficiency[s]
        + mod.Stor_Discharge_MW[s, tmp]
        * hrs_in_tmp
        / mod.stor_discharging_efficiency[s]
    )


# Operational Type Methods
###############################################################################


def power_provision_rule(mod, s, tmp):
    """
    Power provision for generic storage resources is the net power (i.e.
    discharging minus charging). The two variables are constrained to be
    less than or equal to the storage power capacity (with an adjustment for
    reserve-provision), and are also constrained by the storage state of
    charge (i.e. can't charge when the storage is full; can't discharge when
    storage is empty).
    """
    return mod.Stor_Discharge_MW[s, tmp] - mod.Stor_Charge_MW[s, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    If modeled as eligible for RPS, losses incurred by storage (the sum
    over all timepoints of total charging minus total discharging) will count
    against the RPS (i.e. increase RPS requirement, we take the negative of
    the losses as the contribution of the storage to the RPS). By default
     all losses count against the RPS, but this can be derated with the
    stor_losses_factor_in_energy_target parameter (can be between 0 and 1 with
    default of 1). Storage MUST be modeled as eligible for RPS for this rule
    to apply.

    Modeling storage this way can be necessary to avoid having storage behave
    as load (e.g. by charging and discharging at the same time) in order to
    absorb RPS-eligible energy that would otherwise be curtailed, making it
    appear as if it were delivered to load.
    """
    return (
        mod.Stor_Discharge_MW[g, tmp] - mod.Stor_Charge_MW[g, tmp]
    ) * mod.stor_losses_factor_in_energy_target[g]


def variable_om_cost_rule(mod, g, tmp):
    """
    Variable O&M costs are applied only to the storage discharge, i.e. when the
    project is providing power to the system.
    """
    return mod.Stor_Discharge_MW[g, tmp] * mod.variable_om_cost_per_mwh[g]


def variable_om_by_period_cost_rule(mod, prj, tmp):
    """ """
    return (
        mod.Stor_Discharge_MW[prj, tmp]
        * mod.variable_om_cost_per_mwh_by_period[prj, mod.period[tmp]]
    )


def variable_om_by_timepoint_cost_rule(mod, prj, tmp):
    """ """
    return (
        mod.Stor_Discharge_MW[prj, tmp]
        * mod.variable_om_cost_per_mwh_by_timepoint[prj, tmp]
    )


def curtailment_cost_rule(mod, g, tmp):
    """
    Apply curtailment cost to round trip storage loss: to balance
    against curtailment of variable projects.

    Downstream this is summed over all timepoints, so losses from storage (
    the sum of all discharging minus the sum of all charging) will incur the
    curtailment cost. By default all losses incur the curtailment cost,
    but this can be derated with the stor_losses_factor_curtailment parameter
    (default of 1).

    Modeling storage this way can be necessary to avoid having storage behave
    as load (e.g. by charging and discharging at the same time) in order to
    absorb energy that would otherwise be curtailed and incur a cost, making it
    appear as if it were delivered to load.
    """
    return (
        (mod.Stor_Charge_MW[g, tmp] - mod.Stor_Discharge_MW[g, tmp])
        * (
            mod.curtailment_cost_per_powerunithour[g, mod.period[tmp]]
            if (g, mod.period[tmp]) in mod.CURTAILMENT_COST_PRJ_PRDS
            else 0
        )
        * mod.stor_losses_factor_curtailment[g]
    )


def soc_penalty_cost_rule(mod, prj, tmp):
    """ """
    return mod.soc_penalty_cost_per_energyunit[prj] * (
        mod.Energy_Storage_Capacity_MWh[prj, mod.period[tmp]]
        * mod.Availability_Derate[prj, tmp]
        - mod.Stor_Ending_Energy_in_Storage_MWh[prj, tmp]
    )


def soc_last_tmp_penalty_cost_rule(mod, prj, tmp):
    """ """
    if check_if_last_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[prj]
    ):
        return mod.soc_last_tmp_penalty_cost_per_energyunit[prj] * (
            mod.Energy_Storage_Capacity_MWh[prj, mod.period[tmp]]
            * mod.Availability_Derate[prj, tmp]
            - mod.Stor_Ending_Energy_in_Storage_MWh[prj, tmp]
        )
    else:
        return 0


def power_delta_rule(mod, g, tmp):
    """
    This rule is only used in tuning costs, so fine to skip for linked
    horizon's first timepoint.
    """
    if check_if_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ) and (
        check_boundary_type(
            mod=mod,
            tmp=tmp,
            balancing_type=mod.balancing_type_project[g],
            boundary_type="linear",
        )
        or check_boundary_type(
            mod=mod,
            tmp=tmp,
            balancing_type=mod.balancing_type_project[g],
            boundary_type="linked",
        )
    ):
        pass
    else:
        return (mod.Stor_Discharge_MW[g, tmp] - mod.Stor_Charge_MW[g, tmp]) - (
            mod.Stor_Discharge_MW[g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]]
            - mod.Stor_Charge_MW[g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]]
        )


# Input-Output
###############################################################################


def get_model_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return: cursor object with query results
    """

    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    prj_tmp_data = get_prj_temporal_index_opr_inputs_from_db(
        subscenarios=subscenarios,
        weather_iteration=db_weather_iteration,
        hydro_iteration=db_hydro_iteration,
        availability_iteration=db_availability_iteration,
        subproblem=db_subproblem,
        stage=db_stage,
        conn=conn,
        op_type="stor",
        table="inputs_project_stor_exog_state_of_charge",
        subscenario_id_column="stor_exog_state_of_charge_scenario_id",
        data_column="exog_state_of_charge_mwh",
    )

    return prj_tmp_data


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    Get inputs from database and write out the model input
    variable_generator_profiles.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    data = get_model_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )

    fname = "stor_exogenous_state_of_charge.tab"

    write_tab_file_model_inputs(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        fname,
        data,
        replace_nulls=True,
    )


def load_model_data(
    mod,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    load_optype_model_data(
        mod=mod,
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        op_type="stor",
    )

    # Linked timepoint params
    linked_inputs_filename = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "stor_linked_timepoint_params.tab",
    )
    if os.path.exists(linked_inputs_filename):
        data_portal.load(
            filename=linked_inputs_filename,
            index=mod.STOR_LINKED_TMPS,
            param=(
                mod.stor_linked_starting_energy_in_storage,
                mod.stor_linked_discharge,
                mod.stor_linked_charge,
            ),
        )

    # Exogenously specified SOC
    exog_soc_filename = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "stor_exogenous_state_of_charge.tab",
    )
    if os.path.exists(exog_soc_filename):
        data_portal.load(
            filename=exog_soc_filename,
            index=mod.STOR_EXOG_SOC_TMPS,
            param=mod.stor_exogenous_starting_state_of_charge,
        )
    else:
        pass


def add_to_prj_tmp_results(mod):
    results_columns = [
        "starting_energy_mwh",
        "charge_mw",
        "discharge_mw",
        "starting_energy_last_repeat_mwh",
    ]
    data = [
        [
            prj,
            tmp,
            value(mod.Stor_Starting_Energy_in_Storage_MWh[prj, tmp]),
            value(mod.Stor_Charge_MW[prj, tmp]),
            value(mod.Stor_Discharge_MW[prj, tmp]),
            # The energy in storage at the last repeat of a multi-sample
            # horizon's sample block; NaN outside repeated blocks
            (
                value(mod.Stor_Starting_Energy_in_Storage_MWh[prj, tmp])
                + value(mod.Stor_Last_Repeat_SOC_Offset_MWh[prj, tmp])
                if (prj, tmp) in mod.STOR_SAMPLE_BLOCK_OPR_TMPS
                else float("nan")
            ),
        ]
        for (prj, tmp) in mod.STOR_OPR_TMPS
    ]

    optype_dispatch_df = create_results_df(
        index_columns=["project", "timepoint"],
        results_columns=results_columns,
        data=data,
    )

    return results_columns, optype_dispatch_df


def export_results(
    mod,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """

    # Dispatch results added to project_timepoint.csv via add_to_prj_tmp_results()

    # If there's a linked_subproblems_map CSV file, check which of the
    # current subproblem TMPS we should export results for to link to the
    # next subproblem
    tmps_to_link, tmp_linked_tmp_dict = check_for_tmps_to_link(
        scenario_directory=scenario_directory, subproblem=subproblem, stage=stage
    )

    # If the list of timepoints to link is not empty, write the linked
    # timepoint results for this module in the next subproblem's input
    # directory
    if tmps_to_link:
        next_subproblem = str(int(subproblem) + 1)

        # Export params by project and timepoint
        with open(
            os.path.join(
                scenario_directory,
                next_subproblem,
                stage,
                "inputs",
                "stor_linked_timepoint_params.tab",
            ),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")
            writer.writerow(
                [
                    "project",
                    "linked_timepoint",
                    "linked_starting_energy_in_storage",
                    "linked_discharge",
                    "linked_charge",
                ]
            )
            for p, tmp in sorted(mod.STOR_OPR_TMPS):
                if tmp in tmps_to_link:
                    writer.writerow(
                        [
                            p,
                            tmp_linked_tmp_dict[tmp],
                            max(
                                value(mod.Stor_Starting_Energy_in_Storage_MWh[p, tmp]),
                                0,
                            ),
                            max(value(mod.Stor_Discharge_MW[p, tmp]), 0),
                            max(value(mod.Stor_Charge_MW[p, tmp]), 0),
                        ]
                    )


def validate_inputs(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
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
    validate_opchars(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
        "stor",
    )


# ### OTHER ### #
def check_for_soc_infeasibilities(mod, s, tmp, starting_soc):
    if starting_soc < 0:
        warnings.warn(
            f"Starting energy in storage was "
            f"{starting_soc} for project {s}, "
            f"which would have resulted in infeasibility. "
            f"Changed to 0. This can happen due to solver tolerances and "
            f"precision of results. If you didn't expect this, check the "
            f"inputs and results."
        )
        return 0
    elif mod.capacity_type[s] == "stor_spec" and starting_soc > (
        mod.stor_spec_energy_capacity_mwh[s, mod.period[tmp]]
        * mod.avl_exog_cap_derate_outage[s, tmp]
        * mod.avl_exog_cap_derate_weather[s, tmp]
    ):
        warnings.warn(
            f"Starting energy in storage was "
            f"{starting_soc} for project {s}, "
            f"which would have resulted in infeasibility. "
            f"Changed to "
            f"mod.stor_spec_energy_capacity_mwh[s,mod.period[tmp]] "
            f"* mod.Availability_Derate[s, tmp]. This can happen due to "
            f"solver tolerances and precision of results. If you didn't expect "
            f"this, check the inputs and results."
        )
        return (
            mod.stor_spec_energy_capacity_mwh[s, mod.period[tmp]]
            * mod.Availability_Derate[s, tmp]
        )
    else:
        return starting_soc
