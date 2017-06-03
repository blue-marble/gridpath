#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
ELCC characteristics of projects
"""

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
    print("project elcc characteristics")
    # Subscenarios
    c.execute(
        """INSERT INTO subscenarios_project_elcc_chars
        (project_elcc_chars_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            project_elcc_chars_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for proj in proj_prm_type.keys():
        c.execute(
            """INSERT INTO inputs_project_elcc_chars 
            (project_elcc_chars_scenario_id, project, prm_type)
            VALUES ({}, '{}', '{}');""".format(
                project_elcc_chars_scenario_id, proj,
                proj_prm_type[proj]
            )
        )
    io.commit()

    # Update the rest of the data and warn for inconsistencies
    # ELCC simple fraction
    for proj in proj_elcc_simple_fraction.keys():
        c.execute(
            """UPDATE inputs_project_elcc_chars
            SET elcc_simple_fraction = {}
            WHERE project = '{}'
            AND project_elcc_chars_scenario_id = {};""".format(
                proj_elcc_simple_fraction[proj], proj,
                project_elcc_chars_scenario_id
            )
        )
    io.commit()

    # ELCC surface
    for proj in proj_elcc_surface.keys():
        c.execute(
            """UPDATE inputs_project_elcc_chars
            SET contributes_to_elcc_surface = {}
            WHERE project = '{}'
            AND project_elcc_chars_scenario_id = {};""".format(
                proj_elcc_surface[proj], proj,
                project_elcc_chars_scenario_id
            )
        )
    io.commit()

    # Min duration for full capacity credit
    energy_limited_projects = [p[0] for p in c.execute(
        """SELECT project
        FROM inputs_project_elcc_chars
        WHERE prm_type = 'fully_deliverable_energy_limited'
        AND project_elcc_chars_scenario_id = {};""".format(
            project_elcc_chars_scenario_id
        )
    ).fetchall()]

    # Check if all of these projects will be assigned a min duration
    for proj in energy_limited_projects:
        if proj not in proj_min_duration_for_full.keys():
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

    for proj in proj_min_duration_for_full.keys():
        # Check if proj is actually energy-limited, as it doesn't require
        # this param otherwise
        if proj not in energy_limited_projects:
            warnings.warn(
                """Project {} is not of the 
                'fully_deliverable_energy_limited' PRM type in 
                project_elcc_chars_scenario_id {}, so does not 
                need the 'min_duration_for_full_capacity_credit_hours' 
                parameter.""".format(proj, project_elcc_chars_scenario_id)
            )

        c.execute(
            """UPDATE inputs_project_elcc_chars
            SET min_duration_for_full_capacity_credit_hours = {}
            WHERE project = '{}'
            AND project_elcc_chars_scenario_id = {};""".format(
                proj_min_duration_for_full[proj], proj,
                project_elcc_chars_scenario_id
            )
        )
    io.commit()

    # Deliverability group
    energy_only_projects = [p[0] for p in c.execute(
        """SELECT project
        FROM inputs_project_elcc_chars
        WHERE prm_type = 'energy_only_allowed'
        AND project_elcc_chars_scenario_id = {};""".format(
            project_elcc_chars_scenario_id
        )
    ).fetchall()]

    # Check if all of these projects will be assigned a deliverability group
    for proj in energy_only_projects:
        if proj not in proj_deliv_group.keys():
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

    for proj in proj_deliv_group.keys():
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

        c.execute(
            """UPDATE inputs_project_elcc_chars
            SET deliverability_group = '{}'
            WHERE project = '{}'
            AND project_elcc_chars_scenario_id = {};""".format(
                proj_deliv_group[proj], proj,
                project_elcc_chars_scenario_id
            )
        )
    io.commit()


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
    print("deliverability group params")

    # Subscenarios
    c.execute(
        """INSERT INTO subscenarios_project_prm_energy_only
        (prm_energy_only_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            prm_energy_only_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    # Insert data
    for group in deliv_group_params.keys():
        c.execute(
            """INSERT INTO inputs_project_prm_energy_only
            (prm_energy_only_scenario_id,
            deliverability_group, 
            deliverability_group_no_cost_deliverable_capacity_mw,
            deliverability_group_deliverability_cost_per_mw,
            deliverability_group_energy_only_capacity_limit_mw)
            VALUES ({}, '{}', {}, {}, {});""".format(
                prm_energy_only_scenario_id, group,
                deliv_group_params[group][0],
                deliv_group_params[group][1],
                deliv_group_params[group][2]
            )
        )


def elcc_surface(
    io, c,
    prm_zone_scenario_id,
    project_prm_zone_scenario_id,
    elcc_surface_scenario_id,
    scenario_name,
    scenario_description,
    zone_period_facet_intercepts,
    proj_period_facet_coeff
):
    """

    :param io:
    :param c:
    :param prm_zone_scenario_id:
    :param project_prm_zone_scenario_id:
    :param elcc_surface_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param zone_period_facet_intercepts:
    :param proj_period_facet_coeff:
    :return:
    """
    print("elcc surface")

    # Subscenarios
    c.execute(
        """INSERT INTO subscenarios_system_elcc_surface
        (prm_zone_scenario_id, elcc_surface_scenario_id, name, description)
        VALUES ({}, {}, '{}', '{}');""".format(
            prm_zone_scenario_id, elcc_surface_scenario_id,
            scenario_name, scenario_description
        )
    )
    io.commit()

    # ELCC surface intercepts (by PRM zone)
    for zone in zone_period_facet_intercepts.keys():
        for period in zone_period_facet_intercepts[zone].keys():
            for facet in zone_period_facet_intercepts[zone][period].keys():
                c.execute(
                    """INSERT INTO inputs_system_prm_zone_elcc_surface
                    (prm_zone_scenario_id, elcc_surface_scenario_id, prm_zone,
                     period, facet, elcc_surface_intercept)
                    VALUES ({}, {}, '{}', {}, {}, {});""".format(
                        prm_zone_scenario_id, elcc_surface_scenario_id,
                        zone, period, facet,
                        zone_period_facet_intercepts[zone][period][facet]
                    )
                )
    io.commit()

    # ELCC coefficients (by project)
    for proj in proj_period_facet_coeff.keys():
        for period in proj_period_facet_coeff[proj].keys():
            for facet in proj_period_facet_coeff[proj][period].keys():
                c.execute(
                    """INSERT INTO inputs_project_elcc_surface 
                    (prm_zone_scenario_id, 
                    project_prm_zone_scenario_id,
                    elcc_surface_scenario_id, 
                    project, period, facet, elcc_surface_coefficient)
                    VALUES ({}, {}, {}, '{}', {}, {}, {});""".format(
                        prm_zone_scenario_id, project_prm_zone_scenario_id,
                        elcc_surface_scenario_id,
                        proj, period, facet,
                        proj_period_facet_coeff[proj][period][facet]
                    )
                )
    io.commit()
