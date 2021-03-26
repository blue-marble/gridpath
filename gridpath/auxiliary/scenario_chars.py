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
Scenario characteristics in database.
"""

import csv
import os.path

from gridpath.auxiliary.auxiliary import check_for_integer_subdirectories


class OptionalFeatures(object):
    def __init__(self, conn, scenario_id):
        """
        :param cursor:
        :param scenario_id: 
        """
        of_column_names = [
            n for n in get_scenario_table_columns(conn=conn)
            if n.startswith("of_")
        ]

        for of in of_column_names:
            setattr(
                self,
                of.upper(),
                db_column_to_self(
                    column=of, conn=conn, scenario_id=scenario_id
                )
            )

    def get_all_available_features(self):
        all_features = [
            attr[3:].lower() for attr, value in self.__dict__.items()
        ]

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
            n for n in get_scenario_table_columns(conn=conn)
            if n.endswith("_scenario_id")
        ]

        for subscenario in subscenario_column_names:
            setattr(
                self,
                subscenario.upper(),
                db_column_to_self(
                    column=subscenario, conn=conn, scenario_id=scenario_id
                )
            )

    def get_all_available_subscenarios(self):
        all_subscenarios = [
            attr.lower() for attr, value in self.__dict__.items()
            if attr != "SCENARIO_ID"
        ]

        return all_subscenarios


class ScenarioSubproblemStructure(object):
    def __init__(self, all_subproblems, stages_by_subproblem):
        # List of subproblems
        self.ALL_SUBPROBLEMS = all_subproblems
        # List of stages by subproblem in dict {subproblem: [stages]}
        self.STAGES_BY_SUBPROBLEM = stages_by_subproblem


def get_subproblem_structure_from_db(conn, scenario_id):
    """

    :param conn:
    :param scenario_id:
    """
    cursor = conn.cursor()

    # TODO: make sure there is data integrity between subproblems_stages
    #   and inputs_temporal_horizons and inputs_temporal
    all_subproblems = [
        subproblem[0] for subproblem in
        cursor.execute(
            """SELECT subproblem_id
               FROM inputs_temporal_subproblems
               INNER JOIN scenarios
               USING (temporal_scenario_id)
               WHERE scenario_id = {};""".format(scenario_id)
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
               AND subproblem_id = {};""".format(scenario_id, s)
        ).fetchall()
        stages = [stage[0] for stage in stages]  # convert to simple list
        stages_by_subproblem[s] = stages

    return ScenarioSubproblemStructure(
        all_subproblems=all_subproblems,
        stages_by_subproblem=stages_by_subproblem
    )


def get_subproblem_structure_from_disk(scenario_directory):
    # Check if there are subproblem directories
    all_subproblems = \
        check_for_integer_subdirectories(scenario_directory)

    # Make dictionary for the stages by subproblem, starting with empty
    # list for each subproblem
    stages_by_subproblem = {
        subp: [] for subp in all_subproblems
    }

    # If we have subproblems, check for stage subdirectories for each
    # subproblem directory
    if all_subproblems:
        for subproblem in all_subproblems:
            subproblem_dir = os.path.join(
                scenario_directory, subproblem
            )
            stages = check_for_integer_subdirectories(subproblem_dir)
            # TODO: how to deal with pass-through inputs
            # If the list isn't empty, update the stage dictionary and
            # create the stage pass-through directory and input file
            # TODO: we probably don't need a directory for the
            #  pass-through inputs, as it's only one file
            if stages:
                stages_by_subproblem[subproblem] = stages
                # Create the commitment pass-through file (also deletes any
                # prior results)
                # First create the pass-through directory if it doesn't
                # exist
                # TODO: need better handling of deleting prior results?
                pass_through_directory = \
                    os.path.join(subproblem_dir, "pass_through_inputs")
                if not os.path.exists(pass_through_directory):
                    os.makedirs(pass_through_directory)
                with open(
                        os.path.join(
                            pass_through_directory,
                            "fixed_commitment.tab"
                        ), "w", newline=""
                ) as fixed_commitment_file:
                    fixed_commitment_writer = csv.writer(
                        fixed_commitment_file,
                        delimiter="\t", lineterminator="\n"
                    )
                    fixed_commitment_writer.writerow(
                        ["project", "timepoint", "stage",
                         "final_commitment_stage", "commitment"])

    return ScenarioSubproblemStructure(
        all_subproblems=all_subproblems,
        stages_by_subproblem=stages_by_subproblem
    )


class SolverOptions(object):
    def __init__(self, conn, scenario_id):
        """
        :param cursor:
        :param scenario_id:
        """
        cursor = conn.cursor()

        self.SOLVER_OPTIONS_ID = cursor.execute("""
            SELECT solver_options_id 
            FROM scenarios 
            WHERE scenario_id = {}
            """.format(scenario_id)
        ).fetchone()[0]

        if self.SOLVER_OPTIONS_ID is None:
            self.SOLVER = None
        else:
            distinct_solvers = cursor.execute(
                """SELECT DISTINCT solver 
                FROM inputs_options_solver 
                WHERE solver_options_id = {}""".format(self.SOLVER_OPTIONS_ID)
            ).fetchall()
            if len(distinct_solvers) > 1:
                raise ValueError("""
                ERROR: Solver options include more than one solver! Only a 
                single solver must be specified for solver_options_id in the 
                inputs_options_solver table. See solver_options_id {}. 
                """.format(self.SOLVER_OPTIONS_ID))
            else:
                self.SOLVER = distinct_solvers[0][0]

        self.SOLVER_OPTIONS = \
            None if self.SOLVER_OPTIONS_ID is None \
            else {
                row[0]: row[1]
                for row in cursor.execute("""
                    SELECT solver_option_name, solver_option_value
                    FROM inputs_options_solver
                    WHERE solver_options_id = {};
                    """.format(self.SOLVER_OPTIONS_ID)
                ).fetchall() if row[0] is not None and row[0] != ""
            }


def db_column_to_self(column, conn, scenario_id):
    of = True if column.startswith("of") else False
    c = conn.cursor()
    query = c.execute(
        """SELECT {}
           FROM scenarios
           WHERE scenario_id = ?;""".format(column),
        (scenario_id,)
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
    column_names = [
        description[0] for description in scenario_query.description
    ]

    return column_names
