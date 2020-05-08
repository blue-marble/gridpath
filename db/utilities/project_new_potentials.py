#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Candidate project potentials
"""

from db.common_functions import spin_on_database_lock


def update_project_potentials(
        io, c,
        project_new_potential_scenario_id,
        scenario_name,
        scenario_description,
        project_period_potentials
):
    """

    :param io: 
    :param c: 
    :param project_new_potential_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param project_period_potentials: 
    Two-level dictionary with project and period as keys, and the values for 
    min MW, min MWh, max MW, and max MWH in a tuple as value
    :return: 
    """

    # Subscenarios
    subs_data = [(project_new_potential_scenario_id, scenario_name,
            scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_new_potential
         (project_new_potential_scenario_id, name, description)
         VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for prj in list(project_period_potentials.keys()):
        for period in list(project_period_potentials[prj].keys()):
            inputs_data.append(
                (project_new_potential_scenario_id, prj, period,
                 project_period_potentials[prj][period][0],
                 project_period_potentials[prj][period][1],
                 project_period_potentials[prj][period][2],
                 project_period_potentials[prj][period][3])
            )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_new_potential
        (project_new_potential_scenario_id, project, period,
        min_cumulative_new_build_mw,
        min_cumulative_new_build_mwh,
        max_cumulative_new_build_mw, 
        max_cumulative_new_build_mwh)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def update_project_binary_build_sizes(
        io, c,
        project_new_binary_build_size_scenario_id,
        scenario_name,
        scenario_description,
        project_new_binary_build_sizes
):
    """

    :param io:
    :param c:
    :param project_new_binary_build_size_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param project_new_binary_build_sizes:
    Dictionary with project as key, and the values for
    the build size in MW and MWh in a tuple as value
    :return:
    """
    # Subscenarios
    subs_data = [(project_new_binary_build_size_scenario_id, scenario_name,
                  scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_new_binary_build_size
         (project_new_binary_build_size_scenario_id, name, description)
         VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for prj in list(project_new_binary_build_sizes.keys()):
        inputs_data.append(
            (project_new_binary_build_size_scenario_id,
             prj,
             project_new_binary_build_sizes[prj][0],
             project_new_binary_build_sizes[prj][1])
            )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_new_binary_build_size
        (project_new_binary_build_size_scenario_id, 
        project,
        binary_build_size_mw,
        binary_build_size_mwh)
        VALUES (?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
