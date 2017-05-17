#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Scenario characteristics in database
"""


class OptionalFeatures:
    def __init__(self, cursor, scenario_id):
        """
        
        :param cursor: 
        :param scenario_id: 
        """
        self.SCENARIO_ID = scenario_id

        self.OPTIONAL_FEATURE_FUELS = cursor.execute(
            """SELECT of_fuels
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_MULTI_STAGE = cursor.execute(
            """SELECT of_multi_stage
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_TRANSMISSION = cursor.execute(
            """SELECT of_transmission
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_TRANSMISSION_HURDLE_RATES = cursor.execute(
            """SELECT of_transmission_hurdle_rates
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_SIMULTANEOUS_FLOW_LIMITS = cursor.execute(
            """SELECT of_simultaneous_flow_limits
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_LF_RESERVES_UP = cursor.execute(
            """SELECT of_lf_reserves_up
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_LF_RESERVES_DOWN = cursor.execute(
            """SELECT of_lf_reserves_down
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_REGULATION_UP = cursor.execute(
            """SELECT of_regulation_up
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_REGULATION_DOWN = cursor.execute(
            """SELECT of_regulation_down
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_FREQUENCY_RESPONSE = cursor.execute(
            """SELECT of_frequency_response
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_SPINNING_RESERVES = cursor.execute(
            """SELECT of_spinning_reserves
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_RPS = cursor.execute(
            """SELECT of_rps
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_CARBON_CAP = cursor.execute(
            """SELECT of_carbon_cap
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_TRACK_CARBON_IMPORTS = cursor.execute(
            """SELECT of_track_carbon_imports
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_PRM = cursor.execute(
            """SELECT of_prm
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_ELCC_SURFACE = cursor.execute(
            """SELECT of_elcc_surface
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

    def determine_feature_list(self):
        """
        Get list of requested features
        :return: 
        """
        feature_list = list()

        if self.OPTIONAL_FEATURE_FUELS:
            feature_list.append("fuels")
        if self.OPTIONAL_FEATURE_MULTI_STAGE:
            feature_list.append("multi_stage")
        if self.OPTIONAL_FEATURE_TRANSMISSION:
            feature_list.append("transmission")
        if self.OPTIONAL_FEATURE_TRANSMISSION_HURDLE_RATES:
            feature_list.append("transmission_hurdle_rates")
        if self.OPTIONAL_FEATURE_SIMULTANEOUS_FLOW_LIMITS:
            feature_list.append("simultaneous_flow_limits")
        if self.OPTIONAL_FEATURE_LF_RESERVES_UP:
            feature_list.append("lf_reserves_up")
        if self.OPTIONAL_FEATURE_LF_RESERVES_DOWN:
            feature_list.append("lf_reserves_down")
        if self.OPTIONAL_FEATURE_REGULATION_UP:
            feature_list.append("regulation_up")
        if self.OPTIONAL_FEATURE_REGULATION_DOWN:
            feature_list.append("regulation_down")
        if self.OPTIONAL_FEATURE_FREQUENCY_RESPONSE:
            feature_list.append("frequency_response")
        if self.OPTIONAL_FEATURE_SPINNING_RESERVES:
            feature_list.append("spinning_reserves")
        if self.OPTIONAL_FEATURE_RPS:
            feature_list.append("rps")
        if self.OPTIONAL_FEATURE_CARBON_CAP:
            feature_list.append("carbon_cap")
        if self.OPTIONAL_FEATURE_TRACK_CARBON_IMPORTS:
            feature_list.append("track_carbon_imports")
        if self.OPTIONAL_FEATURE_PRM:
            feature_list.append("prm")
        if self.OPTIONAL_FEATURE_ELCC_SURFACE:
            feature_list.append("elcc_surface")

        return feature_list


class SubScenarios:
    def __init__(self, cursor, scenario_id):
        """
        
        :param cursor: 
        :param scenario_id: 
        """
        self.SCENARIO_ID = scenario_id

        self.TIMEPOINT_SCENARIO_ID = cursor.execute(
            """SELECT timepoint_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.LOAD_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT load_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.LF_RESERVES_UP_BA_SCENARIO_ID = cursor.execute(
            """SELECT lf_reserves_up_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.LF_RESERVES_DOWN_BA_SCENARIO_ID = cursor.execute(
            """SELECT lf_reserves_down_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        
        self.REGULATION_UP_BA_SCENARIO_ID = cursor.execute(
            """SELECT regulation_up_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.REGULATION_DOWN_BA_SCENARIO_ID = cursor.execute(
            """SELECT regulation_down_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.FREQUENCY_RESPONSE_BA_SCENARIO_ID = cursor.execute(
            """SELECT frequency_response_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.SPINNING_RESERVES_BA_SCENARIO_ID = cursor.execute(
            """SELECT spinning_reserves_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.RPS_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT rps_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.CARBON_CAP_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT carbon_cap_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PRM_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT prm_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_PORTFOLIO_SCENARIO_ID = cursor.execute(
            """SELECT project_portfolio_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_LOAD_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT project_load_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_LF_RESERVES_UP_BA_SCENARIO_ID = cursor.execute(
            """SELECT project_lf_reserves_up_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_LF_RESERVES_DOWN_BA_SCENARIO_ID = cursor.execute(
            """SELECT project_lf_reserves_down_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        
        self.PROJECT_REGULATION_UP_BA_SCENARIO_ID = cursor.execute(
            """SELECT project_regulation_up_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_REGULATION_DOWN_BA_SCENARIO_ID = cursor.execute(
            """SELECT project_regulation_down_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_FREQUENCY_RESPONSE_BA_SCENARIO_ID = cursor.execute(
            """SELECT project_frequency_response_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_SPINNING_RESERVES_BA_SCENARIO_ID = cursor.execute(
            """SELECT project_spinning_reserves_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_RPS_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT project_rps_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_CARBON_CAP_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT project_carbon_cap_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_PRM_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT project_prm_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_ELCC_CHARS_SCENARIO_ID = cursor.execute(
            """SELECT project_elcc_chars_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_EXISTING_CAPACITY_SCENARIO_ID = cursor.execute(
            """SELECT project_existing_capacity_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_EXISTING_FIXED_COST_SCENARIO_ID = cursor.execute(
            """SELECT project_existing_fixed_cost_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_NEW_COST_SCENARIO_ID = cursor.execute(
            """SELECT project_new_cost_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_NEW_POTENTIAL_SCENARIO_ID = cursor.execute(
            """SELECT project_new_potential_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.CAPACITY_THRESHOLD_COST_SCENARIO_ID = cursor.execute(
            """SELECT capacity_threshold_cost_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID = cursor.execute(
            """SELECT project_operational_chars_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PROJECT_AVAILABILITY_SCENARIO_ID = cursor.execute(
            """SELECT project_availability_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.FUEL_SCENARIO_ID = cursor.execute(
            """SELECT fuel_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.FUEL_PRICE_SCENARIO_ID = cursor.execute(
            """SELECT fuel_price_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.TRANSMISSION_PORTFOLIO_SCENARIO_ID = cursor.execute(
            """SELECT transmission_portfolio_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.TRANSMISSION_LOAD_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT transmission_load_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.TRANSMISSION_EXISTING_CAPACITY_SCENARIO_ID = cursor.execute(
            """SELECT transmission_existing_capacity_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.TRANSMISSION_OPERATIONAL_CHARS_SCENARIO_ID = cursor.execute(
            """SELECT transmission_operational_chars_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.TRANSMISSION_HURDLE_RATE_SCENARIO_ID = cursor.execute(
            """SELECT transmission_hurdle_rate_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.TRANSMISSION_CARBON_CAP_ZONE_SCENARIO_ID = cursor.execute(
            """SELECT transmission_carbon_cap_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_SCENARIO_ID = cursor.execute(
            """SELECT transmission_simultaneous_flow_limit_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_LINE_SCENARIO_ID = \
            cursor.execute(
                """SELECT
                transmission_simultaneous_flow_limit_line_group_scenario_id
                FROM scenarios
                WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.LOAD_SCENARIO_ID = cursor.execute(
            """SELECT load_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.LF_RESERVES_UP_SCENARIO_ID = cursor.execute(
            """SELECT lf_reserves_up_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.LF_RESERVES_DOWN_SCENARIO_ID = cursor.execute(
            """SELECT lf_reserves_down_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        
        self.REGULATION_UP_SCENARIO_ID = cursor.execute(
            """SELECT regulation_up_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.REGULATION_DOWN_SCENARIO_ID = cursor.execute(
            """SELECT regulation_down_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.FREQUENCY_RESPONSE_SCENARIO_ID = cursor.execute(
            """SELECT frequency_response_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.SPINNING_RESERVES_SCENARIO_ID = cursor.execute(
            """SELECT spinning_reserves_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.RPS_TARGET_SCENARIO_ID = cursor.execute(
            """SELECT rps_target_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.CARBON_CAP_TARGET_SCENARIO_ID = cursor.execute(
            """SELECT carbon_cap_target_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.PRM_REQUIREMENT_SCENARIO_ID = cursor.execute(
            """SELECT prm_requirement_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.ELCC_SURFACE_SCENARIO_ID = cursor.execute(
            """SELECT elcc_surface_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.TUNING_SCENARIO_ID = cursor.execute(
            """SELECT tuning_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
