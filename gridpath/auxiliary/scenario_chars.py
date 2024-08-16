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
    def __init__(self, iteration_structure, subproblem_stage_structure):
        # Weather, hydro, and availability iterations
        # {weather_iteration: {hydro_iteration: [availability_iterations]}}
        # If no weather iterations, we're expecting a single key with 0 as value
        # If no hydro iterations, we're expecting a single key with 0 as value
        # If no availability itertions, we're expecting a list with 0 as member
        # [0]
        # No weather, no hydro, no availability: {0: {0: [0]}}
        self.ITERATION_STRUCTURE = iteration_structure
        # List of stages by subproblem in dict {subproblem: [stages]}
        # This should have a single key, 1, if a single subproblem
        # This should be subproblem: [1] when a single stage in the subproblem
        self.SUBPROBLEM_STAGES = subproblem_stage_structure

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
        self.ITERATION_DIRECTORIES = (
            determine_iteration_directories_from_iteration_structure(scenario_structure)
        )
        self.SUBPROBLEM_STAGE_DIRECTORIES = (
            determine_subproblem_stage_directory_structure(scenario_structure)
        )


def determine_iteration_directories_from_iteration_structure(scenario_structure):
    """
    Determine whether we will have iteration (weather, hydro iteration),
    We write the subdirectories if we have multiple items at that level
    """

    iteration_directory_strings_dict = {}

    # Check the top-level keys; these are the weather iterations
    # If no weather iterations, something went wrong upstream, so raise an
    # error (we're expecting at least one weather iteration)
    if len(scenario_structure.ITERATION_STRUCTURE.keys()) == 0:
        raise ValueError("Expecting at least one weather iteration.")

    # Don't make the directory for weather iterations if it's a single
    # iteration with ID 0
    if len(scenario_structure.ITERATION_STRUCTURE.keys()) > 1:
        make_weather_iteration_dirs = True
    elif list(scenario_structure.ITERATION_STRUCTURE.keys())[0] != 0:
        make_weather_iteration_dirs = True
    else:
        make_weather_iteration_dirs = False

    for weather_iteration in scenario_structure.ITERATION_STRUCTURE.keys():
        weather_iteration_str = (
            f"weather_iteration_{weather_iteration}"
            if make_weather_iteration_dirs
            else "empty_string"
        )

        # Check the hydro iteration level
        iteration_directory_strings_dict[weather_iteration_str] = {}
        # Determine whether we will have hydro iterations
        # Make the hydro directories if 1) there are multiple
        # hydro iterations within a weather iteration or 2) there are
        # multiple hydro iterations across weather iterations
        # Case 2) captures case 1), but keeping separate for clarity
        if len(scenario_structure.ITERATION_STRUCTURE[weather_iteration].keys()) > 1:
            make_hydro_iteration_dirs = True
        elif (
            len(
                set(
                    [
                        i
                        for sublist in [
                            scenario_structure.ITERATION_STRUCTURE[w]
                            for w in scenario_structure.ITERATION_STRUCTURE.keys()
                        ]
                        for i in sublist
                    ]
                )
            )
            > 1
        ):
            make_hydro_iteration_dirs = True
        elif (
            list(scenario_structure.ITERATION_STRUCTURE[weather_iteration].keys())[0]
            != 0
        ):
            make_hydro_iteration_dirs = True
        else:
            make_hydro_iteration_dirs = False

        for hydro_iteration in scenario_structure.ITERATION_STRUCTURE[
            weather_iteration
        ].keys():
            hydro_iteration_str = (
                f"hydro_iteration_{hydro_iteration}"
                if make_hydro_iteration_dirs
                else "empty_string"
            )
            iteration_directory_strings_dict[weather_iteration_str][
                hydro_iteration_str
            ] = []

            # Check the availability level
            # Make the availability directories if 1) there are multiple
            # availability iterations within a hydro iteration or 2) there are
            # multiple availability iterations across hydro iterations
            # Case 2) captures case 1), but keeping separate for clarity
            if (
                len(
                    scenario_structure.ITERATION_STRUCTURE[weather_iteration][
                        hydro_iteration
                    ]
                )
                > 1
            ):
                make_availability_iteration_dirs = True
            elif (
                len(
                    set(
                        [
                            i
                            for sublist in [
                                scenario_structure.ITERATION_STRUCTURE[w][h]
                                for w in scenario_structure.ITERATION_STRUCTURE.keys()
                                for h in scenario_structure.ITERATION_STRUCTURE[
                                    w
                                ].keys()
                            ]
                            for i in sublist
                        ]
                    )
                )
                > 1
            ):
                make_availability_iteration_dirs = True
            elif (
                list(
                    scenario_structure.ITERATION_STRUCTURE[weather_iteration][
                        hydro_iteration
                    ]
                )[0]
                != 0
            ):
                make_availability_iteration_dirs = True
            else:
                make_availability_iteration_dirs = False
            for availability_iteration in scenario_structure.ITERATION_STRUCTURE[
                weather_iteration
            ][hydro_iteration]:
                availability_iteration_str = (
                    f"availability_iteration_{availability_iteration}"
                    if make_availability_iteration_dirs
                    else "empty_string"
                )
                iteration_directory_strings_dict[weather_iteration_str][
                    hydro_iteration_str
                ].append(availability_iteration_str)

    return iteration_directory_strings_dict


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

    # Weather iterations
    weather_iterations = [
        row[0]
        for row in cursor.execute(
            """SELECT DISTINCT weather_iteration
               FROM inputs_temporal_iterations
               INNER JOIN scenarios
               USING (temporal_scenario_id)
               WHERE scenario_id = {};""".format(
                scenario_id
            )
        ).fetchall()
    ]

    # Store weather iterations and hydro iterations in dict
    # {weather_iteration: [hydro_iterations]}
    # If we don't find any weather iterations, there were no iterations of
    # any kind (we know there are no hydro and availability iterations since
    # NULL values are not allowed)
    if not weather_iterations:
        iteration_structure_dict = {0: {0: [0]}}
    else:
        iteration_structure_dict = {}
        for weather_iteration in weather_iterations:
            # Get the hydro iterations for this weather iteration
            hydro_iterations = cursor.execute(
                f"""SELECT hydro_iteration
                   FROM inputs_temporal_iterations
                   INNER JOIN scenarios
                   USING (temporal_scenario_id)
                   WHERE scenario_id = {scenario_id}
                   AND weather_iteration = {weather_iteration}
                   ;"""
            ).fetchall()
            hydro_iterations_dict = {
                hydro_iteration[0]: [] for hydro_iteration in hydro_iterations
            }  # to list
            iteration_structure_dict[weather_iteration] = hydro_iterations_dict

            for hydro_iteration in hydro_iterations_dict.keys():
                # Get the availability iterations for this weather/hydro
                # iteration
                availability_iterations = cursor.execute(
                    f"""SELECT availability_iteration
                       FROM inputs_temporal_iterations
                       INNER JOIN scenarios
                       USING (temporal_scenario_id)
                       WHERE scenario_id = {scenario_id}
                       AND weather_iteration = {weather_iteration}
                       AND hydro_iteration = {hydro_iteration}
                       ;"""
                ).fetchall()
                availability_iterations = [
                    availability_iteration[0]
                    for availability_iteration in availability_iterations
                ]
                iteration_structure_dict[weather_iteration][
                    hydro_iteration
                ] = availability_iterations

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
    for subproblem in all_subproblems:
        stages = cursor.execute(
            f"""SELECT stage_id
               FROM inputs_temporal_subproblems_stages
               INNER JOIN scenarios
               USING (temporal_scenario_id)
               WHERE scenario_id = {scenario_id}
               AND subproblem_id = {subproblem}
               ;"""
        ).fetchall()
        stages = [stage[0] for stage in stages]  # convert to simple list
        stages_by_subproblem[subproblem] = stages

    return ScenarioStructure(
        iteration_structure=iteration_structure_dict,
        subproblem_stage_structure=stages_by_subproblem,
    )


def get_scenario_structure_from_disk(scenario_directory):
    iteration_structure_dict = {}

    # Get the iteration structure
    # Check if there are weather directories
    weather_directories = check_for_starting_string_subdirectories(
        main_directory=scenario_directory, starting_string="weather_iteration"
    )

    iteration_structure_dict = {}
    if not weather_directories:
        # Check if there are hydro and availability iterations
        hydro_and_availability_iterations = (
            check_hydro_and_availability_iteration_levels(
                starting_directory=scenario_directory
            )
        )
        iteration_structure_dict = {0: hydro_and_availability_iterations}
    else:
        for weather_directory in weather_directories:
            weather_iteration = int(weather_directory.replace("weather_iteration_", ""))
            w_d_full_path = os.path.join(scenario_directory, weather_directory)
            # Check if there are hydro and availability iterations for this
            # weather iteration
            hydro_and_availability_iterations = (
                check_hydro_and_availability_iteration_levels(
                    starting_directory=w_d_full_path
                )
            )
            iteration_structure_dict[weather_iteration] = (
                hydro_and_availability_iterations
            )

    # Get the subproblem structure
    subproblem_main_directory = get_directory_for_subproblem_structure(
        scenario_directory=scenario_directory
    )
    stages_by_subproblem = check_subproblem_structure(
        subproblem_main_directory=subproblem_main_directory
    )

    return ScenarioStructure(
        iteration_structure=iteration_structure_dict,
        subproblem_stage_structure=stages_by_subproblem,
    )


def check_hydro_and_availability_iteration_levels(starting_directory):
    """
    Check if there are hydro directories in the starting directory.
    If not found, return a dictionary with 0 as key and a list of availability
    iterations found in the starting directory, else return a list with
    the hydro iteration numbers as keys and the availability iterations found
    within each hydro iteration (as list for the respective key).
    """
    # Check for hydro directories in the starting directory
    hydro_directories = check_for_starting_string_subdirectories(
        main_directory=starting_directory, starting_string="hydro_iteration"
    )
    # If there are no hydro directories, check for availability
    # directories in the main directory
    if not hydro_directories:
        availability_iterations = check_availability_iteration_level(
            starting_directory=starting_directory
        )

        hydro_and_availability_iterations = {0: availability_iterations}

    else:
        hydro_and_availability_iterations = {}
        for hydro_directory in hydro_directories:
            hydro_iteration = int(hydro_directory.replace("hydro_iteration_", ""))
            availability_iterations = check_availability_iteration_level(
                starting_directory=os.path.join(starting_directory, hydro_directory)
            )

            hydro_and_availability_iterations[hydro_iteration] = availability_iterations

    return hydro_and_availability_iterations


def check_availability_iteration_level(starting_directory):
    """
    Check if there are availability directories in the starting directory.
    If not found, return a list with 0, else return a list with the
    availability iteration numbers.
    """
    availability_directories = check_for_starting_string_subdirectories(
        main_directory=starting_directory,
        starting_string="availability_iteration",
    )

    # If there are no availability directories, return the "empty"
    # iteration structure
    if not availability_directories:
        availability_iterations = [0]
        # subproblem_main_directory = scenario_directory
    # If there are availability directory, add those iterations to
    # the iteration structure
    else:
        availability_iterations = dir_strings_to_iteration_numbers_list(
            dir_list=availability_directories,
            starting_string="availability_iteration",
        )

    return availability_iterations


def get_directory_for_subproblem_structure(scenario_directory):
    weather_directories = check_for_starting_string_subdirectories(
        main_directory=scenario_directory, starting_string="weather_iteration"
    )
    if weather_directories:
        weather_dir_for_subproblem_structure = weather_directories[0]
    else:
        weather_dir_for_subproblem_structure = ""

    hydro_directories = check_for_starting_string_subdirectories(
        main_directory=os.path.join(
            scenario_directory, weather_dir_for_subproblem_structure
        ),
        starting_string="hydro_iteration",
    )

    if hydro_directories:
        hydro_dir_for_subproblem_structure = hydro_directories[0]
    else:
        hydro_dir_for_subproblem_structure = ""

    availability_directories = check_for_starting_string_subdirectories(
        main_directory=os.path.join(
            scenario_directory,
            weather_dir_for_subproblem_structure,
            hydro_dir_for_subproblem_structure,
        ),
        starting_string="availability_iteration",
    )

    if availability_directories:
        availability_dir_for_subproblem_structure = availability_directories[0]
    else:
        availability_dir_for_subproblem_structure = ""

    directory_for_subproblem_structure = os.path.join(
        scenario_directory,
        weather_dir_for_subproblem_structure,
        hydro_dir_for_subproblem_structure,
        availability_dir_for_subproblem_structure,
    )

    return directory_for_subproblem_structure


def dir_strings_to_iteration_numbers_list(dir_list, starting_string):
    iteration_numbers_list = [d.replace(f"{starting_string}_", "") for d in dir_list]

    return iteration_numbers_list


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
