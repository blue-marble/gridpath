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


from pyomo.environ import Set, Expression


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

    """
    Treatment of inertia reserves. This function creates model components
    related to a inertia reserve requirement, including
    1) an expression aggregating generator-level provision to total provision
    :param m:
    :param d:
    :return:
    """

    # Reserve generators operational generators in timepoint
    # This will be the intersection of the reserve generator set and the set of
    # generators operational in the timepoint
    m.INERTIA_RESERVES_PROJECTS_OPERATIONAL_IN_TIMEPOINT = Set(
        m.TMPS,
        initialize=lambda mod, tmp: mod.INERTIA_RESERVES_PROJECTS
        & mod.OPR_PRJS_IN_TMP[tmp],
    )

    # Reserve provision
    def total_reserve_rule(mod, ba, tmp):
        return sum(
            mod.Provide_Inertia_Reserves_MWs[g, tmp]
            for g in mod.INERTIA_RESERVES_PROJECTS_OPERATIONAL_IN_TIMEPOINT[tmp]
            if mod.inertia_reserves_zone[g] == ba
        )

    m.Total_Inertia_Reserves_Provision_MWs = Expression(
        m.INERTIA_RESERVES_ZONES * m.TMPS, rule=total_reserve_rule
    )
