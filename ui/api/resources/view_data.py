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
            ngifkey='geography_load_zones',
            caption='Load Zones',
            table='inputs_geography_load_zones'
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
            ngifkey='project_load_zones',
            caption='Project Load Zones',
            table='inputs_project_load_zones'
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
            ngifkey='transmission_load_zones',
            caption='Transmission Load Zones',
            table='inputs_transmission_load_zones'
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
            ngifkey='load_profile',
            caption='System Load',
            table='inputs_system_load'
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
            ngifkey='project_portfolio',
            caption='Project Portfolio',
            table='inputs_project_portfolios'
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
            ngifkey='project_existing_capacity',
            caption='Project Specified Capacity',
            table='inputs_project_existing_capacity'
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
            ngifkey='project_existing_fixed_cost',
            caption='Project Specified Fixed Cost',
            table='inputs_project_existing_fixed_cost'
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
            ngifkey='project_new_potential',
            caption='Project New Potential',
            table='inputs_project_new_potential'
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
            ngifkey='project_new_cost',
            caption='Project New Costs',
            table='inputs_project_new_cost'
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
            ngifkey='project_availability',
            caption='Project Availability',
            table='inputs_project_availability'
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
            ngifkey='project_operating_chars',
            caption='Project Operational Characteristics',
            table='inputs_project_operational_chars'
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
            ngifkey='project_fuels',
            caption='Fuels',
            table='inputs_project_fuels'
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
            ngifkey='fuel_prices',
            caption='Fuel Prices',
            table='inputs_project_fuel_prices'
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
            ngifkey='transmission_portfolio',
            caption='Transmission',
            table='inputs_transmission_portfolios'
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
            ngifkey='transmission_existing_capacity',
            caption='Transmission Specified Capacity',
            table='inputs_transmission_existing_capacity'
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
            ngifkey='transmission_operational_chars',
            caption='Transmission Operational Characteristics',
            table='inputs_transmission_operational_chars'
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
            ngifkey='transmission_hurdle_rates',
            caption='Transmission Hurdle Rates',
            table='inputs_transmission_hurdle_rates'
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
            ngifkey='transmission_simultaneous_flow_limits',
            caption='Transmission Simultaneous Flow Limits',
            table='inputs_transmission_simultaneous_flow_limits'
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
            ngifkey='transmission_simultaneous_flow_limit_line_groups',
            caption='Transmission Simultaneous Flow Limits Line Groups',
            table='inputs_transmission_simultaneous_flow_limit_line_groups'
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
            ngifkey='geography_lf_up_bas',
            caption='Load Following Up Balancing Areas',
            table='inputs_geography_lf_reserves_up_bas'
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
            ngifkey='project_lf_up_bas',
            caption='Project Load Following Up Balancing Areas',
            table='inputs_project_lf_reserves_up_bas'
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
            ngifkey='load_following_reserves_up_profile',
            caption='Load Following Up Requirement',
            table='inputs_system_lf_reserves_up'
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
            ngifkey='geography_lf_down_bas',
            caption='Load Following Down Balancing Areas',
            table='inputs_geography_lf_reserves_down_bas'
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
            ngifkey='project_lf_down_bas',
            caption='Project Load Following Down Balancing Areas',
            table='inputs_project_lf_reserves_down_bas'
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
            ngifkey='load_following_reserves_down_profile',
            caption='Load Following Down Requirement',
            table='inputs_system_lf_reserves_down'
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
            ngifkey='geography_reg_up_bas',
            caption='Regulation Up Balancing Areas',
            table='inputs_geography_regulation_up_bas'
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
            ngifkey='project_reg_up_bas',
            caption='Project Regulation Up Balancing Areas',
            table='inputs_project_regulation_up_bas'
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
            ngifkey='regulation_up_profile',
            caption='Regulation Up Requirement',
            table='inputs_system_regulation_up'
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
            ngifkey='geography_reg_down_bas',
            caption='Regulation Down Balancing Areas',
            table='inputs_geography_regulation_down_bas'
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
            ngifkey='project_reg_down_bas',
            caption='Project Regulation Down Balancing Areas',
            table='inputs_project_regulation_down_bas'
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
            ngifkey='regulation_down_profile',
            caption='Regulation Down Requirement',
            table='inputs_system_regulation_down'
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
            ngifkey='geography_spin_bas',
            caption='Spinning Reserves Balancing Areas',
            table='inputs_geography_spinning_reserves_bas'
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
            ngifkey='project_spin_bas',
            caption='Project Spinning Reserves Balancing Areas',
            table='inputs_project_spinning_reserves_bas'
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
            ngifkey='spinning_reserves_profile',
            caption='Spinning Reserves Requirement',
            table='inputs_system_spinning_reserves'
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
            ngifkey='geography_freq_resp_bas',
            caption='Frequency Response Balancing Areas',
            table='inputs_geography_frequency_response_bas'
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
            ngifkey='project_freq_resp_bas',
            caption='Project Frequency Response Balancing Areas',
            table='inputs_project_frequency_response_bas'
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
            ngifkey='frequency_response_profile',
            caption='Frequency Response Requirement',
            table='inputs_system_frequency_response'
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
            ngifkey='geography_rps_areas',
            caption='RPS Areas',
            table='inputs_geography_rps_zones'
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
            ngifkey='project_rps_areas',
            caption='Project RPS Areas',
            table='inputs_project_rps_zones'
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
            ngifkey='rps_target',
            caption='RPS Target',
            table='inputs_system_rps_targets'
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
            ngifkey='geography_carbon_cap_areas',
            caption='Carbon Cap Areas',
            table='inputs_geography_carbon_cap_zones'
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
            ngifkey='project_carbon_cap_areas',
            caption='Project Carbon Cap Areas',
            table='inputs_project_carbon_cap_zones'
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
            ngifkey='transmission_carbon_cap_zones',
            caption='Transmission Carbon Cap Areas',
            table='inputs_transmission_carbon_cap_zones'
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
            ngifkey='carbon_cap_target',
            caption='Carbon Cap Target',
            table='inputs_system_carbon_cap_targets'
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
            ngifkey='prm_areas',
            caption='PRM Areas',
            table='inputs_geography_prm_zones'
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
            ngifkey='project_prm_areas',
            caption='Project PRM Areas',
            table='inputs_project_prm_zones'
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
            ngifkey='prm_requirement',
            caption='PRM Target',
            table='inputs_system_prm_requirement'
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
            ngifkey='project_elcc_chars',
            caption='Project ELCC Characteristics',
            table='inputs_project_elcc_chars'
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
            ngifkey='elcc_surface',
            caption='ELCC Surface',
            table='inputs_project_elcc_surface'
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
            ngifkey='project_prm_energy_only',
            caption='Project Energy-Only Characteristics',
            table='inputs_project_prm_energy_only'
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
            ngifkey='local_capacity_areas',
            caption='Local Capacity Areas',
            table='inputs_geography_local_capacity_zones'
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
            ngifkey='project_local_capacity_areas',
            caption='Project Local Capacity Areas',
            table='inputs_project_local_capacity_zones'
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
            ngifkey='local_capacity_requirement',
            caption='Local Capacity Target',
            table='inputs_system_local_capacity_requirement'
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
            ngifkey='project_local_capacity_chars',
            caption='Project Local Capacity Characteristics',
            table='inputs_project_local_capacity_chars'
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
