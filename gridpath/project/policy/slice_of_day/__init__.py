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
Aggregator for project-level slice-of-day contributions.

Delegates to three contribution-type sub-modules:
  - exceedance  : cap_fac[g, z, p, mn, hr] * Capacity_MW[g, p]
  - flat_block  : Capacity_MW[g, p] in every SOD hour (cap_fac = 1)
  - storage     : endogenous discharge/charge with energy constraints

After calling each sub-module, this module builds the combined non-storage
set PRJ_SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS (exceedance ∪ flat_block),
the per-zone project index SLICE_OF_DAY_PRJS_BY_ZONE, and the unified
Slice_of_Day_Contribution_MW expression that dispatches to the appropriate
sub-expression. These are consumed by
system.policy.slice_of_day.aggregate_slice_of_day_contributions.

Storage contribution is registered separately with the SOD balance by the
storage sub-module via slice_of_day_balance_provision_components.
"""

import csv
import os.path
from pyomo.environ import Set, Expression, value

from gridpath.auxiliary.db_interface import import_csv
from gridpath.common_functions import create_results_df
from gridpath.system.policy.slice_of_day import SLICE_OF_DAY_ZONE_PRD_MONTH_HOUR_DF

from gridpath.project.policy.slice_of_day import exceedance, flat_block, storage


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
    # Delegate to each contribution type
    exceedance.add_model_components(
        m,
        d,
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
    )
    flat_block.add_model_components(
        m,
        d,
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
    )
    storage.add_model_components(
        m,
        d,
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
    )

    # Combined non-storage set (exceedance ∪ flat_block), consumed by
    # aggregate_slice_of_day_contributions
    m.PRJ_SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS = Set(
        dimen=5,
        initialize=lambda mod: list(
            set(mod.PRJ_EXCEEDANCE_SOD_ZONE_PRD_MONTH_HOURS)
            | set(mod.PRJ_FLAT_BLOCK_SOD_ZONE_PRD_MONTH_HOURS)
        ),
    )

    m.SLICE_OF_DAY_PRJS_BY_ZONE = Set(
        m.SLICE_OF_DAY_ZONES,
        initialize=lambda mod, z: list(
            set(
                g
                for (g, zone, p, mn, hr) in mod.PRJ_SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS
                if zone == z
            )
        ),
    )

    def sod_contribution_rule(mod, g, z, p, mn, hr):
        if (g, z, p, mn, hr) in mod.PRJ_EXCEEDANCE_SOD_ZONE_PRD_MONTH_HOURS:
            return mod.Exceedance_Contribution_MW[g, z, p, mn, hr]
        return mod.Flat_Block_Contribution_MW[g, z, p, mn, hr]

    m.Slice_of_Day_Contribution_MW = Expression(
        m.PRJ_SLICE_OF_DAY_ZONE_PRD_MONTH_HOURS,
        rule=sod_contribution_rule,
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
    exceedance.load_model_data(
        m,
        d,
        data_portal,
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
    )
    flat_block.load_model_data(
        m,
        d,
        data_portal,
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
    )
    storage.load_model_data(
        m,
        d,
        data_portal,
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
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
    # Not called directly; each sub-module's write_model_inputs queries
    # independently. Provided here for interface completeness.
    pass


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
    exceedance.write_model_inputs(
        scenario_directory,
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )
    flat_block.write_model_inputs(
        scenario_directory,
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )
    storage.write_model_inputs(
        scenario_directory,
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )


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
    # Add zone-level storage total to the shared SOD dataframe
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

    # Write per-project contributions CSV
    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "project_slice_of_day_contributions.csv",
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
                "cap_fac",
                "discharge_mw",
                "charge_mw",
                "slice_of_day_contribution_mw",
            ]
        )
        for g, z, p, mn, hr in sorted(m.PRJ_EXCEEDANCE_SOD_ZONE_PRD_MONTH_HOURS):
            writer.writerow(
                [
                    g,
                    z,
                    p,
                    mn,
                    hr,
                    value(m.Capacity_MW[g, p]),
                    value(m.exceedance_cap_fac[g, z, p, mn, hr]),
                    None,
                    None,
                    value(m.Exceedance_Contribution_MW[g, z, p, mn, hr]),
                ]
            )
        for g, z, p, mn, hr in sorted(m.PRJ_FLAT_BLOCK_SOD_ZONE_PRD_MONTH_HOURS):
            writer.writerow(
                [
                    g,
                    z,
                    p,
                    mn,
                    hr,
                    value(m.Capacity_MW[g, p]),
                    1.0,
                    None,
                    None,
                    value(m.Flat_Block_Contribution_MW[g, z, p, mn, hr]),
                ]
            )
        for g, z, p, mn, hr in sorted(m.STOR_PRJ_SOD_ZONE_PRD_MONTH_HOURS):
            writer.writerow(
                [
                    g,
                    z,
                    p,
                    mn,
                    hr,
                    value(m.Capacity_MW[g, p]),
                    None,
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
        which_results="project_slice_of_day_contributions",
    )
