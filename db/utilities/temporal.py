#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make temporal subscenarios.
"""
import os
from copy import deepcopy
import pandas as pd
import warnings

from db.common_functions import spin_on_database_lock
from db.utilities.common_functions import get_subscenario_info


def insert_into_database(
    conn,
    temporal_scenario_id
):
    """

    :param conn:
    :param temporal_scenario_id:
    """
    c = conn.cursor()

    # Subproblems
    subproblems_sql = """
        INSERT OR IGNORE INTO inputs_temporal_subproblems
        (temporal_scenario_id, subproblem_id)
        SELECT DISTINCT temporal_scenario_id, subproblem_id
        FROM inputs_temporal
        WHERE temporal_scenario_id = ?;
        """
    spin_on_database_lock(
        conn=conn, cursor=c, sql=subproblems_sql,
        data=(temporal_scenario_id,), many=False
    )

    # Stages
    # TODO: stage_name not currently included; decide whether to keep this
    #  column in the database and how to import data for it if we do want it
    stages_sql = """
        INSERT OR IGNORE INTO inputs_temporal_subproblems_stages
        (temporal_scenario_id, subproblem_id, stage_id)
        SELECT DISTINCT temporal_scenario_id, subproblem_id, stage_id
        FROM inputs_temporal
        WHERE temporal_scenario_id = ?;
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=stages_sql,
                          data=(temporal_scenario_id, ), many=False)

    # TIMEPOINT HORIZONS
    sid_stg_bt_hr_sql = """
        SELECT subproblem_id, stage_id, balancing_type_horizon, horizon
        FROM inputs_temporal_horizons
        JOIN inputs_temporal_subproblems_stages
        USING (temporal_scenario_id, subproblem_id)
        WHERE temporal_scenario_id = ?
        """
    sid_stg_bt_hr = c.execute(sid_stg_bt_hr_sql, (temporal_scenario_id,
                                                  )).fetchall()

    for (sid, stage, bt, hr) in sid_stg_bt_hr:
        tmp_start, tmp_end = c.execute(
            """SELECT tmp_start, tmp_end
            FROM inputs_temporal_horizons
            WHERE temporal_scenario_id = ?
            AND subproblem_id = ?
            AND balancing_type_horizon = ?
            AND horizon = ?""",
            (temporal_scenario_id, sid, bt, hr)
        ).fetchone()

        tmps = [
            tmp for tmp in c.execute("""
                SELECT timepoint
                FROM inputs_temporal
                WHERE temporal_scenario_id = ?
                AND subproblem_id = ?
                AND stage_id = ?
                AND timepoint >= ?
                AND timepoint <= ?
                """, (temporal_scenario_id, sid, stage, tmp_start, tmp_end)
            ).fetchall()
                ]

        for tmp_tuple in tmps:
            tmp = tmp_tuple[0]
            horizon_timepoints_sql = """
                INSERT OR IGNORE INTO inputs_temporal_horizon_timepoints
                (temporal_scenario_id, subproblem_id, stage_id, timepoint, 
                balancing_type_horizon, horizon)
                VALUES (?, ?, ?, ?, ?, ?);
                """
            spin_on_database_lock(conn=conn, cursor=c, sql=horizon_timepoints_sql,
                                  data=(temporal_scenario_id, sid, stage,
                                        tmp, bt, hr),
                                  many=False)


def load_from_csvs(conn, subscenario_directory):
    """
    :param conn:
    :param subscenario_directory: string, path to the directory containing
        the data for this temporal_scenario_id

    Load temporal subscenario data into the database. The data structure for
    loading  temporal data from CSVs is as follows:

    Each temporal subscenario is a directory, with the scenario ID,
    underscore, and the scenario name as the name of the directory (already
    passed here), so we get this to import from the subscenario_directory path.

    Within each subscenario directory there are three required files:
    structure.csv, period_params.csv, and horizon_params.csv. A file
    containing the subscenario description (description.txt) is optional.

    1. *structure.csv*: contains all timepoint-level information for the
    temporal subscenario, including
    subproblem_id, stage_id, timepoint, period, number_of_hours_in_timepoint,
    timepoint_weight, previous_stage_timepoint_map, spinup_or_lookahead,
    month, hour_of_day. Columns must be specified in this order. The horizon
    information for each timepoint must be included as the ending columns of
    this file and must conform to the following structure: the header must
    start with `horizon_` and then include the balancing type, e.g. day
    balancing types will be `horizon_day`. The temporal script will populate
    the subscenarios, stages, timepoints, and horizon_timepoints tables based
    on the information in structure.csv.

    2. *horizon_params.csv*: contains the balancing_type-horizon-level
    information for the temporal subscenario, including subproblem_id,
    balancing_type_horizon, horizon, boundary (must be in this order).
    
    3. *period_params.csv*: contains the period-level information for the
    temporal subscenario, including period, discount_factor,
    number_years_represented (must be in this order).
    """

    # Get the subscenario (id, name, description) data for insertion into the
    # subscenario table and the paths to the required input files
    subscenario_data = get_subscenario_info(
        dir_subsc=True, inputs_dir=subscenario_directory,
        csv_file="structure.csv", project_flag=False,
    )[0]

    # Get the subscenario_id from the subscenario_data tuple
    subscenario_id = subscenario_data[0]

    # INSERT OR IGNORE INTO THE DATABASE
    insert_into_database(
        conn=conn,
        temporal_scenario_id=subscenario_id
    )
