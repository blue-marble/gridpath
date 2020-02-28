#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
ELCC characteristics of projects
"""

from db.common_functions import spin_on_database_lock


import warnings


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
        INSERT INTO subscenarios_project_elcc_chars
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
        INSERT INTO inputs_project_elcc_chars 
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
        # TODO: handle this differently because now we get redundant warnings
        #  when there are no entries in the project_elcc_chars table for the
        #  min_duration (column is there so best you can do is leave it empty)
        if proj not in energy_limited_projects:
            warnings.warn(
                """Project {} is not of the 
                'fully_deliverable_energy_limited' PRM type in 
                project_elcc_chars_scenario_id {}, so does not 
                need the 'min_duration_for_full_capacity_credit_hours' 
                parameter.""".format(proj, project_elcc_chars_scenario_id)
            )
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
        if proj not in energy_only_projects:
            warnings.warn(
                """Project {} is not of the 
                'energy_only_allowed' PRM type in 
                project_elcc_chars_scenario_id {}, so does not 
                need the 'deliverability_group' 
                parameter.""".format(proj, project_elcc_chars_scenario_id)
            )

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
    prm_energy_only_scenario_id,
    scenario_name,
    scenario_description,
    deliv_group_params
):
    """

    :param io:
    :param c:
    :param prm_energy_only_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param deliv_group_params:
    Dictionary with groups as keys and params in a tuple (no_cost_cap,
    deliv_cost, energy_only_limit)
    :return:
    """
    # Subscenarios
    subs_data = [(prm_energy_only_scenario_id, scenario_name,
                  scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_project_prm_energy_only
        (prm_energy_only_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for group in list(deliv_group_params.keys()):
        inputs_data.append(
            (prm_energy_only_scenario_id, group,
             deliv_group_params[group][0],
             deliv_group_params[group][1],
             deliv_group_params[group][2])
        )
    inputs_sql = """
        INSERT INTO inputs_project_prm_energy_only
        (prm_energy_only_scenario_id,
        deliverability_group, 
        deliverability_group_no_cost_deliverable_capacity_mw,
        deliverability_group_deliverability_cost_per_mw,
        deliverability_group_energy_only_capacity_limit_mw)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def elcc_surface(
    io, c,
    elcc_surface_scenario_id,
    scenario_name,
    scenario_description,
    zone_period_facet_intercepts,
    proj_period_facet_coeff
):
    """

    :param io:
    :param c:
    :param elcc_surface_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param zone_period_facet_intercepts:
    :param proj_period_facet_coeff:
    :return:
    """
    # Subscenarios
    subs_data = [(elcc_surface_scenario_id,
                  scenario_name, scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_system_elcc_surface
        (elcc_surface_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # ELCC surface intercepts (by PRM zone)
    ints_data = []
    for zone in list(zone_period_facet_intercepts.keys()):
        for period in list(zone_period_facet_intercepts[zone].keys()):
            for facet in list(
                    zone_period_facet_intercepts[zone][period].keys()
            ):
                ints_data.append(
                    (elcc_surface_scenario_id,
                     zone, period, facet,
                     zone_period_facet_intercepts[zone][period][facet])
                )
    inputs_sql = """
        INSERT INTO inputs_system_prm_zone_elcc_surface
        (elcc_surface_scenario_id, prm_zone,
         period, facet, elcc_surface_intercept)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=ints_data)

    # ELCC coefficients (by project)
    coef_data = []
    for proj in list(proj_period_facet_coeff.keys()):
        for period in list(proj_period_facet_coeff[proj].keys()):
            for facet in list(proj_period_facet_coeff[proj][period].keys()):
                coef_data.append(
                    (elcc_surface_scenario_id, proj, period, facet,
                     proj_period_facet_coeff[proj][period][facet])
                )
    coef_sql = """
        INSERT INTO inputs_project_elcc_surface 
        (elcc_surface_scenario_id, 
        project, period, facet, elcc_surface_coefficient)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=coef_sql, data=coef_data)
