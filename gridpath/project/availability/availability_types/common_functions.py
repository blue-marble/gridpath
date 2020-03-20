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

    # Update the results table with the module-specific results
    insert_sql = """
        INSERT INTO results_project_availability_endogenous
        (scenario_id, project, period, subproblem_id, stage_id, 
        availability_type, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint,
        load_zone, technology, unavailability_decision, start_unavailablity, 
        stop_unavailability, availability_derate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)

    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=results)
