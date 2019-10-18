#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Clear scenario results/statuses or delete scenario completely based on input
from the UI client.
"""

from db.utilities.scenario import delete_scenario_results, delete_scenario
from db.common_functions import connect_to_database


def clear(db_path, scenario_id):
    """

    :param db_path:
    :param scenario_id:
    :return:
    """
    conn = connect_to_database(db_path=db_path)
    delete_scenario_results(conn=conn, scenario_id=scenario_id)


def delete(db_path, scenario_id):
    """

    :param db_path:
    :param scenario_id:
    :return:
    """
    conn = connect_to_database(db_path=db_path)
    delete_scenario(conn=conn, scenario_id=scenario_id)
