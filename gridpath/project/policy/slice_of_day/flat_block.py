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
Slice-of-day contribution for flat_block-type projects.
The contribution is Capacity_MW[g, p] for every (zone, period, month, hour)
in the slice-of-day target schedule — i.e., a cap_fac of 1 in every SOD hour.
No per-project input file is needed; the set of applicable hours is synthesized
from the target schedule in the database.
"""

import csv
import os.path
from pyomo.environ import Set, Expression

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
    m.PRJ_FLAT_BLOCK_SOD_ZONE_PRD_MONTH_HOURS = Set(dimen=5)

    def flat_block_contribution_rule(mod, g, z, p, mn, hr):
        return mod.Capacity_MW[g, p]

    m.Flat_Block_Contribution_MW = Expression(
        m.PRJ_FLAT_BLOCK_SOD_ZONE_PRD_MONTH_HOURS,
        rule=flat_block_contribution_rule,
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
    flat_block_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "project_slice_of_day_flat_block_contributions.tab",
    )
    if os.path.exists(flat_block_file):
        data_portal.load(
            filename=flat_block_file,
            set=m.PRJ_FLAT_BLOCK_SOD_ZONE_PRD_MONTH_HOURS,
            select=(
                "project",
                "slice_of_day_zone",
                "period",
                "sod_month",
                "sod_hour",
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
                  t.period, t.sod_month, t.sod_hour
        FROM inputs_project_slice_of_day_projects ppz
        JOIN inputs_system_slice_of_day_targets t
            ON t.slice_of_day_zone = ppz.slice_of_day_zone
        JOIN
        (SELECT period FROM inputs_temporal_periods
         WHERE temporal_scenario_id = {temporal}) AS relevant_periods
            ON relevant_periods.period = t.period
        JOIN
        (SELECT slice_of_day_zone FROM inputs_geography_slice_of_day_zones
         WHERE slice_of_day_zone_scenario_id = {sod_zone}) AS relevant_zones
            ON relevant_zones.slice_of_day_zone = ppz.slice_of_day_zone
        WHERE ppz.project_slice_of_day_projects_scenario_id = {projects_scenario}
        AND ppz.contribution_type = 'flat_block'
        AND t.slice_of_day_target_scenario_id = {target_scenario}
        GROUP BY ppz.project, ppz.slice_of_day_zone, t.period, t.sod_month, t.sod_hour;
        """.format(
            temporal=subscenarios.TEMPORAL_SCENARIO_ID,
            sod_zone=subscenarios.SLICE_OF_DAY_ZONE_SCENARIO_ID,
            projects_scenario=subscenarios.PROJECT_SLICE_OF_DAY_PROJECTS_SCENARIO_ID,
            target_scenario=subscenarios.SLICE_OF_DAY_TARGET_SCENARIO_ID,
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
            "project_slice_of_day_flat_block_contributions.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(
            ["project", "slice_of_day_zone", "period", "sod_month", "sod_hour"]
        )
        for row in rows:
            writer.writerow(row)
