#!/usr/bin/env python

"""
Add project-level components for downward load-following reserves
"""

from modules.project.operations.reserves.reserve_provision import \
    generic_determine_dynamic_components, generic_add_model_components, \
    generic_load_model_data, generic_export_module_specific_results


def determine_dynamic_components(d, scenario_directory, horizon, stage):
    """

    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    generic_determine_dynamic_components(
        d,
        scenario_directory,
        horizon,
        stage,
        "lf_reserves_down",
        "footroom_variables",
        "lf_reserves_down_zone",
        "Provide_LF_Reserves_Down_MW"
    )


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        scenario_directory,
        horizon,
        stage,
        "LF_RESERVES_DOWN_PROJECTS",
        "lf_reserves_down_zone",
        "LF_RESERVES_DOWN_ZONES",
        "LF_RESERVES_DOWN_PROJECT_OPERATIONAL_TIMEPOINTS",
        "Provide_LF_Reserves_Down_MW"
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
        m,
        d,
        data_portal,
        scenario_directory,
        horizon,
        stage,
        "lf_reserves_down_zone",
        "lf_reserves_down_zone",
        "LF_RESERVES_DOWN_PROJECTS"
    )


def export_module_specific_results(m, d):
    """
    Export project-level results for downward load-following
    :param m:
    :param d:
    :return:
    """

    generic_export_module_specific_results(
        m, d,
        "LF_RESERVES_DOWN_PROJECT_OPERATIONAL_TIMEPOINTS",
        "Provide_LF_Reserves_Down_MW",
        "lf_reserves_down_mw"
    )
