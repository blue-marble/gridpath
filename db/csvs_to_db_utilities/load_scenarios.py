#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load scenarios data
"""

from collections import OrderedDict

from db.utilities import scenario

def load_scenarios(io, c, data_input):
    """
    scenario dictionary
    {optional_feature_or_subscenario: include_flag_or_subscenario_id}
    :param io:
    :param c:
    :param data_input:
    :return:
    """

    for sc in data_input.columns.to_list()[1:]:
        print(sc)
        scenarios = dict()

        scenarios = data_input.set_index('optional_feature_or_subscenarios')[sc].to_dict()

        scenario.create_scenario_all_args(
            io=io, c=c,
            scenario_name=sc,
            of_fuels=scenarios["of_fuels"],
            of_multi_stage=scenarios["of_multi_stage"],
            of_transmission=scenarios["of_transmission"],
            of_transmission_hurdle_rates=scenarios["of_transmission_hurdle_rates"],
            of_simultaneous_flow_limits=scenarios["of_simultaneous_flow_limits"],
            of_lf_reserves_up=scenarios["of_lf_reserves_up"],
            of_lf_reserves_down=scenarios["of_lf_reserves_down"],
            of_regulation_up=scenarios["of_regulation_up"],
            of_regulation_down=scenarios["of_regulation_down"],
            of_frequency_response=scenarios["of_frequency_response"],
            of_spinning_reserves=scenarios["of_spinning_reserves"],
            of_rps=scenarios["of_rps"],
            of_carbon_cap=scenarios["of_carbon_cap"],
            of_track_carbon_imports=scenarios["of_track_carbon_imports"],
            of_prm=scenarios["of_prm"],
            of_local_capacity=scenarios["of_local_capacity"],
            of_elcc_surface=scenarios["of_elcc_surface"],
            of_tuning=scenarios["of_tuning"],
            temporal_scenario_id=scenarios["temporal_scenario_id"],
            load_zone_scenario_id=scenarios["load_zone_scenario_id"],
            lf_reserves_up_ba_scenario_id=
            scenarios["lf_reserves_up_ba_scenario_id"],
            lf_reserves_down_ba_scenario_id=
            scenarios["lf_reserves_down_ba_scenario_id"],
            regulation_up_ba_scenario_id=scenarios["regulation_up_ba_scenario_id"],
            regulation_down_ba_scenario_id=
            scenarios["regulation_down_ba_scenario_id"],
            frequency_response_ba_scenario_id=
            scenarios["frequency_response_ba_scenario_id"],
            spinning_reserves_ba_scenario_id=
            scenarios["spinning_reserves_ba_scenario_id"],
            rps_zone_scenario_id=scenarios["rps_zone_scenario_id"],
            carbon_cap_zone_scenario_id=scenarios["carbon_cap_zone_scenario_id"],
            prm_zone_scenario_id=scenarios["prm_zone_scenario_id"],
            local_capacity_zone_scenario_id=scenarios[
                "local_capacity_zone_scenario_id"],
            project_portfolio_scenario_id=
            scenarios["project_portfolio_scenario_id"],
            project_operational_chars_scenario_id=
            scenarios["project_operational_chars_scenario_id"],
            project_availability_scenario_id=
            scenarios["project_availability_scenario_id"],
            fuel_scenario_id=scenarios["fuel_scenario_id"],
            project_load_zone_scenario_id=
            scenarios["project_load_zone_scenario_id"],
            project_lf_reserves_up_ba_scenario_id=
            scenarios["project_lf_reserves_up_ba_scenario_id"],
            project_lf_reserves_down_ba_scenario_id=
            scenarios["project_lf_reserves_down_ba_scenario_id"],
            project_regulation_up_ba_scenario_id=
            scenarios["project_regulation_up_ba_scenario_id"],
            project_regulation_down_ba_scenario_id=
            scenarios["project_regulation_down_ba_scenario_id"],
            project_frequency_response_ba_scenario_id=
            scenarios["project_frequency_response_ba_scenario_id"],
            project_spinning_reserves_ba_scenario_id=
            scenarios["project_spinning_reserves_ba_scenario_id"],
            project_rps_zone_scenario_id=scenarios["project_rps_zone_scenario_id"],
            project_carbon_cap_zone_scenario_id=
            scenarios["project_carbon_cap_zone_scenario_id"],
            project_prm_zone_scenario_id=scenarios["project_prm_zone_scenario_id"],
            project_elcc_chars_scenario_id=
            scenarios["project_elcc_chars_scenario_id"],
            prm_energy_only_scenario_id=
            scenarios["prm_energy_only_scenario_id"],
            project_local_capacity_zone_scenario_id=scenarios[
                "project_local_capacity_zone_scenario_id"],
            project_local_capacity_chars_scenario_id=
            scenarios["project_local_capacity_chars_scenario_id"],
            project_existing_capacity_scenario_id=
            scenarios["project_existing_capacity_scenario_id"],
            project_existing_fixed_cost_scenario_id=
            scenarios["project_existing_fixed_cost_scenario_id"],
            fuel_price_scenario_id=scenarios["fuel_price_scenario_id"],
            project_new_cost_scenario_id=scenarios["project_new_cost_scenario_id"],
            project_new_potential_scenario_id=
            scenarios["project_new_potential_scenario_id"],
            project_new_binary_build_size_scenario_id=
            scenarios["project_new_binary_build_size_scenario_id"],
            transmission_portfolio_scenario_id=
            scenarios["transmission_portfolio_scenario_id"],
            transmission_load_zone_scenario_id=
            scenarios["transmission_load_zone_scenario_id"],
            transmission_existing_capacity_scenario_id=
            scenarios["transmission_existing_capacity_scenario_id"],
            transmission_operational_chars_scenario_id=
            scenarios["transmission_operational_chars_scenario_id"],
            transmission_hurdle_rate_scenario_id=
            scenarios["transmission_hurdle_rate_scenario_id"],
            transmission_carbon_cap_zone_scenario_id=
            scenarios["transmission_carbon_cap_zone_scenario_id"],
            transmission_simultaneous_flow_limit_scenario_id=
            scenarios["transmission_simultaneous_flow_limit_scenario_id"],
            transmission_simultaneous_flow_limit_line_group_scenario_id=
            scenarios[
                "transmission_simultaneous_flow_limit_line_group_scenario_id"],
            load_scenario_id=scenarios["load_scenario_id"],
            lf_reserves_up_scenario_id=scenarios["lf_reserves_up_scenario_id"],
            lf_reserves_down_scenario_id=scenarios["lf_reserves_down_scenario_id"],
            regulation_up_scenario_id=scenarios["regulation_up_scenario_id"],
            regulation_down_scenario_id=scenarios["regulation_down_scenario_id"],
            frequency_response_scenario_id=
            scenarios["frequency_response_scenario_id"],
            spinning_reserves_scenario_id=
            scenarios["spinning_reserves_scenario_id"],
            rps_target_scenario_id=scenarios["rps_target_scenario_id"],
            carbon_cap_target_scenario_id=scenarios["carbon_cap_target_scenario_id"],
            prm_requirement_scenario_id=scenarios["prm_requirement_scenario_id"],
            elcc_surface_scenario_id=scenarios["elcc_surface_scenario_id"],
            local_capacity_requirement_scenario_id=scenarios[
                "local_capacity_requirement_scenario_id"],
            tuning_scenario_id=scenarios["tuning_scenario_id"],
            solver_options_id=scenarios["solver_options_id"]
        )
