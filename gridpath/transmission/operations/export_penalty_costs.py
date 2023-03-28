# Copyright 2016-2021 Blue Marble Analytics LLC.
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
Operational tuning costs that prevent erratic dispatch in case of degeneracy.
Tuning costs can be applied to hydro up and down ramps (gen_hydro
and gen_hydro_must_take operational types) and to storage up-ramps (
stor operational type) in order to force smoother dispatch.
"""

import os
from pyomo.environ import Var, NonNegativeReals, Constraint, Expression


def add_model_components(m, d, scenario_directory, subproblem, stage):
    # Tuning cost can be applied on exports from a load zone to prioritize
    # meeting local load first
    m.LZ_Exports = Var(m.LOAD_ZONES, m.TMPS, within=NonNegativeReals)

    def exports_tuning_cost_constraint_rule(mod, lz, tmp):
        return (
            mod.LZ_Exports[lz, tmp]
            >= mod.Transmission_from_Zone_MW[lz, tmp]
            - mod.Transmission_to_Zone_MW[lz, tmp]
        )

    m.Positive_Exports_Tuning_Cost_Constraint = Constraint(
        m.LOAD_ZONES, m.TMPS, rule=exports_tuning_cost_constraint_rule
    )

    def export_penalty_cost_rule(mod, lz, tmp):
        return mod.LZ_Exports[lz, tmp] * mod.export_penalty_cost_per_mwh[lz]

    m.Export_Penalty_Cost = Expression(
        m.LOAD_ZONES, m.TMPS, rule=export_penalty_cost_rule
    )
