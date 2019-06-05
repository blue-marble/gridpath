#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function
from __future__ import absolute_import

from .reserve_balance import generic_add_model_components, \
    generic_export_results, generic_save_duals, \
    generic_import_results_to_database


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m,
        d,
        "LF_RESERVES_UP_ZONE_TIMEPOINTS",
        "LF_Reserves_Up_Violation_MW",
        "lf_reserves_up_requirement_mw", 
        "Total_LF_Reserves_Up_Provision_MW",
        "Meet_LF_Reserves_Up_Constraint"
        )


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param stage:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    generic_export_results(scenario_directory, subproblem, stage, m, d,
                           "lf_reserves_up_violation.csv",
                           "lf_reserves_up_violation_mw",
                           "LF_RESERVES_UP_ZONE_TIMEPOINTS",
                           "LF_Reserves_Up_Violation_MW"
                           )


def save_duals(m):
    """

    :param m:
    :return:
    """
    generic_save_duals(m, "Meet_LF_Reserves_Up_Constraint")


def import_results_into_database(scenario_id, subproblem, stage, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """

    print("system lf reserves up balance")

    generic_import_results_to_database(
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
        c=c,
        db=db,
        results_directory=results_directory,
        reserve_type="lf_reserves_up"
    )
