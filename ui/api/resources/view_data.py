# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

from ui.api.common_functions import connect_to_database


# TODO: add the subscenario names (not just IDs) to the inputs tables --
#  this will make it easier to show the right information to the user
#  without having to resort to JOINS

class ViewDataTemporalTimepoints(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='temporal',
            ui_row_name_in_db='temporal'
        )


class ViewDataGeographyLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_zones',
            ui_row_name_in_db='load_zones'
        )


class ViewDataProjectLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_zones',
            ui_row_name_in_db='project_load_zones'
        )


class ViewDataTransmissionLoadZones(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_zones',
            ui_row_name_in_db='transmission_load_zones'
        )


class ViewDataSystemLoad(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='system_load',
            ui_row_name_in_db='system_load'
        )


class ViewDataProjectPortfolio(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity',
            ui_row_name_in_db='portfolio'
        )


class ViewDataProjectExistingCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity',
            ui_row_name_in_db='specified_capacity'
        )


class ViewDataProjectExistingFixedCost(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity',
            ui_row_name_in_db='specified_fixed_cost'
        )


class ViewDataProjectNewPotential(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity',
            ui_row_name_in_db='new_potential'
        )


class ViewDataProjectNewCost(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity',
            ui_row_name_in_db='new_cost'
        )


class ViewDataProjectAvailability(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_capacity',
            ui_row_name_in_db='availability'
        )


class ViewDataProjectOpChar(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='project_opchar',
            ui_row_name_in_db='opchar'
        )


class ViewDataFuels(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='fuels',
            ui_row_name_in_db='fuels'
        )


class ViewDataFuelPrices(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='fuels',
            ui_row_name_in_db='fuel_prices'
        )


class ViewDataTransmissionPortfolio(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_capacity',
            ui_row_name_in_db='portfolio'
        )


class ViewDataTransmissionExistingCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_capacity',
            ui_row_name_in_db='specified_capacity'
        )


class ViewDataTransmissionOpChar(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_opchar',
            ui_row_name_in_db='opchar'
        )


class ViewDataTransmissionHurdleRates(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_hurdle_rates',
            ui_row_name_in_db='hurdle_rates'
        )


class ViewDataTransmissionSimFlowLimits(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_sim_flow_limits',
            ui_row_name_in_db='limits'
        )


class ViewDataTransmissionSimFlowLimitsLineGroups(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='transmission_sim_flow_limits',
            ui_row_name_in_db='groups'
        )


class ViewDataLFUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_up',
            ui_row_name_in_db='bas'
        )


class ViewDataProjectLFUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_up',
            ui_row_name_in_db='projects'
        )


class ViewDataLFUpReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_up',
            ui_row_name_in_db='req'
        )


class ViewDataLFDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_down',
            ui_row_name_in_db='bas'
        )


class ViewDataProjectLFDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_down',
            ui_row_name_in_db='projects'
        )


class ViewDataLFDownReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='load_following_down',
            ui_row_name_in_db='req'
        )


class ViewDataRegUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_up',
            ui_row_name_in_db='bas'
        )


class ViewDataProjectRegUpBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_up',
            ui_row_name_in_db='projects'
        )


class ViewDataRegUpReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_up',
            ui_row_name_in_db='req'
        )


class ViewDataRegDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_down',
            ui_row_name_in_db='bas'
        )


class ViewDataProjectRegDownBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_down',
            ui_row_name_in_db='projects'
        )


class ViewDataRegDownReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='regulation_down',
            ui_row_name_in_db='req'
        )


class ViewDataSpinBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='spinning_reserves',
            ui_row_name_in_db='bas'
        )


class ViewDataProjectSpinBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='spinning_reserves',
            ui_row_name_in_db='projects'
        )


class ViewDataSpinReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='spinning_reserves',
            ui_row_name_in_db='req'
        )


class ViewDataFreqRespBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='frequency_response',
            ui_row_name_in_db='bas'
        )


class ViewDataProjectFreqRespBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='frequency_response',
            ui_row_name_in_db='projects'
        )


class ViewDataFreqRespReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='frequency_response',
            ui_row_name_in_db='bas'
        )


class ViewDataRPSBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='rps',
            ui_row_name_in_db='bas'
        )


class ViewDataProjectRPSBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='rps',
            ui_row_name_in_db='projects'
        )


class ViewDataRPSReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='rps',
            ui_row_name_in_db='req'
        )


class ViewDataCarbonCapBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='carbon_cap',
            ui_row_name_in_db='bas'
        )


class ViewDataProjectCarbonCapBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='carbon_cap',
            ui_row_name_in_db='projects'
        )


class ViewDataTransmissionCarbonCapBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='carbon_cap',
            ui_row_name_in_db='transmission'
        )


class ViewDataCarbonCapReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='carbon_cap',
            ui_row_name_in_db='req'
        )


class ViewDataPRMBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm',
            ui_row_name_in_db='bas'
        )


class ViewDataProjectPRMBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm',
            ui_row_name_in_db='projects'
        )


class ViewDataPRMReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm',
            ui_row_name_in_db='req'
        )


class ViewDataProjectELCCChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm',
            ui_row_name_in_db='project_elcc'
        )


class ViewDataELCCSurface(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm',
            ui_row_name_in_db='elcc'
        )


class ViewDataEnergyOnly(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='prm',
            ui_row_name_in_db='energy_only'
        )


class ViewDataLocalCapacityBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='local_capacity',
            ui_row_name_in_db='bas'
        )


class ViewDataProjectLocalCapacityBAs(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='local_capacity',
            ui_row_name_in_db='projects'
        )


class ViewDataLocalCapacityReq(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='local_capacity',
            ui_row_name_in_db='req'
        )


class ViewDataProjectLocalCapacityChars(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """

        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='local_capacity',
            ui_row_name_in_db='project_chars'
        )


class ViewDataTuning(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ui_table_name_in_db='tuning',
            ui_row_name_in_db='tuning'
        )


def create_data_table_api(db_path, ui_table_name_in_db, ui_row_name_in_db):
    """
    :param db_path:
    :param ui_table_name_in_db:
    :param ui_row_name_in_db:
    :return:
    """
    io, c = connect_to_database(db_path=db_path)

    data_table_api = dict()
    data_table_api['ngIfKey'] = ui_table_name_in_db + '-' + ui_row_name_in_db

    row_metadata = c.execute(
      """SELECT ui_row_caption, ui_row_db_input_table
      FROM ui_scenario_detail_table_row_metadata
      WHERE ui_table = '{}' AND ui_table_row = '{}'""".format(
        ui_table_name_in_db, ui_row_name_in_db
      )
    ).fetchone()


    data_table_api['caption'] = row_metadata[0]
    input_table = row_metadata[1]

    column_names, data_rows = get_table_data(c=c,
                                             input_table=input_table)
    data_table_api['columns'] = column_names
    data_table_api['rowsData'] = data_rows

    return data_table_api


def get_table_data(c, input_table):
    """
    :param db_path:
    :param input_table:
    :return:
    """
    table_data_query = c.execute("""SELECT * FROM {};""".format(input_table))

    column_names = [s[0] for s in table_data_query.description]

    rows_data = []
    for row in table_data_query.fetchall():
        row_values = list(row)
        row_dict = dict(zip(column_names, row_values))
        rows_data.append(row_dict)

    return column_names, rows_data
