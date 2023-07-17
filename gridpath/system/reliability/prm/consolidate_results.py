# Copyright 2016-2023 Blue Marble Analytics.
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

from gridpath.system.reliability.prm import PRM_ZONE_PRD_DF


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export all results from the PROJECT_OPERATIONS_DF that various modules
    have added to
    """

    getattr(d, PRM_ZONE_PRD_DF).to_csv(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "system_prm.csv",
        ),
        sep=",",
        index=True,
    )
