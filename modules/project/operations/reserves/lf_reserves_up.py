#!/usr/bin/env python

"""
Add project-level components for upward load-following reserves
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
        "lf_reserves_up",
        "headroom_variables",
        "lf_reserves_up_zone",
        "Provide_LF_Reserves_Up_MW"
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
        "LF_RESERVES_UP_PROJECTS",
        "lf_reserves_up_zone",
        "LF_RESERVES_UP_ZONES",
        "LF_RESERVES_UP_PROJECT_OPERATIONAL_TIMEPOINTS",
        "Provide_LF_Reserves_Up_MW"
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
        "lf_reserves_up_zone",
        "lf_reserves_up_zone",
        "LF_RESERVES_UP_PROJECTS"
    )


def export_module_specific_results(m, d):
    """
    Export project-level results for upward load-following
    :param m:
    :param d:
    :return:
    """

    generic_export_module_specific_results(
        m, d,
        "LF_RESERVES_UP_PROJECT_OPERATIONAL_TIMEPOINTS",
        "Provide_LF_Reserves_Up_MW",
        "lf_reserves_up_mw"
    )
