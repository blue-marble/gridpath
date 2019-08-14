# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

from ui.api.common_functions import connect_to_database


# ### API: Scenario Detail ### #
class ScenarioDetailAll(Resource):
    """
    All selections for a scenario.
    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        io, c = connect_to_database(db_path=self.db_path)
        scenario_detail_query = c.execute(
          "SELECT * "
          "FROM scenarios_view "
          "WHERE scenario_id = {}".format(scenario_id)
        )

        column_names = [s[0] for s in scenario_detail_query.description]
        column_values = list(list(scenario_detail_query)[0])
        scenario_detail_api = dict(zip(column_names, column_values))

        return scenario_detail_api


class ScenarioDetailName(Resource):
    """
    The name of the a scenario by scenario ID
    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        io, c = connect_to_database(db_path=self.db_path)
        scenario_name = c.execute(
          "SELECT scenario_name "
          "FROM scenarios "
          "WHERE scenario_id = {}".format(scenario_id)
        ).fetchone()[0]

        return scenario_name


class ScenarioDetailFeatures(Resource):
    """
    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            ui_table_name_in_db="features"
        )

        return scenario_detail_api


class ScenarioDetailTemporal(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            ui_table_name_in_db='temporal'
        )

        return scenario_detail_api


class ScenarioDetailGeographyLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            ui_table_name_in_db='load_zones'
        )

        return scenario_detail_api


class ScenarioDetailLoad(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            ui_table_name_in_db='system_load'
        )

        return scenario_detail_api


class ScenarioDetailProjectCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            ui_table_name_in_db='project_capacity'
        )

        return scenario_detail_api


class ScenarioDetailProjectOpChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            ui_table_name_in_db='project_opchar'
        )

        return scenario_detail_api


class ScenarioDetailFuels(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            ui_table_name_in_db='fuels'
        )

        return scenario_detail_api


class ScenarioDetailTransmissionCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            ui_table_name_in_db='transmission_capacity'
        )

        return scenario_detail_api


class ScenarioDetailTransmissionOpChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            ui_table_name_in_db='transmission_opchar'
        )

        return scenario_detail_api


class ScenarioDetailTransmissionHurdleRates(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
          db_path=self.db_path,
          scenario_id=scenario_id,
          ui_table_name_in_db='transmission_hurdle_rates'
        )

        return scenario_detail_api


class ScenarioDetailTransmissionSimFlow(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
          db_path=self.db_path,
          scenario_id=scenario_id,
          ui_table_name_in_db='transmission_sim_flow_limits'
        )

        return scenario_detail_api


class ScenarioDetailLoadFollowingUp(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
          db_path=self.db_path,
          scenario_id=scenario_id,
          ui_table_name_in_db='load_following_up'
        )

        return scenario_detail_api


class ScenarioDetailLoadFollowingDown(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
          db_path=self.db_path,
          scenario_id=scenario_id,
          ui_table_name_in_db='load_following_down'
        )

        return scenario_detail_api


class ScenarioDetailRegulationUp(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
          db_path=self.db_path,
          scenario_id=scenario_id,
          ui_table_name_in_db='regulation_up'
        )

        return scenario_detail_api


class ScenarioDetailRegulationDown(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
          db_path=self.db_path,
          scenario_id=scenario_id,
          ui_table_name_in_db='regulation_down'
        )

        return scenario_detail_api


class ScenarioDetailSpinningReserves(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
          db_path=self.db_path,
          scenario_id=scenario_id,
          ui_table_name_in_db='spinning_reserves'
        )

        return scenario_detail_api


class ScenarioDetailFrequencyResponse(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
          db_path=self.db_path,
          scenario_id=scenario_id,
          ui_table_name_in_db='frequency_response'
        )

        return scenario_detail_api


class ScenarioDetailRPS(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
          db_path=self.db_path,
          scenario_id=scenario_id,
          ui_table_name_in_db='rps'
        )

        return scenario_detail_api


class ScenarioDetailCarbonCap(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
          db_path=self.db_path,
          scenario_id=scenario_id,
          ui_table_name_in_db='carbon_cap'
        )

        return scenario_detail_api


class ScenarioDetailPRM(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
          db_path=self.db_path,
          scenario_id=scenario_id,
          ui_table_name_in_db='prm'
        )

        return scenario_detail_api


class ScenarioDetailLocalCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
            db_path=self.db_path,
            scenario_id=scenario_id,
            ui_table_name_in_db='local_capacity'
        )

        return scenario_detail_api


class ScenarioDetailTuning(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        scenario_detail_api = get_scenario_detail(
          db_path=self.db_path,
          scenario_id=scenario_id,
          ui_table_name_in_db='tuning'
        )

        return scenario_detail_api


def get_scenario_detail(db_path, scenario_id, ui_table_name_in_db):
    """
    :param db_path: the path to the database
    :param scenario_id: integer, the scenario ID
    :param ui_table_name_in_db:
    :return:


    """
    io, c = connect_to_database(db_path=db_path)

    # Get and set the table caption for this table
    table_caption = c.execute(
      """SELECT ui_table, ui_table_caption 
      FROM ui_scenario_detail_table_metadata
      WHERE ui_table = '{}';""".format(ui_table_name_in_db)
    ).fetchone()

    scenario_detail_api = dict()
    scenario_detail_api["uiTableNameInDB"] = table_caption[0]
    scenario_detail_api["scenarioDetailTableCaption"] = table_caption[1]

    # Get the metadata and value for the rows
    scenario_detail_api["scenarioDetailTableRows"] = list()

    row_metadata = c.execute(
      """SELECT ui_table_row, ui_row_caption, ui_row_db_scenarios_view_column, 
      ui_row_db_input_table 
      FROM ui_scenario_detail_table_row_metadata
      WHERE ui_table = '{}'""".format(ui_table_name_in_db)
    ).fetchall()

    for row in row_metadata:
        row_value = c.execute(
          """SELECT {}
            FROM scenarios_view
            WHERE scenario_id = {}""".format(row[2], scenario_id)
        ).fetchone()[0]

        scenario_detail_api["scenarioDetailTableRows"].append({
            'uiRowNameInDB': row[0],
            'rowCaption': row[1],
            'rowValue': row_value,
            'inputTable':  row[3]
        })

    return scenario_detail_api
