#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function
from __future__ import absolute_import

from .reserve_balance import generic_add_model_components, \
    generic_export_results, generic_save_duals, \
    generic_import_results_to_database


def add_model_components(m, di, dc):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m=m,
        d=d,
        reserve_zone_set="SPINNING_RESERVES_ZONES",
        reserve_violation_variable="Spinning_Reserves_Violation_MW",
        reserve_violation_expression
        ="Spinning_Reserves_Violation_MW_Expression",
        reserve_violation_allowed_param="spinning_reserves_allow_violation",
        reserve_requirement_expression="Spin_Requirement",
        total_reserve_provision_expression
        ="Total_Spinning_Reserves_Provision_MW",
        meet_reserve_constraint="Meet_Spinning_Reserves_Constraint"
        )


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    generic_export_results(scenario_directory, subproblem, stage, m, d,
                           "spinning_reserves_violation.csv",
                           "spinning_reserves_violation_mw",
                           "SPINNING_RESERVES_ZONES",
                           "Spinning_Reserves_Violation_MW_Expression"
                           )


def save_duals(m):
    """

    :param m:
    :return:
    """
    generic_save_duals(m, "Meet_Spinning_Reserves_Constraint")


def import_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    if not quiet:
        print("system spinning reserves balance")

    generic_import_results_to_database(
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
        c=c,
        db=db,
        results_directory=results_directory,
        reserve_type="spinning_reserves"
    )
