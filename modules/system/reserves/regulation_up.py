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
        "REGULATION_UP_ZONES",
        "regulation_up_zone",
        "REGULATION_UP_ZONE_TIMEPOINTS",
        "Regulation_Up_Violation_MW",
        "regulation_up_violation_penalty_per_mw",
        "regulation_up_requirement_mw",
        "REGULATION_UP_PROJECTS",
        "Provide_Regulation_Up_MW",
        "Total_Regulation_Up_Provision_MW",
        "Meet_Regulation_Up_Constraint",
        "Regulation_Up_Penalty_Costs"
        )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, horizon, stage,
                            "regulation_up_balancing_areas.tab",
                            "regulation_up_violation_penalty_per_mw",
                            "regulation_up_requirement.tab",
                            "REGULATION_UP_ZONE_TIMEPOINTS",
                            "regulation_up_requirement_mw"
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
                           "regulation_up_violation.csv",
                           "regulation_up_violation_mw",
                           "REGULATION_UP_ZONE_TIMEPOINTS",
                           "Regulation_Up_Violation_MW"
                           )


def save_duals(m):
    """

    :param m:
    :return:
    """
    generic_save_duals(m, "Meet_Regulation_Up_Constraint")
