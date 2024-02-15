# Copyright 2016-2024 Blue Marble Analytics LLC.
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
        conn=conn, cursor=c, sql=subproblems_sql, data=(subscenario_id,), many=False
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
    spin_on_database_lock(
        conn=conn, cursor=c, sql=stages_sql, data=(subscenario_id,), many=False
    )

    # TIMEPOINT HORIZONS
    subproblem_stages = c.execute(
        f"""
        SELECT subproblem_id, stage_id
        FROM inputs_temporal_subproblems_stages
        WHERE temporal_scenario_id = {subscenario_id}
        """
    ).fetchall()

    # For each subproblem-stage, figure out how the timepoints are organized
    # into horizons
    for subproblem, stage in subproblem_stages:
        # Find the relevant balancing_type-horizons for this subproblem, stage
        bt_hr_sql = f"""
            SELECT balancing_type_horizon, horizon, tmp_start, tmp_end
            FROM inputs_temporal_horizon_timepoints_start_end
            WHERE temporal_scenario_id = {subscenario_id}
            AND stage_id = {stage}
            AND (tmp_start, tmp_start_spinup_or_lookahead) in (
                SELECT timepoint, spinup_or_lookahead
                FROM inputs_temporal
                WHERE temporal_scenario_id = {subscenario_id}
                AND subproblem_id = {subproblem}
                AND stage_id = {stage}
                )
            AND (tmp_end, tmp_end_spinup_or_lookahead) in (
                SELECT timepoint, spinup_or_lookahead
                FROM inputs_temporal
                WHERE temporal_scenario_id = {subscenario_id}
                AND subproblem_id = {subproblem}
                AND stage_id = {stage}
                )
            ;
            """

        bt_hr = c.execute(bt_hr_sql, ()).fetchall()

        hor_tmps_tuples_list = list()

        for bt, hr, tmp_start, tmp_end in bt_hr:
            sid_tmps = [
                tmp[0]
                for tmp in c.execute(
                    f"""
                SELECT timepoint
                FROM inputs_temporal
                WHERE temporal_scenario_id = {subscenario_id}
                AND subproblem_id = {subproblem}
                AND stage_id = {stage}
                AND timepoint >= {tmp_start}
                AND timepoint <= {tmp_end}
                ;
                """
                ).fetchall()
            ]

            for tmp in sid_tmps:
                hor_tmps_tuples_list.append(
                    (subscenario_id, subproblem, stage, tmp, bt, hr)
                )

        horizon_timepoints_sql = """
            INSERT INTO inputs_temporal_horizon_timepoints
            (temporal_scenario_id, subproblem_id, stage_id, timepoint, 
            balancing_type_horizon, horizon)
            VALUES (?, ?, ?, ?, ?, ?);
            """

        spin_on_database_lock(
            conn=conn, cursor=c, sql=horizon_timepoints_sql, data=hor_tmps_tuples_list
        )
