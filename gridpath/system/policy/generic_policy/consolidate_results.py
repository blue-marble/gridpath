# Copyright 2016-2024 Blue Marble Analytics.
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


import os.path

from gridpath.system.policy.generic_policy import POLICY_ZONE_PRD_DF, POLICY_MH_DF


def export_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
    d,
):
    """
    Write accumulated results DFs to CSV. Both DFs are built up incrementally
    by upstream modules via .update() before this consolidation step runs.
    """

    results_dir = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "results",
    )

    if m.POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ:
        getattr(d, POLICY_ZONE_PRD_DF).to_csv(
            os.path.join(results_dir, "system_policy_requirements.csv"),
            sep=",",
            index=True,
        )

    if m.POLICIES_ZONE_PRDS_MONTH_HOURS_WITH_REQ:
        getattr(d, POLICY_MH_DF).to_csv(
            os.path.join(results_dir, "system_month_hour_policy_requirements.csv"),
            sep=",",
            index=True,
        )
