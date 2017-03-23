#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from reserve_balance import generic_add_model_components, \
    generic_export_results, generic_save_duals


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        "REGULATION_UP_ZONE_TIMEPOINTS",
        "Regulation_Up_Violation_MW",
        "regulation_up_requirement_mw", 
        "Total_Regulation_Up_Provision_MW",
        "Meet_Regulation_Up_Constraint"
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
