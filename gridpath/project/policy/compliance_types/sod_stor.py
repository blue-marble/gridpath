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
Storage SOD compliance type.

Storage projects contribute net discharge (discharge - charge) to a month-hour
policy requirement. The discharge and charge variables are completely decoupled
from operational dispatch — they represent a hypothetical compliance-accounting
dispatch subject only to policy-specific duration and efficiency constraints:

  1. Hourly discharge  <= Capacity_MW[g, p]
  2. Hourly charge     <= Capacity_MW[g, p]
  3. sum(discharge)    <= Energy_Storage_Capacity_MWh[g, p] * round_trip_efficiency
  4. sum(charge)       >= sum(discharge) / round_trip_efficiency

These constraints are per (project, policy, zone, period, month).
The round-trip efficiency (sod_stor_rte) is specified directly in the
project_policy_zones input alongside the compliance_type.
"""

import csv
import os.path

from pyomo.environ import Set, Param, Var, Constraint, NonNegativeReals


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

    # (project, policy, zone) for storage projects — subset of PROJECT_POLICY_ZONES
    m.STOR_PROJECT_POLICY_ZONES = Set(dimen=3, within=m.PROJECT_POLICY_ZONES)
    m.policy_stor_round_trip_efficiency = Param(
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
            mod.Energy_Storage_Capacity_MWh[prj, prd]
            * mod.policy_stor_round_trip_efficiency[prj, pol, zone]
        )

    m.Stor_Policy_Energy_Limit_Constraint = Constraint(
        m.STOR_PRJ_POL_ZONE_PRD_MNS, rule=energy_limit_rule
    )

    def charge_balance_rule(mod, prj, pol, zone, prd, mn):
        return (
            sum(
                mod.Stor_Policy_Charge_MW[prj, pol, zone, prd, mn, hr]
                for hr in mod.STOR_POL_HOURS_BY_PRJ_ZONE_PRD_MN[prj, pol, zone, prd, mn]
            )
            >= sum(
                mod.Stor_Policy_Discharge_MW[prj, pol, zone, prd, mn, hr]
                for hr in mod.STOR_POL_HOURS_BY_PRJ_ZONE_PRD_MN[prj, pol, zone, prd, mn]
            )
            / mod.policy_stor_round_trip_efficiency[prj, pol, zone]
        )

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
    """
    Load STOR_PROJECT_POLICY_ZONES and policy_stor_round_trip_efficiency from
    the project_policy_zones.tab file (filtering to sod_stor compliance type).
    """
    ppz_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "project_policy_zones.tab",
    )

    stor_ppz = []
    rte_dict = {}
    with open(ppz_file, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["compliance_type"] == "sod_stor":
                prj = row["project"]
                pol = row["policy_name"]
                zone = row["policy_zone"]
                stor_ppz.append((prj, pol, zone))
                rte = row["sod_stor_rte"]
                rte_dict[(prj, pol, zone)] = float(rte)

    data_portal.data()["STOR_PROJECT_POLICY_ZONES"] = {None: stor_ppz}
    data_portal.data()["policy_stor_round_trip_efficiency"] = rte_dict


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
