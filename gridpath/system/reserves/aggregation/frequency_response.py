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

from .reserve_aggregation import generic_add_model_components


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

    generic_add_model_components(
        m,
        d,
        "frequency_response_ba",
        "FREQUENCY_RESPONSE_BAS",
        "FREQUENCY_RESPONSE_PROJECTS",
        "Provide_Frequency_Response_MW",
        "Total_Frequency_Response_Provision_MW",
    )

    m.FREQUENCY_RESPONSE_PARTIAL_PROJECTS_OPERATIONAL_IN_TIMEPOINT = Set(
        m.TMPS,
        initialize=lambda mod, tmp: mod.FREQUENCY_RESPONSE_PARTIAL_PROJECTS
        & mod.OPR_PRJS_IN_TMP[tmp],
    )

    # Reserve provision
    def total_partial_frequency_response_rule(mod, ba, tmp):
        return sum(
            mod.Provide_Frequency_Response_MW[g, tmp]
            for g in mod.FREQUENCY_RESPONSE_PARTIAL_PROJECTS_OPERATIONAL_IN_TIMEPOINT[
                tmp
            ]
            if mod.frequency_response_ba[g] == ba
        )

    m.Total_Partial_Frequency_Response_Provision_MW = Expression(
        m.FREQUENCY_RESPONSE_BAS, m.TMPS, rule=total_partial_frequency_response_rule
    )
