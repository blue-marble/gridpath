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
Scenario characteristics in database.
"""

import csv
import os.path

from gridpath.auxiliary.auxiliary import (
    check_for_integer_subdirectories,
    check_for_starting_string_subdirectories,
)


# TODO: use 0s instead of 1s to indicate no subdirectories?


class OptionalFeatures(object):
    def __init__(self, conn, scenario_id):
        """
        :param cursor:
        :param scenario_id:
        """
        of_column_names = [
            n for n in get_scenario_table_columns(conn=conn) if n.startswith("of_")
        ]

        for of in of_column_names:
            setattr(
                self,
                of.upper(),
                db_column_to_self(column=of, conn=conn, scenario_id=scenario_id),
            )

    def get_all_available_features(self):
        all_features = [attr[3:].lower() for attr, value in self.__dict__.items()]

        return all_features

    def get_active_features(self):
        """
        Get list of requested features
        :return:
        """
        active_features = list()

        for attr, value in self.__dict__.items():
            if value:
                active_features.append(attr[3:].lower())

        return active_features


class SubScenarios(object):
    """
    The subscenario IDs will be used to format SQL queries, so we set them to
    "NULL" (not None) if an ID is not specified for the scenario.
    """

    def __init__(self, conn, scenario_id):
        """

        :param cursor:
        :param scenario_id:
        """
        subscenario_column_names = [
            n
            for n in get_scenario_table_columns(conn=conn)
            if n.endswith("_scenario_id")
        ]

        for subscenario in subscenario_column_names:
            setattr(
                self,
                subscenario.upper(),
                db_column_to_self(
                    column=subscenario, conn=conn, scenario_id=scenario_id
                ),
            )

    def get_all_available_subscenarios(self):
        all_subscenarios = [
            attr.lower()
            for attr, value in self.__dict__.items()
            if attr != "SCENARIO_ID"
        ]

        return all_subscenarios


class ScenarioStructure(object):
    def __init__(self, hydro_years, stages_by_subproblem):
        # Hydro year iterations
        self.HYDRO_YEARS = hydro_years
        # List of stages by subproblem in dict {subproblem: [stages]}
        # This should have a single key, 1, if a single subproblem
        # This should be subproblem: [1] when a single stage in the subproblem
        self.SUBPROBLEM_STAGES = stages_by_subproblem


def get_scenario_structure_from_db(conn, scenario_id):
    """

    :param conn:
    :param scenario_id:
    """
    cursor = conn.cursor()

    # Hydro years
    hydro_years = [
        hydro_year[0]
        for hydro_year in cursor.execute(
            """SELECT hydro_year
               FROM inputs_temporal_hydro_years
               INNER JOIN scenarios
               USING (temporal_scenario_id)
               WHERE scenario_id = {};""".format(
                scenario_id
            )
        ).fetchall()
    ]

    # TODO: make sure there is data integrity between subproblems_stages
    #   and inputs_temporal_horizons and inputs_temporal
    all_subproblems = [
        subproblem[0]
        for subproblem in cursor.execute(
            """SELECT subproblem_id
               FROM inputs_temporal_subproblems
               INNER JOIN scenarios
               USING (temporal_scenario_id)
               WHERE scenario_id = {};""".format(
                scenario_id
            )
        ).fetchall()
    ]

    # Store subproblems and stages in dict {subproblem: [stages]}
    stages_by_subproblem = {}
    for s in all_subproblems:
        stages = cursor.execute(
            """SELECT stage_id
               FROM inputs_temporal_subproblems_stages
               INNER JOIN scenarios
               USING (temporal_scenario_id)
               WHERE scenario_id = {}
               AND subproblem_id = {};""".format(
                scenario_id, s
            )
        ).fetchall()
        stages = [stage[0] for stage in stages]  # convert to simple list
        stages_by_subproblem[s] = stages

    return ScenarioStructure(
        stages_by_subproblem=stages_by_subproblem, hydro_years=hydro_years
    )


def get_scenario_structure_from_disk(scenario_directory):
    # Check if there are hydro year directories
    hydro_directories = check_for_starting_string_subdirectories(
        main_directory=scenario_directory, starting_string="hydro_year"
    )

    hydro_years = [d.replace("hydro_year_", "") for d in hydro_directories]

    # Check if there are subproblem directories
    # If there are hydro directories, assume subproblem structure is the same
    # for each hydro year
    if hydro_years:
        subproblem_main_directory = os.path.join(
            scenario_directory, hydro_directories[0]
        )
    else:
        subproblem_main_directory = scenario_directory

    # Convert to integers
    subproblem_directories = [
        int(i) for i in check_for_integer_subdirectories(subproblem_main_directory)
    ]

    # Make dictionary for the stages by subproblem, starting with empty
    # list for each subproblem
    stages_by_subproblem = {subp: [] for subp in subproblem_directories}

    # If we have subproblems, check for stage subdirectories for each
    # subproblem directory
    if subproblem_directories:
        for subproblem in subproblem_directories:
            subproblem_dir = os.path.join(subproblem_main_directory, str(subproblem))
            # Convert to integers
            stages = [int(i) for i in check_for_integer_subdirectories(subproblem_dir)]
            if stages:
                stages_by_subproblem[subproblem] = stages
            else:
                # If we didn't find stage directories, we have a single
                # stage
                # Downstream, we need a list with just 1 as member
                stages_by_subproblem[subproblem] = [1]
    else:
        # If we didn't find integer directories, we have a single subproblem
        # with a single stage
        # Downstream, we need {1: [1]}
        stages_by_subproblem[1] = [1]

    return ScenarioStructure(
        hydro_years=hydro_years, stages_by_subproblem=stages_by_subproblem
    )


class SolverOptions(object):
    def __init__(self, conn, scenario_id):
        """
        :param cursor:
        :param scenario_id:
        """
        cursor = conn.cursor()

        self.SOLVER_OPTIONS_ID = cursor.execute(
            """
            SELECT solver_options_id 
            FROM scenarios 
            WHERE scenario_id = {}
            """.format(
                scenario_id
            )
        ).fetchone()[0]

        if self.SOLVER_OPTIONS_ID is None:
            self.SOLVER_NAME = None
        else:
            distinct_solvers = cursor.execute(
                """SELECT DISTINCT solver_name 
                FROM inputs_options_solver 
                WHERE solver_options_id = {}""".format(
                    self.SOLVER_OPTIONS_ID
                )
            ).fetchall()
            if len(distinct_solvers) > 1:
                raise ValueError(
                    """
                ERROR: Solver options include more than one solver name! Only a 
                single solver name must be specified for solver_options_id in the 
                inputs_options_solver table. See solver_options_id {}. 
                """.format(
                        self.SOLVER_OPTIONS_ID
                    )
                )
            else:
                self.SOLVER_NAME = distinct_solvers[0][0]

        self.SOLVER_OPTIONS = (
            None
            if self.SOLVER_OPTIONS_ID is None
            else {
                row[0]: row[1]
                for row in cursor.execute(
                    """
                    SELECT solver_option_name, solver_option_value
                    FROM inputs_options_solver
                    WHERE solver_options_id = {};
                    """.format(
                        self.SOLVER_OPTIONS_ID
                    )
                ).fetchall()
                if row[0] is not None and row[0] != ""
            }
        )


def db_column_to_self(column, conn, scenario_id):
    of = True if column.startswith("of") else False
    c = conn.cursor()
    query = c.execute(
        """SELECT {}
           FROM scenarios
           WHERE scenario_id = ?;""".format(
            column
        ),
        (scenario_id,),
    ).fetchone()[0]

    self = "NULL" if query is None and not of else query

    return self


def get_scenario_table_columns(conn):
    c = conn.cursor()

    scenario_query = c.execute(
        """
        SELECT * FROM scenarios;
        """
    )
    column_names = [description[0] for description in scenario_query.description]

    return column_names
