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


from argparse import ArgumentParser
import os.path
import pandas as pd
import sys

from db.common_functions import connect_to_database
from gridpath_data_toolkit.project.project_data_filters_common import (
    get_eia860_sql_filter_string,
    VAR_GEN_FILTER_STR,
    HYDRO_FILTER_STR,
    DISAGG_PROJECT_NAME_STR,
    AGG_PROJECT_NAME_STR,
)


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
        "-fcost_csv",
        "--fixed_cost_csv_location",
        default="../../csvs_open_data/project/fixed_cost",
    )
    parser.add_argument("-fcost_id", "--project_fixed_cost_scenario_id", default=1)
    parser.add_argument(
        "-fcost_name", "--project_fixed_cost_scenario_name", default="base"
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_project_fixed_cost(
    conn,
    eia860_sql_filter_string,
    var_gen_filter_str,
    hydro_filter_str,
    disagg_project_name_str,
    agg_project_name_str,
    study_year,
    csv_location,
    subscenario_id,
    subscenario_name,
):
    sql = f"""
    SELECT {disagg_project_name_str} AS project,
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
   JOIN user_defined_eia_gridpath_key ON
            raw_data_eia860_generators.prime_mover_code = 
            user_defined_eia_gridpath_key.prime_mover_code
            AND energy_source_code_1 = energy_source_code
     WHERE 1 = 1
     AND {eia860_sql_filter_string}
     AND NOT {var_gen_filter_str}
     AND NOT {hydro_filter_str}
    UNION
    -- Aggregated units include wind, offshore wind, solar, and hydro
    SELECT {agg_project_name_str} AS project,
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
    JOIN user_defined_eia_gridpath_key
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


def main(args=None):
    print("Creating project fixed cost inputs")
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    os.makedirs(parsed_args.fixed_cost_csv_location, exist_ok=True)

    conn = connect_to_database(db_path=parsed_args.database)

    get_project_fixed_cost(
        conn=conn,
        eia860_sql_filter_string=get_eia860_sql_filter_string(
            study_year=parsed_args.study_year, region=parsed_args.region
        ),
        study_year=parsed_args.study_year,
        var_gen_filter_str=VAR_GEN_FILTER_STR,
        hydro_filter_str=HYDRO_FILTER_STR,
        disagg_project_name_str=DISAGG_PROJECT_NAME_STR,
        agg_project_name_str=AGG_PROJECT_NAME_STR,
        csv_location=parsed_args.fixed_cost_csv_location,
        subscenario_id=parsed_args.project_fixed_cost_scenario_id,
        subscenario_name=parsed_args.project_fixed_cost_scenario_name,
    )


if __name__ == "__main__":
    main()
