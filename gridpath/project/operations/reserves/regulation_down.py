#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Add project-level components for downward regulation reserves
"""

from gridpath.project.operations.reserves.reserve_provision import \
    generic_determine_dynamic_components, generic_add_model_components, \
    generic_load_model_data, generic_export_module_specific_results, \
    generic_import_results_into_database

# Reserve-module variables
MODULE_NAME = "regulation_down"
# Dynamic components
HEADROOM_OR_FOOTROOM_DICT_NAME = "footroom_variables"
# Inputs
BA_COLUMN_NAME_IN_INPUT_FILE = "regulation_down_zone"
RESERVE_PROVISION_DERATE_COLUMN_NAME_IN_INPUT_FILE = "regulation_down_derate"
RESERVE_BALANCING_AREAS_INPUT_FILE_NAME = \
    "regulation_down_balancing_areas.tab"
# Model components
RESERVE_PROVISION_VARIABLE_NAME = "Provide_Regulation_Down_MW"
RESERVE_PROVISION_DERATE_PARAM_NAME = "regulation_down_derate"
RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME = \
    "regulation_down_reserve_to_energy_adjustment"
RESERVE_BALANCING_AREA_PARAM_NAME = "regulation_down_zone"
RESERVE_PROJECTS_SET_NAME = "REGULATION_DOWN_PROJECTS"
RESERVE_BALANCING_AREAS_SET_NAME = "REGULATION_DOWN_ZONES"
RESERVE_PROJECT_OPERATIONAL_TIMEPOINTS_SET_NAME = \
    "REGULATION_DOWN_PROJECT_OPERATIONAL_TIMEPOINTS"


def determine_dynamic_components(d, scenario_directory, horizon, stage):
    """

    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    generic_determine_dynamic_components(
        d=d,
        scenario_directory=scenario_directory,
        horizon=horizon,
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
        RESERVE_PROJECT_OPERATIONAL_TIMEPOINTS_SET_NAME,
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME,
        reserve_to_energy_adjustment_param=
        RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME
    )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    generic_load_model_data(
        m=m,
        d=d,
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        horizon=horizon,
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


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export project-level results for downward regulation
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    generic_export_module_specific_results(
        m=m,
        d=d,
        scenario_directory=scenario_directory,
        horizon=horizon,
        stage=stage,
        module_name=MODULE_NAME,
        reserve_project_operational_timepoints_set=
        RESERVE_PROJECT_OPERATIONAL_TIMEPOINTS_SET_NAME,
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME,
        reserve_ba_param_name=RESERVE_BALANCING_AREA_PARAM_NAME
    )


def import_results_into_database(
        scenario_id, c, db, results_directory
):
    """

    :param scenario_id: 
    :param c: 
    :param db: 
    :param results_directory:
    :return: 
    """
    print("project regulation down provision")

    generic_import_results_into_database(
        scenario_id=scenario_id,
        c=c,
        db=db,
        results_directory=results_directory,
        reserve_type="regulation_down"
    )
