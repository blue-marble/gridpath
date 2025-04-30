# Copyright 2016-2025 Blue Marble Analytics LLC.
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
This module, aggregates the power production by all operational projects
tagged as demand side.
"""

from pyomo.environ import Constraint


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
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to
    """

    # Load-following rule; only needed if there's a load-following project
    def load_following_rule(mod, prj, tmp):
        """
        **Constraint Name**: EnergyLoadFollowing_Power_Constraint
        **Enforced Over**: ENERGY_LOAD_FOLLOWING_OPR_TMPS

        Set the load following load variable to the actual load. We need the
        former upstream, as the load balance components have not yet been
        added when adding the energy_load_following optype components.
        """
        if mod.operational_type[prj] == "energy_load_following":
            return (
                mod.EnergyLoadFollowing_LZ_Load_in_Tmp[prj, tmp]
                == mod.LZ_Modified_Load_in_Tmp[mod.load_zone[prj], tmp]
            )
        else:
            return Constraint.Skip

    m.EnergyLoadFollowing_Constraint = Constraint(
        m.PRJ_OPR_TMPS, rule=load_following_rule
    )
