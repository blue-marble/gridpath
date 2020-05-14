#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
ELCC characteristics of projects
"""

import os.path
import pandas as pd
import warnings

from db.common_functions import spin_on_database_lock
from db.utilities.common_functions import \
    parse_subscenario_directory_contents, csv_to_tuples


# TODO: validations to add, as they have been removed here (some were
#  already commented out)
#  1. Check that all 'fully_deliverable_energy_limited' projects are
#  assigned a min_duration_for_full_capacity_credit_hours
#  2. Check if all ''energy_only_allowed' projects are assigned a
#  'deliverability group' and that other types are not assigned one


def elcc_surface(
    conn,
    subscenario_data,
    zone_intercepts_data,
    zone_load_data,
    project_coefficients_data,
    project_cap_factors_data
):
    """

    :param conn:
    :param subscenario_data: list of tuples
        (elcc_surface_scenario_id, name, description)
    :param zone_intercepts_data: list of tuples
        (elcc_surface_scenario_id, prm_zone, period, facet,
        elcc_surface_intercept)
    :param zone_load_data: list of tuples
        (elcc_surface_scenario_id, prm_zone, period, prm_peak_load_mw,
        prm_annual_load_mwh)
    :param project_coefficients_data: list of tuples
        (elcc_surface_scenario_id, project, period, facet,
        elcc_surface_coefficient)
    :param project_cap_factors_data: list of tuples
        (elcc_surface_scenario_id, project, elcc_surface_cap_factor)
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

    # ELCC surface intercepts (by PRM zone, period, facet)
    intercepts_sql = """
        INSERT OR IGNORE INTO inputs_system_prm_zone_elcc_surface
        (elcc_surface_scenario_id, prm_zone,
         period, facet, elcc_surface_intercept)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=intercepts_sql,
                          data=zone_intercepts_data)

    # PRM loads for the ELCC surface
    prm_loads_sql = """
        INSERT OR IGNORE INTO inputs_system_prm_zone_elcc_surface_prm_load
        (elcc_surface_scenario_id, prm_zone,
         period, prm_peak_load_mw, prm_annual_load_mwh)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=prm_loads_sql,
                          data=zone_load_data)

    # ELCC coefficients (by project, period, facet)
    coef_sql = """
        INSERT OR IGNORE INTO inputs_project_elcc_surface 
        (elcc_surface_scenario_id, 
        project, period, facet, elcc_surface_coefficient)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=coef_sql,
                          data=project_coefficients_data)

    # Cap factors for the ELCC surface (by project)
    capfac_sql = """
        INSERT OR IGNORE INTO inputs_project_elcc_surface_cap_factors 
        (elcc_surface_scenario_id, project, elcc_surface_cap_factor)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=capfac_sql,
                          data=project_cap_factors_data)

    c.close()


def elcc_surface_load_from_csvs(conn, subscenario_directory):
    """
    :param conn:
    :param subscenario_directory: string, path to the directory containing
        the data for this elcc_surface_scenario_id

    Each ELCC surface subscenario is a directory, with the subscenario ID,
    underscore, and the subscenario name as the name of the directory (already
    passed here), so we get this to import from the subscenario_directory path.

    Within each subscenario directory there are three required files:
    description.txt, zone.csv, and projects.csv.
    """

    # Get the subscenario (id, name, description) data for insertion into the
    # subscenario table and the paths to the required input files
    subscenario_data, \
        [zone_intercepts_file, zone_load_file, project_coefficients_file,
         project_cap_factors_file] = \
        parse_subscenario_directory_contents(
            subscenario_directory=subscenario_directory,
            csv_file_names=[
                "zone_intercepts.csv", "zone_peak_and_annual_load.csv",
                "project_coefficients.csv", "project_cap_factors.csv"
            ]
        )

    # Get the subscenario_id from the subscenario_data tuple
    subscenario_id = subscenario_data[0]

    # Get the ELCC surface intercepts (by zone, period, facet)
    zone_intercepts_tuples_list = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=zone_intercepts_file
    )

    # Get the peak and annual loads for the ELCC surface (by zone and period)
    zone_loads_tuples_list = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=zone_load_file
    )

    # Get the ELCC surface coefficients (by project, period, facet)
    project_coeffs_tuples_list = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=project_coefficients_file
    )

    # Get the cap factors for the ELCC surface (by project)
    project_capfacs_df_tuples_list = csv_to_tuples(
        subscenario_id=subscenario_id, csv_file=project_cap_factors_file
    )

    elcc_surface(
        conn=conn,
        subscenario_data=[subscenario_data],
        zone_intercepts_data=zone_intercepts_tuples_list,
        zone_load_data=zone_loads_tuples_list,
        project_coefficients_data=project_coeffs_tuples_list,
        project_cap_factors_data=project_capfacs_df_tuples_list
    )
