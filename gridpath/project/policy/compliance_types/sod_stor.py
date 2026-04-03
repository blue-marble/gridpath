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
Storage SOD compliance type.

Storage projects contribute net discharge (discharge - charge) to a month-hour
policy requirement. The discharge and charge variables are completely decoupled
from operational dispatch — they represent a hypothetical compliance-accounting
dispatch subject only to policy-specific duration and efficiency constraints:

  1. Hourly discharge  <= Capacity_MW[g, p]
  2. Hourly charge     <= Capacity_MW[g, p]
  3. sum(discharge)    <= Capacity_MW[g, p] * duration_hours * efficiency
  4. sum(charge)       >= sum(discharge) / efficiency

These constraints are per (project, policy, zone, period, month).
"""

import csv
import os.path

from pyomo.environ import Set, Param, Var, Constraint, NonNegativeReals

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
    # -------------------------------------------------------------------------
    # Sets and params
    # -------------------------------------------------------------------------

    # (project, policy, zone) for storage projects — loaded from params file
    m.STOR_PROJECT_POLICY_ZONES = Set(dimen=3, within=m.PROJECT_POLICY_ZONES)
    m.policy_stor_duration_hours = Param(
        m.STOR_PROJECT_POLICY_ZONES, within=NonNegativeReals
    )
    m.policy_stor_efficiency = Param(
        m.STOR_PROJECT_POLICY_ZONES, within=NonNegativeReals
    )

    # (project, policy, zone, period, month) — cross params set with month-hour
    # requirements, filtering to operational periods. One row per unique month
    # across all hours (mirrors STOR_PRJ_SOD_ZONE_PRD_MONTHS in storage.py).
    m.STOR_PRJ_POL_ZONE_PRD_MNS = Set(
        dimen=5,
        initialize=lambda mod: list(
            set(
                (prj, pol, zone, prd, mn)
                for (prj, pol, zone) in mod.STOR_PROJECT_POLICY_ZONES
                for (p, z, prd, mn, hr) in mod.POLICIES_ZONE_PRDS_MONTH_HOURS_WITH_REQ
                if p == pol and z == zone and (prj, prd) in mod.PRJ_OPR_PRDS
            )
        ),
    )

    # (project, policy, zone, period, month, hour) — full hourly index
    m.STOR_PRJ_POL_ZONE_PRD_MN_HRS = Set(
        dimen=6,
        initialize=lambda mod: [
            (prj, pol, zone, prd, mn, hr)
            for (prj, pol, zone, prd, mn) in mod.STOR_PRJ_POL_ZONE_PRD_MNS
            for (p, z, pp, mm, hr) in mod.POLICIES_ZONE_PRDS_MONTH_HOURS_WITH_REQ
            if p == pol and z == zone and pp == prd and mm == mn
        ],
    )

    # Hours for each (project, policy, zone, period, month) — for constraint sums
    m.STOR_POL_HOURS_BY_PRJ_ZONE_PRD_MN = Set(
        m.STOR_PRJ_POL_ZONE_PRD_MNS,
        initialize=lambda mod, prj, pol, zone, prd, mn: [
            hr
            for (p, z, pp, mm, hr) in mod.POLICIES_ZONE_PRDS_MONTH_HOURS_WITH_REQ
            if p == pol and z == zone and pp == prd and mm == mn
        ],
    )

    # -------------------------------------------------------------------------
    # Variables — completely independent of operational dispatch
    # -------------------------------------------------------------------------

    m.Stor_Policy_Discharge_MW = Var(
        m.STOR_PRJ_POL_ZONE_PRD_MN_HRS, within=NonNegativeReals
    )

    m.Stor_Policy_Charge_MW = Var(
        m.STOR_PRJ_POL_ZONE_PRD_MN_HRS, within=NonNegativeReals
    )

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------

    def max_discharge_rule(mod, prj, pol, zone, prd, mn, hr):
        return (
            mod.Stor_Policy_Discharge_MW[prj, pol, zone, prd, mn, hr]
            <= mod.Capacity_MW[prj, prd]
        )

    m.Stor_Policy_Max_Discharge_Constraint = Constraint(
        m.STOR_PRJ_POL_ZONE_PRD_MN_HRS, rule=max_discharge_rule
    )

    def max_charge_rule(mod, prj, pol, zone, prd, mn, hr):
        return (
            mod.Stor_Policy_Charge_MW[prj, pol, zone, prd, mn, hr]
            <= mod.Capacity_MW[prj, prd]
        )

    m.Stor_Policy_Max_Charge_Constraint = Constraint(
        m.STOR_PRJ_POL_ZONE_PRD_MN_HRS, rule=max_charge_rule
    )

    def energy_limit_rule(mod, prj, pol, zone, prd, mn):
        return sum(
            mod.Stor_Policy_Discharge_MW[prj, pol, zone, prd, mn, hr]
            for hr in mod.STOR_POL_HOURS_BY_PRJ_ZONE_PRD_MN[prj, pol, zone, prd, mn]
        ) <= (
            mod.Capacity_MW[prj, prd]
            * mod.policy_stor_duration_hours[prj, pol, zone]
            * mod.policy_stor_efficiency[prj, pol, zone]
        )

    m.Stor_Policy_Energy_Limit_Constraint = Constraint(
        m.STOR_PRJ_POL_ZONE_PRD_MNS, rule=energy_limit_rule
    )

    def charge_balance_rule(mod, prj, pol, zone, prd, mn):
        return sum(
            mod.Stor_Policy_Charge_MW[prj, pol, zone, prd, mn, hr]
            for hr in mod.STOR_POL_HOURS_BY_PRJ_ZONE_PRD_MN[prj, pol, zone, prd, mn]
        ) >= sum(
            mod.Stor_Policy_Discharge_MW[prj, pol, zone, prd, mn, hr]
            for hr in mod.STOR_POL_HOURS_BY_PRJ_ZONE_PRD_MN[prj, pol, zone, prd, mn]
        ) / mod.policy_stor_efficiency[prj, pol, zone]

    m.Stor_Policy_Charge_Balance_Constraint = Constraint(
        m.STOR_PRJ_POL_ZONE_PRD_MNS, rule=charge_balance_rule
    )


def contribution_in_month_hour(mod, prj, policy, zone, prd, mn, hr):
    """
    Net discharge contribution in a (period, month, hour). Completely
    independent of operational dispatch.
    """
    return (
        mod.Stor_Policy_Discharge_MW[prj, policy, zone, prd, mn, hr]
        - mod.Stor_Policy_Charge_MW[prj, policy, zone, prd, mn, hr]
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
    params_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "project_policy_storage_params.tab",
    )
    if os.path.exists(params_file):
        data_portal.load(
            filename=params_file,
            index=m.STOR_PROJECT_POLICY_ZONES,
            param=(m.policy_stor_duration_hours, m.policy_stor_efficiency),
            select=(
                "project",
                "policy_name",
                "policy_zone",
                "duration_hours",
                "efficiency",
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
        """SELECT ppz.project, ppz.policy_name, ppz.policy_zone,
        sp.duration_hours, sp.efficiency
        FROM inputs_project_policy_zones ppz
        JOIN inputs_project_policy_storage_params sp
          ON sp.project = ppz.project
         AND sp.storage_params_scenario_id = ppz.storage_params_scenario_id
        JOIN
        (SELECT policy_name, policy_zone
         FROM inputs_geography_policy_zones
         WHERE policy_zone_scenario_id = {policy_zone_scenario}) as relevant_zones
        USING (policy_name, policy_zone)
        WHERE ppz.project_policy_zone_scenario_id = {project_policy_zone_scenario}
        AND ppz.compliance_type = 'sod_stor';
        """.format(
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
                "project_policy_storage_params.tab",
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
                    "duration_hours",
                    "efficiency",
                ]
            )
            for row in rows:
                writer.writerow(row)
