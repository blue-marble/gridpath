#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Add project-level components for spinning reserves
"""
from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
import pandas as pd

from gridpath.auxiliary.validations import write_validation_to_database, \
    validate_idxs
from gridpath.project.operations.reserves.reserve_provision import \
    generic_determine_dynamic_components, generic_add_model_components, \
    generic_load_model_data, generic_export_module_specific_results, \
    generic_import_results_into_database, generic_get_inputs_from_database


# Reserve-module variables
MODULE_NAME = "spinning_reserves"
# Dynamic components
HEADROOM_OR_FOOTROOM_DICT_NAME = "headroom_variables"
# Inputs
BA_COLUMN_NAME_IN_INPUT_FILE = "spinning_reserves_ba"
RESERVE_PROVISION_DERATE_COLUMN_NAME_IN_INPUT_FILE = "spinning_reserves_derate"
RESERVE_BALANCING_AREAS_INPUT_FILE_NAME = \
    "spinning_reserves_balancing_areas.tab"
# Model components
RESERVE_PROVISION_VARIABLE_NAME = "Provide_Spinning_Reserves_MW"
RESERVE_PROVISION_DERATE_PARAM_NAME = "spinning_reserves_derate"
RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME = \
    "spinning_reserves_reserve_to_energy_adjustment"
RESERVE_BALANCING_AREA_PARAM_NAME = "spinning_reserves_zone"
RESERVE_PROJECTS_SET_NAME = "SPINNING_RESERVES_PROJECTS"
RESERVE_BALANCING_AREAS_SET_NAME = "SPINNING_RESERVES_ZONES"
RESERVE_PRJ_OPR_TMPS_SET_NAME = \
    "SPINNING_RESERVES_PRJ_OPR_TMPS"


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """

    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    generic_determine_dynamic_components(
        d=d,
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        reserve_module=MODULE_NAME,
        headroom_or_footroom_dict=HEADROOM_OR_FOOTROOM_DICT_NAME,
        ba_column_name=BA_COLUMN_NAME_IN_INPUT_FILE,
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME,
        reserve_provision_derate_param_name=
        RESERVE_PROVISION_DERATE_PARAM_NAME,
        reserve_to_energy_adjustment_param_name=
        RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME,
        reserve_balancing_area_param_name=RESERVE_BALANCING_AREA_PARAM_NAME
    )


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m=m,
        d=d,
        reserve_projects_set=RESERVE_PROJECTS_SET_NAME,
        reserve_balancing_area_param=RESERVE_BALANCING_AREA_PARAM_NAME,
        reserve_provision_derate_param=RESERVE_PROVISION_DERATE_PARAM_NAME,
        reserve_balancing_areas_set=RESERVE_BALANCING_AREAS_SET_NAME,
        reserve_project_operational_timepoints_set=
        RESERVE_PRJ_OPR_TMPS_SET_NAME,
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME,
        reserve_to_energy_adjustment_param=
        RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    generic_load_model_data(
        m=m,
        d=d,
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        ba_column_name=BA_COLUMN_NAME_IN_INPUT_FILE,
        derate_column_name=
        RESERVE_PROVISION_DERATE_COLUMN_NAME_IN_INPUT_FILE,
        reserve_balancing_area_param=RESERVE_BALANCING_AREA_PARAM_NAME,
        reserve_provision_derate_param=RESERVE_PROVISION_DERATE_PARAM_NAME,
        reserve_projects_set=RESERVE_PROJECTS_SET_NAME,
        reserve_to_energy_adjustment_param
        =RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME,
        reserve_balancing_areas_input_file
        =RESERVE_BALANCING_AREAS_INPUT_FILE_NAME
    )


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export project-level results for upward load-following
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    generic_export_module_specific_results(
        m=m,
        d=d,
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        module_name=MODULE_NAME,
        reserve_project_operational_timepoints_set=
        RESERVE_PRJ_OPR_TMPS_SET_NAME,
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME,
        reserve_ba_param_name=RESERVE_BALANCING_AREA_PARAM_NAME
    )


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    # Get project BA
    project_bas, prj_derates = generic_get_inputs_from_database(
        subscenarios=subscenarios,
        subproblem=subproblem,
        stage=stage,
        conn=conn,
        reserve_type="spinning_reserves",
        project_ba_subscenario_id=
        subscenarios.PROJECT_SPINNING_RESERVES_BA_SCENARIO_ID,
        ba_subscenario_id=subscenarios.SPINNING_RESERVES_BA_SCENARIO_ID

    )

    return project_bas, prj_derates


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    project_bas, _ = get_inputs_from_database(
        subscenarios, subproblem, stage, conn
    )

    # Convert input data into pandas DataFrame
    df = pd.DataFrame(
        data=project_bas.fetchall(),
        columns=[s[0] for s in project_bas.description]
    )
    bas_w_project = df["spinning_reserves_ba"].unique()

    # Get the required reserve bas
    # TODO: make this into a function similar to get_projects()?
    #  could eventually centralize all these db query functions in one place
    c = conn.cursor()
    bas = c.execute(
        """SELECT spinning_reserves_ba FROM inputs_geography_spinning_reserves_bas
        WHERE spinning_reserves_ba_scenario_id = {}
        """.format(subscenarios.SPINNING_RESERVES_BA_SCENARIO_ID)
    )
    bas = [b[0] for b in bas]  # convert to list

    # Check that each reserve BA has at least one project assigned to it
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_spinning_reserves_bas",
        severity="High",
        errors=validate_idxs(actual_idxs=bas_w_project,
                             req_idxs=bas,
                             idx_label="spinning_reserves_ba",
                             msg="Each reserve BA needs at least 1 "
                                 "project assigned to it.")
    )


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    projects.tab file (to be precise, amend it).
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    project_bas, prj_derates = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Make a dict for easy access
    prj_ba_dict = dict()
    for (prj, ba) in project_bas:
        prj_ba_dict[str(prj)] = "." if ba is None else (str(ba))

    # Make a dict for easy access
    prj_derate_dict = dict()
    for (prj, derate) in prj_derates:
        prj_derate_dict[str(prj)] = "." if derate is None else str(derate)


    # Add params to projects file
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t", lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("spinning_reserves_ba")
        header.append("spinning_reserves_derate")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_ba_dict.keys()):
                row.append(prj_ba_dict[row[0]])
            # If project not specified, specify no BA
            else:
                row.append(".")

            # If project specified, check if derate specified or not
            if row[0] in list(prj_derate_dict.keys()):
                row.append(prj_derate_dict[row[0]])
            # If project not specified, specify no derate
            else:
                row.append(".")

            # Add resulting row to new_rows list
            new_rows.append(row)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"), "w", newline="") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)


def import_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c: 
    :param db: 
    :param results_directory:
    :param quiet:
    :return: 
    """
    if not quiet:
        print("project spinning reserves provision")

    generic_import_results_into_database(
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
        c=c,
        db=db,
        results_directory=results_directory,
        reserve_type="spinning_reserves"
    )
