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

import pandas as pd

from gridpath.auxiliary.db_interface import import_csv

PRM_ZONE_PRD_DF = "prm_zone_period_df"


def export_results(scenario_directory, subproblem, stage, m, d):
    """ """
    # First create the results dataframes
    # Other modules will update these dataframe with actual results
    # The results dataframes are by index

    # Zone-period DF
    z_prd_df = pd.DataFrame(
        columns=[
            "prm_zone",
            "period",
            "discount_factor",
            "number_years_represented",
        ],
        data=[
            [
                z,
                p,
                m.discount_factor[p],
                m.number_years_represented[p],
            ]
            for (z, p) in m.PRM_ZONE_PERIODS_WITH_REQUIREMENT
        ],
    ).set_index(["prm_zone", "period"])

    z_prd_df.sort_index(inplace=True)

    # Add the dataframe to the dynamic components to pass to other modules
    setattr(d, PRM_ZONE_PRD_DF, z_prd_df)


def import_results_into_database(
    scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    import_csv(
        conn=db,
        cursor=c,
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
        quiet=quiet,
        results_directory=results_directory,
        which_results="system_prm",
    )
