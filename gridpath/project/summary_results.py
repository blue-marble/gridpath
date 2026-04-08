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

""" """

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
    """ """

    project_summary_df = pd.DataFrame(
        columns=[
            "project",
            "period",
            "capacity_type",
            "operational_type",
            "technology",
            "load_zone",
            "total_delivered_bulk_power_mwh",
            "cap_factor_equivalent",
            "capacity_mw",
            "energy_mwh",
            "hyb_gen_capacity_mw",
            "hyb_stor_capacity_mw",
            "stor_energy_capacity_mwh",
            "fuel_prod_capacity_fuelunitperhour",
            "fuel_rel_capacity_fuelunitperhour",
            "fuel_stor_capacity_fuelunit",
        ],
        data=[
            [
                prj,
                prd,
                m.capacity_type[prj],
                m.operational_type[prj],
                m.technology[prj],
                m.load_zone[prj],
                sum(
                    value(m.Bulk_Power_Provision_MW[_prj, tmp])
                    * m.hrs_in_tmp[tmp]
                    * m.tmp_weight[tmp]
                    for (_prj, tmp) in m.PRJ_OPR_TMPS
                    if _prj == prj and m.period[tmp] == prd
                ),
                (
                    sum(
                        (
                            value(m.Bulk_Power_Provision_MW[_prj, tmp])
                            / value(m.Capacity_MW[prj, prd])
                        )
                        * m.hrs_in_tmp[tmp]
                        * m.tmp_weight[tmp]
                        for (_prj, tmp) in m.PRJ_OPR_TMPS
                        if _prj == prj and m.period[tmp] == prd
                    )
                    / sum(
                        m.hrs_in_tmp[tmp] * m.tmp_weight[tmp]
                        for tmp in m.TMPS_IN_PRD[prd]
                    )
                    if value(m.Capacity_MW[prj, prd]) > 0
                    else None
                ),
                value(m.Capacity_MW[prj, prd]),
                value(m.Energy_MWh[prj, prd]),
                value(m.Hyb_Gen_Capacity_MW[prj, prd]),
                value(m.Hyb_Stor_Capacity_MW[prj, prd]),
                value(m.Energy_Storage_Capacity_MWh[prj, prd]),
                value(m.Fuel_Production_Capacity_FuelUnitPerHour[prj, prd]),
                value(m.Fuel_Release_Capacity_FuelUnitPerHour[prj, prd]),
                value(m.Fuel_Storage_Capacity_FuelUnit[prj, prd]),
            ]
            for (prj, prd) in m.PRJ_OPR_PRDS
        ],
    ).set_index(["project", "period"])

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
            "project_period_summary.csv",
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
        which_results="project_period_summary",
    )
