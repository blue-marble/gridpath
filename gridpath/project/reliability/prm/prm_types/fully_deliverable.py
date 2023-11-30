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
Fully deliverable projects (no energy-only allowed)
"""

from pyomo.environ import Set

from gridpath.auxiliary.auxiliary import subset_init_by_param_value


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

    :param m:
    :param d:
    :return:
    """
    m.FULLY_DELIVERABLE_PRM_PROJECTS = Set(
        within=m.PRM_PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod=mod,
            set_name="PRM_PROJECTS",
            param_name="prm_type",
            param_value="fully_deliverable",
        ),
    )


def elcc_eligible_capacity_rule(mod, g, p):
    """

    :param mod:
    :param g:
    :param p:
    :return:
    """
    return mod.Capacity_MW[g, p]
