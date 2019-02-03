#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function
from __future__ import absolute_import

import csv
import os.path
from pyomo.environ import Var, Constraint, NonNegativeReals

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
        "FREQUENCY_RESPONSE_BA_TIMEPOINTS",
        "Frequency_Response_Violation_MW",
        "frequency_response_requirement_mw", 
        "Total_Frequency_Response_Provision_MW",
        "Meet_Frequency_Response_Constraint"
        )

    m.Frequency_Response_Partial_Violation_MW = Var(
        m.FREQUENCY_RESPONSE_BA_TIMEPOINTS, within=NonNegativeReals
    )

    # Partial frequency response requirement constraint
    def meet_partial_frequency_response_rule(mod, ba, tmp):
        return mod.Total_Partial_Frequency_Response_Provision_MW[ba, tmp] \
            + mod.Frequency_Response_Partial_Violation_MW[ba, tmp] \
            == mod.frequency_response_requirement_partial_mw[ba, tmp]

    m.Meet_Frequency_Response_Partial_Constraint = \
        Constraint(m.FREQUENCY_RESPONSE_BA_TIMEPOINTS,
                   rule=meet_partial_frequency_response_rule)


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
                           "frequency_response_violation.csv",
                           "frequency_response_violation_mw",
                           "FREQUENCY_RESPONSE_BA_TIMEPOINTS",
                           "Frequency_Response_Violation_MW"
                           )

    generic_export_results(scenario_directory, horizon, stage, m, d,
                           "frequency_response_partial_violation.csv",
                           "frequency_response_partial_violation_mw",
                           "FREQUENCY_RESPONSE_BA_TIMEPOINTS",
                           "Frequency_Response_Partial_Violation_MW"
                           )


def save_duals(m):
    """

    :param m:
    :return:
    """
    generic_save_duals(m, "Meet_Frequency_Response_Constraint")
    generic_save_duals(m, "Meet_Frequency_Response_Partial_Constraint")


def import_results_into_database(scenario_id, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """

    print("system frequency response balance")

    generic_import_results_to_database(
        scenario_id=scenario_id,
        c=c,
        db=db,
        results_directory=results_directory,
        reserve_type="frequency_response"
    )

    generic_import_results_to_database(
        scenario_id=scenario_id,
        c=c,
        db=db,
        results_directory=results_directory,
        reserve_type="frequency_response_partial"
    )
