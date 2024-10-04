# Copyright 2021 (c) Crown Copyright, GC.
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

    m.INST_PEN_PRJ_OPERATIONAL_IN_TIMEPOINT = Set(
        m.TMPS, initialize=lambda mod, tmp: mod.INST_PEN_PRJS & mod.OPR_PRJS_IN_TMP[tmp]
    )

    # instantaneous penetration provision
    def total_instantaneous_penetration_rule(mod, z, tmp):
        """
        Calculate the instantaneous penetration for each zone and timepoint.
        :param mod:
        :param z:
        :param tmp:
        :return:
        """
        return sum(
            mod.Power_Provision_MW[g, tmp]
            for g in mod.INST_PEN_PRJ_OPERATIONAL_IN_TIMEPOINT[tmp]
            if mod.instantaneous_penetration_zone[g] == z
        )

    m.Total_Instantaneous_Penetration_Energy_MWh = Expression(
        m.INSTANTANEOUS_PENETRATION_ZONES * m.TMPS,
        rule=total_instantaneous_penetration_rule,
    )
