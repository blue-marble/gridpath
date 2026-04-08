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
Slice-of-day contribution for exceedance-type projects.
The contribution is cap_fac[g, z, p, mn, hr] * Capacity_MW[g, p], where the
cap_fac is a per-project exceedance shape loaded from the database.
"""

import csv
import os.path
from pyomo.environ import Set, Param, Expression, NonNegativeReals

from gridpath.auxiliary.db_interface import directories_to_db_values


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
    m.PRJ_EXCEEDANCE_SOD_ZONE_PRD_MONTH_HOURS = Set(dimen=5)

    m.exceedance_cap_fac = Param(
        m.PRJ_EXCEEDANCE_SOD_ZONE_PRD_MONTH_HOURS, within=NonNegativeReals
    )

    def exceedance_contribution_rule(mod, g, z, p, mn, hr):
        return mod.exceedance_cap_fac[g, z, p, mn, hr] * mod.Capacity_MW[g, p]

    m.Exceedance_Contribution_MW = Expression(
        m.PRJ_EXCEEDANCE_SOD_ZONE_PRD_MONTH_HOURS,
        rule=exceedance_contribution_rule,
    )


def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    exceedance_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "project_slice_of_day_exceedance_contributions.tab",
    )
    if os.path.exists(exceedance_file):
        data_portal.load(
            filename=exceedance_file,
            index=m.PRJ_EXCEEDANCE_SOD_ZONE_PRD_MONTH_HOURS,
            param=m.exceedance_cap_fac,
            select=(
                "project",
                "slice_of_day_zone",
                "period",
                "sod_month",
                "sod_hour",
                "cap_fac",
            ),
        )


def get_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    c = conn.cursor()
    return c.execute(
        """SELECT ppz.project, ppz.slice_of_day_zone,
                  ev.period, ev.sod_month, ev.sod_hour, ev.cap_fac
        FROM inputs_project_slice_of_day_projects ppz
        JOIN inputs_project_slice_of_day_exceedance_values ev
            ON ev.project = ppz.project
            AND ev.exceedance_values_scenario_id = ppz.exceedance_values_scenario_id
        JOIN
        (SELECT period FROM inputs_temporal_periods
         WHERE temporal_scenario_id = {temporal}) AS relevant_periods
            ON relevant_periods.period = ev.period
        JOIN
        (SELECT slice_of_day_zone FROM inputs_geography_slice_of_day_zones
         WHERE slice_of_day_zone_scenario_id = {sod_zone}) AS relevant_zones
            ON relevant_zones.slice_of_day_zone = ppz.slice_of_day_zone
        WHERE ppz.project_slice_of_day_projects_scenario_id = {projects_scenario}
        AND ppz.contribution_type = 'exceedance';
        """.format(
            temporal=subscenarios.TEMPORAL_SCENARIO_ID,
            sod_zone=subscenarios.SLICE_OF_DAY_ZONE_SCENARIO_ID,
            projects_scenario=subscenarios.PROJECT_SLICE_OF_DAY_PROJECTS_SCENARIO_ID,
        )
    ).fetchall()


def validate_inputs(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    pass


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    rows = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "project_slice_of_day_exceedance_contributions.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(
            [
                "project",
                "slice_of_day_zone",
                "period",
                "sod_month",
                "sod_hour",
                "cap_fac",
            ]
        )
        for row in rows:
            writer.writerow(row)
