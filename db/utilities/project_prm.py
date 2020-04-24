#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
ELCC characteristics of projects
"""

import warnings

from db.common_functions import spin_on_database_lock
from db.utilities.common_functions import \
    parse_subscenario_directory_contents, csv_to_tuples


def project_elcc_chars(
        io, c,
        project_elcc_chars_scenario_id,
        scenario_name,
        scenario_description,
        proj_prm_type,
        proj_elcc_simple_fraction,
        proj_elcc_surface,
        proj_min_duration_for_full,
        proj_deliv_group

):
    """

    :param io:
    :param c:
    :param project_elcc_chars_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param proj_prm_type:
    :param proj_elcc_simple_fraction:
    :param proj_elcc_surface:
    :param proj_min_duration_for_full:
    :param proj_deliv_group:
    :return:
    """
    # Subscenarios
    subs_data = [
        (project_elcc_chars_scenario_id, scenario_name, scenario_description)
    ]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_elcc_chars
        (project_elcc_chars_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for proj in list(proj_prm_type.keys()):
        inputs_data.append(
            (project_elcc_chars_scenario_id, proj, proj_prm_type[proj])
        )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_elcc_chars 
        (project_elcc_chars_scenario_id, project, prm_type)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)

    # Update the rest of the data and warn for inconsistencies
    # ELCC simple fraction
    update_data = []
    for proj in list(proj_elcc_simple_fraction.keys()):
        update_data.append(
            (proj_elcc_simple_fraction[proj], proj,
             project_elcc_chars_scenario_id)
        )
    update_sql = """
        UPDATE inputs_project_elcc_chars
        SET elcc_simple_fraction = ?
        WHERE project = ?
        AND project_elcc_chars_scenario_id = ?;
        """
    spin_on_database_lock(conn=io, cursor=c, sql=update_sql, data=update_data)

    # ELCC surface
    surf_data = []
    for proj in list(proj_elcc_surface.keys()):
        surf_data.append(
            (proj_elcc_surface[proj], proj, project_elcc_chars_scenario_id)
        )
    surf_sql = """
        UPDATE inputs_project_elcc_chars
        SET contributes_to_elcc_surface = ?
        WHERE project = ?
        AND project_elcc_chars_scenario_id = ?;
        """
    spin_on_database_lock(conn=io, cursor=c, sql=surf_sql, data=surf_data)

    # Min duration for full capacity credit
    energy_limited_projects = [p[0] for p in c.execute(
        """SELECT project
        FROM inputs_project_elcc_chars
        WHERE prm_type = 'fully_deliverable_energy_limited'
        AND project_elcc_chars_scenario_id = {};
        """.format(
            project_elcc_chars_scenario_id
        )
    ).fetchall()]

    # Check if all of these projects will be assigned a min duration
    for proj in energy_limited_projects:
        if proj not in list(proj_min_duration_for_full.keys()):
            warnings.warn(
                """Project {} is of the 'fully_deliverable_energy_limited' 
                PRM type in project_elcc_chars_scenario_id {}, so should be 
                assigned a value for the 
                'min_duration_for_full_capacity_credit_hours' parameter. 
                Add this project to the proj_min_duration_for_full 
                dictionary.""".format(
                    proj, project_elcc_chars_scenario_id
                )
            )

    min_dur_data = []
    for proj in list(proj_min_duration_for_full.keys()):
        # Check if proj is actually energy-limited, as it doesn't require
        # this param otherwise
        # TODO: handle this differently because now we woul get redundant
        #  warnings when there are no entries in the project_elcc_chars
        #  table for the min_duration (column is there so best you can do is
        #  leave it empty)
        if proj not in energy_limited_projects:
            # warnings.warn(
            #     """Project {} is not of the
            #     'fully_deliverable_energy_limited' PRM type in
            #     project_elcc_chars_scenario_id {}, so does not
            #     need the 'min_duration_for_full_capacity_credit_hours'
            #     parameter.""".format(proj, project_elcc_chars_scenario_id)
            # )
            pass
        min_dur_data.append(
            (proj_min_duration_for_full[proj], proj,
             project_elcc_chars_scenario_id)
        )
    min_dur_sql = """
        UPDATE inputs_project_elcc_chars
        SET min_duration_for_full_capacity_credit_hours = ?
        WHERE project = ?
        AND project_elcc_chars_scenario_id = ?;
        """
    spin_on_database_lock(conn=io, cursor=c, sql=min_dur_sql,
                          data=min_dur_data)

    # Deliverability group
    energy_only_projects = [p[0] for p in c.execute(
        """SELECT project
        FROM inputs_project_elcc_chars
        WHERE prm_type = 'energy_only_allowed'
        AND project_elcc_chars_scenario_id = {};
        """.format(
            project_elcc_chars_scenario_id
        )
    ).fetchall()]

    # Check if all of these projects will be assigned a deliverability group
    for proj in energy_only_projects:
        if proj not in list(proj_deliv_group.keys()):
            warnings.warn(
                """Project {} is of the 'energy_only_allowed' 
                PRM type in project_elcc_chars_scenario_id {}, so should be 
                assigned a value for the 
                'deliverability_group' parameter. 
                Add this project to the proj_deliv_group 
                dictionary.""".format(
                    proj, project_elcc_chars_scenario_id
                )
            )

    del_g_data = []
    for proj in list(proj_deliv_group.keys()):
        # Check if proj is actually energy-only, as it doesn't require
        # this param otherwise
        # TODO: commenting out the warning for now, but figure out how to
        #  handle this situation
        if proj not in energy_only_projects:
            # warnings.warn(
            #     """Project {} is not of the
            #     'energy_only_allowed' PRM type in
            #     project_elcc_chars_scenario_id {}, so does not
            #     need the 'deliverability_group'
            #     parameter.""".format(proj, project_elcc_chars_scenario_id)
            # )
            pass

        del_g_data.append(
            (proj_deliv_group[proj], proj, project_elcc_chars_scenario_id)
        )
    del_g_sql = """
        UPDATE inputs_project_elcc_chars
        SET deliverability_group = ?
        WHERE project = ?
        AND project_elcc_chars_scenario_id = ?;
        """
    spin_on_database_lock(conn=io, cursor=c, sql=del_g_sql, data=del_g_data)


def deliverability_groups(
    io, c,
    subscenario_data, inputs_data
):
    """

    :param io:
    :param c:
    :param subscenario_data:
    :param inputs_data:
    """
    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_prm_energy_only
        (prm_energy_only_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_prm_energy_only
        (prm_energy_only_scenario_id,
        deliverability_group, 
        deliverability_group_no_cost_deliverable_capacity_mw,
        deliverability_group_deliverability_cost_per_mw,
        deliverability_group_energy_only_capacity_limit_mw)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def elcc_surface(
    conn,
    subscenario_data,
    zone_data,
    projects_data
):
    """

    :param conn:
    :param subscenario_data: list of tuples
        (elcc_surface_scenario_id, name, description)
    :param zone_data: list of tuples
        (elcc_surface_scenario_id, prm_zone, period, facet,
        elcc_surface_intercept)
    :param projects_data: list of tuples
        (elcc_surface_scenario_id, project, period, facet,
        elcc_surface_coefficient)
    """

    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_system_elcc_surface
        (elcc_surface_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # ELCC surface intercepts (by PRM zone)
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_system_prm_zone_elcc_surface
        (elcc_surface_scenario_id, prm_zone,
         period, facet, elcc_surface_intercept)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql, data=zone_data)

    # ELCC coefficients (by project)
    coef_sql = """
        INSERT OR IGNORE INTO inputs_project_elcc_surface 
        (elcc_surface_scenario_id, 
        project, period, facet, elcc_surface_coefficient)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=coef_sql,
                          data=projects_data)


def elcc_surface_load_from_csvs(conn, subscenario_directory):
    """
    :param conn:
    :param subscenario_directory: string, path to the directory containing
        the data for this elcc_surface_scenario_id

    Each ELCC surface subscenario is a directory, with the subscenario ID,
    underscore, and the subscenario name as the name of the directory (already
    passed here), so we get this to import from the subscenario_directory path.

    Within each subscenario directory there are two required files:
    zone.csv and projects.csv. A file with the subscenario description
    (description.txt) is optional.
    """

    # Get the subscenario (id, name, description) data for insertion into the
    # subscenario table and the paths to the required input files
    subscenario_data, [zone_file, projects_file] = \
        parse_subscenario_directory_contents(
            subscenario_directory=subscenario_directory,
            csv_file_names=["zone.csv", "projects.csv"]
        )

    # Get the subscenario_id from the subscenario_data tuple
    subscenario_id = subscenario_data[0]

    # Get the ELCC surface intercepts (by zone)
    zone_tuples_list = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=zone_file
    )

    # Get the ELCC surface coefficients (by project)
    projects_tuples_list = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=projects_file
    )

    elcc_surface(
        conn=conn,
        subscenario_data=[subscenario_data],
        zone_data=zone_tuples_list,
        projects_data=projects_tuples_list
    )
