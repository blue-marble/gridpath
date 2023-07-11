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


"""

import os.path

from gridpath.project import PROJECT_PERIOD_DF


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export all results from the PROJECT_CAPACITY_DF that various modules
    have added to
    """
    prj_cap_df = getattr(d, PROJECT_PERIOD_DF)

    # TODO: wrap in spin on database lock
    prj_cap_df.to_csv(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "project_period.csv",
        ),
        sep=",",
        index=True,
    )
