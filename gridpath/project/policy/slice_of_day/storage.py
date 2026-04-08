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
Slice-of-day contribution for storage resources.

Storage resources can contribute positively (discharge) or negatively (charge)
to the slice-of-day requirement in each hour. The hourly net contribution is
determined endogenously, subject to the following constraints per
(project, zone, period, month):

1. Hourly discharge <= Capacity_MW[g, p]
2. Hourly charge    <= Capacity_MW[g, p]
3. sum(discharge)   <= Capacity_MW[g, p] * duration_hours * efficiency
4. sum(charge)      >= sum(discharge) / efficiency

Input:
  - project_slice_of_day_storage_params.tab : duration_hours and efficiency
    per (project, slice_of_day_zone)

The (project, zone, period, month, hour) set is derived automatically by
crossing the params (project, zone) entries against the hours already defined
in SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS. No separate hourly membership file is
needed.

If the params file is absent the sets are empty and no constraints are added.
"""

import csv
import os.path
from pyomo.environ import (
    Set,
    Param,
    Var,
    Constraint,
    Expression,
    NonNegativeReals,
)

from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.auxiliary.dynamic_components import (
    slice_of_day_balance_provision_components,
)


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
    # Sets
    # -------------------------------------------------------------------------

    m.STOR_PRJ_SOD_ZONES = Set(dimen=2)

    m.STOR_PRJ_SOD_ZONE_PRD_MONTHS = Set(
        dimen=4,
        initialize=lambda mod: [
            (g, z, p, mn)
            for (g, z) in mod.STOR_PRJ_SOD_ZONES
            for (zz, p, mn, hr) in mod.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
            if zz == z and (g, p) in mod.PRJ_OPR_PRDS
        ],
    )

    m.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS = Set(
        dimen=5,
        initialize=lambda mod: [
            (g, z, p, mn, hr)
            for (g, z, p, mn) in mod.STOR_PRJ_SOD_ZONE_PRD_MONTHS
            for (zz, pp, mn2, hr) in mod.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
            if zz == z and pp == p and mn2 == mn
        ],
    )

    m.STOR_SOD_HOURS_BY_PRJ_ZONE_PRD_MONTH = Set(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTHS,
        initialize=lambda mod, g, z, p, mn: [
            hr
            for (zz, pp, mn2, hr) in mod.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
            if zz == z and pp == p and mn2 == mn
        ],
    )

    m.STOR_SOD_PRJS_BY_ZONE = Set(
        m.SLICE_OF_DAY_ZONES,
        initialize=lambda mod, z: list(
            set(g for (g, zone) in mod.STOR_PRJ_SOD_ZONES if zone == z)
        ),
    )

    # -------------------------------------------------------------------------
    # Params
    # -------------------------------------------------------------------------

    m.stor_sod_duration_hours = Param(m.STOR_PRJ_SOD_ZONES, within=NonNegativeReals)

    m.stor_sod_efficiency = Param(m.STOR_PRJ_SOD_ZONES, within=NonNegativeReals)

    # -------------------------------------------------------------------------
    # Variables
    # -------------------------------------------------------------------------

    m.Storage_SOD_Discharge_MW = Var(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS, within=NonNegativeReals
    )

    m.Storage_SOD_Charge_MW = Var(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS, within=NonNegativeReals
    )

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------

    def max_discharge_rule(mod, g, z, p, mn, hr):
        return mod.Storage_SOD_Discharge_MW[g, z, p, mn, hr] <= mod.Capacity_MW[g, p]

    m.Storage_SOD_Max_Discharge_Constraint = Constraint(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS, rule=max_discharge_rule
    )

    def max_charge_rule(mod, g, z, p, mn, hr):
        return mod.Storage_SOD_Charge_MW[g, z, p, mn, hr] <= mod.Capacity_MW[g, p]

    m.Storage_SOD_Max_Charge_Constraint = Constraint(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS, rule=max_charge_rule
    )

    def energy_limit_rule(mod, g, z, p, mn):
        return sum(
            mod.Storage_SOD_Discharge_MW[g, z, p, mn, hr]
            for hr in mod.STOR_SOD_HOURS_BY_PRJ_ZONE_PRD_MONTH[g, z, p, mn]
        ) <= (
            mod.Capacity_MW[g, p]
            * mod.stor_sod_duration_hours[g, z]
            * mod.stor_sod_efficiency[g, z]
        )

    m.Storage_SOD_Energy_Limit_Constraint = Constraint(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTHS, rule=energy_limit_rule
    )

    def charge_balance_rule(mod, g, z, p, mn):
        return (
            sum(
                mod.Storage_SOD_Charge_MW[g, z, p, mn, hr]
                for hr in mod.STOR_SOD_HOURS_BY_PRJ_ZONE_PRD_MONTH[g, z, p, mn]
            )
            >= sum(
                mod.Storage_SOD_Discharge_MW[g, z, p, mn, hr]
                for hr in mod.STOR_SOD_HOURS_BY_PRJ_ZONE_PRD_MONTH[g, z, p, mn]
            )
            / mod.stor_sod_efficiency[g, z]
        )

    m.Storage_SOD_Charge_Balance_Constraint = Constraint(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTHS, rule=charge_balance_rule
    )

    # -------------------------------------------------------------------------
    # Expressions
    # -------------------------------------------------------------------------

    def storage_sod_contribution_rule(mod, g, z, p, mn, hr):
        return (
            mod.Storage_SOD_Discharge_MW[g, z, p, mn, hr]
            - mod.Storage_SOD_Charge_MW[g, z, p, mn, hr]
        )

    m.Storage_SOD_Contribution_MW = Expression(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS,
        rule=storage_sod_contribution_rule,
    )

    def total_storage_sod_contribution_rule(mod, z, p, mn, hr):
        return sum(
            mod.Storage_SOD_Contribution_MW[g, z, p, mn, hr]
            for g in mod.STOR_SOD_PRJS_BY_ZONE[z]
            if (g, z, p, mn, hr) in mod.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS
            and (g, p) in mod.PRJ_OPR_PRDS
        )

    m.Total_Storage_SOD_Contribution_MW = Expression(
        m.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS,
        rule=total_storage_sod_contribution_rule,
    )

    getattr(d, slice_of_day_balance_provision_components).append(
        "Total_Storage_SOD_Contribution_MW"
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
        "project_slice_of_day_storage_params.tab",
    )
    if os.path.exists(params_file):
        data_portal.load(
            filename=params_file,
            index=m.STOR_PRJ_SOD_ZONES,
            param=(m.stor_sod_duration_hours, m.stor_sod_efficiency),
            select=(
                "project",
                "slice_of_day_zone",
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
        """SELECT ppz.project, ppz.slice_of_day_zone,
                  sp.duration_hours, sp.efficiency
        FROM inputs_project_slice_of_day_projects ppz
        JOIN inputs_project_slice_of_day_storage_params sp
            ON sp.project = ppz.project
            AND sp.storage_params_scenario_id = ppz.storage_params_scenario_id
        JOIN
        (SELECT slice_of_day_zone FROM inputs_geography_slice_of_day_zones
         WHERE slice_of_day_zone_scenario_id = {sod_zone}) AS relevant_zones
            ON relevant_zones.slice_of_day_zone = ppz.slice_of_day_zone
        WHERE ppz.project_slice_of_day_projects_scenario_id = {projects_scenario}
        AND ppz.contribution_type = 'stor';
        """.format(
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
            "project_slice_of_day_storage_params.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(
            ["project", "slice_of_day_zone", "duration_hours", "efficiency"]
        )
        for row in rows:
            writer.writerow(row)
