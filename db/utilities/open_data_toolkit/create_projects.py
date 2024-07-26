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

import csv
from argparse import ArgumentParser
import os.path
import pandas as pd
import sys

from db.common_functions import connect_to_database


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument("-db", "--database", default="../../open_data.db")
    parser.add_argument("-rep", "--report_date", default="2023-01-01")
    parser.add_argument("-y", "--study_year", default=2026)
    parser.add_argument("-r", "--region", default="WECC")
    parser.add_argument(
        "-p_csv",
        "--portfolio_csv_location",
        default="../../csvs_open_data/project/portfolios",
    )
    parser.add_argument("-p_id", "--project_portfolio_scenario_id", default=1)
    parser.add_argument(
        "-p_name", "--project_portfolio_scenario_name", default="wecc_plants_units"
    )
    parser.add_argument(
        "-lz_csv",
        "--load_zone_csv_location",
        default="../../csvs_open_data/project/load_zones",
    )
    parser.add_argument("-lz_id", "--project_load_zone_scenario_id", default=1)
    parser.add_argument(
        "-lz_name", "--project_load_zone_scenario_name", default="wecc_baas"
    )
    parser.add_argument(
        "-avl_csv",
        "--availability_csv_location",
        default="../../csvs_open_data/project/availability",
    )
    parser.add_argument("-avl_id", "--project_availability_scenario_id", default=1)
    parser.add_argument(
        "-avl_name", "--project_availability_scenario_name", default="no_derates"
    )
    parser.add_argument(
        "-cap_csv",
        "--specified_capacity_csv_location",
        default="../../csvs_open_data/project/capacity_specified",
    )
    parser.add_argument(
        "-cap_id", "--project_specified_capacity_scenario_id", default=1
    )
    parser.add_argument(
        "-cap_name", "--project_specified_capacity_scenario_name", default="base"
    )
    parser.add_argument(
        "-fcost_csv",
        "--fixed_cost_csv_location",
        default="../../csvs_open_data/project/fixed_cost",
    )
    parser.add_argument("-fcost_id", "--project_fixed_cost_scenario_id", default=1)
    parser.add_argument(
        "-fcost_name", "--project_fixed_cost_scenario_name", default="base"
    )
    parser.add_argument(
        "-fuels_csv",
        "--fuels_csv_location",
        default="../../csvs_open_data/project/opchar/fuels",
    )
    parser.add_argument("-fuel_id", "--project_fuel_scenario_id", default=1)
    parser.add_argument("-fuel_name", "--project_fuel_scenario_name", default="base")

    parser.add_argument(
        "-hr_csv",
        "--hr_csv_location",
        default="../../csvs_open_data/project/opchar/heat_rates",
    )
    parser.add_argument("-hr_id", "--project_hr_scenario_id", default=1)
    parser.add_argument("-hr_name", "--project_hr_scenario_name",
                        default="generic")

    parser.add_argument(
        "-opchar_csv",
        "--opchar_csv_location",
        default="../../csvs_open_data/project/opchar",
    )
    parser.add_argument(
        "-opchar_id", "--project_operational_chars_scenario_id", default=1
    )
    parser.add_argument(
        "-opchar_name",
        "--project_operational_chars_scenario_name",
        default="wecc_plants_opchar",
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


# TODO: refactor queries to their components


def get_project_portfolio_for_region(
    conn,
    report_date,
    study_year,
    region,
    csv_location,
    subscenario_id,
    subscenario_name,
):
    """
    Unit level except for wind (onshore and offshore) and solar PV, which are
    aggregated to the BA-level.
    TODO: disaggregate the hybrids out of the wind/solar project and combine
     with their battery components
    """
    # For disaggregated unit-level projects, use plant_id_eia__generator_id
    # as the project name
    # For BA-aggregated projects, use prime_mover_BA
    sql = f"""
    -- Disaggregated units
    SELECT plant_id_eia || '__' || REPLACE(REPLACE(generator_id, ' ', '_'), '-', 
        '_') AS project, 
    NULL as specified, 
    NULL as new_build, capacity_type
    FROM raw_data_eia860_generators
    JOIN raw_data_aux_eia_prime_mover_key
    USING (prime_mover_code)
    --WHERE report_date = '{report_date}' -- get latest
    WHERE (unixepoch(current_planned_generator_operating_date) < unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
    AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
    AND balancing_authority_code_eia in (
        SELECT baa
        FROM raw_data_aux_baa_key
        WHERE region = '{region}'
    )
    AND (plant_id_eia, generator_id) NOT IN (
            SELECT DISTINCT plant_id_eia, generator_id
            FROM raw_data_eia860_generators
            WHERE prime_mover_code IN ('WT', 'WS', 'PV')
        )
    UNION
    -- Aggregated units
    SELECT DISTINCT 
        CASE WHEN prime_mover_code = 'WT' THEN 'Wind' 
        ELSE 
            CASE WHEN prime_mover_code = 'WS' THEN 'Wind_Offshore' 
            ELSE 'Solar'
            END
        END || '_' || balancing_authority_code_eia AS project,
        NULL as specified,
        NULL as new_build,
        capacity_type
    FROM raw_data_eia860_generators
    JOIN raw_data_aux_eia_prime_mover_key
    USING (prime_mover_code)
    --WHERE report_date = '{report_date}' -- get latest
    WHERE (unixepoch(current_planned_generator_operating_date) < unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
    AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
    AND balancing_authority_code_eia in (
        SELECT baa
        FROM raw_data_aux_baa_key
        WHERE region = '{region}'
    )
    AND (plant_id_eia, generator_id) IN (
            SELECT DISTINCT plant_id_eia, generator_id
            FROM raw_data_eia860_generators
            WHERE prime_mover_code IN ('WT', 'WS', 'PV')
    )
    """

    df = pd.read_sql(sql, conn)
    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_{subscenario_name}.csv"),
        index=False,
    )


def get_project_load_zones(
    conn,
    report_date,
    study_year,
    region,
    csv_location,
    subscenario_id,
    subscenario_name,
):
    sql = f"""
    SELECT plant_id_eia || '__' || REPLACE(REPLACE(generator_id, ' ', '_'), '-', 
        '_') AS project, balancing_authority_code_eia AS load_zone
    FROM raw_data_eia860_generators
    --WHERE report_date = '{report_date}' -- get latest
    WHERE (unixepoch(current_planned_generator_operating_date) < unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
    AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
    AND balancing_authority_code_eia in (
        SELECT baa
        FROM raw_data_aux_baa_key
        WHERE region = '{region}'
    )
    AND (plant_id_eia, generator_id) NOT IN (
            SELECT DISTINCT plant_id_eia, generator_id
            FROM raw_data_eia860_generators
            WHERE prime_mover_code IN ('WT', 'WS', 'PV')
        )
    UNION
    SELECT DISTINCT 
        CASE WHEN prime_mover_code = 'WT' THEN 'Wind' 
        ELSE 
            CASE WHEN prime_mover_code = 'WS' THEN 'Wind_Offshore' 
            ELSE 'Solar'
            END
        END || '_' || balancing_authority_code_eia AS project,
        balancing_authority_code_eia AS load_zone
    FROM raw_data_eia860_generators
    --WHERE report_date = '{report_date}' -- get latest
    WHERE (unixepoch(current_planned_generator_operating_date) < unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
    AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
    AND balancing_authority_code_eia in (
        SELECT baa
        FROM raw_data_aux_baa_key
        WHERE region = '{region}'
    )
    AND (plant_id_eia, generator_id) IN (
            SELECT DISTINCT plant_id_eia, generator_id
            FROM raw_data_eia860_generators
            WHERE prime_mover_code IN ('WT', 'WS', 'PV')
        )
    """

    df = pd.read_sql(sql, conn)
    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_" f"{subscenario_name}.csv"),
        index=False,
    )


def get_project_availability(
    conn,
    report_date,
    study_year,
    region,
    csv_location,
    subscenario_id,
    subscenario_name,
):
    sql = f"""
    SELECT plant_id_eia || '__' || REPLACE(REPLACE(generator_id, ' ', '_'), '-', 
        '_') AS project, 
    'exogenous' AS availability_type,
    NULL AS exogenous_availability_independent_scenario_id,
    NULL AS exogenous_availability_weather_scenario_id,
    NULL AS endogenous_availability_scenario_id
    FROM raw_data_eia860_generators
    --WHERE report_date = '{report_date}' -- get latest
    WHERE (unixepoch(current_planned_generator_operating_date) < unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
    AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
    AND balancing_authority_code_eia in (
        SELECT baa
        FROM raw_data_aux_baa_key
        WHERE region = '{region}'
    )
    AND (plant_id_eia, generator_id) NOT IN (
            SELECT DISTINCT plant_id_eia, generator_id
            FROM raw_data_eia860_generators
            WHERE prime_mover_code IN ('WT', 'WS', 'PV')
        )
    UNION
    SELECT DISTINCT 
        CASE WHEN prime_mover_code = 'WT' THEN 'Wind' 
        ELSE 
            CASE WHEN prime_mover_code = 'WS' THEN 'Wind_Offshore' 
            ELSE 'Solar'
            END
        END || '_' || balancing_authority_code_eia AS project, 
        'exogenous' AS availability_type,
    NULL AS exogenous_availability_independent_scenario_id,
    NULL AS exogenous_availability_weather_scenario_id,
    NULL AS endogenous_availability_scenario_id
    FROM raw_data_eia860_generators
    --WHERE report_date = '{report_date}' -- get latest
    WHERE (unixepoch(current_planned_generator_operating_date) < unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
    AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
    AND balancing_authority_code_eia in (
        SELECT baa
        FROM raw_data_aux_baa_key
        WHERE region = '{region}'
    )
    AND (plant_id_eia, generator_id) IN (
            SELECT DISTINCT plant_id_eia, generator_id
            FROM raw_data_eia860_generators
            WHERE prime_mover_code IN ('WT', 'WS', 'PV')
        )
    """

    df = pd.read_sql(sql, conn)
    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_" f"{subscenario_name}.csv"),
        index=False,
    )


# TODO: battery durations are hardcoded right now for when not provided (1h
#  for batteries/flywheels and 12 hours for pumped hydro)
def get_project_capacity(
    conn,
    report_date,
    study_year,
    region,
    csv_location,
    subscenario_id,
    subscenario_name,
):
    sql = f"""
    SELECT plant_id_eia || '__' || REPLACE(REPLACE(generator_id, ' ', '_'), '-', 
        '_') AS project, 
        {study_year} as period,
        capacity_mw AS specified_capacity_mw,
        NULL AS hyb_gen_specified_capacity_mw,
        NULL AS hyb_stor_specified_capacity_mw,
        CASE 
            WHEN prime_mover_code NOT IN ('BA', 'ES', 'FW', 'PS') THEN NULL
            ELSE 
                CASE
                    WHEN energy_storage_capacity_mwh IS NULL
                    THEN 
                        CASE
                            WHEN prime_mover_code = 'PS' THEN 12.0*capacity_mw
                            ELSE capacity_mw
                        END
                    ELSE energy_storage_capacity_mwh
                END
        END
            AS specified_capacity_mwh,
        NULL AS fuel_production_capacity_fuelunitperhour,
        NULL AS fuel_release_capacity_fuelunitperhour,
        NULL AS fuel_storage_capacity_fuelunit
    FROM raw_data_eia860_generators
    --WHERE report_date = '{report_date}' -- get latest
    WHERE (unixepoch(current_planned_generator_operating_date) < unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
    AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
    AND balancing_authority_code_eia in (
        SELECT baa
        FROM raw_data_aux_baa_key
        WHERE region = '{region}'
    )
    AND (plant_id_eia, generator_id) NOT IN (
            SELECT DISTINCT plant_id_eia, generator_id
            FROM raw_data_eia860_generators
            WHERE prime_mover_code IN ('WT', 'WS', 'PV')
        )
    UNION
    SELECT DISTINCT 
        CASE WHEN prime_mover_code = 'WT' THEN 'Wind' 
        ELSE 
            CASE WHEN prime_mover_code = 'WS' THEN 'Wind_Offshore' 
            ELSE 'Solar'
            END
        END || '_' || balancing_authority_code_eia AS project,
        {study_year} as period,
        SUM(capacity_mw) AS specified_capacity_mw,
        NULL AS hyb_gen_specified_capacity_mw,
        NULL AS hyb_stor_specified_capacity_mw,
        SUM(energy_storage_capacity_mwh) AS specified_capacity_mwh,
        NULL AS fuel_production_capacity_fuelunitperhour,
        NULL AS fuel_release_capacity_fuelunitperhour,
        NULL AS fuel_storage_capacity_fuelunit
    FROM raw_data_eia860_generators
    --WHERE report_date = '{report_date}' -- get latest
    WHERE (unixepoch(current_planned_generator_operating_date) < unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
    AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
    AND balancing_authority_code_eia in (
        SELECT baa
        FROM raw_data_aux_baa_key
        WHERE region = '{region}'
    )
    AND (plant_id_eia, generator_id) IN (
            SELECT DISTINCT plant_id_eia, generator_id
            FROM raw_data_eia860_generators
            WHERE prime_mover_code IN ('WT', 'WS', 'PV')
        )
    GROUP BY project
    """

    df = pd.read_sql(sql, conn)
    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_" f"{subscenario_name}.csv"),
        index=False,
    )


def get_project_fixed_cost(
    conn,
    report_date,
    study_year,
    region,
    csv_location,
    subscenario_id,
    subscenario_name,
):
    sql = f"""
    SELECT plant_id_eia || '__' || REPLACE(REPLACE(generator_id, ' ', '_'), '-', 
        '_') AS project,
        {study_year} as period,
        0 AS fixed_cost_per_mw_yr,
        NULL AS hyb_gen_fixed_cost_per_mw_yr,
        NULL AS hyb_stor_fixed_cost_per_mw_yr,
        CASE WHEN prime_mover_code NOT IN ('BA', 'ES', 'FW', 'PS') 
            THEN NULL
            ELSE 0
        END
            AS fixed_cost_per_mwh_year,
        NULL AS fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr,
        NULL AS fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr,
        NULL AS fuel_storage_capacity_fixed_cost_per_fuelunit_yr
    FROM raw_data_eia860_generators
    --WHERE report_date = '{report_date}' -- get latest
    WHERE (unixepoch(current_planned_generator_operating_date) < unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
    AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
    AND balancing_authority_code_eia in (
        SELECT baa
        FROM raw_data_aux_baa_key
        WHERE region = '{region}'
    )
    AND (plant_id_eia, generator_id) NOT IN (
            SELECT DISTINCT plant_id_eia, generator_id
            FROM raw_data_eia860_generators
            WHERE prime_mover_code IN ('WT', 'WS', 'PV')
        )
    UNION
    SELECT DISTINCT 
        CASE WHEN prime_mover_code = 'WT' THEN 'Wind' 
        ELSE 
            CASE WHEN prime_mover_code = 'WS' THEN 'Wind_Offshore' 
            ELSE 'Solar'
            END
        END || '_' || balancing_authority_code_eia AS project, 
        {study_year} as period,
        0 AS specified_fixed_cost_mw,
        NULL AS hyb_gen_specified_fixed_cost_mw,
        NULL AS hyb_stor_specified_fixed_cost_mw,
        CASE
            WHEN energy_storage_capacity_mwh IS NULL THEN NULL
            ELSE 0
            END 
            AS specified_fixed_cost_mwh,
        NULL AS fuel_production_fixed_cost_fuelunitperhour,
        NULL AS fuel_release_fixed_cost_fuelunitperhour,
        NULL AS fuel_storage_fixed_cost_fuelunit
    FROM raw_data_eia860_generators
    --WHERE report_date = '{report_date}' -- get latest
    WHERE (unixepoch(current_planned_generator_operating_date) < unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
    AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
    AND balancing_authority_code_eia in (
        SELECT baa
        FROM raw_data_aux_baa_key
        WHERE region = '{region}'
    )
    AND (plant_id_eia, generator_id) IN (
            SELECT DISTINCT plant_id_eia, generator_id
            FROM raw_data_eia860_generators
            WHERE prime_mover_code IN ('WT', 'WS', 'PV')
        )
    ;
    """

    df = pd.read_sql(sql, conn)
    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_" f"{subscenario_name}.csv"),
        index=False,
    )


def get_project_fuels(
    conn,
    report_date,
    study_year,
    region,
    csv_location,
    subscenario_id,
    subscenario_name,
):

    # Only coal, gas, and fuel oil for now (with aeo prices)
    sql = f"""
        SELECT plant_id_eia || '__' || REPLACE(REPLACE(generator_id, ' ', '_'), '-', 
            '_') AS project, 
            fuel || '_' || fuel_region as fuel
        FROM raw_data_eia860_generators
        JOIN raw_data_aux_eia_energy_source_key ON (energy_source_code_1 = code)
        JOIN raw_data_aux_baa_key ON (balancing_authority_code_eia = baa)
        WHERE (unixepoch(current_planned_generator_operating_date) >= unixepoch(
        '{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
        AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
        AND balancing_authority_code_eia in (
            SELECT baa
            FROM raw_data_aux_baa_key
            WHERE region = '{region}'
        )
        AND aeo_prices = 1
        """

    c = conn.cursor()
    header = ["fuel", "min_fraction_in_fuel_blend", "max_fraction_in_fuel_blend"]
    for project, fuel in c.execute(sql).fetchall():
        if fuel is not None:
            with open(
                os.path.join(
                    csv_location,
                    f"{project}-{subscenario_id}" f"-{subscenario_name}.csv",
                ),
                "w",
            ) as filepath:
                writer = csv.writer(filepath, delimiter=",")
                writer.writerow(header)
                writer.writerow([fuel, None, None])


def get_project_heat_rates(
    conn,
    report_date,
    study_year,
    region,
    csv_location,
    subscenario_id,
    subscenario_name,
):

    # Only coal, gas, and fuel oil for now (with aeo prices)
    sql = f"""
        SELECT plant_id_eia || '__' || REPLACE(REPLACE(generator_id, ' ', '_'), '-', 
            '_') AS project, 
            prime_mover_code, fuel, heat_rate_mmbtu_per_mwh, min_load_fraction
        FROM raw_data_eia860_generators
        JOIN raw_data_aux_eia_energy_source_key ON (energy_source_code_1 = code)
        JOIN raw_data_aux_full_load_heat_rates USING (prime_mover_code, fuel)
        WHERE (unixepoch(current_planned_generator_operating_date) >= unixepoch(
        '{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
        AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
        AND balancing_authority_code_eia in (
            SELECT baa
            FROM raw_data_aux_baa_key
            WHERE region = '{region}'
        )
        AND aeo_prices = 1
        """

    c = conn.cursor()
    header = ["period", "load_point_fraction", "average_heat_rate_mmbtu_per_mwh"]
    for (
        project,
        prime_mover_code,
        fuel,
        heat_rate_mmbtu_per_mwh,
        min_load_fraction,
    ) in c.execute(sql).fetchall():
        c2 = conn.cursor()
        min_load_heat_rate_coefficient = c2.execute(
            f"""
            SELECT average_heat_rate_coefficient
            FROM raw_data_aux_heat_rate_curve
            WHERE load_point_fraction = {min_load_fraction}
            ;
            """
        ).fetchone()[0]
        with open(
            os.path.join(
                csv_location,
                f"{project}-{subscenario_id}" f"-{subscenario_name}.csv",
            ),
            "w",
        ) as filepath:
            writer = csv.writer(filepath, delimiter=",")
            writer.writerow(header)
            writer.writerow(
                [
                    0,
                    min_load_fraction,
                    min_load_heat_rate_coefficient * heat_rate_mmbtu_per_mwh,
                ]
            )
            writer.writerow([0, 1, heat_rate_mmbtu_per_mwh])


# TODO: hardcoded params
# TODO: refactor queries to ensure consistency for which projects are selected
def get_project_opchar(
    conn,
    report_date,
    study_year,
    region,
    csv_location,
    subscenario_id,
    subscenario_name,
):
    sql = f"""
     SELECT plant_id_eia || '__' || REPLACE(REPLACE(generator_id, ' ', '_'), '-', 
         '_') AS project,
         'test' as technology,
         CASE WHEN prime_mover_code NOT IN ('BA', 'ES', 'FW', 'PS') 
             THEN 'gen_simple'
             ELSE 'stor'
         END
             AS operational_type,
         'week' AS balancing_type_project,
         0 AS variable_om_cost_per_mwh,
         NULL AS variable_om_cost_by_period_scenario_id,	
         NULL AS project_fuel_scenario_id,
         NULL AS heat_rate_curves_scenario_id,	
         NULL AS variable_om_curves_scenario_id,
         NULL AS startup_chars_scenario_id,	
         NULL AS min_stable_level_fraction,
         NULL AS unit_size_mw,
         NULL AS startup_cost_per_mw,	
         NULL AS shutdown_cost_per_mw,
         NULL AS startup_fuel_mmbtu_per_mw,	
         NULL AS startup_plus_ramp_up_rate,
         NULL AS shutdown_plus_ramp_down_rate,	
         NULL AS ramp_up_when_on_rate,
         NULL AS ramp_down_when_on_rate,	
         NULL AS ramp_up_violation_penalty,
         NULL AS ramp_down_violation_penalty,	
         NULL AS min_up_time_hours,
         NULL AS min_up_time_violation_penalty,	
         NULL AS min_down_time_hours,
         NULL AS min_down_time_violation_penalty,	
         NULL AS cycle_selection_scenario_id,
         NULL AS supplemental_firing_scenario_id,	
         NULL AS allow_startup_shutdown_power,
         CASE WHEN prime_mover_code NOT IN ('BA', 'ES', 'FW', 'PS') 
             THEN NULL
             ELSE 1
         END AS storage_efficiency,	
         CASE WHEN prime_mover_code NOT IN ('BA', 'ES', 'FW', 'PS') 
             THEN NULL
             ELSE 0.9
         END AS charging_efficiency,
         CASE WHEN prime_mover_code NOT IN ('BA', 'ES', 'FW', 'PS') 
             THEN NULL
             ELSE 0.9
         END AS discharging_efficiency,	
         NULL AS charging_capacity_multiplier,
         NULL AS discharging_capacity_multiplier,	
         NULL AS soc_penalty_cost_per_energyunit,
         NULL AS soc_last_tmp_penalty_cost_per_energyunit,
         NULL AS flex_load_static_profile_scenario_id,
         NULL AS minimum_duration_hours,	
         NULL AS maximum_duration_hours,
         NULL AS aux_consumption_frac_capacity,	
         NULL AS aux_consumption_frac_power,
         NULL AS last_commitment_stage,	
         NULL AS variable_generator_profile_scenario_id,
         NULL AS curtailment_cost_per_pwh,	
         NULL AS hydro_operational_chars_scenario_id,
         NULL AS lf_reserves_up_derate,	
         NULL AS lf_reserves_down_derate,
         NULL AS regulation_up_derate,	
         NULL AS regulation_down_derate,
         NULL AS frequency_response_derate,	
         NULL AS spinning_reserves_derate,
         NULL AS lf_reserves_up_ramp_rate,	
         NULL AS lf_reserves_down_ramp_rate,
         NULL AS regulation_up_ramp_rate,
         NULL AS regulation_down_ramp_rate,
         NULL AS frequency_response_ramp_rate,
         NULL AS spinning_reserves_ramp_rate,
         NULL AS powerunithour_per_fuelunit,
         NULL AS cap_factor_limits_scenario_id,
         NULL AS partial_availability_threshold,
         NULL AS stor_exog_state_of_charge_scenario_id,
         NULL AS nonfuel_carbon_emissions_per_mwh
     FROM raw_data_eia860_generators
     --WHERE report_date = '{report_date}' -- get latest
     WHERE (unixepoch(current_planned_generator_operating_date) < unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
     AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
     AND balancing_authority_code_eia in (
         SELECT baa
         FROM raw_data_aux_baa_key
         WHERE region = '{region}'
     )
     AND (plant_id_eia, generator_id) NOT IN (
             SELECT DISTINCT plant_id_eia, generator_id
             FROM raw_data_eia860_generators
             WHERE prime_mover_code IN ('WT', 'WS', 'PV')
         )
     UNION
     SELECT DISTINCT 
         CASE WHEN prime_mover_code = 'WT' THEN 'Wind' 
         ELSE 
             CASE WHEN prime_mover_code = 'WS' THEN 'Wind_Offshore' 
             ELSE 'Solar'
             END
         END || '_' || balancing_authority_code_eia AS project,
         'test' as technology,
         'gen_var_must_take' AS operational_type,
         'week' AS balancing_type_project,
         0 AS variable_om_cost_per_mwh,
         NULL AS variable_om_cost_by_period_scenario_id,	
         NULL AS project_fuel_scenario_id,
         NULL AS heat_rate_curves_scenario_id,	
         NULL AS variable_om_curves_scenario_id,
         NULL AS startup_chars_scenario_id,	
         NULL AS min_stable_level_fraction,
         NULL AS unit_size_mw,
         NULL AS startup_cost_per_mw,	
         NULL AS shutdown_cost_per_mw,
         NULL AS startup_fuel_mmbtu_per_mw,	
         NULL AS startup_plus_ramp_up_rate,
         NULL AS shutdown_plus_ramp_down_rate,	
         NULL AS ramp_up_when_on_rate,
         NULL AS ramp_down_when_on_rate,	
         NULL AS ramp_up_violation_penalty,
         NULL AS ramp_down_violation_penalty,	
         NULL AS min_up_time_hours,
         NULL AS min_up_time_violation_penalty,	
         NULL AS min_down_time_hours,
         NULL AS min_down_time_violation_penalty,	
         NULL AS cycle_selection_scenario_id,
         NULL AS supplemental_firing_scenario_id,	
         NULL AS allow_startup_shutdown_power,
         NULL AS storage_efficiency,	
         NULL AS charging_efficiency,
         NULL AS discharging_efficiency,	
         NULL AS charging_capacity_multiplier,
         NULL AS discharging_capacity_multiplier,	
         NULL AS soc_penalty_cost_per_energyunit,
         NULL AS soc_last_tmp_penalty_cost_per_energyunit,
         NULL AS flex_load_static_profile_scenario_id,
         NULL AS minimum_duration_hours,	
         NULL AS maximum_duration_hours,
         NULL AS aux_consumption_frac_capacity,	
         NULL AS aux_consumption_frac_power,
         NULL AS last_commitment_stage,	
         1 AS variable_generator_profile_scenario_id,
         NULL AS curtailment_cost_per_pwh,	
         NULL AS hydro_operational_chars_scenario_id,
         NULL AS lf_reserves_up_derate,	
         NULL AS lf_reserves_down_derate,
         NULL AS regulation_up_derate,	
         NULL AS regulation_down_derate,
         NULL AS frequency_response_derate,	
         NULL AS spinning_reserves_derate,
         NULL AS lf_reserves_up_ramp_rate,	
         NULL AS lf_reserves_down_ramp_rate,
         NULL AS regulation_up_ramp_rate,
         NULL AS regulation_down_ramp_rate,
         NULL AS frequency_response_ramp_rate,
         NULL AS spinning_reserves_ramp_rate,
         NULL AS powerunithour_per_fuelunit,
         NULL AS cap_factor_limits_scenario_id,
         NULL AS partial_availability_threshold,
         NULL AS stor_exog_state_of_charge_scenario_id,
         NULL AS nonfuel_carbon_emissions_per_mwh
     FROM raw_data_eia860_generators
     --WHERE report_date = '{report_date}' -- get latest
     WHERE (unixepoch(current_planned_generator_operating_date) < unixepoch('{study_year}-01-01') or current_planned_generator_operating_date IS NULL)
     AND (unixepoch(generator_retirement_date) > unixepoch('{study_year}-12-31') or generator_retirement_date IS NULL)
     AND balancing_authority_code_eia in (
         SELECT baa
         FROM raw_data_aux_baa_key
         WHERE region = '{region}'
     )
     AND (plant_id_eia, generator_id) IN (
             SELECT DISTINCT plant_id_eia, generator_id
             FROM raw_data_eia860_generators
             WHERE prime_mover_code IN ('WT', 'WS', 'PV')
         )
     GROUP BY project
     """

    df = pd.read_sql(sql, conn)

    # Enforce integer for ID columns
    # Can add column names to the list
    # Note that this must be 'Int64'
    df[["variable_generator_profile_scenario_id"]] = df[
        ["variable_generator_profile_scenario_id"]
    ].astype("Int64")

    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_" f"{subscenario_name}.csv"),
        index=False,
    )


def main(args=None):
    print("Creating projects")
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    conn = connect_to_database(db_path=parsed_args.database)

    get_project_portfolio_for_region(
        conn=conn,
        report_date=parsed_args.report_date,
        study_year=parsed_args.study_year,
        region=parsed_args.region,
        csv_location=parsed_args.portfolio_csv_location,
        subscenario_id=parsed_args.project_portfolio_scenario_id,
        subscenario_name=parsed_args.project_portfolio_scenario_name,
    )

    get_project_load_zones(
        conn=conn,
        report_date=parsed_args.report_date,
        study_year=parsed_args.study_year,
        region=parsed_args.region,
        csv_location=parsed_args.load_zone_csv_location,
        subscenario_id=parsed_args.project_load_zone_scenario_id,
        subscenario_name=parsed_args.project_load_zone_scenario_name,
    )

    get_project_availability(
        conn=conn,
        report_date=parsed_args.report_date,
        study_year=parsed_args.study_year,
        region=parsed_args.region,
        csv_location=parsed_args.availability_csv_location,
        subscenario_id=parsed_args.project_availability_scenario_id,
        subscenario_name=parsed_args.project_availability_scenario_name,
    )

    get_project_capacity(
        conn=conn,
        report_date=parsed_args.report_date,
        study_year=parsed_args.study_year,
        region=parsed_args.region,
        csv_location=parsed_args.specified_capacity_csv_location,
        subscenario_id=parsed_args.project_specified_capacity_scenario_id,
        subscenario_name=parsed_args.project_specified_capacity_scenario_name,
    )

    get_project_fixed_cost(
        conn=conn,
        report_date=parsed_args.report_date,
        study_year=parsed_args.study_year,
        region=parsed_args.region,
        csv_location=parsed_args.fixed_cost_csv_location,
        subscenario_id=parsed_args.project_fixed_cost_scenario_id,
        subscenario_name=parsed_args.project_fixed_cost_scenario_name,
    )

    get_project_fuels(
        conn=conn,
        report_date=parsed_args.report_date,
        study_year=parsed_args.study_year,
        region=parsed_args.region,
        csv_location=parsed_args.fuels_csv_location,
        subscenario_id=parsed_args.project_fuel_scenario_id,
        subscenario_name=parsed_args.project_fuel_scenario_name,
    )

    get_project_heat_rates(
        conn=conn,
        report_date=parsed_args.report_date,
        study_year=parsed_args.study_year,
        region=parsed_args.region,
        csv_location=parsed_args.hr_csv_location,
        subscenario_id=parsed_args.project_hr_scenario_id,
        subscenario_name=parsed_args.project_hr_scenario_name,
    )

    get_project_opchar(
        conn=conn,
        report_date=parsed_args.report_date,
        study_year=parsed_args.study_year,
        region=parsed_args.region,
        csv_location=parsed_args.opchar_csv_location,
        subscenario_id=parsed_args.project_operational_chars_scenario_id,
        subscenario_name=parsed_args.project_operational_chars_scenario_name,
    )


if __name__ == "__main__":
    main()
