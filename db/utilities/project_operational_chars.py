#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Project operational characteristics
"""


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
    c.execute(
        """INSERT INTO subscenarios_project_operational_chars (
        project_operational_chars_scenario_id, name,
        description) VALUES ({}, '{}', '{}');""".format(
            project_operational_chars_scenario_id, scenario_name,
            scenario_description
        ))
    io.commit()

    # Insert all projects into operational chars table
    c.execute(
        """INSERT INTO inputs_project_operational_chars
        (project_operational_chars_scenario_id, project)
        SELECT {}, project
        FROM inputs_project_all;""".format(
            project_operational_chars_scenario_id
        )
    )
    io.commit()


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

    for project in project_char.keys():
        c.execute(
            """UPDATE inputs_project_operational_chars
            SET {} = {}
            WHERE project = '{}'
            AND project_operational_chars_scenario_id = {};""".format(
                column,
                ("'" + project_char[project] + "'"
                    if type(project_char[project]) is str
                    else project_char[project]),
                project,
                project_operational_chars_scenario_id)
        )
    io.commit()


def update_project_opchar_variable_gen_profile_scenario_id(
        io, c,
        project_operational_chars_scenario_id,
        variable_generator_profile_scenario_id
):
    """
    Update all 'variable' and 'variable_no_curtailment' project under a given 
    project_operational_chars_scenario_id with a single 
    variable_generator_profile_scenario_id
    :param io: 
    :param c: 
    :param project_operational_chars_scenario_id: 
    :param variable_generator_profile_scenario_id: 
    :return: 
    """
    print("project opchar variable profiles scenario id")
    c.execute(
        """UPDATE inputs_project_operational_chars
        SET variable_generator_profile_scenario_id = {}
        WHERE (operational_type = 'variable' 
        OR operational_type = 'variable_no_curtailment')
        AND project_operational_chars_scenario_id = {};""".format(
            variable_generator_profile_scenario_id,
            project_operational_chars_scenario_id
        )
    )
    io.commit()


def update_project_opchar_hydro_opchar_scenario_id(
        io, c,
        project_operational_chars_scenario_id,
        hydro_operational_chars_scenario_id
):
    """
    Update all 'hydro_noncurtailable' and 'hydro_curtailable' projects under 
    a given project_operational_chars_scenario_id with a single 
    hydro_operational_chars_scenario_id
    :param io: 
    :param c: 
    :param project_operational_chars_scenario_id: 
    :param hydro_operational_chars_scenario_id: 
    :return: 
    """
    print("project opchar hydro opchar scenario id")
    c.execute(
        """UPDATE inputs_project_operational_chars
        SET hydro_operational_chars_scenario_id = {}
        WHERE (operational_type = 'hydro_curtailable'
        OR operational_type ='hydro_noncurtailable')
        AND project_operational_chars_scenario_id = {};""".format(
            hydro_operational_chars_scenario_id,
            project_operational_chars_scenario_id
        )
    )
    io.commit()


def update_project_variable_profiles(
        io, c,
        variable_generator_profile_scenario_id,
        scenario_name,
        scenario_description,
        proj_tmp_profiles

):
    """
    
    :param io: 
    :param c: 
    :param variable_generator_profile_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param proj_tmp_profiles: 
    Nested dictionary: top-level key is the project name, second-level key 
    is the timepoint, and the value is the capacity factor for that 
    project-timepoint
    :return: 
    """
    print("project variable profiles")
    # Subscenarios
    c.execute(
        """INSERT INTO subscenarios_project_variable_generator_profiles
        (variable_generator_profile_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            variable_generator_profile_scenario_id, scenario_name,
            scenario_description
        )
    )
    io.commit()

    # Insert data
    for prj in proj_tmp_profiles.keys():
        print("..." + prj)
        for tmp in proj_tmp_profiles[prj].keys():
            c.execute(
                """INSERT INTO inputs_project_variable_generator_profiles
                (variable_generator_profile_scenario_id, project, 
                timepoint, cap_factor)
                VALUES ({}, '{}', {}, {});""".format(
                    variable_generator_profile_scenario_id, prj, tmp,
                    proj_tmp_profiles[prj][tmp]
                )
            )
            io.commit()


def update_project_hydro_opchar(
        io, c,
        hydro_operational_chars_scenario_id,
        scenario_name,
        scenario_description,
        proj_horizon_chars
):
    """
    
    :param io: 
    :param c: 
    :param hydro_operational_chars_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param proj_horizon_chars: 
    Nested dictionary: top-level key is the project name, second key is the 
    horizon, third-level keys are 'mwa' (the energy budget (MWa)), 
    min_mw (minimum MW) and max_mw (maximum MW), with a value for each
    :return: 
    """
    print("project hydro operating characteristics")

    # Subscenarios
    c.execute(
        """INSERT INTO subscenarios_project_hydro_operational_chars
        (hydro_operational_chars_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            hydro_operational_chars_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for p in proj_horizon_chars.keys():
        for h in proj_horizon_chars[p].keys():
            c.execute(
                """INSERT INTO inputs_project_hydro_operational_chars
                (hydro_operational_chars_scenario_id, project, horizon, 
                average_power_mwa, min_power_mw, max_power_mw)
                VALUES ({}, '{}', {}, {}, {}, {});""".format(
                    hydro_operational_chars_scenario_id,
                    p, h,
                    proj_horizon_chars[p][h]["mwa"],
                    proj_horizon_chars[p][h]["min_mw"],
                    proj_horizon_chars[p][h]["max_mw"]
                )
            )
    io.commit()

if __name__ == "__main__":
    pass
