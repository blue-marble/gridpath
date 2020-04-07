#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
System reseves
"""
from db.common_functions import spin_on_database_lock


def insert_system_reserves(
        io, c,
        subscenario_data,
        input_data,
        reserve_type
):
    """
    :param io: 
    :param c: 
    :param subscenario_data:
    :param input_data:
    :param reserve_type:
    :return: 
    """
    # Subscenario
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_system_{}
        ({}_scenario_id, name, description)
        VALUES (?, ?, ?);
        """.format(reserve_type, reserve_type)
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subscenario_data)

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
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=input_data)


if __name__ == "__main__":
    pass
