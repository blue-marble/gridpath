# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

# ### API: New Scenario Settings ### #

# TODO: need to require setting 'name' column to be unique
# TODO: figure out how to deal with tables with two (or more) subscenario IDs
from ui.api.common_functions import connect_to_database


class ScenarioNewTemporal(Resource):
    """

    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='temporal'
        )
        return setting_options_api


class ScenarioNewLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_zones'
        )
        return setting_options_api


class ScenarioNewLoad(Resource):
    """

    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='system_load'
        )
        return setting_options_api


class ScenarioNewProjectCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
      self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity'
        )
        return setting_options_api


class ScenarioNewProjectOpChar(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_opchar'
        )
        return setting_options_api


class ScenarioNewFuels(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='fuels'
        )
        return setting_options_api


class ScenarioNewTransmissionCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_capacity'
        )
        return setting_options_api


class ScenarioNewTransmissionOpChar(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_opchar'
        )
        return setting_options_api


class ScenarioNewTransmissionHurdleRates(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_hurdle_rates'
        )
        return setting_options_api


class ScenarioNewTransmissionSimFlowLimits(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_sim_flow_limits'
        )
        return setting_options_api


class ScenarioNewLFReservesUp(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_up'
        )
        return setting_options_api


class ScenarioNewLFReservesDown(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_down'
        )
        return setting_options_api


class ScenarioNewRegulationUp(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_up'
        )
        return setting_options_api


class ScenarioNewRegulationDown(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_down'
        )
        return setting_options_api


class ScenarioNewSpinningReserves(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='spinning_reserves'
        )
        return setting_options_api


class ScenarioNewFrequencyResponse(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='frequency_response'
        )
        return setting_options_api


class ScenarioNewRPS(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='rps'
        )
        return setting_options_api


class ScenarioNewCarbonCap(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='carbon_cap'
        )
        return setting_options_api


class ScenarioNewPRM(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm'
        )
        return setting_options_api


class ScenarioNewLocalCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        setting_options_api = create_scenario_new_api(
            db_path=self.db_path,
            ui_table_name_in_db='local_capacity'
        )
        return setting_options_api


# TODO: add tuning
class SettingTuning(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        pass


def create_scenario_new_api(db_path, ui_table_name_in_db):
    """
    :param db_path: the path to the database file
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

    scenario_new_api = {
      "uiTableNameInDB": table_caption[0],
      "tableCaption": table_caption[1],
      "settingRows": []
    }

    row_metadata = c.execute(
      """SELECT ui_table_row, 
      ui_row_caption, ui_row_db_subscenario_table_id_column, 
      ui_row_db_subscenario_table
      FROM ui_scenario_detail_table_row_metadata
      WHERE ui_table = '{}';""".format(
        ui_table_name_in_db
      )
    ).fetchall()

    for row in row_metadata:
        print(row)
        ui_row_name_in_db = row[0]
        row_caption = row[1]
        row_subscenario_id = row[2]
        row_subscenario_table = row[3]

        setting_options_query = c.execute(
            """SELECT {}, name FROM {};""".format(
              row_subscenario_id, row_subscenario_table
            )
        ).fetchall()

        settings = []
        for setting in setting_options_query:
            settings.append(
                {'id': setting[0], 'name': setting[1]}
            )

        scenario_new_api["settingRows"].append({
          "uiRowNameInDB": ui_row_name_in_db,
          "rowName": row_caption,
          "rowFormControlName": row_subscenario_id,
          "settingOptions": settings
        })

    return scenario_new_api
