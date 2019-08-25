# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

from ui.server.common_functions import connect_to_database


# TODO: add the subscenario names (not just IDs) to the inputs tables --
#  this will make it easier to show the right information to the user
#  without having to resort to JOINS

class ViewDataTemporalTimepoints(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='temporal',
            ui_row_name_in_db='temporal',
            scenario_id=scenario_id
        )


class ViewDataGeographyLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_zones',
            ui_row_name_in_db='load_zones',
            scenario_id=scenario_id
        )


class ViewDataProjectLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_zones',
            ui_row_name_in_db='project_load_zones',
            scenario_id=scenario_id
        )


class ViewDataTransmissionLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_zones',
            ui_row_name_in_db='transmission_load_zones',
            scenario_id=scenario_id
        )


class ViewDataSystemLoad(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='system_load',
            ui_row_name_in_db='system_load',
            scenario_id=scenario_id
        )


class ViewDataProjectPortfolio(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity',
            ui_row_name_in_db='portfolio',
            scenario_id=scenario_id
        )


class ViewDataProjectExistingCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity',
            ui_row_name_in_db='specified_capacity',
            scenario_id=scenario_id
        )


class ViewDataProjectExistingFixedCost(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity',
            ui_row_name_in_db='specified_fixed_cost',
            scenario_id=scenario_id
        )


class ViewDataProjectNewPotential(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity',
            ui_row_name_in_db='new_potential',
            scenario_id=scenario_id
        )


class ViewDataProjectNewCost(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity',
            ui_row_name_in_db='new_cost',
            scenario_id=scenario_id
        )


class ViewDataProjectAvailability(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity',
            ui_row_name_in_db='availability',
            scenario_id=scenario_id
        )


class ViewDataProjectOpChar(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_opchar',
            ui_row_name_in_db='opchar',
            scenario_id=scenario_id
        )


class ViewDataFuels(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='fuels',
            ui_row_name_in_db='fuels',
            scenario_id=scenario_id
        )


class ViewDataFuelPrices(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='fuels',
            ui_row_name_in_db='fuel_prices',
            scenario_id=scenario_id
        )


class ViewDataTransmissionPortfolio(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_capacity',
            ui_row_name_in_db='portfolio',
            scenario_id=scenario_id
        )


class ViewDataTransmissionExistingCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_capacity',
            ui_row_name_in_db='specified_capacity',
            scenario_id=scenario_id
        )


class ViewDataTransmissionOpChar(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_opchar',
            ui_row_name_in_db='opchar',
            scenario_id=scenario_id
        )


class ViewDataTransmissionHurdleRates(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_hurdle_rates',
            ui_row_name_in_db='hurdle_rates',
            scenario_id=scenario_id
        )


class ViewDataTransmissionSimFlowLimits(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_sim_flow_limits',
            ui_row_name_in_db='limits',
            scenario_id=scenario_id
        )


class ViewDataTransmissionSimFlowLimitsLineGroups(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_sim_flow_limits',
            ui_row_name_in_db='groups',
            scenario_id=scenario_id
        )


class ViewDataLFUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_up',
            ui_row_name_in_db='bas',
            scenario_id=scenario_id
        )


class ViewDataProjectLFUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_up',
            ui_row_name_in_db='projects',
            scenario_id=scenario_id
        )


class ViewDataLFUpReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_up',
            ui_row_name_in_db='req',
            scenario_id=scenario_id
        )


class ViewDataLFDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_down',
            ui_row_name_in_db='bas',
            scenario_id=scenario_id
        )


class ViewDataProjectLFDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_down',
            ui_row_name_in_db='projects',
            scenario_id=scenario_id
        )


class ViewDataLFDownReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_down',
            ui_row_name_in_db='req',
            scenario_id=scenario_id
        )


class ViewDataRegUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_up',
            ui_row_name_in_db='bas',
            scenario_id=scenario_id
        )


class ViewDataProjectRegUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_up',
            ui_row_name_in_db='projects',
            scenario_id=scenario_id
        )


class ViewDataRegUpReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_up',
            ui_row_name_in_db='req',
            scenario_id=scenario_id
        )


class ViewDataRegDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_down',
            ui_row_name_in_db='bas',
            scenario_id=scenario_id
        )


class ViewDataProjectRegDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_down',
            ui_row_name_in_db='projects',
            scenario_id=scenario_id
        )


class ViewDataRegDownReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_down',
            ui_row_name_in_db='req',
            scenario_id=scenario_id
        )


class ViewDataSpinBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='spinning_reserves',
            ui_row_name_in_db='bas',
            scenario_id=scenario_id
        )


class ViewDataProjectSpinBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='spinning_reserves',
            ui_row_name_in_db='projects',
            scenario_id=scenario_id
        )


class ViewDataSpinReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='spinning_reserves',
            ui_row_name_in_db='req',
            scenario_id=scenario_id
        )


class ViewDataFreqRespBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='frequency_response',
            ui_row_name_in_db='bas',
            scenario_id=scenario_id
        )


class ViewDataProjectFreqRespBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='frequency_response',
            ui_row_name_in_db='projects',
            scenario_id=scenario_id
        )


class ViewDataFreqRespReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='frequency_response',
            ui_row_name_in_db='bas',
            scenario_id=scenario_id
        )


class ViewDataRPSBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='rps',
            ui_row_name_in_db='bas',
            scenario_id=scenario_id
        )


class ViewDataProjectRPSBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='rps',
            ui_row_name_in_db='projects',
            scenario_id=scenario_id
        )


class ViewDataRPSReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='rps',
            ui_row_name_in_db='req',
            scenario_id=scenario_id
        )


class ViewDataCarbonCapBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='carbon_cap',
            ui_row_name_in_db='bas',
            scenario_id=scenario_id
        )


class ViewDataProjectCarbonCapBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='carbon_cap',
            ui_row_name_in_db='projects',
            scenario_id=scenario_id
        )


class ViewDataTransmissionCarbonCapBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='carbon_cap',
            ui_row_name_in_db='transmission',
            scenario_id=scenario_id
        )


class ViewDataCarbonCapReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='carbon_cap',
            ui_row_name_in_db='req',
            scenario_id=scenario_id
        )


class ViewDataPRMBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm',
            ui_row_name_in_db='bas',
            scenario_id=scenario_id
        )


class ViewDataProjectPRMBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm',
            ui_row_name_in_db='projects',
            scenario_id=scenario_id
        )


class ViewDataPRMReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm',
            ui_row_name_in_db='req',
            scenario_id=scenario_id
        )


class ViewDataProjectELCCChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm',
            ui_row_name_in_db='project_elcc',
            scenario_id=scenario_id
        )


class ViewDataELCCSurface(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm',
            ui_row_name_in_db='elcc',
            scenario_id=scenario_id
        )


class ViewDataEnergyOnly(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm',
            ui_row_name_in_db='energy_only',
            scenario_id=scenario_id
        )


class ViewDataLocalCapacityBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='local_capacity',
            ui_row_name_in_db='bas',
            scenario_id=scenario_id
        )


class ViewDataProjectLocalCapacityBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='local_capacity',
            ui_row_name_in_db='projects',
            scenario_id=scenario_id
        )


class ViewDataLocalCapacityReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='local_capacity',
            ui_row_name_in_db='req',
            scenario_id=scenario_id
        )


class ViewDataProjectLocalCapacityChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='local_capacity',
            ui_row_name_in_db='project_chars',
            scenario_id=scenario_id
        )


class ViewDataTuning(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='tuning',
            ui_row_name_in_db='tuning',
            scenario_id=scenario_id
        )


class ViewDataValidation(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        io, c = connect_to_database(db_path=self.db_path)

        scenario_name = c.execute(
          "SELECT scenario_name "
          "FROM scenarios "
          "WHERE scenario_id = {};".format(scenario_id)
        ).fetchone()[0]
        data_table_api = dict()
        data_table_api['ngIfKey'] = "validation"
        data_table_api['caption'] = "{} Validation Errors".format(
          scenario_name)

        column_names, data_rows = get_table_data(
          c=c, input_table='mod_input_validation',
          subscenario_id_column=None, subscenario_id='all',
        )
        data_table_api['columns'] = column_names
        data_table_api['rowsData'] = data_rows

        return data_table_api


def create_data_table_api(
  db_path, ui_table_name_in_db, ui_row_name_in_db, scenario_id
):
    """
    :param db_path:
    :param ui_table_name_in_db:
    :param ui_row_name_in_db:
    :param scenario_id:
    :return:
    """
    # Convert scenario_id to integer, as it's passed as string
    scenario_id = int(scenario_id)

    # Connect to database
    io, c = connect_to_database(db_path=db_path)

    # Make the data table API
    data_table_api = dict()
    data_table_api['ngIfKey'] = ui_table_name_in_db + '-' + ui_row_name_in_db

    row_metadata = c.execute(
      """SELECT ui_row_caption, ui_row_db_input_table, 
      ui_row_db_subscenario_table_id_column
      FROM ui_scenario_detail_table_row_metadata
      WHERE ui_table = '{}' AND ui_table_row = '{}'""".format(
        ui_table_name_in_db, ui_row_name_in_db
      )
    ).fetchone()

    data_table_api['caption'] = row_metadata[0]
    input_table = row_metadata[1]
    subscenario_id_column = row_metadata[2]

    # Get the subscenario_id for the scenario
    if scenario_id == 0:
        subscenario_id = "all"
    else:
        subscenario_id = c.execute(
          """SELECT {} FROM scenarios WHERE scenario_id = {}""".format(
            subscenario_id_column, scenario_id
          )
        ).fetchone()[0]

    column_names, data_rows = get_table_data(
      c=c,
      input_table=input_table,
      subscenario_id_column=subscenario_id_column,
      subscenario_id=subscenario_id
    )
    data_table_api['columns'] = column_names
    data_table_api['rowsData'] = data_rows

    return data_table_api


def get_table_data(c, input_table, subscenario_id_column, subscenario_id):
    """
    :param c:
    :param input_table:
    :param subscenario_id_column:
    :param subscenario_id:
    :return:
    """
    if subscenario_id == "all":
        query_where = ""
    else:
        query_where = " WHERE {} = {}".format(
          subscenario_id_column, subscenario_id
        )
    table_data_query = c.execute(
      """SELECT * FROM {}{};""".format(input_table, query_where)
    )

    column_names = [s[0] for s in table_data_query.description]

    rows_data = []
    for row in table_data_query.fetchall():
        row_values = list(row)
        row_dict = dict(zip(column_names, row_values))
        rows_data.append(row_dict)

    return column_names, rows_data
