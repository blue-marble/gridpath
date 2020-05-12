#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Project operational characteristics
"""
from db.common_functions import spin_on_database_lock
import sqlite3
import numpy as np


def make_scenario_and_insert_all_projects(
        io, c,
        project_operational_chars_scenario_id,
        scenario_name,
        scenario_description
):
    """

    :param io:
    :param c:
    :param project_operational_chars_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :return:
    """
    # Subscenarios
    subs_data = [(project_operational_chars_scenario_id, scenario_name,
                  scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_operational_chars (
        project_operational_chars_scenario_id, name,
        description) VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert all projects into operational chars table
    all_projects = c.execute("SELECT project "
                             "FROM inputs_project_all;").fetchall()
    inputs_data = [(project_operational_chars_scenario_id, p[0])
                   for p in all_projects]
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_operational_chars
        (project_operational_chars_scenario_id, project)
        VALUES (?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def update_project_opchar_column(
        io, c,
        project_operational_chars_scenario_id,
        column,
        project_char,
):
    """
    Update column in the op char table
    :param io:
    :param c:
    :param projects:
    :return:
    """
    update_data = []
    for project in list(project_char.keys()):
        update_data.append(
            (project_char[project],
             project,
             project_operational_chars_scenario_id))
    update_sql = """
        UPDATE inputs_project_operational_chars
        SET {} = ?
        WHERE project = ?
        AND project_operational_chars_scenario_id = ?;
        """.format(column)
    spin_on_database_lock(conn=io, cursor=c, sql=update_sql, data=update_data)


def update_project_opchar_variable_gen_profile_scenario_id(
        io, c,
        project_operational_chars_scenario_id,
        variable_generator_profile_scenario_id
):
    """
    Update all 'gen_var' and 'gen_var_must_take' project under a given
    project_operational_chars_scenario_id with a single
    variable_generator_profile_scenario_id
    :param io:
    :param c:
    :param project_operational_chars_scenario_id:
    :param variable_generator_profile_scenario_id:
    :return:
    """
    update_data = [
        (variable_generator_profile_scenario_id,
         project_operational_chars_scenario_id)
    ]
    update_sql = """
        UPDATE inputs_project_operational_chars
        SET variable_generator_profile_scenario_id = ?
        WHERE (operational_type = 'gen_var' 
        OR operational_type = 'gen_var_must_take')
        AND project_operational_chars_scenario_id = ?;
        """
    spin_on_database_lock(conn=io, cursor=c, sql=update_sql, data=update_data)


def update_project_opchar_hydro_opchar_scenario_id(
        io, c,
        project_operational_chars_scenario_id,
        hydro_operational_chars_scenario_id
):
    """
    Update all 'gen_hydro_must_take' and 'gen_hydro' projects under
    a given project_operational_chars_scenario_id with a single
    hydro_operational_chars_scenario_id
    :param io:
    :param c:
    :param project_operational_chars_scenario_id:
    :param hydro_operational_chars_scenario_id:
    :return:
    """
    update_data = [
        (hydro_operational_chars_scenario_id,
         project_operational_chars_scenario_id)
    ]
    update_sql = """
        UPDATE inputs_project_operational_chars
        SET hydro_operational_chars_scenario_id = ?
        WHERE (operational_type = 'gen_hydro'
        OR operational_type ='gen_hydro_must_take')
        AND project_operational_chars_scenario_id = ?;
        """
    spin_on_database_lock(conn=io, cursor=c, sql=update_sql, data=update_data)


def update_project_variable_profiles(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    """
    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_variable_generator_profiles
        (project, variable_generator_profile_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_variable_generator_profiles
        (project, variable_generator_profile_scenario_id, stage_id,
        timepoint, cap_factor)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


def update_project_hydro_opchar(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    """
    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_hydro_operational_chars
        (project, hydro_operational_chars_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_hydro_operational_chars
        (project, hydro_operational_chars_scenario_id, 
        balancing_type_project, horizon, period, 
        average_power_fraction, min_power_fraction, max_power_fraction)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


def update_project_hr_curves(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    """
    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_heat_rate_curves
        (project, heat_rate_curves_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_heat_rate_curves
        (project, heat_rate_curves_scenario_id, period, load_point_fraction, 
        average_heat_rate_mmbtu_per_mwh)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


def update_project_vom_curves(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    """
    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_variable_om_curves
        (project, variable_om_curves_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_variable_om_curves
        (project, variable_om_curves_scenario_id, period, load_point_fraction, 
        average_variable_om_cost_per_mwh)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


def update_project_startup_chars(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    """
    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_startup_chars
        (project, startup_chars_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_startup_chars
        (project, startup_chars_scenario_id, 
        down_time_cutoff_hours, startup_plus_ramp_up_rate, startup_cost_per_mw)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


def load_from_csv(io, c, subscenario_input, data_input):
    """
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    # TODO: why is this needed? We're missing documentation
    # TODO: can this be handled differently without having to hard code?
    operational_chars_integers = ['heat_rate_curves_scenario_id',
                                  'variable_om_curves_scenario_id',
                                  'startup_chars_scenario_id',
                                  'min_up_time_hours', 'min_down_time_hours',
                                  'variable_generator_profile_scenario_id',
                                  'hydro_operational_chars_scenario_id']
    operational_chars_non_integers = data_input.columns.difference(
        operational_chars_integers + ['id', 'project']).tolist()

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['id'] == sc_id)]
        # Make subscenario and insert all projects into operational
        # characteristics table; we'll then update that table with the
        # operational characteristics each project needs
        make_scenario_and_insert_all_projects(
            io=io, c=c,
            project_operational_chars_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description
        )

        # ### Operational chars integers ### #
        for op_chars in operational_chars_integers:
            if data_input_subscenario[op_chars].notnull().sum() != 0:
                operational_chars_df = \
                    data_input_subscenario.loc[
                        :, ['project', op_chars]
                    ].dropna()
                operational_chars_df[[op_chars]] = operational_chars_df[
                    [op_chars]].astype(int)  # Otherwise they could be floats or numpy ints
                operational_chars_dict = operational_chars_df.set_index(
                    'project')[op_chars].to_dict()

                update_project_opchar_column(
                    io=io, c=c,
                    project_operational_chars_scenario_id=sc_id,
                    column=op_chars,
                    project_char=operational_chars_dict
                )

        # ### Operational chars non-integers (strings and floats) ### #
        for op_chars in operational_chars_non_integers:
            if data_input_subscenario[op_chars].notnull().sum() != 0:
                operational_chars_dict = \
                    data_input_subscenario.loc[
                        :, ['project', op_chars]
                    ].dropna().set_index('project')[op_chars].to_dict()

                update_project_opchar_column(
                    io=io, c=c,
                    project_operational_chars_scenario_id=sc_id,
                    column=op_chars,
                    project_char=operational_chars_dict
                )


if __name__ == "__main__":
    pass
