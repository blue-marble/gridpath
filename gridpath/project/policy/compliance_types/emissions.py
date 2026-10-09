# Copyright 2026 Sylvan Energy Analytics LLC.
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
The *emissions* compliance type: the project contributes its carbon
emissions (:code:`Project_Carbon_Emissions`, in tonnes per timepoint, weighted
to the horizon by the aggregation) toward the policy requirement. Paired with
a ``max`` requirement, this gives an emissions cap on the mapped projects; with
a load coefficient, a cap on the emissions per unit of load.
"""

from pyomo.environ import Set


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
    | | :code:`EMISSIONS_PROJECT_POLICY_ZONES`                                |
    | | *Within*: :code:`PROJECT_POLICY_ZONES`                                |
    |                                                                         |
    | Three-dimensional set of the project, policy and policy zone            |
    | combinations with the *emissions* compliance type.                      |
    +-------------------------------------------------------------------------+
    """
    m.EMISSIONS_PROJECT_POLICY_ZONES = Set(
        dimen=3,
        within=m.PROJECT_POLICY_ZONES,
        initialize=lambda mod: [
            (prj, policy, zone)
            for (prj, policy, zone) in mod.PROJECT_POLICY_ZONES
            if mod.compliance_type[prj, policy, zone] == "emissions"
        ],
    )


# Compliance type methods
###############################################################################
def contribution_in_timepoint(mod, prj, policy, zone, tmp):
    """
    The project's carbon emissions in the timepoint.
    """
    return mod.Project_Carbon_Emissions[prj, tmp]
