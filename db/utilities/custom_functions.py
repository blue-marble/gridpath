# Copyright 2016-2020 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Custom functions to be run after loading data from CSVs.
"""

from db.common_functions import spin_on_database_lock


def temporal(conn, subscenario_id):
    """

    :param conn:
    :param subscenario_id:
    """
    c = conn.cursor()

    # Subproblems
    subproblems_sql = """
        INSERT INTO inputs_temporal_subproblems
        (temporal_scenario_id, subproblem_id)
        SELECT DISTINCT temporal_scenario_id, subproblem_id
        FROM inputs_temporal
        WHERE temporal_scenario_id = ?;
        """
    spin_on_database_lock(
        conn=conn, cursor=c, sql=subproblems_sql,
        data=(subscenario_id,), many=False
    )

    # Stages
    # TODO: stage_name not currently included; decide whether to keep this
    #  column in the database and how to import data for it if we do want it
    stages_sql = """
        INSERT INTO inputs_temporal_subproblems_stages
        (temporal_scenario_id, subproblem_id, stage_id)
        SELECT DISTINCT temporal_scenario_id, subproblem_id, stage_id
        FROM inputs_temporal
        WHERE temporal_scenario_id = ?;
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=stages_sql,
                          data=(subscenario_id,), many=False)

    # TIMEPOINT HORIZONS
    sid_stg_bt_hr_sql = """
        SELECT subproblem_id, stage_id, balancing_type_horizon, horizon
        FROM inputs_temporal_horizons
        JOIN inputs_temporal_subproblems_stages
        USING (temporal_scenario_id, subproblem_id)
        WHERE temporal_scenario_id = ?
        """
    sid_stg_bt_hr = c.execute(
        sid_stg_bt_hr_sql, (subscenario_id,)
    ).fetchall()

    hor_tmps_tuples_list = list()
    for (sid, stage, bt, hr) in sid_stg_bt_hr:
        tmp_start_tmp_end = c.execute(
            """SELECT tmp_start, tmp_end
            FROM inputs_temporal_horizon_timepoints_start_end
            WHERE temporal_scenario_id = ?
            AND subproblem_id = ?
            AND stage_id = ?
            AND balancing_type_horizon = ?
            AND horizon = ?""",
            (subscenario_id, sid, stage, bt, hr)
        ).fetchall()

        tmps = []
        for tmp_start, tmp_end in tmp_start_tmp_end:
            tmps += [
                tmp for tmp in c.execute("""
                SELECT timepoint
                FROM inputs_temporal
                WHERE temporal_scenario_id = ?
                AND subproblem_id = ?
                AND stage_id = ?
                AND timepoint >= ?
                AND timepoint <= ?
                """, (subscenario_id, sid, stage, tmp_start, tmp_end)
                ).fetchall()
            ]

        for tmp_tuple in tmps:
            tmp = tmp_tuple[0]

            hor_tmps_tuples_list.append((subscenario_id, sid, stage, tmp, bt, hr))

    horizon_timepoints_sql = """
        INSERT INTO inputs_temporal_horizon_timepoints
        (temporal_scenario_id, subproblem_id, stage_id, timepoint, 
        balancing_type_horizon, horizon)
        VALUES (?, ?, ?, ?, ?, ?);
        """

    spin_on_database_lock(conn=conn, cursor=c, sql=horizon_timepoints_sql,
                          data=hor_tmps_tuples_list)
