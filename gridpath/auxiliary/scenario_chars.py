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

import os.path

from gridpath.auxiliary.auxiliary import (
    check_for_integer_subdirectories,
    check_for_starting_string_subdirectories,
)


# TODO: conslidate use 0s and 1s to indicate no subdirectories?


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
    def __init__(self, hydro_years_by_weather_year, stages_by_subproblem):
        # Weather and hydro iterations {weather_year: [hydro_years]}
        # If no weather iterations, we're expecting a single key with 0 as value
        # If no hydro iterations, we're expecting a list with 0 as member [0]
        # No weather, no hydro: {0: [0]}
        self.WEATHER_YEAR_HYDRO_YEARS = hydro_years_by_weather_year
        # List of stages by subproblem in dict {subproblem: [stages]}
        # This should have a single key, 1, if a single subproblem
        # This should be subproblem: [1] when a single stage in the subproblem
        self.SUBPROBLEM_STAGES = stages_by_subproblem

        # If any subproblem's stage list is non-empty, we have stages, so set
        # the MULTI_STAGE flag to True to pass to determine_modules
        # This tells the determine_modules function to include the
        # stages-related modules
        self.MULTI_STAGE = any(
            [
                len(self.SUBPROBLEM_STAGES[subp]) > 1
                for subp in list(self.SUBPROBLEM_STAGES.keys())
            ]
        )


class ScenarioDirectoryStructure(object):
    def __init__(self, scenario_structure):
        self.WEATHER_YEAR_HYDRO_YEAR_DIRECTORIES = (
            determine_weather_year_hydro_year_directory_structure(scenario_structure)
        )
        self.SUBPROBLEM_STAGE_DIRECTORIES = (
            determine_subproblem_stage_directory_structure(scenario_structure)
        )


def determine_weather_year_hydro_year_directory_structure(scenario_structure):
    """
    Determine whether we will have iteration (weather, hydro year),
    We write the subdirectories if we have multiple items at that level
    """

    weather_year_hydro_year_directory_strings = {}

    # If no weather iterations, something went wrong upstream, so raise an
    # error (we're expecting at least 1)
    if len(scenario_structure.WEATHER_YEAR_HYDRO_YEARS.keys()) == 0:
        raise ValueError("Expecting at least one weather iteration.")

    if len(scenario_structure.WEATHER_YEAR_HYDRO_YEARS.keys()) > 1:
        make_weather_year_dirs = True
    else:
        make_weather_year_dirs = False

    for weather_year in scenario_structure.WEATHER_YEAR_HYDRO_YEARS.keys():
        weather_year_str = (
            f"weather_year_{weather_year}" if make_weather_year_dirs else ""
        )

        weather_year_hydro_year_directory_strings[weather_year_str] = []
        # Determine whether we will have hydro iterations
        if len(scenario_structure.WEATHER_YEAR_HYDRO_YEARS[weather_year]) > 1:
            make_hydro_year_dirs = True
        else:
            make_hydro_year_dirs = False

        for hydro_year in scenario_structure.WEATHER_YEAR_HYDRO_YEARS[weather_year]:
            hydro_year_str = f"hydro_year_{hydro_year}" if make_hydro_year_dirs else ""
            weather_year_hydro_year_directory_strings[weather_year_str].append(
                hydro_year_str
            )

    return weather_year_hydro_year_directory_strings


def determine_subproblem_stage_directory_structure(scenario_structure):
    """
    The subproblem structure is the same within each iteration
    If we only have a single subproblem AND it does not have stages, set the
    subproblem_string to an empty string (the subproblem directory should not
    have been created)
    If we have multiple subproblems or a single subproblems with stages,
    we're expecting a subproblem directory
    """
    subproblem_stage_directory_strings = {}

    if (
        len(scenario_structure.SUBPROBLEM_STAGES) <= 1
        and scenario_structure.MULTI_STAGE is False
    ):
        make_subproblem_directories = False
    else:
        make_subproblem_directories = True

    for subproblem in scenario_structure.SUBPROBLEM_STAGES.keys():
        # If there are subproblems/stages, input directory will be nested
        if make_subproblem_directories:
            subproblem_str = str(subproblem)
        else:
            subproblem_str = ""

        subproblem_stage_directory_strings[subproblem_str] = []

        stages = scenario_structure.SUBPROBLEM_STAGES[subproblem]
        if len(stages) == 1:
            make_stage_directories = False
        else:
            make_stage_directories = True

        for stage in stages:
            if make_stage_directories:
                stage_str = str(stage)
            else:
                stage_str = ""

            subproblem_stage_directory_strings[subproblem_str].append(stage_str)

    return subproblem_stage_directory_strings


def get_scenario_structure_from_db(conn, scenario_id):
    """

    :param conn:
    :param scenario_id:
    """
    cursor = conn.cursor()

    # Weather years
    all_weather_years = [
        row[0]
        for row in cursor.execute(
            """SELECT DISTINCT weather_year
               FROM inputs_temporal_iterations
               INNER JOIN scenarios
               USING (temporal_scenario_id)
               WHERE scenario_id = {};""".format(
                scenario_id
            )
        ).fetchall()
    ]

    # Store weather years and hydro years in dict {weather_year: [hydro_years]}
    # If we don't find any weather years, there were no iterations (we know
    # there are no hydro years since NULL values are not allowed for weather
    # or hydro years)
    if not all_weather_years:
        hydro_years_by_weather_year = {0: [0]}
    else:
        hydro_years_by_weather_year = {}
        for weather_year in all_weather_years:
            hydro_years = cursor.execute(
                f"""SELECT hydro_year
                   FROM inputs_temporal_iterations
                   INNER JOIN scenarios
                   USING (temporal_scenario_id)
                   WHERE scenario_id = {scenario_id}
                   AND weather_year = {weather_year};"""
            ).fetchall()
            hydro_years = [hydro_year[0] for hydro_year in hydro_years]  # to list
            hydro_years_by_weather_year[weather_year] = hydro_years

    # TODO: make sure there is data integrity between subproblems_stages
    #   and inputs_temporal_horizons and inputs_temporal
    # TODO: probably don't need a separate table for subproblems, but can get
    #  the subproblems from the subproblems_stages table
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
    for weather_year in all_subproblems:
        stages = cursor.execute(
            """SELECT stage_id
               FROM inputs_temporal_subproblems_stages
               INNER JOIN scenarios
               USING (temporal_scenario_id)
               WHERE scenario_id = {}
               AND subproblem_id = {};""".format(
                scenario_id, weather_year
            )
        ).fetchall()
        stages = [stage[0] for stage in stages]  # convert to simple list
        stages_by_subproblem[weather_year] = stages

    return ScenarioStructure(
        stages_by_subproblem=stages_by_subproblem,
        hydro_years_by_weather_year=hydro_years_by_weather_year,
    )


def get_scenario_structure_from_disk(scenario_directory):
    hydro_years_by_weather_year = {}
    stages_by_subproblem = {}

    # Check if there are weather directories
    weather_directories = check_for_starting_string_subdirectories(
        main_directory=scenario_directory, starting_string="weather_year"
    )

    if not weather_directories:
        (
            hydro_years,
            subproblem_main_directory,
        ) = check_for_hydro_year_directories(starting_directory=scenario_directory)
        hydro_years_by_weather_year = {0: hydro_years}
        stages_by_subproblem = check_subproblem_structure(
            subproblem_main_directory=subproblem_main_directory
        )
    else:
        for w_d in weather_directories:
            weather_year = int(w_d.replace("weather_year_", ""))
            w_d_full_path = os.path.join(scenario_directory, w_d)
            (
                hydro_years,
                subproblem_main_directory,
            ) = check_for_hydro_year_directories(starting_directory=w_d_full_path)
            hydro_years_by_weather_year[weather_year] = hydro_years
            stages_by_subproblem = check_subproblem_structure(
                subproblem_main_directory=subproblem_main_directory
            )

    return ScenarioStructure(
        hydro_years_by_weather_year=hydro_years_by_weather_year,
        stages_by_subproblem=stages_by_subproblem,
    )


def check_for_hydro_year_directories(starting_directory):
    hydro_directories = check_for_starting_string_subdirectories(
        main_directory=starting_directory, starting_string="hydro_year"
    )

    hydro_years = [d.replace("hydro_year_", "") for d in hydro_directories]

    # Check if there are subproblem directories
    # If there are hydro directories, assume subproblem structure is the same
    # for each hydro year
    # If there are no hydro directories, the starting directory is the main
    # subproblem directory
    if hydro_years:
        subproblem_main_directory = os.path.join(
            starting_directory, hydro_directories[0]
        )
    else:
        # If we don't find any directories, return a list with 0
        hydro_years = [0]
        subproblem_main_directory = starting_directory

    return hydro_years, subproblem_main_directory


def check_subproblem_structure(subproblem_main_directory):
    # Convert to integers
    subproblem_directories = [
        str(i) for i in check_for_integer_subdirectories(subproblem_main_directory)
    ]

    # Make dictionary for the stages by subproblem, starting with empty
    # list for each subproblem
    stages_by_subproblem = {subp: [] for subp in subproblem_directories}

    # If we have subproblems, check for stage subdirectories for each
    # subproblem directory
    if subproblem_directories:
        for subproblem in subproblem_directories:
            subproblem_dir = os.path.join(subproblem_main_directory, subproblem)
            # Convert to integers
            stages = [str(i) for i in check_for_integer_subdirectories(subproblem_dir)]
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

    return stages_by_subproblem


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
