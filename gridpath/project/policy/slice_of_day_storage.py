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
    per (project, slice_of_day_zone, period, month)

The (project, zone, period, month, hour) set is derived automatically by
crossing the params (project, zone, period, month) entries against the hours
already defined in SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS. No separate hourly
membership file is needed.

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
    value,
)

from gridpath.auxiliary.db_interface import import_csv, directories_to_db_values
from gridpath.auxiliary.dynamic_components import (
    slice_of_day_balance_provision_components,
)
from gridpath.common_functions import create_results_df
from gridpath.system.policy.slice_of_day import (
    SLICE_OF_DAY_ZONE_PRD_MONTH_HOUR_DF,
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
    """
    :param m:
    :param d:
    :return:
    """

    # -------------------------------------------------------------------------
    # Sets
    # -------------------------------------------------------------------------

    # (project, zone, period, month) loaded from the params file
    m.STOR_PRJ_SOD_ZONE_PRD_MONTHS = Set(dimen=4)

    # (project, zone, period, month, hour) derived by crossing the params set
    # with the hours defined in SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
    m.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS = Set(
        dimen=5,
        initialize=lambda mod: [
            (g, z, p, mn, hr)
            for (g, z, p, mn) in mod.STOR_PRJ_SOD_ZONE_PRD_MONTHS
            for (zz, pp, mn2, hr) in mod.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
            if zz == z and pp == p and mn2 == mn
        ],
    )

    # Hours for each (project, zone, period, month)
    m.STOR_SOD_HOURS_BY_PRJ_ZONE_PRD_MONTH = Set(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTHS,
        initialize=lambda mod, g, z, p, mn: [
            hr
            for (zz, pp, mn2, hr) in mod.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
            if zz == z and pp == p and mn2 == mn
        ],
    )

    # Storage projects in each SOD zone
    m.STOR_SOD_PRJS_BY_ZONE = Set(
        m.SLICE_OF_DAY_ZONES,
        initialize=lambda mod, z: list(
            set(g for (g, zone, p, mn) in mod.STOR_PRJ_SOD_ZONE_PRD_MONTHS if zone == z)
        ),
    )

    # -------------------------------------------------------------------------
    # Params
    # -------------------------------------------------------------------------

    # Hours of storage duration (energy capacity / power capacity)
    m.stor_sod_duration_hours = Param(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTHS, within=NonNegativeReals
    )

    # Round-trip efficiency (fraction, e.g. 0.85)
    m.stor_sod_efficiency = Param(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTHS, within=NonNegativeReals
    )

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

    # 1. Hourly discharge <= capacity
    def max_discharge_rule(mod, g, z, p, mn, hr):
        return mod.Storage_SOD_Discharge_MW[g, z, p, mn, hr] <= mod.Capacity_MW[g, p]

    m.Storage_SOD_Max_Discharge_Constraint = Constraint(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS, rule=max_discharge_rule
    )

    # 2. Hourly charge <= capacity
    def max_charge_rule(mod, g, z, p, mn, hr):
        return mod.Storage_SOD_Charge_MW[g, z, p, mn, hr] <= mod.Capacity_MW[g, p]

    m.Storage_SOD_Max_Charge_Constraint = Constraint(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS, rule=max_charge_rule
    )

    # 3. Monthly energy limit: sum(discharge) <= capacity * duration * efficiency
    def energy_limit_rule(mod, g, z, p, mn):
        return sum(
            mod.Storage_SOD_Discharge_MW[g, z, p, mn, hr]
            for hr in mod.STOR_SOD_HOURS_BY_PRJ_ZONE_PRD_MONTH[g, z, p, mn]
        ) <= (
            mod.Capacity_MW[g, p]
            * mod.stor_sod_duration_hours[g, z, p, mn]
            * mod.stor_sod_efficiency[g, z, p, mn]
        )

    m.Storage_SOD_Energy_Limit_Constraint = Constraint(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTHS, rule=energy_limit_rule
    )

    # 4. Monthly charge balance: sum(charge) >= sum(discharge) / efficiency
    def charge_balance_rule(mod, g, z, p, mn):
        return sum(
            mod.Storage_SOD_Charge_MW[g, z, p, mn, hr]
            for hr in mod.STOR_SOD_HOURS_BY_PRJ_ZONE_PRD_MONTH[g, z, p, mn]
        ) >= sum(
            mod.Storage_SOD_Discharge_MW[g, z, p, mn, hr]
            for hr in mod.STOR_SOD_HOURS_BY_PRJ_ZONE_PRD_MONTH[g, z, p, mn]
        ) / mod.stor_sod_efficiency[
            g, z, p, mn
        ]

    m.Storage_SOD_Charge_Balance_Constraint = Constraint(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTHS, rule=charge_balance_rule
    )

    # -------------------------------------------------------------------------
    # Expressions
    # -------------------------------------------------------------------------

    # Project-level net contribution (positive = discharging, negative = charging)
    def storage_sod_contribution_rule(mod, g, z, p, mn, hr):
        return (
            mod.Storage_SOD_Discharge_MW[g, z, p, mn, hr]
            - mod.Storage_SOD_Charge_MW[g, z, p, mn, hr]
        )

    m.Storage_SOD_Contribution_MW = Expression(
        m.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS,
        rule=storage_sod_contribution_rule,
    )

    # Zone-level aggregation, indexed over SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
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

    # Register with the SOD balance
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
    """
    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

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
            index=m.STOR_PRJ_SOD_ZONE_PRD_MONTHS,
            param=(m.stor_sod_duration_hours, m.stor_sod_efficiency),
            select=(
                "project",
                "slice_of_day_zone",
                "period",
                "sod_month",
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
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return: cursor of params rows
    """
    c = conn.cursor()

    params_rows = c.execute(
        """SELECT project, slice_of_day_zone, period, sod_month, duration_hours, efficiency
        FROM inputs_project_slice_of_day_storage_params
        JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {temporal}) as relevant_periods
        USING (period)
        JOIN
        (SELECT slice_of_day_zone
        FROM inputs_geography_slice_of_day_zones
        WHERE slice_of_day_zone_scenario_id = {sod_zone}) as relevant_zones
        USING (slice_of_day_zone)
        WHERE project_slice_of_day_storage_params_scenario_id = {sod_stor_params_scenario};
        """.format(
            temporal=subscenarios.TEMPORAL_SCENARIO_ID,
            sod_zone=subscenarios.SLICE_OF_DAY_ZONE_SCENARIO_ID,
            sod_stor_params_scenario=subscenarios.PROJECT_SLICE_OF_DAY_STORAGE_PARAMS_SCENARIO_ID,
        )
    )

    return params_rows


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
    """
    Write project_slice_of_day_storage_params.tab from database.
    """

    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    params_rows = get_inputs_from_database(
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
            ["project", "slice_of_day_zone", "period", "sod_month", "duration_hours", "efficiency"]
        )
        for row in params_rows:
            writer.writerow(row)


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
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    # Add zone-level storage total to the shared system SOD dataframe so it
    # appears in system_slice_of_day.csv alongside the non-storage contribution.
    results_columns = ["total_storage_sod_contribution_mw"]
    data = [
        [
            z,
            p,
            mn,
            hr,
            value(m.Total_Storage_SOD_Contribution_MW[z, p, mn, hr]),
        ]
        for (z, p, mn, hr) in m.SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
    ]
    results_df = create_results_df(
        index_columns=["slice_of_day_zone", "period", "sod_month", "sod_hour"],
        results_columns=results_columns,
        data=data,
    )
    for c in results_columns:
        getattr(d, SLICE_OF_DAY_ZONE_PRD_MONTH_HOUR_DF)[c] = None
    getattr(d, SLICE_OF_DAY_ZONE_PRD_MONTH_HOUR_DF).update(results_df)

    if not m.STOR_PRJ_SOD_ZONE_PRD_MONTHS:
        return

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "project_slice_of_day_storage_contributions.csv",
        ),
        "w",
        newline="",
    ) as results_file:
        writer = csv.writer(results_file)
        writer.writerow(
            [
                "project",
                "slice_of_day_zone",
                "period",
                "sod_month",
                "sod_hour",
                "capacity_mw",
                "discharge_mw",
                "charge_mw",
                "net_contribution_mw",
            ]
        )
        for (g, z, p, mn, hr) in sorted(m.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS):
            writer.writerow(
                [
                    g,
                    z,
                    p,
                    mn,
                    hr,
                    value(m.Capacity_MW[g, p]),
                    value(m.Storage_SOD_Discharge_MW[g, z, p, mn, hr]),
                    value(m.Storage_SOD_Charge_MW[g, z, p, mn, hr]),
                    value(m.Storage_SOD_Contribution_MW[g, z, p, mn, hr]),
                ]
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
        which_results="project_slice_of_day_storage_contributions",
    )
