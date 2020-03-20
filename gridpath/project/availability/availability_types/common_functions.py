#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path

from db.common_functions import spin_on_database_lock


def insert_availability_results(
     db, c, results_directory, scenario_id, results_file
):
    results = []
    with open(os.path.join(results_directory, results_file), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)
        header = next(reader)

        for row in reader:
            results.append((scenario_id,) + tuple(row))

    # Get the CREATE statemnt for the persistent table
    tbl_sql = c.execute("""
        SELECT sql 
        FROM sqlite_master
        WHERE type='table'
        AND name='results_project_availability_endogenous'
        """).fetchone()[0]

    # Create a temporary table with the same structure as the persistent table
    temp_tbl_sql = \
        tbl_sql.replace(
            "CREATE TABLE results_project_availability_endogenous",
            """CREATE TEMPORARY TABLE 
            temp_results_project_availability_endogenous{}""".format(
                scenario_id
            )
        )

    spin_on_database_lock(conn=db, cursor=c, sql=temp_tbl_sql,
                          data=(), many=False)

    # Insert the results into the temporary table
    insert_temp_sql = """
        INSERT INTO temp_results_project_availability_endogenous{}
        (scenario_id, project, period, subproblem_id, stage_id, 
        availability_type, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint,
        load_zone, technology, unavailability_decision, start_unavailablity, 
        stop_unavailability, availability_derate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """.format(scenario_id)

    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert the ordered results into the permanent table
    insert_sql = """
        INSERT INTO results_project_availability_endogenous
        (scenario_id, project, period, subproblem_id, stage_id, 
        availability_type, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint,
        load_zone, technology, unavailability_decision, start_unavailablity, 
        stop_unavailability, availability_derate)
        SELECT scenario_id, project, period, subproblem_id, stage_id, 
        availability_type, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint,
        load_zone, technology, unavailability_decision, start_unavailablity, 
        stop_unavailability, availability_derate
        FROM temp_results_project_availability_endogenous{}
        ORDER BY scenario_id, subproblem_id, stage_id, project, timepoint
    """.format(scenario_id)

    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql,
                          data=(), many=False)

    # Drop the temporary table
    drop_temp_sql = """
        DROP TABLE temp_results_project_availability_endogenous{}
    """.format(scenario_id)

    spin_on_database_lock(conn=db, cursor=c, sql=drop_temp_sql,
                          data=(), many=False)
