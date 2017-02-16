#!/usr/bin/env python

"""
Add project-level components for upward regulation reserves
"""

from modules.project.operations.reserves.reserve_provision import \
    generic_determine_dynamic_components, generic_add_model_components, \
    generic_load_model_data, generic_export_module_specific_results

# Reserve-module variables
MODULE_NAME = "regulation_up"
# Dynamic components
HEADROOM_OR_FOOTROOM_DICT_NAME = "headroom_variables"
# Inputs
BA_COLUMN_NAME_IN_INPUT_FILE = "regulation_up_zone"
RESERVE_PROVISION_DERATE_COLUMN_NAME_IN_INPUT_FILE = "regulation_up_derate"
RESERVE_BALANCING_AREAS_INPUT_FILE_NAME = \
    "regulation_up_balancing_areas.tab"
# Model components
RESERVE_PROVISION_VARIABLE_NAME = "Provide_Regulation_Up_MW"
RESERVE_PROVISION_DERATE_PARAM_NAME = "regulation_up_derate"
RESERVE_PROVISION_SUBHOURLY_ADJUSTMEN_PARAM_NAME = \
    "regulation_up_provision_subhourly_energy_adjustment"
RESERVE_BALANCING_AREA_PARAM_NAME = "regulation_up_zone"
RESERVE_PROJECTS_SET_NAME = "REGULATION_UP_PROJECTS"
RESERVE_BALANCING_AREAS_SET_NAME = "REGULATION_UP_ZONES"
RESERVE_PROJECT_OPERATIONAL_TIMEPOINTS_SET_NAME = \
    "REGULATION_UP_PROJECT_OPERATIONAL_TIMEPOINTS"


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
        reserve_provision_subhourly_adjustment_param_name=
        RESERVE_PROVISION_SUBHOURLY_ADJUSTMEN_PARAM_NAME,
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
        reserve_provision_subhourly_adjustment_param=
        RESERVE_PROVISION_SUBHOURLY_ADJUSTMEN_PARAM_NAME
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
        reserve_provision_subhourly_adjustment_param
        =RESERVE_PROVISION_SUBHOURLY_ADJUSTMEN_PARAM_NAME,
        reserve_balancing_areas_input_file
        =RESERVE_BALANCING_AREAS_INPUT_FILE_NAME
    )


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export project-level results for upward regulation
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
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME
    )
