#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create scenario
"""
from __future__ import print_function


def create_scenario(
        io, c,
        scenario_name,
        of_fuels,
        of_multi_stage,
        of_transmission,
        of_transmission_hurdle_rates,
        of_simultaneous_flow_limits,
        of_lf_reserves_up,
        of_lf_reserves_down,
        of_regulation_up,
        of_regulation_down,
        of_frequency_response,
        of_spinning_reserves,
        of_rps,
        of_carbon_cap,
        of_track_carbon_imports,
        of_prm,
        of_local_capacity,
        of_elcc_surface,
        timepoint_scenario_id,
        load_zone_scenario_id,
        lf_reserves_up_ba_scenario_id,
        lf_reserves_down_ba_scenario_id,
        regulation_up_ba_scenario_id,
        regulation_down_ba_scenario_id,
        frequency_response_ba_scenario_id,
        spinning_reserves_ba_scenario_id,
        rps_zone_scenario_id,
        carbon_cap_zone_scenario_id,
        prm_zone_scenario_id,
        local_capacity_zone_scenario_id,
        project_portfolio_scenario_id,
        project_operational_chars_scenario_id,
        project_availability_scenario_id,
        fuel_scenario_id,
        project_load_zone_scenario_id,
        project_lf_reserves_up_ba_scenario_id,
        project_lf_reserves_down_ba_scenario_id,
        project_regulation_up_ba_scenario_id,
        project_regulation_down_ba_scenario_id,
        project_frequency_response_ba_scenario_id,
        project_spinning_reserves_ba_scenario_id,
        project_rps_zone_scenario_id,
        project_carbon_cap_zone_scenario_id,
        project_prm_zone_scenario_id,
        project_elcc_chars_scenario_id,
        prm_energy_only_scenario_id,
        project_local_capacity_zone_scenario_id,
        project_local_capacity_chars_scenario_id,
        project_existing_capacity_scenario_id,
        project_existing_fixed_cost_scenario_id,
        fuel_price_scenario_id,
        project_new_cost_scenario_id,
        project_new_potential_scenario_id,
        transmission_portfolio_scenario_id,
        transmission_load_zone_scenario_id,
        transmission_existing_capacity_scenario_id,
        transmission_operational_chars_scenario_id,
        transmission_hurdle_rate_scenario_id,
        transmission_carbon_cap_zone_scenario_id,
        transmission_simultaneous_flow_limit_scenario_id,
        transmission_simultaneous_flow_limit_line_group_scenario_id,
        load_scenario_id,
        lf_reserves_up_scenario_id,
        lf_reserves_down_scenario_id,
        regulation_up_scenario_id,
        regulation_down_scenario_id,
        frequency_response_scenario_id,
        spinning_reserves_scenario_id,
        rps_target_scenario_id,
        carbon_cap_target_scenario_id,
        prm_requirement_scenario_id,
        local_capacity_requirement_scenario_id,
        elcc_surface_scenario_id,
        tuning_scenario_id
):
    """
    The scenario_id column is auto increment, so not inserted directly
    :param io:
    :param c:
    :param scenario_name:
    :param of_fuels:
    :param of_multi_stage:
    :param of_transmission:
    :param of_transmission_hurdle_rates:
    :param of_simultaneous_flow_limits:
    :param of_lf_reserves_up:
    :param of_lf_reserves_down:
    :param of_regulation_up:
    :param of_regulation_down:
    :param of_frequency_response:
    :param of_spinning_reserves:
    :param of_rps:
    :param of_carbon_cap:
    :param of_track_carbon_imports:
    :param of_prm:
    :param of_local_capacity:
    :param of_elcc_surface:
    :param timepoint_scenario_id:
    :param load_zone_scenario_id:
    :param lf_reserves_up_ba_scenario_id:
    :param lf_reserves_down_ba_scenario_id:
    :param regulation_up_ba_scenario_id:
    :param regulation_down_ba_scenario_id:
    :param frequency_response_ba_scenario_id:
    :param spinning_reserves_ba_scenario_id:
    :param rps_zone_scenario_id:
    :param carbon_cap_zone_scenario_id:
    :param prm_zone_scenario_id:
    :param local_capacity_zone_scenario_id:
    :param project_portfolio_scenario_id:
    :param project_operational_chars_scenario_id:
    :param project_availability_scenario_id:
    :param fuel_scenario_id:
    :param project_load_zone_scenario_id:
    :param project_lf_reserves_up_ba_scenario_id:
    :param project_lf_reserves_down_ba_scenario_id:
    :param project_regulation_up_ba_scenario_id:
    :param project_regulation_down_ba_scenario_id:
    :param project_frequency_response_ba_scenario_id:
    :param project_spinning_reserves_ba_scenario_id:
    :param project_rps_zone_scenario_id:
    :param project_carbon_cap_zone_scenario_id:
    :param project_prm_zone_scenario_id:
    :param project_elcc_chars_scenario_id:
    :param prm_energy_only_scenario_id:
    :param project_local_capacity_zone_scenario_id:
    :param project_local_capacity_chars_scenario_id
    :param project_existing_capacity_scenario_id:
    :param project_existing_fixed_cost_scenario_id:
    :param fuel_price_scenario_id:
    :param project_new_cost_scenario_id:
    :param project_new_potential_scenario_id:
    :param transmission_portfolio_scenario_id:
    :param transmission_load_zone_scenario_id:
    :param transmission_existing_capacity_scenario_id:
    :param transmission_operational_chars_scenario_id:
    :param transmission_hurdle_rate_scenario_id:
    :param transmission_carbon_cap_zone_scenario_id:
    :param transmission_simultaneous_flow_limit_scenario_id:
    :param transmission_simultaneous_flow_limit_line_group_scenario_id:
    :param load_scenario_id:
    :param lf_reserves_up_scenario_id:
    :param lf_reserves_down_scenario_id:
    :param regulation_up_scenario_id:
    :param regulation_down_scenario_id:
    :param frequency_response_scenario_id:
    :param spinning_reserves_scenario_id:
    :param rps_target_scenario_id:
    :param carbon_cap_target_scenario_id:
    :param prm_requirement_scenario_id:
    :param elcc_surface_scenario_id:
    :param local_capacity_requirement_scenario_id:
    :param tuning_scenario_id:
    :return:
    """

    print("creating scenario '{}'".format(scenario_name))
    c.execute(
        """INSERT INTO scenarios (
        scenario_name,
        of_fuels,
        of_multi_stage,
        of_transmission,
        of_transmission_hurdle_rates,
        of_simultaneous_flow_limits,
        of_lf_reserves_up,
        of_lf_reserves_down,
        of_regulation_up,
        of_regulation_down,
        of_frequency_response,
        of_spinning_reserves,
        of_rps,
        of_carbon_cap,
        of_track_carbon_imports,
        of_prm,
        of_local_capacity,
        of_elcc_surface,
        timepoint_scenario_id,
        load_zone_scenario_id,
        lf_reserves_up_ba_scenario_id,
        lf_reserves_down_ba_scenario_id,
        regulation_up_ba_scenario_id,
        regulation_down_ba_scenario_id,
        frequency_response_ba_scenario_id,
        spinning_reserves_ba_scenario_id,
        rps_zone_scenario_id,
        carbon_cap_zone_scenario_id,
        prm_zone_scenario_id,
        local_capacity_zone_scenario_id,
        project_portfolio_scenario_id,
        project_operational_chars_scenario_id,
        project_availability_scenario_id,
        fuel_scenario_id,
        project_load_zone_scenario_id,
        project_lf_reserves_up_ba_scenario_id,
        project_lf_reserves_down_ba_scenario_id,
        project_regulation_up_ba_scenario_id,
        project_regulation_down_ba_scenario_id,
        project_frequency_response_ba_scenario_id,
        project_spinning_reserves_ba_scenario_id,
        project_rps_zone_scenario_id,
        project_carbon_cap_zone_scenario_id,
        project_prm_zone_scenario_id,
        project_elcc_chars_scenario_id,
        prm_energy_only_scenario_id,
        project_local_capacity_zone_scenario_id,
        project_local_capacity_chars_scenario_id,
        project_existing_capacity_scenario_id,
        project_existing_fixed_cost_scenario_id,
        fuel_price_scenario_id,
        project_new_cost_scenario_id,
        project_new_potential_scenario_id,
        transmission_portfolio_scenario_id,
        transmission_load_zone_scenario_id,
        transmission_existing_capacity_scenario_id,
        transmission_operational_chars_scenario_id,
        transmission_hurdle_rate_scenario_id,
        transmission_carbon_cap_zone_scenario_id,
        transmission_simultaneous_flow_limit_scenario_id,
        transmission_simultaneous_flow_limit_line_group_scenario_id,
        load_scenario_id,
        lf_reserves_up_scenario_id,
        lf_reserves_down_scenario_id,
        regulation_up_scenario_id,
        regulation_down_scenario_id,
        frequency_response_scenario_id,
        spinning_reserves_scenario_id,
        rps_target_scenario_id,
        carbon_cap_target_scenario_id,
        prm_requirement_scenario_id,
        elcc_surface_scenario_id,
        local_capacity_requirement_scenario_id,
        tuning_scenario_id
        ) VALUES (
        '{}',
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {}
        );""".format(
            scenario_name,
            of_fuels,
            of_multi_stage,
            of_transmission,
            of_transmission_hurdle_rates,
            of_simultaneous_flow_limits,
            of_lf_reserves_up,
            of_lf_reserves_down,
            of_regulation_up,
            of_regulation_down,
            of_frequency_response,
            of_spinning_reserves,
            of_rps,
            of_carbon_cap,
            of_track_carbon_imports,
            of_prm,
            of_local_capacity,
            of_elcc_surface,
            timepoint_scenario_id,
            load_zone_scenario_id,
            lf_reserves_up_ba_scenario_id,
            lf_reserves_down_ba_scenario_id,
            regulation_up_ba_scenario_id,
            regulation_down_ba_scenario_id,
            frequency_response_ba_scenario_id,
            spinning_reserves_ba_scenario_id,
            rps_zone_scenario_id,
            carbon_cap_zone_scenario_id,
            prm_zone_scenario_id,
            local_capacity_zone_scenario_id,
            project_portfolio_scenario_id,
            project_operational_chars_scenario_id,
            project_availability_scenario_id,
            fuel_scenario_id,
            project_load_zone_scenario_id,
            project_lf_reserves_up_ba_scenario_id,
            project_lf_reserves_down_ba_scenario_id,
            project_regulation_up_ba_scenario_id,
            project_regulation_down_ba_scenario_id,
            project_frequency_response_ba_scenario_id,
            project_spinning_reserves_ba_scenario_id,
            project_rps_zone_scenario_id,
            project_carbon_cap_zone_scenario_id,
            project_prm_zone_scenario_id,
            project_elcc_chars_scenario_id,
            prm_energy_only_scenario_id,
            project_local_capacity_zone_scenario_id,
            project_local_capacity_chars_scenario_id,
            project_existing_capacity_scenario_id,
            project_existing_fixed_cost_scenario_id,
            fuel_price_scenario_id,
            project_new_cost_scenario_id,
            project_new_potential_scenario_id,
            transmission_portfolio_scenario_id,
            transmission_load_zone_scenario_id,
            transmission_existing_capacity_scenario_id,
            transmission_operational_chars_scenario_id,
            transmission_hurdle_rate_scenario_id,
            transmission_carbon_cap_zone_scenario_id,
            transmission_simultaneous_flow_limit_scenario_id,
            transmission_simultaneous_flow_limit_line_group_scenario_id,
            load_scenario_id,
            lf_reserves_up_scenario_id,
            lf_reserves_down_scenario_id,
            regulation_up_scenario_id,
            regulation_down_scenario_id,
            frequency_response_scenario_id,
            spinning_reserves_scenario_id,
            rps_target_scenario_id,
            carbon_cap_target_scenario_id,
            prm_requirement_scenario_id,
            elcc_surface_scenario_id,
            local_capacity_requirement_scenario_id,
            tuning_scenario_id
        )
    )

    io.commit()
