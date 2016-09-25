#!/usr/bin/env python

from reserve_requirements import generic_add_model_components, \
    generic_load_model_data, generic_export_results, generic_save_duals


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
        "LF_RESERVES_DOWN_ZONES",
        "lf_reserves_down_zone",
        "LF_RESERVES_DOWN_ZONE_TIMEPOINTS",
        "LF_Reserves_Down_Violation_MW",
        "lf_reserves_down_violation_penalty_per_mw",
        "lf_reserves_down_requirement_mw",
        "LF_RESERVES_DOWN_PROJECTS",
        "Provide_LF_Reserves_Down_MW",
        "Total_LF_Reserves_Down_Provision_MW",
        "Meet_LF_Reserves_Down_Constraint",
        "LF_Reserves_Down_Penalty_Costs"
        )


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    generic_load_model_data(m, data_portal, scenario_directory, horizon, stage,
                            "load_following_down_balancing_areas.tab",
                            "lf_reserves_down_violation_penalty_per_mw",
                            "lf_reserves_down_requirement.tab",
                            "LF_RESERVES_DOWN_ZONE_TIMEPOINTS",
                            "lf_reserves_down_requirement_mw"
                            )


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    generic_export_results(scenario_directory, horizon, stage, m, d,
                           "lf_reserves_down_violation.csv",
                           "lf_reserves_down_violation_mw",
                           "LF_RESERVES_DOWN_ZONE_TIMEPOINTS",
                           "LF_Reserves_Down_Violation_MW"
                           )


def save_duals(m):
    """

    :param m:
    :return:
    """
    generic_save_duals(m, "Meet_LF_Reserves_Down_Constraint")
