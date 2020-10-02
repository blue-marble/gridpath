#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Scenario characteristics in database
"""

from builtins import object


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

    def determine_active_features(self):
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
        self.SCENARIO_ID = scenario_id

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
            if attr is not "SCENARIO_ID"
        ]

        return all_subscenarios

    @staticmethod
    def determine_subscenarios_by_feature(conn):
        """

        :param cursor:
        :return:
        """
        c = conn.cursor()

        feature_sc = c.execute(
            """SELECT feature, subscenario_id
            FROM mod_feature_subscenarios"""
        ).fetchall()
        feature_sc_dict = {}
        for f, sc in feature_sc:
            if f in feature_sc_dict:
                feature_sc_dict[f].append(sc.upper())
            else:
                feature_sc_dict[f] = [sc.upper()]
        return feature_sc_dict

    # TODO: refactor this in capacity_types/__init__? (similar functions are
    #   used in prm_types/operational_types etc.
    def get_required_capacity_type_modules(self, c):
        """
        Get the required capacity type submodules based on the database inputs
        for the specified scenario_id. Required modules are the unique set of
        generator capacity types in the scenario's portfolio. Get the list based
        on the project_operational_chars_scenario_id of the scenario_id.

        This list will be used to know for which capacity type submodules we
        should validate inputs, get inputs from database , or save results to
        database. It is also used to figure out which suscenario_ids are required
        inputs (e.g. cost inputs are required when there are new build resources)

        Note: once we have determined the dynamic components, this information
        will also be stored in the DynamicComponents class object.

        :param c: database cursor
        :return: List of the required capacity type submodules
        """

        project_portfolio_scenario_id = c.execute(
            """SELECT project_portfolio_scenario_id 
            FROM scenarios 
            WHERE scenario_id = {}""".format(self.SCENARIO_ID)
        ).fetchone()[0]

        required_capacity_type_modules = [
            p[0] for p in c.execute(
                """SELECT DISTINCT capacity_type 
                FROM inputs_project_portfolios
                WHERE project_portfolio_scenario_id = {}""".format(
                    project_portfolio_scenario_id
                )
            ).fetchall()
        ]

        return required_capacity_type_modules


class SubProblems(object):
    def __init__(self, conn, scenario_id):
        """

        :param conn:
        :param scenario_id:
        """
        cursor = conn.cursor()

        # TODO: make sure there is data integrity between subproblems_stages
        #   and inputs_temporal_horizons and inputs_temporal
        subproblems = cursor.execute(
            """SELECT subproblem_id
               FROM inputs_temporal_subproblems
               INNER JOIN scenarios
               USING (temporal_scenario_id)
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchall()
        # SQL returns a list of tuples [(1,), (2,)] so convert to simple list
        self.SUBPROBLEMS = [subproblem[0] for subproblem in subproblems]

        # store subproblems and stages in dict {subproblem: [stages]}
        self.SUBPROBLEM_STAGE_DICT = {}
        for s in self.SUBPROBLEMS:
            stages = cursor.execute(
                """SELECT stage_id
                   FROM inputs_temporal_subproblems_stages
                   INNER JOIN scenarios
                   USING (temporal_scenario_id)
                   WHERE scenario_id = {}
                   AND subproblem_id = {};""".format(scenario_id, s)
            ).fetchall()
            stages = [stage[0] for stage in stages]  # convert to simple list
            self.SUBPROBLEM_STAGE_DICT[s] = stages


class SolverOptions(object):
    def __init__(self, conn, scenario_id):
        """
        :param cursor:
        :param scenario_id:
        """
        cursor = conn.cursor()

        self.SCENARIO_ID = scenario_id
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
                ).fetchall() if row[0] is not None and row[0] is not ""
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
