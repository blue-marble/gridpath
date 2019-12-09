#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Project operational characteristics
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock


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
        INSERT INTO subscenarios_project_operational_chars (
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
        INSERT INTO inputs_project_operational_chars
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

    print("project " + column)

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
    print("project opchar variable profiles scenario id")
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
    print("project opchar hydro opchar scenario id")
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
        io, c,
        proj_profile_names,
        proj_tmp_profiles
):
    """

    :param io:
    :param c:
    :param proj_profile_names: nested dictionary; top level is the project
        name, second-level is the scenario id; the value is a tuple with the
        scenario name and the scenario description
    :param proj_tmp_profiles:
        Nested dictionary: top-level key is the project name, second-level key
        is the scenario id, third-level key is the stage, fourth level
        key is the timepoint, and the value is the capacity factor for that
        project-timepoint.
    :return:
    """
    print("project variable profiles")
    # Subscenarios
    subs_data = []
    for prj in proj_profile_names.keys():
        for scenario_id in proj_profile_names[prj].keys():
            subs_data.append(
                (prj, scenario_id, proj_profile_names[prj][scenario_id][0],
                 proj_profile_names[prj][scenario_id][1])
            )
    subs_sql = """
        INSERT INTO subscenarios_project_variable_generator_profiles
        (project, variable_generator_profile_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for prj in list(proj_tmp_profiles.keys()):
        print("..." + prj)
        for scenario in list(proj_tmp_profiles[prj].keys()):
            for stage in proj_tmp_profiles[prj][scenario].keys():
                for tmp in list(
                        proj_tmp_profiles[prj][scenario][stage].keys()
                ):
                    inputs_data.append(
                        (prj, scenario, stage, tmp,
                            proj_tmp_profiles[prj][scenario][stage][tmp])
                    )
    inputs_sql = """
        INSERT INTO inputs_project_variable_generator_profiles
        (project, variable_generator_profile_scenario_id, stage_id,
        timepoint, cap_factor)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def update_project_hydro_opchar(
        io, c,
        proj_opchar_names,
        proj_horizon_chars
):
    """

    :param io:
    :param c:
    :param proj_opchar_names: nested dictionary; top level is the project
        name, second-level is the scenario id; the value is a tuple with the
        scenario name and the scenario description
    :param proj_horizon_chars:
        Nested dictionary: top-level key is the project name, second key is
        the balancing type, third key is the horizon, fourth-level keys are
        'period' (the period of the horizon), 'avg' (the energy budget in avg
        fraction of capacity), min (minimum as fraction of capacity) and max
        (maximum as fraction of capacity), with a value for each
    :return:
    """
    print("project hydro operating characteristics")

    # Subscenarios
    subs_data = []
    for prj in proj_opchar_names.keys():
        for scenario_id in proj_opchar_names[prj].keys():
            subs_data.append(
                (prj, scenario_id, proj_opchar_names[prj][scenario_id][0],
                 proj_opchar_names[prj][scenario_id][1])
            )
    subs_sql = """
        INSERT INTO subscenarios_project_hydro_operational_chars
        (project, hydro_operational_chars_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for p in list(proj_horizon_chars.keys()):
        for scenario in list(proj_horizon_chars[p].keys()):
            for bt in list(proj_horizon_chars[p][scenario].keys()):
                for h in list(proj_horizon_chars[p][scenario][bt].keys()):
                    inputs_data.append(
                        (p, scenario, bt, h,
                         proj_horizon_chars[p][scenario][bt][h]["period"],
                         proj_horizon_chars[p][scenario][bt][h]["avg"],
                         proj_horizon_chars[p][scenario][bt][h]["min"],
                         proj_horizon_chars[p][scenario][bt][h]["max"])
                    )
    inputs_sql = """
        INSERT INTO inputs_project_hydro_operational_chars
        (project, hydro_operational_chars_scenario_id, 
        balancing_type_project, horizon, period, 
        average_power_fraction, min_power_fraction, max_power_fraction)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def update_project_hr_curves(
        io, c,
        proj_opchar_names,
        proj_hr_chars
):
    """

    :param io:
    :param c:
    :param proj_opchar_names: nested dictionary; top level key is the
    project, second key is the heat_rate_curves_scenario_id, the value is a
    tuple with the name and description of heat rate curve scenario
    :param proj_hr_chars: nested dictionary; top level key is the project,
    second-level key is the heat_rate_curves_scenario_id, the third-level
    key is the heat rate curve point and the value is a tuple with the load
    point and average heat rate at that load point
    :return:
    """
    print("project heat rate curves")

    # Subscenarios
    subs_data = []
    for prj in proj_opchar_names.keys():
        for scenario_id in proj_opchar_names[prj].keys():
            subs_data.append(
                (prj, scenario_id, proj_opchar_names[prj][scenario_id][0],
                 proj_opchar_names[prj][scenario_id][1])
            )
    subs_sql = """
        INSERT INTO subscenarios_project_heat_rate_curves
        (project, heat_rate_curves_scenario_id, name, description)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for p in list(proj_hr_chars.keys()):
        for scenario in list(proj_hr_chars[p].keys()):
            for hr_curve_point in list(proj_hr_chars[p][scenario].keys()):
                print(proj_hr_chars[p][scenario][hr_curve_point])
                inputs_data.append(
                    (p, scenario,
                     proj_hr_chars[p][scenario][hr_curve_point][0],
                     proj_hr_chars[p][scenario][hr_curve_point][1])
                )
    inputs_sql = """
        INSERT INTO inputs_project_heat_rate_curves
        (project, heat_rate_curves_scenario_id, load_point_mw, 
        average_heat_rate_mmbtu_per_mwh)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


if __name__ == "__main__":
    pass
