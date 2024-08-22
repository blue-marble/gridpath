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
from db.utilities.gridpath_data_toolkit.project.project_data_filters_common import (
    get_eia860_sql_filter_string,
    HYDRO_FILTER_STR,
    VAR_GEN_FILTER_STR,
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
        "-lz_csv",
        "--load_zone_csv_location",
        default="../../csvs_open_data/project/load_zones",
    )
    parser.add_argument("-lz_id", "--project_load_zone_scenario_id", default=1)
    parser.add_argument(
        "-lz_name", "--project_load_zone_scenario_name", default="wecc_baas"
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


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
    JOIN aux_eia_gridpath_key ON
            raw_data_eia860_generators.prime_mover_code = 
            aux_eia_gridpath_key.prime_mover_code
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
    JOIN aux_eia_gridpath_key
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
    print("Creating project load zone inputs")
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    os.makedirs(parsed_args.load_zone_csv_location, exist_ok=True)

    conn = connect_to_database(db_path=parsed_args.database)

    get_project_load_zones(
        conn=conn,
        eia860_sql_filter_string=get_eia860_sql_filter_string(
            study_year=parsed_args.study_year, region=parsed_args.region
        ),
        var_gen_filter_str=VAR_GEN_FILTER_STR,
        hydro_filter_str=HYDRO_FILTER_STR,
        csv_location=parsed_args.load_zone_csv_location,
        subscenario_id=parsed_args.project_load_zone_scenario_id,
        subscenario_name=parsed_args.project_load_zone_scenario_name,
    )


if __name__ == "__main__":
    main()
