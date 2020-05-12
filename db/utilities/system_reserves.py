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
        tmp_req,
        percent_req,
        percent_map,
        reserve_type
):
    """
    :param conn:
    :param subscenario_data:
    :param tmp_req:
    :param percent_req:
    :param percent_map:
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

    # Insert the by-timepoint requirement
    if reserve_type == "frequency_response":
        tmp_req_sql = """
            INSERT OR IGNORE INTO inputs_system_{}
            ({}_scenario_id, {}_ba, stage_id, timepoint, {}_mw, {}_partial_mw)
            VALUES (?, ?, ?, ?, ?, ?);
            """.format(reserve_type, reserve_type, reserve_type,
                       reserve_type, reserve_type)
    else:
        tmp_req_sql = """
            INSERT OR IGNORE INTO inputs_system_{}
            ({}_scenario_id, {}_ba, stage_id, timepoint, {}_mw)
            VALUES (?, ?, ?, ?, ?);
            """.format(reserve_type, reserve_type, reserve_type, reserve_type)
    spin_on_database_lock(conn=conn, cursor=c, sql=tmp_req_sql, data=tmp_req)

    # Insert the percent-of-load requirement & map
    pcnt_req_sql = """
        INSERT OR IGNORE INTO inputs_system_{}_percent
        ({}_scenario_id, {}_ba, percent_load_req)
        VALUES (?, ?, ?);
        """.format(reserve_type, reserve_type, reserve_type)
    spin_on_database_lock(
        conn=conn, cursor=c, sql=pcnt_req_sql, data=percent_req
    )

    pcnt_req_map_sql = """
        INSERT OR IGNORE INTO inputs_system_{}_percent_lz_map
        ({}_scenario_id, {}_ba, load_zone)
        VALUES (?, ?, ?);
        """.format(reserve_type, reserve_type, reserve_type)
    spin_on_database_lock(
        conn=conn, cursor=c, sql=pcnt_req_map_sql, data=percent_map
    )

    c.close()


def load_from_csvs(conn, subscenario_directory, reserve_type):
    """
    :param conn:
    :param subscenario_directory: string, path to the directory containing
        the data for this reserve_scenario_id
    :param reserve_type:

    Load temporal reserve data into the database. The data structure for
    loading reserve data from CSVs is as follows:

    Each reserve req subscenario is a directory, with the scenario ID,
    underscore, and the scenario name as the name of the directory (already
    passed here), so we get this to import from the subscenario_directory path.

    Within each subscenario directory there are three required files:
    timepoint.csv, percentage.csv, and percentage_load_zone_map.csv. A file
    containing the subscenario description (description.txt) is optional.

    1. *timepoint.csv*: contains timepoint-level reserve requirement
    specifications for each BA that has them.

    2. *percentage.csv*: contains the percent of load requirement
    specification for each BA that has it.

    3. *percentage_load_zone_map.csv*: contains the BA-to-load_zones mapping
    for the percentage requirement.

    Any of those files can be blank (header only).
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

    percent_req_tuples = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=percentage_file
    )
    percent_map_tuples = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=map_file
    )

    insert_system_reserves(
        conn=conn,
        subscenario_data=[subscenario_data],
        tmp_req=timepoint_req_tuples,
        percent_req=percent_req_tuples,
        percent_map=percent_map_tuples,
        reserve_type=reserve_type
    )


if __name__ == "__main__":
    pass
