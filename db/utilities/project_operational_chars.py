#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Project operational characteristics
"""
from __future__ import print_function


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

    for project in list(project_char.keys()):
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
    for prj in proj_profile_names.keys():
        for scenario_id in proj_profile_names[prj].keys():
            c.execute(
                """INSERT INTO subscenarios_project_variable_generator_profiles
                (project, variable_generator_profile_scenario_id, name, description)
                VALUES ('{}', {}, '{}', '{}');""".format(
                    prj, scenario_id, proj_profile_names[prj][scenario_id][0],
                    proj_profile_names[prj][scenario_id][1]
                )
            )
    io.commit()

    # Insert data
    for prj in list(proj_tmp_profiles.keys()):
        print("..." + prj)
        for scenario in list(proj_tmp_profiles[prj].keys()):
            for stage in proj_tmp_profiles[prj][scenario].keys():
                for tmp in list(
                        proj_tmp_profiles[prj][scenario][stage].keys()
                ):
                    c.execute(
                        """INSERT INTO inputs_project_variable_generator_profiles
                        (project, variable_generator_profile_scenario_id, stage_id,
                        timepoint, cap_factor)
                        VALUES ('{}', {}, {}, {}, {});""".format(
                            prj, scenario, stage, tmp,
                            proj_tmp_profiles[prj][scenario][stage][tmp]
                        )
                    )
            io.commit()


def update_project_hydro_opchar(
        io, c,
        proj_opchar_names,
        proj_horizon_chars
):
    """

    :param io:
    :param c:
    :param proj_opchar_names:
    :param proj_horizon_chars:
    Nested dictionary: top-level key is the project name, second key is the
    horizon, third-level keys are 'mwa' (the energy budget (MWa)),
    min_mw (minimum MW) and max_mw (maximum MW), with a value for each
    :return:
    """
    print("project hydro operating characteristics")

    # Subscenarios
    for prj in proj_opchar_names.keys():
        for scenario_id in proj_opchar_names[prj].keys():
            c.execute(
                """INSERT INTO subscenarios_project_hydro_operational_chars
                (project, hydro_operational_chars_scenario_id, name, description)
                VALUES ('{}', {}, '{}', '{}');""".format(
                    prj, scenario_id, proj_opchar_names[prj][scenario_id][0],
                    proj_opchar_names[prj][scenario_id][1]
                )
            )
    io.commit()

    # Insert data
    for p in list(proj_horizon_chars.keys()):
        for scenario in list(proj_horizon_chars[p].keys()):
            for h in list(proj_horizon_chars[p][scenario].keys()):
                c.execute(
                    """INSERT INTO inputs_project_hydro_operational_chars
                    (project, hydro_operational_chars_scenario_id, horizon, 
                    average_power_mwa, min_power_mw, max_power_mw)
                    VALUES ('{}', {}, {}, {}, {}, {});""".format(
                        p, scenario, h,
                        proj_horizon_chars[p][scenario][h]["mwa"],
                        proj_horizon_chars[p][scenario][h]["min_mw"],
                        proj_horizon_chars[p][scenario][h]["max_mw"]
                    )
                )
    io.commit()


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
    for prj in proj_opchar_names.keys():
        for scenario_id in proj_opchar_names[prj].keys():
            c.execute(
                """INSERT INTO subscenarios_project_heat_rate_curves
                (project, heat_rate_curves_scenario_id, name, description)
                VALUES ('{}', {}, '{}', '{}');""".format(
                    prj, scenario_id, proj_opchar_names[prj][scenario_id][0],
                    proj_opchar_names[prj][scenario_id][1]
                )
            )
    io.commit()

    # Insert data
    for p in list(proj_hr_chars.keys()):
        for scenario in list(proj_hr_chars[p].keys()):
            for hr_curve_point in list(proj_hr_chars[p][scenario].keys()):
                print(proj_hr_chars[p][scenario][hr_curve_point])
                c.execute(
                    """INSERT INTO inputs_project_heat_rate_curves
                    (project, heat_rate_curves_scenario_id, load_point_mw, 
                    average_heat_rate_mmbtu_per_mwh)
                    VALUES ('{}', {}, {}, {});""".format(
                        p, scenario,
                        proj_hr_chars[p][scenario][hr_curve_point][0],
                        proj_hr_chars[p][scenario][hr_curve_point][1]
                    )
                )
    io.commit()


if __name__ == "__main__":
    pass
