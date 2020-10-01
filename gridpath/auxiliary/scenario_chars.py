#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Scenario characteristics in database
"""

from builtins import object


class OptionalFeatures(object):
    def __init__(self, cursor, scenario_id):
        """
        :param cursor:
        :param scenario_id: 
        """

        self.SCENARIO_ID = scenario_id

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

        self.OPTIONAL_FEATURE_LOCAL_CAPACITY = cursor.execute(
            """SELECT of_local_capacity
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

        self.OPTIONAL_FEATURE_TUNING = cursor.execute(
            """SELECT of_tuning
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]

    def determine_feature_list(self):
        """
        Get list of requested features
        :return: 
        """
        feature_list = list()

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
        if self.OPTIONAL_FEATURE_LOCAL_CAPACITY:
            feature_list.append("local_capacity")
        if self.OPTIONAL_FEATURE_TUNING:
            feature_list.append("tuning")

        return feature_list


class SubScenarios(object):
    """
    The subscenario IDs will be used to format SQL queries, so we set them to
    "NULL" (not None) if an ID is not specified for the scenario.
    """
    def __init__(self, cursor, scenario_id):
        """
        
        :param cursor: 
        :param scenario_id: 
        """
        self.SCENARIO_ID = scenario_id

        # TODO: refactor this
        temporal_sid = cursor.execute(
            """SELECT temporal_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.TEMPORAL_SCENARIO_ID = \
            "NULL" if temporal_sid is None else temporal_sid

        lz_sid = cursor.execute(
            """SELECT load_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.LOAD_ZONE_SCENARIO_ID = \
            "NULL" if lz_sid is None else lz_sid

        lf_res_up_ba_sid = cursor.execute(
            """SELECT lf_reserves_up_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.LF_RESERVES_UP_BA_SCENARIO_ID = \
            "NULL" if lf_res_up_ba_sid is None else lf_res_up_ba_sid

        lf_res_down_ba_sid = cursor.execute(
            """SELECT lf_reserves_down_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.LF_RESERVES_DOWN_BA_SCENARIO_ID = \
            "NULL" if lf_res_down_ba_sid is None else lf_res_down_ba_sid
        
        reg_up_ba_sid = cursor.execute(
            """SELECT regulation_up_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.REGULATION_UP_BA_SCENARIO_ID = \
            "NULL" if reg_up_ba_sid is None else reg_up_ba_sid

        reg_down_ba_sid = cursor.execute(
            """SELECT regulation_down_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.REGULATION_DOWN_BA_SCENARIO_ID = \
            "NULL" if reg_down_ba_sid is None else reg_down_ba_sid

        freq_resp_ba_sid = cursor.execute(
            """SELECT frequency_response_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.FREQUENCY_RESPONSE_BA_SCENARIO_ID = \
            "NULL" if freq_resp_ba_sid is None else freq_resp_ba_sid

        spin_res_ba_sid = cursor.execute(
            """SELECT spinning_reserves_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.SPINNING_RESERVES_BA_SCENARIO_ID = \
            "NULL" if spin_res_ba_sid is None else spin_res_ba_sid

        rps_zone_sid = cursor.execute(
            """SELECT rps_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.RPS_ZONE_SCENARIO_ID = \
            "NULL" if rps_zone_sid is None else rps_zone_sid

        carbon_cap_zone_sid = cursor.execute(
            """SELECT carbon_cap_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.CARBON_CAP_ZONE_SCENARIO_ID = \
            "NULL" if carbon_cap_zone_sid is None else carbon_cap_zone_sid

        prm_zone_sid = cursor.execute(
            """SELECT prm_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PRM_ZONE_SCENARIO_ID = \
            "NULL" if prm_zone_sid is None else prm_zone_sid

        loc_cap_zone_sid = cursor.execute(
            """SELECT local_capacity_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.LOCAL_CAPACITY_ZONE_SCENARIO_ID = \
            "NULL" if loc_cap_zone_sid is None else loc_cap_zone_sid

        market_sid = cursor.execute(
            """SELECT market_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.MARKET_SCENARIO_ID = \
            "NULL" if market_sid is None else market_sid

        market_price_sid = cursor.execute(
            """SELECT market_price_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.MARKET_PRICE_SCENARIO_ID = \
            "NULL" if market_price_sid is None else market_price_sid

        proj_portfolio_sid = cursor.execute(
            """SELECT project_portfolio_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_PORTFOLIO_SCENARIO_ID = \
            "NULL" if proj_portfolio_sid is None else proj_portfolio_sid

        proj_lz_sid = cursor.execute(
            """SELECT project_load_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_LOAD_ZONE_SCENARIO_ID = \
            "NULL" if proj_lz_sid is None else proj_lz_sid

        p_lf_res_up_ba_sid = cursor.execute(
            """SELECT project_lf_reserves_up_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_LF_RESERVES_UP_BA_SCENARIO_ID = \
            "NULL" if p_lf_res_up_ba_sid is None else p_lf_res_up_ba_sid

        p_lf_res_down_ba_sid = cursor.execute(
            """SELECT project_lf_reserves_down_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_LF_RESERVES_DOWN_BA_SCENARIO_ID = \
            "NULL" if p_lf_res_down_ba_sid is None else p_lf_res_down_ba_sid
        
        p_reg_up_ba_sid = cursor.execute(
            """SELECT project_regulation_up_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_REGULATION_UP_BA_SCENARIO_ID = \
            "NULL" if p_reg_up_ba_sid is None else p_reg_up_ba_sid

        p_reg_down_ba_sid = cursor.execute(
            """SELECT project_regulation_down_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_REGULATION_DOWN_BA_SCENARIO_ID = \
            "NULL" if p_reg_down_ba_sid is None else p_reg_down_ba_sid

        p_fr_ba_sid = cursor.execute(
            """SELECT project_frequency_response_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_FREQUENCY_RESPONSE_BA_SCENARIO_ID = \
            "NULL" if p_fr_ba_sid is None else p_fr_ba_sid

        p_sp_ba_sid = cursor.execute(
            """SELECT project_spinning_reserves_ba_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_SPINNING_RESERVES_BA_SCENARIO_ID = \
            "NULL" if p_sp_ba_sid is None else p_sp_ba_sid

        p_rps_z_sid = cursor.execute(
            """SELECT project_rps_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_RPS_ZONE_SCENARIO_ID = \
            "NULL" if p_rps_z_sid is None else p_rps_z_sid

        p_cc_z_sid = cursor.execute(
            """SELECT project_carbon_cap_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_CARBON_CAP_ZONE_SCENARIO_ID = \
            "NULL" if p_cc_z_sid is None else p_cc_z_sid

        p_prm_z_sid = cursor.execute(
            """SELECT project_prm_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_PRM_ZONE_SCENARIO_ID = \
            "NULL" if p_prm_z_sid is None else p_prm_z_sid

        p_elcc_char_sid = cursor.execute(
            """SELECT project_elcc_chars_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_ELCC_CHARS_SCENARIO_ID = \
            "NULL" if p_elcc_char_sid is None else p_elcc_char_sid

        p_lc_z_sid = cursor.execute(
            """SELECT project_local_capacity_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_LOCAL_CAPACITY_ZONE_SCENARIO_ID = \
            "NULL" if p_lc_z_sid is None else p_lc_z_sid

        p_lc_char_sid = cursor.execute(
            """SELECT project_local_capacity_chars_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_LOCAL_CAPACITY_CHARS_SCENARIO_ID = \
            "NULL" if p_lc_char_sid is None else p_lc_char_sid

        lz_mh_sid = cursor.execute(
            """SELECT load_zone_market_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.LOAD_ZONE_MARKET_SCENARIO_ID = \
            "NULL" if lz_mh_sid is None else lz_mh_sid

        p_ecap_sid = cursor.execute(
            """SELECT project_specified_capacity_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID = \
            "NULL" if p_ecap_sid is None else p_ecap_sid

        p_efc_sid = cursor.execute(
            """SELECT project_specified_fixed_cost_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_SPECIFIED_FIXED_COST_SCENARIO_ID = \
            "NULL" if p_efc_sid is None else p_efc_sid

        p_ncost_sid = cursor.execute(
            """SELECT project_new_cost_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_NEW_COST_SCENARIO_ID = \
            "NULL" if p_ncost_sid is None else p_ncost_sid

        p_npot_sid = cursor.execute(
            """SELECT project_new_potential_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_NEW_POTENTIAL_SCENARIO_ID = \
            "NULL" if p_npot_sid is None else p_npot_sid

        p_nbbsize_sid = cursor.execute(
            """SELECT project_new_binary_build_size_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_NEW_BINARY_BUILD_SIZE_SCENARIO_ID = \
            "NULL" if p_nbbsize_sid is None else p_nbbsize_sid

        p_capgrp_sid = cursor.execute(
            """SELECT project_capacity_group_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_CAPACITY_GROUP_SCENARIO_ID = \
            "NULL" if p_capgrp_sid is None else p_capgrp_sid

        p_capgrp_req_sid = cursor.execute(
            """SELECT project_capacity_group_requirement_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_CAPACITY_GROUP_REQUIREMENT_SCENARIO_ID = \
            "NULL" if p_capgrp_req_sid is None else p_capgrp_req_sid

        prm_en_only_sid = cursor.execute(
            """SELECT prm_energy_only_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PRM_ENERGY_ONLY_SCENARIO_ID = \
            "NULL" if prm_en_only_sid is None else prm_en_only_sid

        p_opchar_sid = cursor.execute(
            """SELECT project_operational_chars_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID = \
            "NULL" if p_opchar_sid is None else p_opchar_sid

        p_av_sid = cursor.execute(
            """SELECT project_availability_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PROJECT_AVAILABILITY_SCENARIO_ID = \
            "NULL" if p_av_sid is None else p_av_sid

        fuel_sid = cursor.execute(
            """SELECT fuel_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.FUEL_SCENARIO_ID = \
            "NULL" if fuel_sid is None else fuel_sid

        fuel_price_sid = cursor.execute(
            """SELECT fuel_price_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.FUEL_PRICE_SCENARIO_ID = \
            "NULL" if fuel_price_sid is None else fuel_price_sid

        tx_port_sid = cursor.execute(
            """SELECT transmission_portfolio_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.TRANSMISSION_PORTFOLIO_SCENARIO_ID = \
            "NULL" if tx_port_sid is None else tx_port_sid

        tx_lz_sid = cursor.execute(
            """SELECT transmission_load_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.TRANSMISSION_LOAD_ZONE_SCENARIO_ID = \
            "NULL" if tx_lz_sid is None else tx_lz_sid

        tx_ecap_sid = cursor.execute(
            """SELECT transmission_specified_capacity_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.TRANSMISSION_SPECIFIED_CAPACITY_SCENARIO_ID = \
            "NULL" if tx_ecap_sid is None else tx_ecap_sid

        tx_ncost_sid = cursor.execute(
            """SELECT transmission_new_cost_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.TRANSMISSION_NEW_COST_SCENARIO_ID = \
            "NULL" if tx_ncost_sid is None else tx_ncost_sid

        tx_opchar = cursor.execute(
            """SELECT transmission_operational_chars_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.TRANSMISSION_OPERATIONAL_CHARS_SCENARIO_ID = \
            "NULL" if tx_opchar is None else tx_opchar

        tx_hurdle_sid = cursor.execute(
            """SELECT transmission_hurdle_rate_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.TRANSMISSION_HURDLE_RATE_SCENARIO_ID = \
            "NULL" if tx_hurdle_sid is None else tx_hurdle_sid

        tx_cc_z_sid = cursor.execute(
            """SELECT transmission_carbon_cap_zone_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.TRANSMISSION_CARBON_CAP_ZONE_SCENARIO_ID = \
            "NULL" if tx_cc_z_sid is None else tx_cc_z_sid

        tx_sim_f_sid = cursor.execute(
            """SELECT transmission_simultaneous_flow_limit_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_SCENARIO_ID = \
            "NULL" if tx_sim_f_sid is None else tx_sim_f_sid

        tx_sim_f_line_sid = \
            cursor.execute(
                """SELECT
                transmission_simultaneous_flow_limit_line_group_scenario_id
                FROM scenarios
                WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_LINE_SCENARIO_ID = \
            "NULL" if tx_sim_f_line_sid is None else tx_sim_f_line_sid

        load_sid = cursor.execute(
            """SELECT load_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.LOAD_SCENARIO_ID = \
            "NULL" if load_sid is None else load_sid

        lf_res_up_sid = cursor.execute(
            """SELECT lf_reserves_up_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.LF_RESERVES_UP_SCENARIO_ID = \
            "NULL" if lf_res_up_sid is None else lf_res_up_sid

        lf_res_down_sid = cursor.execute(
            """SELECT lf_reserves_down_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.LF_RESERVES_DOWN_SCENARIO_ID = \
            "NULL" if lf_res_down_sid is None else lf_res_down_sid
        
        reg_up_sid = cursor.execute(
            """SELECT regulation_up_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.REGULATION_UP_SCENARIO_ID = \
            "NULL" if reg_up_sid is None else reg_up_sid

        reg_down_sid = cursor.execute(
            """SELECT regulation_down_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.REGULATION_DOWN_SCENARIO_ID = \
            "NULL" if reg_down_sid is None else reg_down_sid

        fr_sid = cursor.execute(
            """SELECT frequency_response_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.FREQUENCY_RESPONSE_SCENARIO_ID = \
            "NULL" if fr_sid is None else fr_sid

        spin_sid = cursor.execute(
            """SELECT spinning_reserves_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.SPINNING_RESERVES_SCENARIO_ID = \
            "NULL" if spin_sid is None else spin_sid

        rps_sid = cursor.execute(
            """SELECT rps_target_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.RPS_TARGET_SCENARIO_ID = \
            "NULL" if rps_sid is None else rps_sid

        cc_sid = cursor.execute(
            """SELECT carbon_cap_target_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.CARBON_CAP_TARGET_SCENARIO_ID = \
            "NULL" if cc_sid is None else cc_sid

        prm_sid = cursor.execute(
            """SELECT prm_requirement_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.PRM_REQUIREMENT_SCENARIO_ID = \
            "NULL" if prm_sid is None else prm_sid

        elcc_sid = cursor.execute(
            """SELECT elcc_surface_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.ELCC_SURFACE_SCENARIO_ID = \
            "NULL" if elcc_sid is None else elcc_sid

        lc_sid = cursor.execute(
            """SELECT local_capacity_requirement_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.LOCAL_CAPACITY_REQUIREMENT_SCENARIO_ID = \
            "NULL" if lc_sid is None else lc_sid

        tuning_sid = cursor.execute(
            """SELECT tuning_scenario_id
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
        self.TUNING_SCENARIO_ID = \
            "NULL" if tuning_sid is None else tuning_sid

        self.subscenario_ids_by_feature = \
            self.determine_subscenarios_by_feature(cursor)

    @staticmethod
    def determine_subscenarios_by_feature(cursor):
        """

        :param cursor:
        :return:
        """
        feature_sc = cursor.execute(
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
    def __init__(self, cursor, scenario_id):
        """

        :param cursor:
        :param scenario_id:
        """

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
    def __init__(self, cursor, scenario_id):
        """
        :param cursor:
        :param scenario_id:
        """

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
