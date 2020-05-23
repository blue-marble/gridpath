#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
Custom functions for loading data from CSVs.
"""

from db.common_functions import spin_on_database_lock


def finalize_temporal(
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
