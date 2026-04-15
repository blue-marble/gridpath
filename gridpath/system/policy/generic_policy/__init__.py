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

import pandas as pd

from gridpath.auxiliary.db_interface import import_csv

POLICY_ZONE_PRD_DF = "policy_zone_period_df"
POLICY_MH_DF = "policy_month_hour_df"


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
    """ """
    # First create the results dataframes
    # Other modules will update these dataframes with actual results

    p_z_bt_h_df = pd.DataFrame(
        columns=[
            "policy_name",
            "policy_zone",
            "balancing_type_horizon",
            "horizon",
        ],
        data=[
            [p, z, bt, h] for (p, z, bt, h) in m.POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ
        ],
    ).set_index(["policy_name", "policy_zone", "balancing_type_horizon", "horizon"])

    p_z_bt_h_df.sort_index(inplace=True)
    setattr(d, POLICY_ZONE_PRD_DF, p_z_bt_h_df)

    if m.POLICIES_ZONE_PRDS_MONTH_HOURS_WITH_REQ:
        p_z_prd_mn_hr_df = pd.DataFrame(
            columns=[
                "policy_name",
                "policy_zone",
                "period",
                "policy_month",
                "policy_hour",
            ],
            data=[
                [p, z, prd, mn, hr]
                for (p, z, prd, mn, hr) in m.POLICIES_ZONE_PRDS_MONTH_HOURS_WITH_REQ
            ],
        ).set_index(
            ["policy_name", "policy_zone", "period", "policy_month", "policy_hour"]
        )

        p_z_prd_mn_hr_df.sort_index(inplace=True)
        setattr(d, POLICY_MH_DF, p_z_prd_mn_hr_df)


def import_results_into_database(
    scenario_id,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    c,
    db,
    results_directory,
    quiet,
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
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        quiet=quiet,
        results_directory=results_directory,
        which_results="system_policy_requirements",
    )

    import_csv(
        conn=db,
        cursor=c,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        quiet=quiet,
        results_directory=results_directory,
        which_results="system_month_hour_policy_requirements",
    )
