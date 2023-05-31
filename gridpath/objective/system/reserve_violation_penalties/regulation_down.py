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


from .aggregate_reserve_violation_penalties import (
    generic_record_dynamic_components,
    generic_add_model_components,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        scenario_directory,
        subproblem,
        stage,
        "REGULATION_DOWN_ZONES",
        "Regulation_Down_Violation_MW_Expression",
        "regulation_down_violation_penalty_per_mw",
        "Regulation_Down_Penalty_Costs",
    )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    generic_record_dynamic_components(
        dynamic_components, "Regulation_Down_Penalty_Costs"
    )
