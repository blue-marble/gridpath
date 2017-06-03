#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Candidate project potentials
"""


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
    c.execute(
        """INSERT INTO subscenarios_project_new_potential
         (project_new_potential_scenario_id, name, description)
         VALUES ({}, '{}', '{}');""".format(
            project_new_potential_scenario_id, scenario_name,
            scenario_description
        )
    )
    io.commit()

    # Insert data
    for prj in project_period_potentials.keys():
        for period in project_period_potentials[prj].keys():
            c.execute(
                """INSERT INTO inputs_project_new_potential
                (project_new_potential_scenario_id, project, period,
                minimum_cumulative_new_build_mw,
                minimum_cumulative_new_build_mwh,
                maximum_cumulative_new_build_mw, 
                maximum_cumulative_new_build_mwh)
                VALUES ({}, '{}', {}, {}, {}, {}, {});""".format(
                    project_new_potential_scenario_id, prj, period,
                    'NULL' if project_period_potentials[prj][period][0] is
                    None else project_period_potentials[prj][period][0],
                    'NULL' if project_period_potentials[prj][period][1] is
                    None else project_period_potentials[prj][period][1],
                    'NULL' if project_period_potentials[prj][period][2] is
                    None else project_period_potentials[prj][period][2],
                    'NULL' if project_period_potentials[prj][period][3] is
                    None else project_period_potentials[prj][period][3]

                )
            )
    io.commit()
