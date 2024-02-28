# Copyright 2016-2024 Blue Marble Analytics LLC.
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
import pandas as pd
from pyomo.environ import value

from gridpath.auxiliary.db_interface import import_csv


def export_summary_results(
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
    Export all results from the PROJECT_CAPACITY_DF and PROJECT_OPERATIONS_DF
    that various modules have added to
    """

    project_summary_df = pd.DataFrame(
        columns=[
            "project",
            "capacity_type",
            "availability_type",
            "operational_type",
            "technology",
            "load_zone",
            "total_delivered_power",
        ],
        data=[
            [
                prj,
                m.capacity_type[prj],
                m.availability_type[prj],
                m.operational_type[prj],
                m.technology[prj],
                m.load_zone[prj],
                sum(
                    value(m.Power_Provision_MW[_prj, tmp])
                    for (_prj, tmp) in m.PRJ_OPR_TMPS
                    if _prj == prj
                ),
            ]
            for prj in m.PROJECTS
        ],
    ).set_index(["project"])

    project_summary_df.sort_index(inplace=True)

    project_summary_df.to_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "project_summary.csv",
        ),
        sep=",",
        index=True,
    )


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
        which_results="project_summary",
    )
