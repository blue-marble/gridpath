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


from __future__ import absolute_import

from .aggregate_reserve_violation_penalties import \
    generic_record_dynamic_components, generic_add_model_components


def add_model_components(m, d, subproblem_stage_directory):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        subproblem_stage_directory,
        "SPINNING_RESERVES_ZONES",
        "Spinning_Reserves_Violation_MW_Expression",
        "spinning_reserves_violation_penalty_per_mw",
        "Spinning_Reserves_Penalty_Costs"
        )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    generic_record_dynamic_components(dynamic_components,
                                      "Spinning_Reserves_Penalty_Costs")
