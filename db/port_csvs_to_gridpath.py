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
from argparse import ArgumentParser

# Data-import modules
from db.common_functions import connect_to_database
from db.create_database import get_database_file_path

import db.utilities.common_functions as db_util_common
from db.utilities import temporal, simultaneous_flows, \
    simultaneous_flow_groups, project_prm, system_reserves, project_zones, \
    rps, project_capacity_groups

from db.csvs_to_db_utilities import csvs_read, \
    load_geography, load_project_specified_params, load_project_new_costs, \
    load_project_new_potentials, load_project_local_capacity_chars, \
    load_project_prm, load_transmission_zones, load_transmission_portfolios, \
    load_transmission_hurdle_rates, load_transmission_operational_chars, \
    load_scenarios, load_fuels, load_project_availability, \
    load_project_zones, load_solver_options, \
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

    """

    c = conn.cursor()

    #### MASTER CSV DATA ####
    # If include flag is 1, then read the feature, subscenario_id, table, and
    # path into a dictionary and call the specific function for the feature
    csv_data_master = pd.read_csv(
        os.path.join(csv_path, 'csv_data_master.csv')
    )

    #### LOAD TEMPORAL DATA ####
    temporal_directory = get_data_folder_path(
        csv_path=csv_path, csv_data_master=csv_data_master, table="temporal"
    )
    if temporal_directory is not None:
        temporal_subscenario_directories = \
            db_util_common.get_directory_subscenarios(
                main_directory=temporal_directory,
                quiet=quiet
            )
        for subscenario_directory in temporal_subscenario_directories:
            temporal.load_from_csvs(
                conn=conn, subscenario_directory=subscenario_directory
            )
    else:
        print("ERROR: inputs_temporal table is required")
        sys.exit()

    #### LOAD LOAD (DEMAND) DATA ####

    ## GEOGRAPHY ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="geography_load_zones",
        conn=conn,
        load_method=load_geography.load_geography_load_zones,
        none_message="ERROR: geography_load_zones table is required",
        quiet=quiet
    )

    ## PROJECT LOAD ZONES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_load_zones",
        conn=conn,
        load_method=load_project_zones.load_project_load_zones,
        none_message="ERROR: project_load_zones table is required",
        quiet=quiet
    )

    ## SYSTEM LOAD ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="system_load",
        conn=conn,
        load_method=load_system_load.load_system_static_load,
        none_message="ERROR: system_load table is required",
        quiet=quiet
    )

    #### LOAD PROJECTS DATA ####

    ## PROJECT LIST AND OPERATIONAL CHARS ##
    # Note projects list is pulled from the project_operational_chars table
    # TODO: this shouldn't get pulled from the operational chars table but
    #  from a separate table; the only reason it works is that we have
    #  INSERT OR IGNORE and can cause issues
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_operational_chars",
        conn=conn,
        load_method=load_project_list.load_project_list,
        none_message="",
        quiet=quiet
    )

    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_operational_chars",
        conn=conn,
        load_method=
        load_project_operational_chars.load_project_operational_chars,
        none_message="ERROR: project_operational_chars table is required",
        quiet=quiet
    )

    ## PROJECT HYDRO GENERATOR PROFILES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_hydro_operational_chars",
        conn=conn,
        load_method=load_project_operational_chars.load_project_hydro_opchar,
        none_message="",
        quiet=quiet,
        use_project_method=True
    )

    ## PROJECT VARIABLE GENERATOR PROFILES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_variable_generator_profiles",
        conn=conn,
        load_method=
        load_project_operational_chars.load_project_variable_profiles,
        none_message="",
        quiet=quiet,
        use_project_method=True
    )

    ## PROJECT PORTFOLIOS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_portfolios",
        conn=conn,
        load_method=load_project_portfolios.load_project_portfolios,
        none_message="",
        quiet=quiet
    )


    ## PROJECT EXISTING CAPACITIES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_specified_capacity",
        conn=conn,
        load_method=
        load_project_specified_params.load_project_specified_capacities,
        none_message="",
        quiet=quiet
    )

    ## PROJECT EXISTING FIXED COSTS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_specified_fixed_cost",
        conn=conn,
        load_method=
        load_project_specified_params.load_project_specified_fixed_costs,
        none_message="",
        quiet=quiet
    )

    ## PROJECT NEW POTENTIAL ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_new_potential",
        conn=conn,
        load_method=load_project_new_potentials.load_project_new_potentials,
        none_message="",
        quiet=quiet
    )

    ## PROJECT NEW BINARY BUILD SIZE ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_new_binary_build_size",
        conn=conn,
        load_method=load_project_new_potentials.load_project_new_binary_build_sizes,
        none_message="",
        quiet=quiet
    )

    ## PROJECT NEW COSTS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_new_cost",
        conn=conn,
        load_method=load_project_new_costs.load_project_new_costs,
        none_message="",
        quiet=quiet
    )

    ## PROJECT GROUP CAPACITY REQUIREMENTS ##
    if csv_data_master.loc[
        csv_data_master['table'] == 'project_capacity_group_requirements',
        'include'
    ].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_capacity_group_requirements',
            'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = \
            csvs_read.csv_read_data(data_folder_path, quiet)
        sub_tuples = [
            tuple(x) for x in csv_subscenario_input.to_records(index=False)
        ]
        inputs_tuples = [
            tuple(x) for x in csv_data_input.to_records(index=False)
        ]
        project_capacity_groups.insert_capacity_group_requirements(
            conn, sub_tuples, inputs_tuples
        )

    if csv_data_master.loc[
        csv_data_master['table'] == 'project_capacity_groups',
        'include'
    ].iloc[0] == 1:
        data_folder_path = os.path.join(folder_path, csv_data_master.loc[
            csv_data_master['table'] == 'project_capacity_groups',
            'path'].iloc[0])
        (csv_subscenario_input, csv_data_input) = \
            csvs_read.csv_read_data(data_folder_path, quiet)
        sub_tuples = [
            tuple(x) for x in csv_subscenario_input.to_records(index=False)
        ]
        inputs_tuples = [
            tuple(x) for x in csv_data_input.to_records(index=False)
        ]
        project_capacity_groups.insert_capacity_group_projects(
            conn, sub_tuples, inputs_tuples
        )

    ## PROJECT ELCC CHARS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_elcc_chars",
        conn=conn,
        load_method=load_project_prm.load_project_prm,
        none_message="",
        quiet=quiet
    )

    ## DELIVERABILITY GROUPS ##
    dg_subscenario, dg_inputs = read_data_for_insertion_into_db(
        csv_data_master=csv_data_master,
        folder_path=csv_path,
        quiet=quiet,
        table="project_prm_energy_only"
    )

    project_prm.deliverability_groups(
        conn, c, dg_subscenario, dg_inputs
    )

    ## PROJECT LOCAL CAPACITY CHARS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_local_capacity_chars",
        conn=conn,
        load_method=
        load_project_local_capacity_chars.load_project_local_capacity_chars,
        none_message="",
        quiet=quiet
    )

    #### LOAD PROJECT AVAILABILITY DATA ####

    ## PROJECT AVAILABILITY TYPES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_availability_types",
        conn=conn,
        load_method=load_project_availability.load_project_availability_types,
        none_message="",
        quiet=quiet
    )

    ## PROJECT AVAILABILITY EXOGENOUS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_availability_exogenous",
        conn=conn,
        load_method=
        load_project_availability.load_project_availability_exogenous,
        none_message="",
        quiet=quiet,
        use_project_method=True
    )

    ## PROJECT AVAILABILITY ENDOGENOUS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_availability_endogenous",
        conn=conn,
        load_method=
        load_project_availability.load_project_availability_endogenous,
        none_message="",
        quiet=quiet,
        use_project_method=True
    )

    #### LOAD PROJECT HEAT RATE DATA ####

    ## PROJECT HEAT RATES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_heat_rate_curves",
        conn=conn,
        load_method=load_project_operational_chars.load_project_hr_curves,
        none_message="",
        quiet=quiet,
        use_project_method=True
    )

    #### LOAD PROJECT VARIALE OM DATA ####

    ## PROJECT VARIABLE OM ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_variable_om_curves",
        conn=conn,
        load_method=load_project_operational_chars.load_project_vom_curves,
        none_message="",
        quiet=quiet,
        use_project_method=True
    )

    #### LOAD PROJECT STARTUP CHARS DATA ####

    ## PROJECT STARTUP CHARS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_startup_chars",
        conn=conn,
        load_method=load_project_operational_chars.load_project_startup_chars,
        none_message="",
        quiet=quiet,
        use_project_method=True
    )

    #### LOAD FUELS DATA ####

    ## FUEL CHARS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_fuels",
        conn=conn,
        load_method=load_fuels.load_fuels,
        none_message="",
        quiet=quiet
    )

    ## FUEL PRICES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_fuel_prices",
        conn=conn,
        load_method=load_fuels.load_fuel_prices,
        none_message="",
        quiet=quiet
    )

    #### LOAD POLICY DATA ####

    ## GEOGRAPHY CARBON CAP ZONES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="geography_carbon_cap_zones",
        conn=conn,
        load_method=load_geography.load_geography_carbon_cap_zones,
        none_message="",
        quiet=quiet
    )

    ## GEOGRAPHY LOCAL CAPACITY ZONES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="geography_local_capacity_zones",
        conn=conn,
        load_method=load_geography.load_geography_local_capacity_zones,
        none_message="",
        quiet=quiet
    )

    ## GEOGRAPHY PRM ZONES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="geography_prm_zones",
        conn=conn,
        load_method=load_geography.load_geography_prm_zones,
        none_message="",
        quiet=quiet
    )

    ## GEOGRAPHY RPS ZONES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="geography_rps_zones",
        conn=conn,
        load_method=load_geography.load_geography_rps_zones,
        none_message="",
        quiet=quiet
    )

    ## PROJECT POLICY (CARBON CAP, PRM, RPS, LOCAL CAPACITY) ZONES ##
    for policy_type in policy_list:
        policy_dir = get_data_folder_path(
            csv_path=csv_path, csv_data_master=csv_data_master,
            table="project_{}_zones".format(policy_type)
        )
        if policy_dir is not None:
            (csv_subscenario_input, csv_data_input) = \
                csvs_read.csv_read_data(policy_dir, quiet)
            load_project_zones.load_project_policy_zones(
                conn, c, csv_subscenario_input, csv_data_input, policy_type
            )

    ## SYSTEM CARBON CAP TARGETS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="system_carbon_cap_targets",
        conn=conn,
        load_method=load_system_carbon_cap.load_system_carbon_cap_targets,
        none_message="",
        quiet=quiet
    )

    ## SYSTEM LOCAL CAPACITY TARGETS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="system_local_capacity_requirement",
        conn=conn,
        load_method=
        load_system_local_capacity.load_system_local_capacity_requirement,
        none_message="",
        quiet=quiet
    )

    ## SYSTEM PRM TARGETS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="system_prm_requirement",
        conn=conn,
        load_method=load_system_prm.load_system_prm_requirement,
        none_message="",
        quiet=quiet
    )

    ## SYSTEM RPS TARGETS ##
    rps_target_dir = get_data_folder_path(
        csv_path=csv_path, csv_data_master=csv_data_master,
        table="system_rps_targets"
    )
    if rps_target_dir is not None:
        rps_target_subscenario_directories = \
            db_util_common.get_directory_subscenarios(
                main_directory=rps_target_dir,
                quiet=quiet
            )
        for subscenario_directory in rps_target_subscenario_directories:
            rps.load_from_csvs(
                conn=conn, subscenario_directory=subscenario_directory
            )

    #### LOAD RESERVES DATA ####

    ## GEOGRAPHY BAS ##
    for reserve_type in reserves_list:
        reserve_dir = get_data_folder_path(
            csv_path=csv_path, csv_data_master=csv_data_master,
            table="geography_{}_bas".format(reserve_type)
        )
        if reserve_dir is not None:
            (csv_subscenario_input, csv_data_input) = \
                csvs_read.csv_read_data(reserve_dir, quiet)
            load_geography.load_geography_reserves_bas(
                conn, c, csv_subscenario_input, csv_data_input, reserve_type
            )

    ## PROJECT RESERVES BAS ##
    for reserve_type in reserves_list:
        subscenario, inputs = read_data_for_insertion_into_db(
            csv_data_master=csv_data_master,
            folder_path=csv_path,
            quiet=quiet,
            table="project_{}_bas".format(reserve_type)
        )

        project_zones.project_reserve_bas(
            conn, c, reserve_type, subscenario, inputs
        )

    ## SYSTEM RESERVES ##
    for reserve_type in reserves_list:
        if csv_data_master.loc[
            csv_data_master['table'] == "system_" + reserve_type,
            'include'
        ].iloc[0] == 1:
            data_folder_path = os.path.join(csv_path, csv_data_master.loc[
                csv_data_master['table']
                == "system_" + reserve_type, 'path'
            ].iloc[0])

            reserve_subscenario_directories = \
                db_util_common.get_directory_subscenarios(
                    main_directory=data_folder_path,
                    quiet=quiet
                )

            for subscenario_directory in reserve_subscenario_directories:
                system_reserves.load_from_csvs(
                    conn, subscenario_directory=subscenario_directory,
                    reserve_type=reserve_type
                )

    #### LOAD TRANSMISSION DATA ####

    ## LOAD TANSMISSION EXISTING CAPACITIES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="transmission_specified_capacity",
        conn=conn,
        load_method=load_transmission_capacities.load_transmission_capacities,
        none_message="",
        quiet=quiet
    )

    ## LOAD TRANSMISSION PORTFOLIOS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="transmission_portfolios",
        conn=conn,
        load_method=load_transmission_portfolios.load_transmission_portfolios,
        none_message="",
        quiet=quiet
    )

    ## LOAD TRANSMISSION ZONES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="transmission_load_zones",
        conn=conn,
        load_method=load_transmission_zones.load_transmission_zones,
        none_message="",
        quiet=quiet
    )

    ## LOAD TRANSMISSION CARBON_CAP_ZONES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="transmission_carbon_cap_zones",
        conn=conn,
        load_method=load_transmission_zones.load_transmission_carbon_cap_zones,
        none_message="",
        quiet=quiet
    )

    ## LOAD TRANSMISSION OPERATIONAL CHARS ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="transmission_operational_chars",
        conn=conn,
        load_method=
        load_transmission_operational_chars.load_transmission_operational_chars,
        none_message="",
        quiet=quiet
    )

    ## LOAD TRANSMISSION NEW COST ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="transmission_new_cost",
        conn=conn,
        load_method=load_transmission_new_cost.load_transmission_new_cost,
        none_message="",
        quiet=quiet
    )

    ## LOAD TRANSMISSION HURDLE RATES ##
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="transmission_hurdle_rates",
        conn=conn,
        load_method=load_transmission_hurdle_rates.load_transmission_hurdle_rates,
        none_message="",
        quiet=quiet
    )

    ## LOAD TRANSMISSION SIMULTANEOUS FLOW LIMITS ##
    sfl_subscenario, sfl_inputs = read_data_for_insertion_into_db(
        csv_data_master=csv_data_master,
        folder_path=csv_path,
        quiet=quiet,
        table="transmission_simultaneous_flow_limits"
    )
    simultaneous_flows.insert_into_database(
        conn, c, sfl_subscenario, sfl_inputs
    )

    sflg_subscenario, sflg_inputs = read_data_for_insertion_into_db(
        csv_data_master=csv_data_master,
        folder_path=csv_path,
        quiet=quiet,
        table="transmission_simultaneous_flow_limit_line_groups"
    )
    simultaneous_flow_groups.insert_into_database(
        conn, c, sflg_subscenario, sflg_inputs
    )

    # TODO: organize all PRM-related data in one place
    # TODO: refactor this to consolidate with temporal inputs loading and
    #  any other subscenarios that are based on a directory
    ## LOAD ELCC SURFACE DATA ##
    elcc_surface_dir = get_data_folder_path(
        csv_path=csv_path, csv_data_master=csv_data_master,
        table="system_prm_zone_elcc_surface"
    )
    if elcc_surface_dir is not None:
        elcc_surface_subscenario_directories = \
            db_util_common.get_directory_subscenarios(
                main_directory=elcc_surface_dir,
                quiet=quiet
            )
        for subscenario_directory in elcc_surface_subscenario_directories:
            project_prm.elcc_surface_load_from_csvs(
                conn=conn, subscenario_directory=subscenario_directory
            )

    #### LOAD SCENARIOS DATA ####
    scenarios_dir = get_data_folder_path(
        csv_path=csv_path, csv_data_master=csv_data_master,
        table="scenarios"
    )
    if scenarios_dir is not None:
        f_number = 0
        for f in os.listdir(scenarios_dir):
            if f.endswith(".csv") and 'template' not in f and 'scenario' in f \
                    and 'ignore' not in f:
                if not quiet:
                    print(f)
                f_number = f_number + 1
                csv_data_input = pd.read_csv(os.path.join(scenarios_dir, f))
                if f_number > 1:
                    print('Error: More than one scenario csv input files')

        load_scenarios.load_scenarios(conn, c, csv_data_input)
    else:
        print("ERROR: scenarios table is required")


    #### LOAD SOLVER OPTIONS ####
    solver_dir = get_data_folder_path(
        csv_path=csv_path, csv_data_master=csv_data_master,
        table="solver"
    )
    if solver_dir is not None:
        for f in os.listdir(solver_dir):
            if f.endswith(".csv") and 'template' not in f and 'options' in f:
                if not quiet:
                    print(f)
                csv_solver_options = pd.read_csv(os.path.join(solver_dir, f))
            if f.endswith(".csv") and 'template' not in f \
                    and 'descriptions' in f:
                if not quiet:
                    print(f)
                csv_solver_descriptions = \
                    pd.read_csv(os.path.join(solver_dir, f))

        load_solver_options.load_solver_options(
            conn, c, csv_solver_options, csv_solver_descriptions
        )
    else:
        print("ERROR: solver tables are required")


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


def get_data_folder_path(csv_path, csv_data_master, table):
    if csv_data_master.loc[
        csv_data_master['table'] == table, 'include'
    ].iloc[0] == 1:
        data_folder_path = os.path.join(
            csv_path,
            csv_data_master.loc[
                csv_data_master['table'] == table,
                'path'
            ].iloc[0]
        )
    else:
        data_folder_path = None

    return data_folder_path


def read_and_load_inputs(
        csv_path, csv_data_master, table, conn, load_method,
        quiet, none_message, use_project_method=False
):
    data_folder_path = get_data_folder_path(
        csv_path=csv_path, csv_data_master=csv_data_master, table=table
    )
    if data_folder_path is not None:
        if not use_project_method:
            (csv_subscenario_input, csv_data_input) = \
                csvs_read.csv_read_data(
                    folder_path=data_folder_path, quiet=quiet
                )
        else:
            (csv_subscenario_input, csv_data_input) = \
                csvs_read.csv_read_project_data(
                    folder_path=data_folder_path, quiet=quiet
                )
        c = conn.cursor()
        load_method(conn, c, csv_subscenario_input, csv_data_input)
    else:
        print(none_message)


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
