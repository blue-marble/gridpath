#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
RPS targets
"""

import os.path
import pandas as pd

from db.common_functions import spin_on_database_lock


def insert_rps_targets(
        conn,
        subscenario_data,
        zone_period_targets,
        rps_zone_load_zone_map
):
    """
    :param conn:
    :param subscenario_data:
    :param zone_period_targets: list of tuples (rps_target_scenario_id,
        rps_zone, period, subproblem_id, stage_id, rps_target_mwh)
    :param rps_zone_load_zone_map: list of tuples (rps_target_scenario_id,
        rps_zone, load_zone)
    """

    c = conn.cursor()

    print(subscenario_data)

    # Subscenario
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_system_rps_targets
        (rps_target_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(
        conn=conn, cursor=c, sql=subs_sql, data=subscenario_data
    )

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_system_rps_targets
        (rps_target_scenario_id, rps_zone, period, subproblem_id, stage_id,
        rps_target_mwh, rps_target_percentage)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=zone_period_targets)


def load_from_csvs(conn, subscenario_directory):
    # TODO: refactor with temporal inputs

    # Required input files
    description_file = os.path.join(subscenario_directory, "description.txt")
    targets_file = os.path.join(subscenario_directory, "targets.csv")
    lz_map_file = os.path.join(subscenario_directory, "load_zone_mapping.csv")

    # Get subscenario ID, name, and description
    # The subscenario directory must start with an integer for the
    # subscenario_id followed by "_" and then the subscenario name
    # The subscenario description must be in the description.txt file under
    # the subscenario directory
    directory_basename = os.path.basename(subscenario_directory)
    subscenario_id = int(directory_basename.split("_", 1)[0])
    subscenario_name = directory_basename.split("_", 1)[1]

    # TODO: make this optional
    with open(description_file, "r") as f:
        subscenario_description = f.read()

    # TODO: this df + subscenario to tuples method can be refactored
    # Load in the targets
    targets_df = pd.read_csv(targets_file, delimiter=",")
    targets_tuples_for_import = [
        (subscenario_id,) + tuple(x)
        for x in targets_df.to_records(index=False)
    ]

    # Load in the mapping
    mapping_df = pd.read_csv(lz_map_file, delimiter=",")
    mapping_tuples_for_import = [
        (subscenario_id,) + tuple(x)
        for x in mapping_df.to_records(index=False)
    ]

    insert_rps_targets(
        conn=conn,
        subscenario_data=[(subscenario_id, subscenario_name,
                          subscenario_description)],
        zone_period_targets=targets_tuples_for_import,
        rps_zone_load_zone_map=mapping_tuples_for_import
    )


if __name__ == "__main__":
    pass
