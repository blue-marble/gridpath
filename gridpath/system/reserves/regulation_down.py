#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from reserve_requirements import generic_add_model_components, \
    generic_load_model_data, generic_export_results, generic_save_duals


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        "REGULATION_DOWN_ZONES",
        "regulation_down_zone",
        "REGULATION_DOWN_ZONE_TIMEPOINTS",
        "Regulation_Down_Violation_MW",
        "regulation_down_violation_penalty_per_mw",
        "regulation_down_requirement_mw",
        "REGULATION_DOWN_PROJECTS",
        "Provide_Regulation_Down_MW",
        "Total_Regulation_Down_Provision_MW",
        "Meet_Regulation_Down_Constraint",
        "Regulation_Down_Penalty_Costs"
        )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    generic_load_model_data(m, d, data_portal,
                            scenario_directory, horizon, stage,
                            "regulation_down_balancing_areas.tab",
                            "regulation_down_violation_penalty_per_mw",
                            "regulation_down_requirement.tab",
                            "REGULATION_DOWN_ZONE_TIMEPOINTS",
                            "regulation_down_requirement_mw"
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
                           "regulation_down_violation.csv",
                           "regulation_down_violation_mw",
                           "REGULATION_DOWN_ZONE_TIMEPOINTS",
                           "Regulation_Down_Violation_MW"
                           )


def save_duals(m):
    """

    :param m:
    :return:
    """
    generic_save_duals(m, "Meet_Regulation_Down_Constraint")
