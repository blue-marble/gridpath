# Copyright 2016-2023 Blue Marble Analytics LLC.
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
Create hydro iteration inputs for a temporal scenario ID and balancing
type from an year/month table.
"""

from argparse import ArgumentParser
import sys

from db.common_functions import connect_to_database, spin_on_database_lock
from db.utilities.common_functions import generic_insert_subscenario_info


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    parser.add_argument("--database")
    parser.add_argument("--temporal_scenario_id")
    parser.add_argument("--balancing_type")
    parser.add_argument("--hydro_operational_chars_scenario_id")
    parser.add_argument("--hydro_operational_chars_scenario_name")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def calculate_from_project_year_month_data(
    conn, temporal_scenario_id, hydro_operational_chars_scenario_id, balancing_type
):
    c = conn.cursor()

    sql = f"""
        INSERT INTO inputs_project_hydro_operational_chars (
                project, hydro_operational_chars_scenario_id, 
                hydro_iteration, subproblem_id, stage_id, 
                balancing_type_project, horizon, average_power_fraction, 
                min_power_fraction, max_power_fraction
        )
              
        SELECT
                project,
                {hydro_operational_chars_scenario_id},
                hydro_iteration,
                subproblem_id,
                stage_id,
                balancing_type,
                horizon, 
                sum(month_weight * average_power_fraction) as average_power_fraction,
                sum(month_weight * min_power_fraction) as min_power_fraction,
                sum(month_weight * max_power_fraction) as max_power_fraction
                FROM (

                SELECT
                project,
                temporal_scenario_id,
                hydro_iteration,
                subproblem_id,
                stage_id,
                balancing_type,
                horizon, 
                month_table.month,
                hours_in_month,
                total_hours,
                CAST(hours_in_month as REAL)/total_hours as month_weight,
                average_power_fraction,
                min_power_fraction, 
                max_power_fraction
                    -- Figure out the month weights for each 
                    -- subproblem/stage/balancing_type/horizon
                    -- (e.g., if a weekly horizon spans months)
                FROM (
                        SELECT 
                            temporal_scenario_id,
                            subproblem_id,
                            stage_id,
                            balancing_type_horizon as balancing_type,
                            horizon,
                            month,
                            sum(number_of_hours_in_timepoint) as hours_in_month
                        FROM inputs_temporal_horizon_timepoints
                        JOIN inputs_temporal
                        USING (temporal_scenario_id, subproblem_id, stage_id, timepoint)
                        WHERE temporal_scenario_id = {temporal_scenario_id}
                        AND balancing_type = '{balancing_type}'
                        GROUP BY 
                            temporal_scenario_id,
                            subproblem_id,
                            stage_id, 
                            balancing_type,
                            horizon,
                            month
                    ) as month_table
        
                    JOIN (
                        SELECT 
                            temporal_scenario_id,
                            subproblem_id, 
                            stage_id, 
                            balancing_type_horizon as balancing_type, 
                            horizon, 
                            sum(number_of_hours_in_timepoint) as total_hours
                        FROM inputs_temporal_horizon_timepoints
                        JOIN inputs_temporal
                        USING (temporal_scenario_id, subproblem_id, stage_id, timepoint)
                        WHERE temporal_scenario_id = {temporal_scenario_id}
                        AND balancing_type = '{balancing_type}'
                        GROUP BY 
                            temporal_scenario_id, 
                            subproblem_id, 
                            stage_id, 
                            balancing_type_horizon, 
                            horizon
                    ) as total_table
                    USING (
                        temporal_scenario_id,
                        subproblem_id,
                        stage_id,
                        balancing_type,
                        horizon
                        )
                  -- Hydro chars
                    JOIN inputs_project_hydro_operational_chars_iterations 
                    USING (month)
                GROUP BY 
                    project,
                    temporal_scenario_id,
                    hydro_iteration,
                    subproblem_id,
                    stage_id,
                    balancing_type,
                    horizon,
                    month
                )
            GROUP BY project,
            temporal_scenario_id,
            hydro_iteration,
            subproblem_id,
            stage_id,
            balancing_type,
            horizon
    """

    spin_on_database_lock(conn=conn, cursor=c, sql=sql, data=(), many=False)


if __name__ == "__main__":
    parsed_args = parse_arguments(args=sys.argv[1:])
    conn = connect_to_database(db_path=parsed_args.database)

    calculate_from_project_year_month_data(
        conn=conn,
        temporal_scenario_id=parsed_args.temporal_scenario_id,
        hydro_operational_chars_scenario_id=parsed_args.hydro_operational_chars_scenario_id,
        balancing_type=parsed_args.balancing_type,
    )
