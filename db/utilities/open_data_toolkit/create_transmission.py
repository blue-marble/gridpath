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
import numpy as np
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
        default="../../csvs_open_data/transmission/portfolios",
    )
    parser.add_argument("-p_id", "--transmission_portfolio_scenario_id", default=1)
    parser.add_argument(
        "-p_name", "--transmission_portfolio_scenario_name", default="eia930"
    )
    parser.add_argument(
        "-lz_csv",
        "--load_zone_csv_location",
        default="../../csvs_open_data/transmission/load_zones",
    )
    parser.add_argument("-lz_id", "--transmission_load_zone_scenario_id", default=1)
    parser.add_argument(
        "-lz_name", "--transmission_load_zone_scenario_name", default="wecc_baas"
    )
    parser.add_argument(
        "-avl_csv",
        "--availability_csv_location",
        default="../../csvs_open_data/transmission/availability",
    )
    parser.add_argument("-avl_id", "--transmission_availability_scenario_id", default=1)
    parser.add_argument(
        "-avl_name", "--transmission_availability_scenario_name", default="no_derates"
    )
    parser.add_argument(
        "-cap_csv",
        "--specified_capacity_csv_location",
        default="../../csvs_open_data/transmission/capacity_specified",
    )
    parser.add_argument(
        "-cap_id", "--transmission_specified_capacity_scenario_id", default=1
    )
    parser.add_argument(
        "-cap_name", "--transmission_specified_capacity_scenario_name", default="base"
    )
    parser.add_argument(
        "-fcost_csv",
        "--fixed_cost_csv_location",
        default="../../csvs_open_data/transmission/fixed_cost",
    )
    parser.add_argument("-fcost_id", "--transmission_fixed_cost_scenario_id", default=1)
    parser.add_argument(
        "-fcost_name", "--transmission_fixed_cost_scenario_name", default="base"
    )
    parser.add_argument(
        "-fuels_csv",
        "--fuels_csv_location",
        default="../../csvs_open_data/transmission/opchar/fuels",
    )
    parser.add_argument("-fuel_id", "--transmission_fuel_scenario_id", default=1)
    parser.add_argument(
        "-fuel_name", "--transmission_fuel_scenario_name", default="base"
    )

    parser.add_argument(
        "-hr_csv",
        "--hr_csv_location",
        default="../../csvs_open_data/transmission/opchar/heat_rates",
    )
    parser.add_argument("-hr_id", "--transmission_hr_scenario_id", default=1)
    parser.add_argument(
        "-hr_name", "--transmission_hr_scenario_name", default="generic"
    )

    parser.add_argument(
        "-opchar_csv",
        "--opchar_csv_location",
        default="../../csvs_open_data/transmission/opchar",
    )
    parser.add_argument(
        "-opchar_id", "--transmission_operational_chars_scenario_id", default=1
    )
    parser.add_argument(
        "-opchar_name",
        "--transmission_operational_chars_scenario_name",
        default="wecc_tx_opchar",
    )

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_tx_portfolio_for_region(
    all_links,
    csv_location,
    subscenario_id,
    subscenario_name,
):
    """ """
    tx_lines = [f"{link[0]}_{link[1]}" for link in all_links]
    df = pd.DataFrame(tx_lines, columns=["transmission_line"])
    df["capacity_type"] = "tx_spec"

    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_{subscenario_name}.csv"),
        index=False,
    )


def get_tx_load_zones(
    all_links,
    csv_location,
    subscenario_id,
    subscenario_name,
):
    """ """
    lz_dict = {
        "transmission_line": [f"{link[0]}_{link[1]}" for link in all_links],
        "load_zone_from": [link[0] for link in all_links],
        "load_zone_to": [link[1] for link in all_links],
    }

    df = pd.DataFrame(lz_dict)

    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_{subscenario_name}.csv"),
        index=False,
    )


def get_tx_capacities(
    conn,
    all_links,
    period,
    cap,
    threshold,
    csv_location,
    subscenario_id,
    subscenario_name,
):
    df_list = []
    from_to_combos = []
    for lz_from, lz_to in all_links:
        if (lz_from, lz_to) not in from_to_combos:
            # Exclude values abs(x) >= cap
            # TODO: this is based on a manual scan of the data; we need a more robust
            #  way of cleaning it and detecting outliers
            min_max_sql = f"""
                SELECT
                    CASE WHEN max(i1) IS NULL THEN 0 ELSE max(i1) END,
                    CASE WHEN min(i1) IS NULL THEN 0 ELSE min(i1) END,
                    CASE WHEN max(i2) IS NULL THEN 0 ELSE max(i2) END,
                    CASE WHEN min(i2) IS NULL THEN 0 ELSE min(i2) END
                FROM (
                SELECT datetime_pst, from1, to1, i1, from2, to2, i2, i1/i2, i2/i1 FROM (
                SELECT datetime_pst, balancing_authority_code_eia as from1, balancing_authority_code_adjacent_eia as to1, interchange_reported_mwh as i1
                FROM raw_data_aux_eia930_hourly_interchange
                WHERE balancing_authority_code_eia = '{lz_from}' AND 
                balancing_authority_code_adjacent_eia = '{lz_to}'
                AND abs(interchange_reported_mwh) <= {cap}
                ) as tbl1
                JOIN (
                SELECT datetime_pst, balancing_authority_code_eia as from2, balancing_authority_code_adjacent_eia as to2, interchange_reported_mwh as i2
                FROM raw_data_aux_eia930_hourly_interchange
                WHERE balancing_authority_code_eia = '{lz_to}' 
                AND balancing_authority_code_adjacent_eia = '{lz_from}'
                AND abs(interchange_reported_mwh) <= {cap}
                ) as tbl2
                USING (datetime_pst)
                )
            """

            c = conn.cursor()
            max_i1, min_i1, max_i2, min_i2 = c.execute(min_max_sql).fetchone()

            # If the same is reported on both sides (within some threshold
            # percentage), use values directly and take the average
            if (1 - threshold) * -min_i2 <= max_i1 <= (1 + threshold) * -min_i2 or (
                1 - threshold
            ) * max_i1 <= -min_i2 <= (1 + threshold) * max_i1:
                max_to_use = np.mean([max_i1, -min_i2])
            else:
                max_to_use = min([max_i1, -min_i2])

            if (1 - threshold) * max_i2 <= -min_i1 <= (1 + threshold) * max_i2 or (
                1 - threshold
            ) * -min_i1 <= max_i2 <= (1 + threshold) * -min_i1:
                min_to_use = np.mean([-min_i1, max_i2])
            else:
                min_to_use = min([-min_i1, max_i2])

            tx_capacity = max([max_to_use, min_to_use])

            df = pd.DataFrame(
                {
                    "transmission_line": [f"{lz_from}_{lz_to}"],
                    "period": [period],
                    "min_mw": [-tx_capacity],
                    "max_mw": [tx_capacity],
                    "fixed_cost_per_mw_yr": [0],
                }
            )

            df_list.append(df)

            from_to_combos.append((lz_from, lz_to))
            from_to_combos.append((lz_to, lz_from))

    # Concat the individual line dataframes for export
    df = pd.concat(df_list)
    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_{subscenario_name}.csv"),
        index=False,
    )


def get_tx_availability(
    all_links,
    csv_location,
    subscenario_id,
    subscenario_name,
):
    """ """
    tx_lines = [f"{link[0]}_{link[1]}" for link in all_links]
    df = pd.DataFrame(tx_lines, columns=["transmission_line"])
    df["availability_type"] = "exogenous"
    df["exogenous_availability_scenario_id"] = None
    df["endogenous_availability_scenario_id"] = None

    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_{subscenario_name}.csv"),
        index=False,
    )


def get_tx_opchar(all_links, csv_location, subscenario_id, subscenario_name):
    tx_lines = [f"{link[0]}_{link[1]}" for link in all_links]
    df = pd.DataFrame(tx_lines, columns=["transmission_line"])
    df["operational_type"] = "tx_simple"
    df["tx_simple_loss_factor"] = 0.02
    df["reactance_ohms"] = None

    df.to_csv(
        os.path.join(csv_location, f"{subscenario_id}_{subscenario_name}.csv"),
        index=False,
    )


def main(args=None):
    print("Creating transmission")
    if args is None:
        args = sys.argv[1:]

    parsed_args = parse_arguments(args=args)

    conn = connect_to_database(db_path=parsed_args.database)

    c = conn.cursor()

    all_links = c.execute(
        f"""
            SELECT DISTINCT balancing_authority_code_eia, balancing_authority_code_adjacent_eia
            FROM raw_data_aux_eia930_hourly_interchange
            WHERE balancing_authority_code_eia in (
            SELECT baa FROM (
                SELECT DISTINCT baa from (
                    SELECT DISTINCT balancing_authority_code_eia as baa
                    FROM raw_data_aux_eia930_hourly_interchange
                    UNION
                    SELECT DISTINCT balancing_authority_code_adjacent_eia as ba
                    FROM raw_data_aux_eia930_hourly_interchange
                    )
                )
                LEFT OUTER JOIN
                raw_data_aux_baa_key
                USING (baa)
            WHERE region = 'WECC'
            )
            AND
            balancing_authority_code_adjacent_eia in (
            SELECT baa FROM (
                SELECT DISTINCT baa from (
                    SELECT DISTINCT balancing_authority_code_eia as baa
                    FROM raw_data_aux_eia930_hourly_interchange
                    UNION
                    SELECT DISTINCT balancing_authority_code_adjacent_eia as ba
                    FROM raw_data_aux_eia930_hourly_interchange
                    )
                )
                LEFT OUTER JOIN
                raw_data_aux_baa_key
                USING (baa)
            WHERE region = 'WECC'
            )
            ;
            """
    ).fetchall()

    get_tx_portfolio_for_region(
        all_links=all_links,
        csv_location=parsed_args.portfolio_csv_location,
        subscenario_id=parsed_args.transmission_portfolio_scenario_id,
        subscenario_name=parsed_args.transmission_portfolio_scenario_name,
    )

    get_tx_load_zones(
        all_links=all_links,
        csv_location=parsed_args.load_zone_csv_location,
        subscenario_id=parsed_args.transmission_load_zone_scenario_id,
        subscenario_name=parsed_args.transmission_load_zone_scenario_name,
    )

    get_tx_capacities(
        conn=conn,
        all_links=all_links,
        period=2026,
        cap=19000,
        threshold=0.5,
        csv_location=parsed_args.specified_capacity_csv_location,
        subscenario_id=parsed_args.transmission_specified_capacity_scenario_id,
        subscenario_name=parsed_args.transmission_specified_capacity_scenario_name,
    )

    get_tx_availability(
        all_links=all_links,
        csv_location=parsed_args.availability_csv_location,
        subscenario_id=parsed_args.transmission_availability_scenario_id,
        subscenario_name=parsed_args.transmission_availability_scenario_name,
    )

    get_tx_opchar(
        all_links=all_links,
        csv_location=parsed_args.opchar_csv_location,
        subscenario_id=parsed_args.transmission_operational_chars_scenario_id,
        subscenario_name=parsed_args.transmission_operational_chars_scenario_name,
    )


if __name__ == "__main__":
    main()
