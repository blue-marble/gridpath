# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

from db.common_functions import connect_to_database


class ServerStatus(Resource):
    """
    Server status; response will be 'running'; if HTTP error is caught,
    server status will be set to 'down'
    """

    @staticmethod
    def get():
        return 'running'


class ScenarioRunStatus(Resource):
    """
    Number of scenarios by run status type.
    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        conn = connect_to_database(db_path=self.db_path)
        c = conn.cursor()

        run_status_api = c.execute("""
            SELECT run_status_name, COUNT(run_status_id)
            FROM scenarios
            JOIN mod_run_status_types
              USING (run_status_id)
            GROUP BY run_status_name
        """).fetchall()

        return run_status_api


class ScenarioValidationStatus(Resource):
    """
    Number of scenarios by validation status type.
    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        conn = connect_to_database(db_path=self.db_path)
        c = conn.cursor()

        validation_status_api = c.execute("""
                SELECT validation_status_name, COUNT(validation_status_id)
                FROM scenarios
                JOIN mod_validation_status_types
                  USING (validation_status_id)
                GROUP BY validation_status_name
            """).fetchall()

        return validation_status_api
