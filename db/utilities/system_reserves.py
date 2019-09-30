#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
System reseves
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock


def insert_system_reserves(
        io, c,
        reserve_scenario_id,
        scenario_name,
        scenario_description,
        ba_stage_timepoint_reserve_req,
        reserve_type
):
    """
    :param io: 
    :param c: 
    :param reserve_scenario_id: 
    :param scenario_name: 
    :param scenario_description:
    :param stage_id:
    :param ba_stage_timepoint_reserve_req:
    :param reserve_type:
    :return: 
    """

    print("system reserves {}".format(reserve_type))

    # Subscenario
    subs_data = [(reserve_scenario_id,
                  scenario_name,
                  scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_system_{}
        ({}_scenario_id, name, description)
        VALUES (?, ?, ?);
        """.format(reserve_type, reserve_type)
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for ba in list(ba_stage_timepoint_reserve_req.keys()):
        for stage in list(ba_stage_timepoint_reserve_req[ba].keys()):
            for tmp in list(ba_stage_timepoint_reserve_req[ba][stage].keys()):
                inputs_data.append(
                    (reserve_scenario_id, ba, stage, tmp,
                     ba_stage_timepoint_reserve_req[ba][stage][tmp])
                )
    inputs_sql = """
        INSERT INTO inputs_system_{}
        ({}_scenario_id, {}_ba, stage_id, timepoint, {}_mw)
        VALUES (?, ?, ?, ?, ?);
        """.format(reserve_type, reserve_type, reserve_type, reserve_type)
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


if __name__ == "__main__":
    pass
