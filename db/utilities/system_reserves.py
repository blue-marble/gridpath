#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
System reseves
"""
from db.common_functions import spin_on_database_lock
from db.utilities.common_functions import \
    parse_subscenario_directory_contents, csv_to_tuples


def insert_system_reserves(
        conn,
        subscenario_data,
        input_data,
        reserve_type
):
    """
    :param conn:
    :param c: 
    :param subscenario_data:
    :param input_data:
    :param reserve_type:
    :return: 
    """
    c = conn.cursor()

    # Subscenario
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_system_{}
        ({}_scenario_id, name, description)
        VALUES (?, ?, ?);
        """.format(reserve_type, reserve_type)
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql, data=subscenario_data)

    # Insert data
    if reserve_type == "frequency_response":
        inputs_sql = """
            INSERT OR IGNORE INTO inputs_system_{}
            ({}_scenario_id, {}_ba, stage_id, timepoint, {}_mw, {}_partial_mw)
            VALUES (?, ?, ?, ?, ?, ?);
            """.format(reserve_type, reserve_type, reserve_type,
                       reserve_type, reserve_type)
    else:
        inputs_sql = """
            INSERT OR IGNORE INTO inputs_system_{}
            ({}_scenario_id, {}_ba, stage_id, timepoint, {}_mw)
            VALUES (?, ?, ?, ?, ?);
            """.format(reserve_type, reserve_type, reserve_type, reserve_type)
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql, data=input_data)


def load_from_csvs(conn, subscenario_directory, reserve_type):
    """
    :param conn:
    :param subscenario_directory: string, path to the directory containing
        the data for this reserve_scenario_id
    :param reserve_type:
    """
    # Get the subscenario (id, name, description) data for insertion into the
    # subscenario table and the paths to the required input files
    subscenario_data, [timepoint_file, percentage_file, map_file] = \
        parse_subscenario_directory_contents(
            subscenario_directory=subscenario_directory,
            csv_file_names=[
                "timepoint.csv", "percentage.csv",
                "percentage_load_zone_map.csv"
            ]
        )

    # Get the subscenario_id from the subscenario_data tuple
    subscenario_id = subscenario_data[0]

    # Load in the targets and mapping
    timepoint_req_tuples = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=timepoint_file
    )

    percentage_req_tuples = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=percentage_file
    )
    percentage_map_tuples = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=map_file
    )

    return insert_system_reserves(
        conn=conn,
        subscenario_data=[subscenario_data],
        input_data=timepoint_req_tuples,
        reserve_type=reserve_type
    )


if __name__ == "__main__":
    pass
