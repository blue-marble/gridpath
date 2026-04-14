# Copyright 2026 Sylvan Energy Analytics LLC.
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
Exceedance SOD compliance type.

Contributes cap_fac[g, policy, zone, period, month, hour] * Capacity_MW[g, period]
for each (period, month, hour) in a month-hour policy requirement. Completely
decoupled from operational timepoints.
"""

import csv
import os.path

from pyomo.environ import Set, Param, NonNegativeReals

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
    m.PRJ_POLICY_ZONE_PRD_MONTH_HR_EXCEEDANCE = Set(dimen=6)
    m.exceedance_cap_fac = Param(
        m.PRJ_POLICY_ZONE_PRD_MONTH_HR_EXCEEDANCE, within=NonNegativeReals
    )


def contribution_in_month_hour(mod, prj, policy, zone, prd, mn, hr):
    """
    Capacity-weighted contribution in a (period, month, hour).
    Returns 0 if this project has no exceedance value for the given index.
    Only valid for month-hour policy requirements.
    """
    idx = (prj, policy, zone, prd, mn, hr)
    if idx in mod.PRJ_POLICY_ZONE_PRD_MONTH_HR_EXCEEDANCE:
        return mod.exceedance_cap_fac[idx] * mod.Capacity_MW[prj, prd]
    else:
        return 0


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
        "project_policy_exceedance_values.tab",
    )
    if os.path.exists(exceedance_file):
        data_portal.load(
            filename=exceedance_file,
            index=m.PRJ_POLICY_ZONE_PRD_MONTH_HR_EXCEEDANCE,
            param=m.exceedance_cap_fac,
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
        """SELECT ppz.project, ppz.policy_name, ppz.policy_zone,
        ev.period, ev.policy_month, ev.policy_hour, ev.cap_fac
        FROM
        (SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {portfolio}) as relevant_projects
        JOIN inputs_project_policy_zones ppz
          USING (project)
        JOIN inputs_project_policy_exceedance_values ev
          ON ev.project = ppz.project
         AND ev.exceedance_values_scenario_id = ppz.exceedance_values_scenario_id
        JOIN
        (SELECT DISTINCT period FROM inputs_temporal
         WHERE temporal_scenario_id = {temporal}
         AND subproblem_id = {subproblem}
         AND stage_id = {stage}) as relevant_periods
        USING (period)
        JOIN
        (SELECT policy_name, policy_zone
         FROM inputs_geography_policy_zones
         WHERE policy_zone_scenario_id = {policy_zone_scenario}) as relevant_zones
        USING (policy_name, policy_zone)
        WHERE ppz.project_policy_zone_scenario_id = {project_policy_zone_scenario}
        AND ppz.compliance_type = 'sod_exceedance';
        """.format(
            portfolio=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            temporal=subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem=subproblem,
            stage=stage,
            policy_zone_scenario=subscenarios.POLICY_ZONE_SCENARIO_ID,
            project_policy_zone_scenario=subscenarios.PROJECT_POLICY_ZONE_SCENARIO_ID,
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
    if rows:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "project_policy_exceedance_values.tab",
            ),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")
            writer.writerow(
                [
                    "project",
                    "policy_name",
                    "policy_zone",
                    "period",
                    "policy_month",
                    "policy_hour",
                    "cap_fac",
                ]
            )
            for row in rows:
                writer.writerow(row)
