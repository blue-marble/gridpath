# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

from db.common_functions import connect_to_database


# ### API: Scenarios List ### #
class Scenarios(Resource):
    """
    The list of scenarios.
    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        io, c = connect_to_database(self.db_path)

        scenarios_query = c.execute(
            """SELECT scenario_id, scenario_name, validation_status, run_status
            FROM scenarios_view
            ORDER by scenario_id ASC;"""
        )

        scenarios_api = []
        for s in scenarios_query:
            # TODO: make this more robust than relying on column order
            scenarios_api.append(
                {'id': s[0], 'name': s[1], 'validationStatus': s[2],
                 'runStatus': s[3]}
            )

        return scenarios_api
