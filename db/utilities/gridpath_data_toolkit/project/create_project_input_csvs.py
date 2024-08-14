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
    parser.add_argument("-hr_name", "--project_hr_scenario_name", default="generic")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


# TODO: refactor queries to their components


def get_project_portfolio_for_region(
    conn,
    eia860_sql_filter_string,
    var_gen_filter_str,
    hydro_filter_str,
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
    NULL as new_build,
    gridpath_capacity_type AS capacity_type
    FROM raw_data_eia860_generators
    JOIN raw_data_aux_eia_gridpath_key ON
            raw_data_eia860_generators.prime_mover_code = 
            raw_data_aux_eia_gridpath_key.prime_mover_code
            AND energy_source_code_1 = energy_source_code
     WHERE 1 = 1
     AND {eia860_sql_filter_string}
     AND NOT {var_gen_filter_str}
     AND NOT {hydro_filter_str}
    UNION
    -- Aggregated units include wind, offshore wind, solar, and hydro
    SELECT DISTINCT 
        agg_project || '_' || balancing_authority_code_eia AS project,
        NULL as specified,
        NULL as new_build,
        gridpath_capacity_type AS capacity_type
    FROM raw_data_eia860_generators
    JOIN raw_data_aux_eia_gridpath_key
    USING (prime_mover_code)
    WHERE 1 = 1
    AND {eia860_sql_filter_string}
    AND ({var_gen_filter_str} OR {hydro_filter_str})
    ;
    """

    df = pd.read_sql(sql, conn)
    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_{subscenario_name}.csv"),
        index=False,
    )


def get_project_load_zones(
    conn,
    eia860_sql_filter_string,
    var_gen_filter_str,
    hydro_filter_str,
    csv_location,
    subscenario_id,
    subscenario_name,
):
    sql = f"""
    SELECT plant_id_eia || '__' || REPLACE(REPLACE(generator_id, ' ', '_'), '-', 
        '_') AS project, balancing_authority_code_eia AS load_zone
    FROM raw_data_eia860_generators
    JOIN raw_data_aux_eia_gridpath_key ON
            raw_data_eia860_generators.prime_mover_code = 
            raw_data_aux_eia_gridpath_key.prime_mover_code
            AND energy_source_code_1 = energy_source_code
    WHERE 1 = 1
    AND {eia860_sql_filter_string}
    AND NOT {var_gen_filter_str}
    AND NOT {hydro_filter_str}
    -- Aggregated units include wind, offshore wind, solar, and hydro
    UNION
    SELECT DISTINCT 
        agg_project || '_' || balancing_authority_code_eia AS project,
        balancing_authority_code_eia AS load_zone
    FROM raw_data_eia860_generators
    JOIN raw_data_aux_eia_gridpath_key
    USING (prime_mover_code)
    WHERE 1 = 1
    AND {eia860_sql_filter_string}
    AND ({var_gen_filter_str} OR {hydro_filter_str})
    ;
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
    eia860_sql_filter_string,
    var_gen_filter_str,
    hydro_filter_str,
    study_year,
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
            WHEN raw_data_eia860_generators.prime_mover_code NOT IN ('BA', 
            'ES', 'FW', 'PS') THEN NULL
            ELSE 
                CASE
                    WHEN energy_storage_capacity_mwh IS NULL
                    THEN 
                        CASE
                            WHEN raw_data_eia860_generators.prime_mover_code 
                            = 'PS' THEN 12.0*capacity_mw
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
    JOIN raw_data_aux_eia_gridpath_key ON
            raw_data_eia860_generators.prime_mover_code = 
            raw_data_aux_eia_gridpath_key.prime_mover_code
            AND energy_source_code_1 = energy_source_code
     WHERE 1 = 1
     AND {eia860_sql_filter_string}
     AND NOT {var_gen_filter_str}
     AND NOT {hydro_filter_str}
    UNION
    -- Aggregated units include wind, offshore wind, solar, and hydro
    SELECT DISTINCT 
        agg_project || '_' || balancing_authority_code_eia AS project,
        {study_year} as period,
        SUM(capacity_mw) AS specified_capacity_mw,
        NULL AS hyb_gen_specified_capacity_mw,
        NULL AS hyb_stor_specified_capacity_mw,
        SUM(energy_storage_capacity_mwh) AS specified_capacity_mwh,
        NULL AS fuel_production_capacity_fuelunitperhour,
        NULL AS fuel_release_capacity_fuelunitperhour,
        NULL AS fuel_storage_capacity_fuelunit
    FROM raw_data_eia860_generators
    JOIN raw_data_aux_eia_gridpath_key
    USING (prime_mover_code)
    WHERE 1 = 1
    AND {eia860_sql_filter_string}
    AND ({var_gen_filter_str} OR {hydro_filter_str})
    GROUP BY project
    ;
    """

    df = pd.read_sql(sql, conn)
    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_" f"{subscenario_name}.csv"),
        index=False,
    )


def get_project_fixed_cost(
    conn,
    eia860_sql_filter_string,
    var_gen_filter_str,
    hydro_filter_str,
    study_year,
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
        CASE WHEN raw_data_eia860_generators.prime_mover_code NOT IN ('BA', 
        'ES', 'FW', 'PS') 
            THEN NULL
            ELSE 0
        END
            AS fixed_cost_per_mwh_year,
        NULL AS fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr,
        NULL AS fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr,
        NULL AS fuel_storage_capacity_fixed_cost_per_fuelunit_yr
    FROM raw_data_eia860_generators
   JOIN raw_data_aux_eia_gridpath_key ON
            raw_data_eia860_generators.prime_mover_code = 
            raw_data_aux_eia_gridpath_key.prime_mover_code
            AND energy_source_code_1 = energy_source_code
     WHERE 1 = 1
     AND {eia860_sql_filter_string}
     AND NOT {var_gen_filter_str}
     AND NOT {hydro_filter_str}
    UNION
    -- Aggregated units include wind, offshore wind, solar, and hydro
    SELECT DISTINCT 
        agg_project || '_' || balancing_authority_code_eia AS project,
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
    JOIN raw_data_aux_eia_gridpath_key
    USING (prime_mover_code)
    WHERE 1 = 1
    AND {eia860_sql_filter_string}
    AND ({var_gen_filter_str} OR {hydro_filter_str})
    ;
    """

    df = pd.read_sql(sql, conn)
    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_" f"{subscenario_name}.csv"),
        index=False,
    )


# Fuels and heat rates for gen_commit_bin/lin
def get_project_fuels(
    conn,
    eia860_sql_filter_string,
    fuel_filter_str,
    csv_location,
    subscenario_id,
    subscenario_name,
):

    # Only coal, gas, and fuel oil for now (with aeo prices)
    # TODO: temporarily assign all to CISO to CA_North in raw_data_aux_baa_key
    sql = f"""
        SELECT plant_id_eia || '__' || REPLACE(REPLACE(generator_id, ' ', '_'), '-', 
            '_') AS project, 
            gridpath_generic_fuel || '_' || fuel_region as fuel
        FROM raw_data_eia860_generators
        JOIN raw_data_aux_eia_gridpath_key ON
            raw_data_eia860_generators.prime_mover_code = 
            raw_data_aux_eia_gridpath_key.prime_mover_code
            AND energy_source_code_1 = energy_source_code
        JOIN raw_data_aux_baa_key ON (balancing_authority_code_eia = baa)
        WHERE 1 = 1
        AND {eia860_sql_filter_string}
        AND {fuel_filter_str}
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
    eia860_sql_filter_string,
    heat_rate_filter_str,
    csv_location,
    subscenario_id,
    subscenario_name,
):

    # Only coal, gas, and fuel oil for now (with aeo prices)
    sql = f"""
        SELECT plant_id_eia || '__' || REPLACE(REPLACE(generator_id, ' ', '_'), '-', 
            '_') AS project, 
            raw_data_eia860_generators.prime_mover_code, gridpath_generic_fuel, 
            heat_rate_mmbtu_per_mwh, min_load_fraction
        FROM raw_data_eia860_generators
        JOIN raw_data_aux_eia_gridpath_key ON
            raw_data_eia860_generators.prime_mover_code = 
            raw_data_aux_eia_gridpath_key.prime_mover_code
            AND energy_source_code_1 = energy_source_code
        WHERE 1 = 1
        AND {eia860_sql_filter_string}
        AND {heat_rate_filter_str}
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


def main(args=None):
    print("Creating projects")
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    conn = connect_to_database(db_path=parsed_args.database)

    eia860_sql_filter_string = f"""
    (unixepoch(current_planned_generator_operating_date) < unixepoch(
     '{parsed_args.study_year}-01-01') or current_planned_generator_operating_date IS NULL)
     AND (unixepoch(generator_retirement_date) > unixepoch('{parsed_args.study_year}-12-31') or generator_retirement_date IS NULL)
     AND balancing_authority_code_eia in (
         SELECT baa
         FROM raw_data_aux_baa_key
         WHERE region = '{parsed_args.region}'
     )
    """
    fuel_filter_str = (
        """gridpath_operational_type IN ('gen_commit_bin', 'gen_commit_lin')"""
    )
    heat_rate_filter_str = (
        """gridpath_operational_type IN ('gen_commit_bin', 'gen_commit_lin')"""
    )
    stor_filter_str = """gridpath_operational_type = 'stor'"""
    var_gen_filter_str = (
        """gridpath_operational_type IN ('gen_var', 'gen_var_must_take')"""
    )
    hydro_filter_str = (
        """gridpath_operational_type IN ('gen_hydro', 'gen_hydro_must_take')"""
    )

    get_project_portfolio_for_region(
        conn=conn,
        eia860_sql_filter_string=eia860_sql_filter_string,
        var_gen_filter_str=var_gen_filter_str,
        hydro_filter_str=hydro_filter_str,
        csv_location=parsed_args.portfolio_csv_location,
        subscenario_id=parsed_args.project_portfolio_scenario_id,
        subscenario_name=parsed_args.project_portfolio_scenario_name,
    )

    get_project_load_zones(
        conn=conn,
        eia860_sql_filter_string=eia860_sql_filter_string,
        var_gen_filter_str=var_gen_filter_str,
        hydro_filter_str=hydro_filter_str,
        csv_location=parsed_args.load_zone_csv_location,
        subscenario_id=parsed_args.project_load_zone_scenario_id,
        subscenario_name=parsed_args.project_load_zone_scenario_name,
    )

    get_project_capacity(
        conn=conn,
        eia860_sql_filter_string=eia860_sql_filter_string,
        study_year=parsed_args.study_year,
        var_gen_filter_str=var_gen_filter_str,
        hydro_filter_str=hydro_filter_str,
        csv_location=parsed_args.specified_capacity_csv_location,
        subscenario_id=parsed_args.project_specified_capacity_scenario_id,
        subscenario_name=parsed_args.project_specified_capacity_scenario_name,
    )

    get_project_fixed_cost(
        conn=conn,
        eia860_sql_filter_string=eia860_sql_filter_string,
        var_gen_filter_str=var_gen_filter_str,
        hydro_filter_str=hydro_filter_str,
        study_year=parsed_args.study_year,
        csv_location=parsed_args.fixed_cost_csv_location,
        subscenario_id=parsed_args.project_fixed_cost_scenario_id,
        subscenario_name=parsed_args.project_fixed_cost_scenario_name,
    )

    get_project_fuels(
        conn=conn,
        eia860_sql_filter_string=eia860_sql_filter_string,
        fuel_filter_str=fuel_filter_str,
        csv_location=parsed_args.fuels_csv_location,
        subscenario_id=parsed_args.project_fuel_scenario_id,
        subscenario_name=parsed_args.project_fuel_scenario_name,
    )

    get_project_heat_rates(
        conn=conn,
        eia860_sql_filter_string=eia860_sql_filter_string,
        heat_rate_filter_str=heat_rate_filter_str,
        csv_location=parsed_args.hr_csv_location,
        subscenario_id=parsed_args.project_hr_scenario_id,
        subscenario_name=parsed_args.project_hr_scenario_name,
    )


if __name__ == "__main__":
    main()
