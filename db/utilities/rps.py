#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
RPS targets
"""

from db.common_functions import spin_on_database_lock
from db.utilities.common_functions import \
    parse_subscenario_directory_contents, csv_to_tuples


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
    targets_sql = """
        INSERT OR IGNORE INTO inputs_system_rps_targets
        (rps_target_scenario_id, rps_zone, period, subproblem_id, stage_id,
        rps_target_mwh, rps_target_percentage)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=targets_sql,
                          data=zone_period_targets)

    mapping_sql = """
        INSERT OR IGNORE INTO inputs_system_rps_target_load_zone_map
        (rps_target_scenario_id, rps_zone, load_zone)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=mapping_sql,
                          data=rps_zone_load_zone_map)

    c.close()


def load_from_csvs(conn, subscenario_directory):

    # Get the subscenario (id, name, description) data for insertion into the
    # subscenario table and the paths to the required input files
    subscenario_data, [targets_file, lz_map_file] = \
        parse_subscenario_directory_contents(
            subscenario_directory=subscenario_directory,
            csv_file_names=["targets.csv", "load_zone_mapping.csv"]
        )

    # Get the subscenario_id from the subscenario_data tuple
    subscenario_id = subscenario_data[0]

    # Load in the targets and mapping
    targets_tuples_for_import = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=targets_file
    )
    mapping_tuples_for_import = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=lz_map_file
    )

    insert_rps_targets(
        conn=conn,
        subscenario_data=[subscenario_data],
        zone_period_targets=targets_tuples_for_import,
        rps_zone_load_zone_map=mapping_tuples_for_import
    )


if __name__ == "__main__":
    pass
