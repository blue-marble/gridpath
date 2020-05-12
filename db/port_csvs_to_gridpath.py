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
from db.utilities import carbon_cap, fuels, geography, project_availability, \
    project_capacity_groups, project_list, project_local_capacity_chars, \
    project_new_costs, project_new_potentials, project_operational_chars, \
    project_portfolios, project_prm, project_specified_params, \
    project_zones, rps, simultaneous_flows, \
    simultaneous_flow_groups, system_load, system_local_capacity, system_prm, \
    system_reserves, temporal, transmission_capacities, \
    transmission_hurdle_rates, transmission_new_cost, \
    transmission_operational_chars, transmission_portfolios, \
    transmission_zones, scenario, solver_options

from db.csvs_to_db_utilities import csvs_read

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
    # Handled differently, as a temporal_scenario_id involves multiple files
    temporal_directory = get_inputs_dir(
        csvs_main_dir=csv_path, csv_data_master=csv_data_master,
        table="temporal"
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
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="geography_load_zones",
        insert_method=geography.geography_load_zones,
        none_message="ERROR: geography_load_zones table is required"

    )

    ## PROJECT LOAD ZONES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_load_zones",
        insert_method=project_zones.project_load_zones,
        none_message="ERROR: project_load_zones table is required"

    )

    ## SYSTEM LOAD ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="system_load",
        insert_method=system_load.insert_system_static_loads,
        none_message="ERROR: system_load table is required"

    )


    #### LOAD PROJECTS DATA ####
    ## PROJECT LIST
    # Note projects list is pulled from the project_operational_chars table
    # TODO: this shouldn't get pulled from the operational chars table but
    #  from a separate table; need to determine appropriate method
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_operational_chars",
        conn=conn,
        load_method=project_list.load_from_csv,
        none_message="",
        quiet=quiet
    )

    # PROJECT OPERATIONAL CHARS
    read_and_load_inputs(
        csv_path=csv_path,
        csv_data_master=csv_data_master,
        table="project_operational_chars",
        conn=conn,
        load_method=project_operational_chars.load_from_csv,
        none_message="ERROR: project_operational_chars table is required",
        quiet=quiet
    )

    ## PROJECT HYDRO GENERATOR PROFILES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_hydro_operational_chars",
        insert_method=project_operational_chars.update_project_hydro_opchar,
        none_message="",
        use_project_method=True
    )

    ## PROJECT VARIABLE GENERATOR PROFILES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_variable_generator_profiles",
        insert_method=
        project_operational_chars.update_project_variable_profiles,
        none_message="",
        use_project_method=True
    )

    ## PROJECT PORTFOLIOS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_portfolios",
        insert_method=project_portfolios.update_project_portfolios,
        none_message=""

    )

    ## PROJECT EXISTING CAPACITIES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_specified_capacity",
        insert_method=project_specified_params.update_project_capacities,
        none_message=""
    )

    ## PROJECT EXISTING FIXED COSTS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_specified_fixed_cost",
        insert_method=project_specified_params.update_project_fixed_costs,
        none_message=""
    )

    ## PROJECT NEW POTENTIAL ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_new_potential",
        insert_method=project_new_potentials.update_project_potentials,
        none_message=""
    )

    ## PROJECT NEW BINARY BUILD SIZE ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_new_binary_build_size",
        insert_method=project_new_potentials.update_project_binary_build_sizes,
        none_message=""
    )

    ## PROJECT NEW COSTS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_new_cost",
        insert_method=project_new_costs.update_project_new_costs,
        none_message=""
    )

    ## PROJECT GROUP CAPACITY REQUIREMENTS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_capacity_group_requirements",
        insert_method=
        project_capacity_groups.insert_capacity_group_requirements,
        none_message=""
    )

    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_capacity_groups",
        insert_method=
        project_capacity_groups.insert_capacity_group_projects,
        none_message=""
    )

    ## PROJECT ELCC CHARS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_elcc_chars",
        insert_method=project_prm.project_elcc_chars,
        none_message=""
    )

    ## DELIVERABILITY GROUPS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_prm_energy_only",
        insert_method=project_prm.deliverability_groups,
        none_message=""
    )

    ## PROJECT LOCAL CAPACITY CHARS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_local_capacity_chars",
        insert_method=
        project_local_capacity_chars.insert_project_local_capacity_chars,
        none_message=""
    )

    #### LOAD PROJECT AVAILABILITY DATA ####

    ## PROJECT AVAILABILITY TYPES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_availability_types",
        insert_method=
        project_availability.make_scenario_and_insert_types_and_ids,
        none_message=""
    )

    ## PROJECT AVAILABILITY EXOGENOUS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_availability_exogenous",
        insert_method=
        project_availability.insert_project_availability_exogenous,
        none_message="",
        use_project_method=True
    )

    ## PROJECT AVAILABILITY ENDOGENOUS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_availability_endogenous",
        insert_method=
        project_availability.insert_project_availability_endogenous,
        none_message="",
        use_project_method=True
    )

    #### LOAD PROJECT HEAT RATE DATA ####

    ## PROJECT HEAT RATES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_heat_rate_curves",
        insert_method=project_operational_chars.update_project_hr_curves,
        none_message="",
        use_project_method=True
    )

    #### LOAD PROJECT VARIALE OM DATA ####

    ## PROJECT VARIABLE OM ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_variable_om_curves",
        insert_method=project_operational_chars.update_project_vom_curves,
        none_message="",
        use_project_method=True
    )


    #### LOAD PROJECT STARTUP CHARS DATA ####

    ## PROJECT STARTUP CHARS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_startup_chars",
        insert_method=project_operational_chars.update_project_startup_chars,
        none_message="",
        use_project_method=True
    )

    #### LOAD FUELS DATA ####

    ## FUEL CHARS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_fuels",
        insert_method=fuels.update_fuels,
        none_message=""
    )

    ## FUEL PRICES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="project_fuel_prices",
        insert_method=fuels.update_fuel_prices,
        none_message=""
    )

    #### LOAD POLICY DATA ####

    ## GEOGRAPHY CARBON CAP ZONES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="geography_carbon_cap_zones",
        insert_method=geography.geography_carbon_cap_zones,
        none_message=""
    )

    ## GEOGRAPHY LOCAL CAPACITY ZONES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="geography_local_capacity_zones",
        insert_method=geography.geography_local_capacity_zones,
        none_message=""
    )

    ## GEOGRAPHY PRM ZONES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="geography_prm_zones",
        insert_method=geography.geography_prm_zones,
        none_message=""
    )

    ## GEOGRAPHY RPS ZONES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="geography_rps_zones",
        insert_method=geography.geography_rps_zones,
        none_message=""
    )

    ## PROJECT POLICY (CARBON CAP, PRM, RPS, LOCAL CAPACITY) ZONES ##
    for policy_type in policy_list:
        read_data_and_insert_into_db(
            conn=conn,
            csv_data_master=csv_data_master,
            csvs_main_dir=csv_path,
            quiet=quiet,
            table="project_{}_zones".format(policy_type),
            insert_method=project_zones.project_policy_zones,
            none_message="",
            policy_type=policy_type
        )

    ## SYSTEM CARBON CAP TARGETS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="system_carbon_cap_targets",
        insert_method=carbon_cap.insert_carbon_cap_targets,
        none_message=""
    )

    ## SYSTEM LOCAL CAPACITY TARGETS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="system_local_capacity_requirement",
        insert_method=system_local_capacity.local_capacity_requirement,
        none_message=""
    )

    ## SYSTEM PRM TARGETS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="system_prm_requirement",
        insert_method=system_prm.prm_requirement,
        none_message=""
    )

    ## SYSTEM RPS TARGETS ##
    # Handled differently since an rps_target_scenario_id requires multiple
    # files
    rps_target_dir = get_inputs_dir(
        csvs_main_dir=csv_path, csv_data_master=csv_data_master,
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
        read_data_and_insert_into_db(
            conn=conn,
            csv_data_master=csv_data_master,
            csvs_main_dir=csv_path,
            quiet=quiet,
            table="geography_{}_bas".format(reserve_type),
            insert_method=geography.geography_reserve_bas,
            none_message="",
            reserve_type=reserve_type
        )

    ## PROJECT RESERVES BAS ##
    for reserve_type in reserves_list:
        read_data_and_insert_into_db(
            conn=conn,
            csv_data_master=csv_data_master,
            csvs_main_dir=csv_path,
            quiet=quiet,
            table="project_{}_bas".format(reserve_type),
            insert_method=project_zones.project_reserve_bas,
            none_message="",
            reserve_type=reserve_type
        )


    ## SYSTEM RESERVES ##
    # Handled differently since a reserve_type_scenario_id requires multiple
    # files
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
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="transmission_specified_capacity",
        insert_method=transmission_capacities.insert_transmission_capacities,
        none_message=""
    )

    ## LOAD TRANSMISSION PORTFOLIOS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="transmission_portfolios",
        insert_method=transmission_portfolios.insert_transmission_portfolio,
        none_message=""
    )


    ## LOAD TRANSMISSION ZONES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="transmission_load_zones",
        insert_method=transmission_zones.insert_transmission_load_zones,
        none_message=""
    )

    ## LOAD TRANSMISSION CARBON_CAP_ZONES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="transmission_carbon_cap_zones",
        insert_method=transmission_zones.insert_transmission_carbon_cap_zones,
        none_message=""
    )

    ## LOAD TRANSMISSION OPERATIONAL CHARS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="transmission_operational_chars",
        insert_method=
        transmission_operational_chars.transmission_operational_chars,
        none_message=""
    )

    ## LOAD TRANSMISSION NEW COST ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="transmission_new_cost",
        insert_method=transmission_new_cost.transmision_new_cost,
        none_message=""
    )

    ## LOAD TRANSMISSION HURDLE RATES ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="transmission_hurdle_rates",
        insert_method=
        transmission_hurdle_rates.insert_transmission_hurdle_rates,
        none_message=""
    )

    ## LOAD TRANSMISSION SIMULTANEOUS FLOW LIMITS ##
    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="transmission_simultaneous_flow_limits",
        insert_method=
        simultaneous_flows.insert_into_database,
        none_message=""
    )

    read_data_and_insert_into_db(
        conn=conn,
        csv_data_master=csv_data_master,
        csvs_main_dir=csv_path,
        quiet=quiet,
        table="transmission_simultaneous_flow_limit_line_groups",
        insert_method=simultaneous_flow_groups.insert_into_database,
        none_message=""
    )


    # TODO: organize all PRM-related data in one place
    # TODO: refactor this to consolidate with temporal inputs loading and
    #  any other subscenarios that are based on a directory
    ## LOAD ELCC SURFACE DATA ##
    # Handled differently since an elcc_surface_scenario_id requires multiple
    # files
    elcc_surface_dir = get_inputs_dir(
        csvs_main_dir=csv_path, csv_data_master=csv_data_master,
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
    scenarios_dir = get_inputs_dir(
        csvs_main_dir=csv_path, csv_data_master=csv_data_master,
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

        scenario.load_scenarios_from_csv(conn, c, csv_data_input)
    else:
        print("ERROR: scenarios table is required")


    #### LOAD SOLVER OPTIONS ####
    solver_dir = get_inputs_dir(
        csvs_main_dir=csv_path, csv_data_master=csv_data_master,
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

        solver_options.load_solver_options(
            conn, c, csv_solver_options, csv_solver_descriptions
        )
    else:
        print("ERROR: solver tables are required")


def read_data_and_insert_into_db(
        conn, csv_data_master, csvs_main_dir, quiet, table, insert_method,
        none_message, use_project_method=False, **kwargs
):
    """
    Read data, convert to tuples, and insert into database.
    """
    # Check if we should include the table
    inputs_dir = get_inputs_dir(
        csvs_main_dir=csvs_main_dir, csv_data_master=csv_data_master,
        table=table
    )

    # If the table is included, make a list of tuples for the subscenario
    # and inputs, and insert into the database via the relevant method
    if inputs_dir is not None:
        if not use_project_method:
            (csv_subscenario_input, csv_data_input) = \
                csvs_read.csv_read_data(inputs_dir, quiet)
        else:
            (csv_subscenario_input, csv_data_input) = \
                csvs_read.csv_read_project_data(
                    inputs_dir, quiet
                )

        subscenario_tuples = [
            tuple(x) for x in csv_subscenario_input.to_records(index=False)
        ]
        inputs_tuples = [
            tuple(x) for x in csv_data_input.to_records(index=False)
         ]

        # Insertion method
        insert_method(
            conn=conn,
            subscenario_data=subscenario_tuples,
            inputs_data=inputs_tuples,
            **kwargs
        )
    # If not included, print the none_message
    else:
        print(none_message)


def get_inputs_dir(csvs_main_dir, csv_data_master, table):
    if csv_data_master.loc[
        csv_data_master['table'] == table, 'include'
    ].iloc[0] == 1:
        inputs_dir = os.path.join(
            csvs_main_dir,
            csv_data_master.loc[
                csv_data_master['table'] == table,
                'path'
            ].iloc[0]
        )
    else:
        inputs_dir = None

    return inputs_dir


def read_and_load_inputs(
        csv_path, csv_data_master, table, conn, load_method,
        quiet, none_message, use_project_method=False
):
    data_folder_path = get_inputs_dir(
        csvs_main_dir=csv_path, csv_data_master=csv_data_master, table=table
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
