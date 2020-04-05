#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The *port_csvs_to_gridpath.py* script ports the input data provided through
csvs to the sql database, which is created using the create_database.py
script. The csv_data_master.csv has the list of all the tables in the
gridpath database. The 'required' column in this csv indicates whether the
table is required [1] or optional [0]. The 'include' column indicates
whether the user would like to include this table and import the csv data
into this table [1] or omit the table [0]. The paths to the csv data
subfolders that house the csv scenario data for each table are also proided
in this master csv.

Input csvs for tables required for optional features are under the
'features' subfolder

The script will look for CSV files in each table's subfolder. It is
expecting that the CSV filenames will conform to a certain structure
indicating the ID and name for the subscenarios, and contain the data for
the subscenarios. See csvs_to_db_utilities.csvs_read for the  specific
requirements depending on the function called from that module.

The scenario.csv under the scenario folder holds the input data for the
scenario table, which indicates which subscenarios should be included in a
particular scenario by providing the subscenario_id. Each scenario has a
separate column. The user-defined name of the scenario should be entered as
the name of the scenario column.

The input params for this script include database name (db_name_, database
path (db_location), and csvs folder path (csv_location. The defaults are the
"io.db" database and "csvs" folder located under the "db" folder.

"""

import numpy as np
import os
import pandas as pd
import sqlite3
import sys
import warnings
from argparse import ArgumentParser

# Data-import modules
from db.common_functions import connect_to_database
from db.create_database import get_database_file_path

from db.utilities import temporal, simultaneous_flows, simultaneous_flow_groups

from db.csvs_to_db_utilities import csvs_read, \
    load_geography, load_project_specified_params, load_project_new_costs, \
    load_project_new_potentials, load_project_local_capacity_chars, \
    load_project_prm, load_transmission_zones, load_transmission_portfolios, \
    load_transmission_hurdle_rates, load_transmission_operational_chars, \
    load_system_rps, load_scenarios, load_fuels, load_project_availability, \
    load_system_reserves, load_project_zones, load_solver_options, \
    load_system_carbon_cap, load_transmission_new_cost, load_project_list, \
    load_project_operational_chars, load_system_prm, load_project_portfolios, \
    load_transmission_capacities, load_system_load, load_system_local_capacity

# Policy and reserves list
policy_list = ['carbon_cap', 'prm', 'rps', 'local_capacity']
reserves_list = ['frequency_response', 'lf_reserves_down', 'lf_reserves_up',
                 'regulation_down', 'regulation_up', 'spinning_reserves']


def parse_arguments(args):
    """
    :param args: the script arguments specified by the user
    :return: the parsed known argument values (<class 'argparse.Namespace'>
    Python object)

    Parse the known arguments.
    """
    parser = ArgumentParser(add_help=True)

    # Database name and location options
    # Adding defaults here even though the connect_to_database function has its own defaults
    # because parser passes a text string of None and not a python None
    parser.add_argument("--db_name", default="io",
                        help="Name of the database without the db extension.")
    parser.add_argument("--db_location", default=".",
                        help="Path to the database (relative to "
                             "port_csvs_to_db.py).")
    parser.add_argument("--csv_location", default="csvs",
                        help="Path to the csvs folder including folder name (relative to "
                             "port_csvs_to_db.py).")
    parser.add_argument("--quiet", default=False, action="store_true",
                        help="Don't print output.")
    #TODO: Using this argument for using the get_database_file_path function in create_database
    # but not sure if we need it.
    parser.add_argument("--in_memory", default=False, action="store_true",
                        help="Create in-memory database. The db_name and "
                             "db_location argument will be inactive.")

    parsed_arguments = parser.parse_known_args(args=args)[0]

    return parsed_arguments


def get_csv_folder_path(parsed_arguments, relative_path=".."):
    """
    :param parsed_arguments: the parsed script arguments
    :return: the path to the csv folder

    Get the csv folder path from the script arguments.
    If no csv folder is specified, assume that the folder is
    called 'csvs' and it is located under the 'db' folder.
    """

    csv_path = str(parsed_arguments.csv_location)

    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__),
                                relative_path, "db", "csvs")

    if not os.path.isdir(csv_path):
        raise OSError(
            "The csv folder {} was not found. Did you mean to "
            "specify a different csv folder?".format(
                os.path.abspath(csv_path)
            )
        )

    return csv_path


def load_csv_data(conn, csv_path, quiet):
    """
    The 'main' method parses the database name along with path as
    script arguments, reads the data from csvs, and loads the data
    in the database.

    TODO: update description
    """

    c2 = conn.cursor()

    #### MASTER CSV DATA ####
    # if include flag is 1, then read the feature, subscenario_id, table, and path into a dictionary and call the specific function for the feature
    # TODO: remove subscenario_id from master csv table. It's redundant.
    #folder_path = os.path.join(os.getcwd(),'db', 'csvs')
    folder_path = csv_path
    csv_data_master = pd.read_csv(os.path.join(folder_path, 'csv_data_master.csv'))

    #### LOAD TEMPORAL DATA ####
    if csv_data_master.loc[
        csv_data_master['table'] == 'temporal', 'include'
    ].iloc[0] != 1:
        print("ERROR: inputs_temporal table is required")
        sys.exit()
    else:
        temporal_directory = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'temporal', 'path'].iloc[
            0])
    # Get list of subdirectories (which are the names of our subscenarios)
    # Each temporal subscenario is a directory, with the scenario ID,
    # underscore, and the scenario name as the name of the directory (already
    # passed here).
    temporal_subscenarios = sorted(next(os.walk(temporal_directory))[1])
    for temporal_subscenario in temporal_subscenarios:
        if not quiet:
            print(temporal_subscenario)
        if not temporal_subscenario.split("_")[0].isdigit():
            warnings.warn(
                "Temporal subfolder `{}` does not start with an integer to "
                "indicate the subscenario ID and CSV import script will fail. "
                "Please follow the required folder naming structure "
                "<subscenarioID_subscenarioName>, e.g. "
                "'1_default4periods'.".format(temporal_subscenario)
            )
        subscenario_directory = os.path.join(
            temporal_directory, temporal_subscenario)
        temporal.load_from_csvs(
            conn=conn, subscenario_directory=subscenario_directory
        )

    #### LOAD LOAD (DEMAND) DATA ####

    ## GEOGRAPHY ##
    if csv_data_master.loc[csv_data_master['table'] == 'geography_load_zones', 'include'].iloc[0] != 1:
        print("ERROR: geography_load_zones table is required")
    else:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'geography_load_zones', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_geography.load_geography_load_zones(conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT LOAD ZONES ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_load_zones', 'include'].iloc[0] != 1:
        print("ERROR: project_load_zones table is required")
    else:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_load_zones', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_project_zones.load_project_load_zones(conn, c2, csv_subscenario_input, csv_data_input)

    ## SYSTEM LOAD ##
    if csv_data_master.loc[csv_data_master['table'] == 'system_load', 'include'].iloc[0] != 1:
        print("ERROR: system_load table is required")
    else:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'system_load', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_system_load.load_system_static_load(conn, c2, csv_subscenario_input, csv_data_input)

    #### LOAD PROJECTS DATA ####

    ## PROJECT LIST AND OPERATIONAL CHARS ##
    # Note projects list is pulled from the project_operational_chars table
    if csv_data_master.loc[csv_data_master['table'] == 'project_operational_chars', 'include'].iloc[0] != 1:
        print("ERROR: project_operational_chars table is required")
    else:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_operational_chars', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        # This function is essential before any other project data is loaded in db. It loads the projects list.
        load_project_list.load_project_list(conn, c2, csv_subscenario_input, csv_data_input)
        load_project_operational_chars.load_project_operational_chars(conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT HYDRO GENERATOR PROFILES ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_hydro_operational_chars', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_hydro_operational_chars', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_project_data(data_folder_path, quiet)
        load_project_operational_chars.load_project_hydro_opchar(conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT VARIABLE GENERATOR PROFILES ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_variable_generator_profiles', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_variable_generator_profiles', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = \
            csvs_read.csv_read_project_data(data_folder_path, quiet)
        load_project_operational_chars.load_project_variable_profiles(conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT PORTFOLIOS ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_portfolios', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_portfolios', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_project_portfolios.load_project_portfolios(conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT EXISTING CAPACITIES ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_specified_capacity', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_specified_capacity', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_project_specified_params.load_project_specified_capacities(conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT EXISTING FIXED COSTS ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_specified_fixed_cost', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_specified_fixed_cost', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_project_specified_params.load_project_specified_fixed_costs(conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT NEW POTENTIAL ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_new_potential', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_new_potential', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_project_new_potentials.load_project_new_potentials(conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT NEW BINARY BUILD SIZE ##
    if csv_data_master.loc[csv_data_master['table'] ==
                           'project_new_binary_build_size', 'include'].iloc[
        0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_new_binary_build_size',
            'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_project_new_potentials.load_project_new_binary_build_sizes(
            conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT NEW COSTS ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_new_cost', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_new_cost', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_project_new_costs.load_project_new_costs(conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT ELCC CHARS ##
    if csv_data_master.loc[csv_data_master['table'] ==
                           'project_elcc_chars', 'include'].iloc[
        0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_elcc_chars',
            'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_project_prm.load_project_prm(
            conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT LOCAL CAPACITY CHARS ##
    if csv_data_master.loc[csv_data_master['table'] ==
                           'project_local_capacity_chars', 'include'].iloc[
        0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_local_capacity_chars',
            'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_project_local_capacity_chars.load_project_local_capacity_chars(
            conn, c2, csv_subscenario_input, csv_data_input)

    #### LOAD PROJECT AVAILABILITY DATA ####

    ## PROJECT AVAILABILITY TYPES ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_availability_types', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_availability_types', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_project_availability.load_project_availability_types(conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT AVAILABILITY EXOGENOUS ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_availability_exogenous', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_availability_exogenous', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = \
            csvs_read.csv_read_project_data(data_folder_path, quiet)
        load_project_availability.load_project_availability_exogenous(conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT AVAILABILITY ENDOGENOUS ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_availability_endogenous', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_availability_endogenous', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = \
            csvs_read.csv_read_project_data(data_folder_path, quiet)
        load_project_availability.load_project_availability_endogenous(conn, c2, csv_subscenario_input, csv_data_input)

    #### LOAD PROJECT HEAT RATE DATA ####

    ## PROJECT HEAT RATES ##
    if csv_data_master.loc[
        csv_data_master['table'] == 'project_heat_rate_curves', 'include'
    ].iloc[0] == 1:
        data_folder_path = os.path.join(
            folder_path,
            csv_data_master.loc[
                csv_data_master['table'] == 'project_heat_rate_curves', 'path'
            ].iloc[0]
        )
        (csv_subscenario_input, csv_data_input) = \
            csvs_read.csv_read_project_data(data_folder_path, quiet)
        load_project_operational_chars.load_project_hr_curves(
            conn, c2, csv_subscenario_input, csv_data_input
        )

    #### LOAD PROJECT STARTUP CHARS DATA ####

    ## PROJECT STARTUP CHARS ##
    if csv_data_master.loc[csv_data_master['table'] ==
                           'project_startup_chars', 'include'].iloc[0] \
            == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_startup_chars',
            'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = \
            csvs_read.csv_read_project_data(
            data_folder_path, quiet)
        load_project_operational_chars.load_project_startup_chars(conn, c2,
                                                       csv_subscenario_input, csv_data_input)

    #### LOAD FUELS DATA ####

    ## FUEL CHARS ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_fuels', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_fuels', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_fuels.load_fuels(conn, c2, csv_subscenario_input, csv_data_input)

    ## FUEL PRICES ##
    if csv_data_master.loc[csv_data_master['table'] == 'project_fuel_prices', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_fuel_prices', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_fuels.load_fuel_prices(conn, c2, csv_subscenario_input, csv_data_input)

    #### LOAD POLICY DATA ####

    ## GEOGRAPHY CARBON CAP ZONES ##
    if csv_data_master.loc[csv_data_master['table'] == 'geography_carbon_cap_zones', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'geography_carbon_cap_zones', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_geography.load_geography_carbon_cap_zones(conn, c2, csv_subscenario_input, csv_data_input)

    ## GEOGRAPHY LOCAL CAPACITY ZONES ##
    if csv_data_master.loc[csv_data_master['table'] == 'geography_local_capacity_zones', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'geography_local_capacity_zones', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_geography.load_geography_local_capacity_zones(conn, c2, csv_subscenario_input, csv_data_input)

    ## GEOGRAPHY PRM ZONES ##
    if csv_data_master.loc[csv_data_master['table'] == 'geography_prm_zones', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'geography_prm_zones', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_geography.load_geography_prm_zones(conn, c2, csv_subscenario_input, csv_data_input)

    ## GEOGRAPHY RPS ZONES ##
    if csv_data_master.loc[csv_data_master['table'] == 'geography_rps_zones', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'geography_rps_zones', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_geography.load_geography_rps_zones(conn, c2, csv_subscenario_input, csv_data_input)

    ## PROJECT POLICY (CARBON CAP, PRM, RPS, LOCAL CAPACITY) ZONES ##
    for policy_type in policy_list:
        if csv_data_master.loc[csv_data_master['table'] == 'project_' + policy_type + '_zones', 'include'].iloc[0] == 1:
            data_folder_path = os.path.join(folder_path, csv_data_master.loc[
                csv_data_master['table'] == 'project_' + policy_type + '_zones', 'path'].iloc[0])
            (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
            load_project_zones.load_project_policy_zones(conn, c2, csv_subscenario_input, csv_data_input, policy_type)

    ## SYSTEM CARBON CAP TARGETS ##
    if csv_data_master.loc[csv_data_master['table'] == 'system_carbon_cap_targets', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'system_carbon_cap_targets', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_system_carbon_cap.load_system_carbon_cap_targets(conn, c2, csv_subscenario_input, csv_data_input)

    ## SYSTEM LOCAL CAPACITY TARGETS ##
    if csv_data_master.loc[csv_data_master['table'] ==
                           'system_local_capacity_requirement',
                           'include'].iloc[
        0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'system_local_capacity_requirement',
            'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_system_local_capacity.load_system_local_capacity_requirement(
            conn, c2, csv_subscenario_input, csv_data_input)


    ## SYSTEM PRM TARGETS ##
    if csv_data_master.loc[csv_data_master['table'] == 'system_prm_requirement', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'system_prm_requirement', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_system_prm.load_system_prm_requirement(conn, c2, csv_subscenario_input, csv_data_input)

    ## SYSTEM RPS TARGETS ##
    if csv_data_master.loc[csv_data_master['table'] == 'system_rps_targets', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'system_rps_targets', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_system_rps.load_system_rps_targets(conn, c2, csv_subscenario_input, csv_data_input)

    #### LOAD RESERVES DATA ####

    ## GEOGRAPHY BAS ##
    for reserve_type in reserves_list:
        if csv_data_master.loc[csv_data_master['table'] == 'geography_' + reserve_type + '_bas', 'include'].iloc[0] == 1:
            data_folder_path = os.path.join(folder_path, csv_data_master.loc[
                csv_data_master['table'] == 'geography_' + reserve_type + '_bas', 'path'].iloc[0])
            (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
            load_geography.load_geography_reserves_bas(conn, c2, csv_subscenario_input, csv_data_input, reserve_type)

    ## PROJECT RESERVES BAS ##
    for reserve_type in reserves_list:
        if csv_data_master.loc[csv_data_master['table'] == 'project_' + reserve_type + '_bas', 'include'].iloc[0] == 1:
            data_folder_path = os.path.join(folder_path, csv_data_master.loc[
                csv_data_master['table'] == 'project_' + reserve_type + '_bas', 'path'].iloc[0])
            (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
            load_project_zones.load_project_reserve_bas(conn, c2, csv_subscenario_input, csv_data_input, reserve_type)

    ## SYSTEM RESERVES ##
    for reserve_type in reserves_list:
        if csv_data_master.loc[csv_data_master['table'] == 'system_' + reserve_type, 'include'].iloc[0] == 1:
            data_folder_path = os.path.join(folder_path, csv_data_master.loc[
                csv_data_master['table'] == 'system_' + reserve_type, 'path'].iloc[0])
            (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
            load_system_reserves.load_system_reserves(conn, c2, csv_subscenario_input, csv_data_input, reserve_type)

    #### LOAD TRANSMISSION DATA ####

    ## LOAD TANSMISSION EXISTING CAPACITIES ##
    if csv_data_master.loc[csv_data_master['table'] == 'transmission_specified_capacity', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'transmission_specified_capacity', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_transmission_capacities.load_transmission_capacities(conn, c2, csv_subscenario_input, csv_data_input)

    ## LOAD TRANSMISSION PORTFOLIOS ##
    if csv_data_master.loc[csv_data_master['table'] == 'transmission_portfolios', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'transmission_portfolios', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_transmission_portfolios.load_transmission_portfolios(conn, c2, csv_subscenario_input, csv_data_input)

    ## LOAD TRANSMISSION ZONES ##
    if csv_data_master.loc[csv_data_master['table'] == 'transmission_load_zones', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'transmission_load_zones', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_transmission_zones.load_transmission_zones(conn, c2, csv_subscenario_input, csv_data_input)

    ## LOAD TRANSMISSION CARBON_CAP_ZONES ##
    if csv_data_master.loc[csv_data_master['table'] ==
                           'transmission_carbon_cap_zones', 'include'].iloc[
        0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master[
                'table'] == 'transmission_carbon_cap_zones', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(
            data_folder_path, quiet)
        load_transmission_zones.load_transmission_carbon_cap_zones(
            conn, c2, csv_subscenario_input, csv_data_input)

    ## LOAD TRANSMISSION OPERATIONAL CHARS ##
    if csv_data_master.loc[csv_data_master['table'] == 'transmission_operational_chars', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'transmission_operational_chars', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_transmission_operational_chars.load_transmission_operational_chars(conn, c2, csv_subscenario_input, csv_data_input)

    ## LOAD TRANSMISSION NEW COST ##
    if csv_data_master.loc[csv_data_master['table'] == 'transmission_new_cost', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'transmission_new_cost', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_transmission_new_cost.load_transmission_new_cost(conn, c2, csv_subscenario_input, csv_data_input)

    ## LOAD TRANSMISSION HURDLE RATES ##
    if csv_data_master.loc[csv_data_master['table'] == 'transmission_hurdle_rates', 'include'].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'transmission_hurdle_rates', 'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = csvs_read.csv_read_data(data_folder_path, quiet)
        load_transmission_hurdle_rates.load_transmission_hurdle_rates(conn, c2, csv_subscenario_input, csv_data_input)

    ## LOAD TRANSMISSION SIMULTANEOUS FLOW LIMITS ##
    sfl_subscenario, sfl_inputs = read_data_for_insertion_into_db(
        csv_data_master=csv_data_master,
        folder_path=folder_path,
        quiet=quiet,
        table="transmission_simultaneous_flow_limits"
    )
    simultaneous_flows.insert_into_database(
        conn, c2, sfl_subscenario, sfl_inputs
    )

    sflg_subscenario, sflg_inputs = read_data_for_insertion_into_db(
        csv_data_master=csv_data_master,
        folder_path=folder_path,
        quiet=quiet,
        table="transmission_simultaneous_flow_limit_line_groups"
    )
    simultaneous_flow_groups.insert_into_database(
        conn, c2, sflg_subscenario, sflg_inputs
    )


    #### LOAD SCENARIOS DATA ####
    if csv_data_master.loc[csv_data_master['table'] == 'scenarios', 'include'].iloc[0] != 1:
        print("ERROR: scenarios table is required")
    else:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'scenarios', 'path'].iloc[0])

        f_number = 0
        for f in os.listdir(data_folder_path):
            if f.endswith(".csv") and 'template' not in f and 'scenario' in f and 'ignore' not in f:
                if not quiet:
                    print(f)
                f_number = f_number + 1
                csv_data_input = pd.read_csv(os.path.join(data_folder_path, f))
                if f_number > 1:
                    print('Error: More than one scenario csv input files')

        load_scenarios.load_scenarios(conn, c2, csv_data_input)

    #### LOAD SOLVER OPTIONS ####
    if csv_data_master.loc[csv_data_master['table'] == 'solver', 'include'].iloc[0] != 1:
        print("ERROR: solver tables are required")
    else:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'solver', 'path'].iloc[0])

        for f in os.listdir(data_folder_path):
            if f.endswith(".csv") and 'template' not in f and 'options' in f:
                if not quiet:
                    print(f)
                csv_solver_options = pd.read_csv(os.path.join(data_folder_path, f))
            if f.endswith(".csv") and 'template' not in f and 'descriptions' in f:
                if not quiet:
                    print(f)
                csv_solver_descriptions = pd.read_csv(os.path.join(data_folder_path, f))

        load_solver_options.load_solver_options(conn, c2, csv_solver_options, csv_solver_descriptions)

    #### Code to debug
    # subscenario_input = csv_subscenario_input
    # data_input = csv_data_input


def read_data_for_insertion_into_db(
        csv_data_master, folder_path, quiet, table
):
    """
    :param csv_data_master:
    :param folder_path:
    :param quiet:
    :param table:
    :return:

    Read data and convert to tuples for insertion into database.
    """
    if csv_data_master.loc[
        csv_data_master['table'] == table,
        'include'
    ].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == table,
            'path'
        ].iloc[0])
        (csv_subscenario_input, csv_data_input) = \
            csvs_read.csv_read_data(data_folder_path, quiet)
        subscenario_tuples = \
            [tuple(x) for x in csv_subscenario_input.to_records(index=False)]
        inputs_tuples = \
            [tuple(x) for x in csv_data_input.to_records(index=False)]

        return subscenario_tuples, inputs_tuples
    # Return empty lists if we're not including this table
    else:
        return [], []


def main(args=None):
    """
    The 'main' method parses the database name along with path as
    script arguments and loads the data in the database.
    """
    if args is None:
        args = sys.argv[1:]
    parsed_args = parse_arguments(args=args)

    db_path = get_database_file_path(parsed_arguments=parsed_args)
    csv_path = get_csv_folder_path(parsed_arguments=parsed_args)

    # Register numpy types with sqlite, so that they are properly inserted
    # from pandas dataframes
    # https://stackoverflow.com/questions/38753737/inserting-numpy-integer-types-into-sqlite-with-python3
    sqlite3.register_adapter(np.int64, lambda val: int(val))
    sqlite3.register_adapter(np.float64, lambda val: float(val))

    # connect to database
    conn = connect_to_database(db_path=db_path)

    # Load data
    load_csv_data(conn=conn, csv_path=csv_path, quiet=parsed_args.quiet)

    # Close connection
    conn.close()


if __name__ == "__main__":
    main()
