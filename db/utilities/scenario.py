#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Create or update scenario.
"""
import warnings

from db.common_functions import spin_on_database_lock


def create_scenario_all_args(
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
        of_tuning,
        temporal_scenario_id,
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
        tuning_scenario_id,
        solver_options_id
):
    """
    Insert a scenario by explicitly specifying the value for each column (
    the columns are arguments to this function). The scenario_id column is
    auto increment, so is not inserted directly.
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
    :param of_tuning:
    :param temporal_scenario_id:
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
    :param solver_options_id:
    :return:
    """

    print("creating scenario {}".format(scenario_name))
    sc_data = (
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
        of_tuning,
        temporal_scenario_id,
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
        tuning_scenario_id,
        solver_options_id)
    sc_sql = \
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
        of_tuning,
        temporal_scenario_id,
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
        tuning_scenario_id,
        solver_options_id
        ) VALUES (
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?
        );"""

    spin_on_database_lock(conn=io, cursor=c, sql=sc_sql, data=sc_data,
                          many=False)


def create_scenario(io, c, column_values_dict):
    """
    Flexible way to insert a scenario that does not require specifying
    values for all columns. Columns can be skipped entirely or None can be
    specified as their value (in which case this function will insert a NULL
    value for that column). The scenario_id column is auto increment, so
    should not be inserted directly. If the scenario_id is specified,
    it will be skipped (not inserted) and a warning will be raised.

    :param io: the database connection object
    :param c: database cursor object
    :param column_values_dict: dictionary containing the scenarios table
        column names to populate as keys and the scenarios table column
        values as the dictionary values
    :return: None
    """
    column_names_sql_string = str()
    column_values_sql_string = str()
    column_values_data = tuple()

    # TODO: add a check that the column names are correct and values are
    #  integers
    for column_name in column_values_dict.keys():
        print(column_name)
        if column_name == 'scenario_id':
            warnings.warn(
                "The scenario_id is an AUTOINCREMENT column and should not be "
                "inserted directly. \n"
                "Your scenario will be assigned a scenario_id automatically.\n"
                "Remove the 'scenario_id' key from the dictionary to avoid "
                "seeing this warning again.")
        else:
            if list(column_values_dict.keys()).index(column_name) == 0:
                column_names_sql_string += "{}, ".format(column_name)
                column_values_sql_string += "?,"
                column_values_data = (column_values_dict[column_name],)
            elif list(column_values_dict.keys()).index(column_name) \
                    == len(list(column_values_dict.keys())) - 1:
                column_names_sql_string += "{}".format(column_name)
                column_values_sql_string += "?"
                column_values_data = \
                    column_values_data + (column_values_dict[column_name],)
            else:
                column_names_sql_string += "{}, ".format(column_name)
                column_values_sql_string += "?,"
                column_values_data = \
                    column_values_data + (column_values_dict[column_name],)

    sql = """
        INSERT INTO scenarios ({}) VALUES ({});
    """.format(column_names_sql_string, column_values_sql_string)

    spin_on_database_lock(conn=io, cursor=c, sql=sql, data=column_values_data,
                          many=False)


def update_scenario_multiple_columns(
        io, c,
        scenario_name,
        column_values_dict
):
    """

    :param io:
    :param c:
    :param scenario_name:
    :param column_values_dict:
    :return:
    """
    for column_name in column_values_dict:
        update_scenario_single_column(
            io=io,
            c=c,
            scenario_name=scenario_name,
            column_name=column_name,
            column_value=column_values_dict[column_name]
        )


def update_scenario_single_column(
        io, c,
        scenario_name,
        column_name,
        column_value
):
    """

    :param io:
    :param c:
    :param scenario_name:
    :param column_name:
    :param column_value:
    :return:
    """
    # If no value specified, update to NULL
    if column_value is None:
        column_value = 'NULL'

    # Update the column value for the scenario
    update_sql = """
        UPDATE scenarios
        SET {} = ?
        WHERE scenario_name = ?;
        """.format(column_name)

    spin_on_database_lock(conn=io, cursor=c, sql=update_sql,
                          data=(column_value, scenario_name),
                          many=False)


def delete_scenario(conn, scenario_id):
    """
    :param conn: the database connection object
    :param scenario_id: the scenario_id to delete

    Delete a scenario fully, i.e. delete from all results tables, status
    tables, and the scenarios table.
    """
    c = conn.cursor()
    all_tables = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()

    results_tables = [
        tbl[0] for tbl in all_tables if tbl[0].startswith("results")
    ]
    status_tables = [
        tbl[0] for tbl in all_tables if tbl[0].startswith("status")
    ]

    # Delete from all results and status tables
    tbls_data = []
    for tbl in results_tables + status_tables:
        tbls_data.append((tbl,))
    tbls_sql = \
        """DELETE FROM {} WHERE scenario_id = ?;""".format(
            tbl, scenario_id
        )
    spin_on_database_lock(conn=conn, cursor=c, sql=tbls_sql, data=tbls_data)

    # Delete from scenarios table
    sc_id_sql = "DELETE FROM scenarios WHERE scenario_id = ?"
    spin_on_database_lock(conn=conn, cursor=c, sql=sc_id_sql,
                          data=(scenario_id,),
                          many=False)
