#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Candidate project potentials
"""
from __future__ import print_function

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
    print("project new potentials")

    # Subscenarios
    subs_data = [(project_new_potential_scenario_id, scenario_name,
            scenario_description)]
    subs_sql = \
        """INSERT INTO subscenarios_project_new_potential
         (project_new_potential_scenario_id, name, description)
         VALUES (?, ?, ?);"""
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for prj in list(project_period_potentials.keys()):
        for period in list(project_period_potentials[prj].keys()):
            inputs_data.append(
                (project_new_potential_scenario_id, prj, period,
                 'NULL' if project_period_potentials[prj][period][0] is
                 None else project_period_potentials[prj][period][0],
                 'NULL' if project_period_potentials[prj][period][1] is
                 None else project_period_potentials[prj][period][1],
                 'NULL' if project_period_potentials[prj][period][2] is
                 None else project_period_potentials[prj][period][2],
                 'NULL' if project_period_potentials[prj][period][3] is
                 None else project_period_potentials[prj][period][3])
            )
    inputs_sql = \
        """INSERT INTO inputs_project_new_potential
        (project_new_potential_scenario_id, project, period,
        minimum_cumulative_new_build_mw,
        minimum_cumulative_new_build_mwh,
        maximum_cumulative_new_build_mw, 
        maximum_cumulative_new_build_mwh)
        VALUES (?, ?, ?, ?, ?, ?, ?);"""
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
