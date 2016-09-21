#!/usr/bin/env python

import csv
import os.path

from reserve_requirements import add_generic_reserve_components


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    add_generic_reserve_components(
        m,
        d,
        reserve_violation_variable="Regulation_Up_Violation_MW",
        reserve_violation_penalty_param="regulation_up_violation_penalty_mw",
        reserve_requirement_param="regulation_up_requirement_mw",
        reserve_generator_set="REGULATION_UP_RESOURCES",
        generator_reserve_provision_variable="Provide_Regulation_Up_MW",
        total_reserve_provision_variable="Total_Regulation_Up_Provision_MW",
        meet_reserve_constraint="Meet_Regulation_Up_Constraint",
        objective_function_reserve_penalty_cost_component=
        "Regulation_Up_Penalty_Cost"
        )


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs",
                                           "regulation_up_requirement.tab"),
                     param=m.regulation_up_requirement_mw

                     )


def export_results(scenario_directory, horizon, stage, m):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "regulation_up_violation.csv"), "wb") \
            as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["zone", "timepoint",
                         "regulation_up_violation_mw"]
                        )
        for z in getattr(m, "LOAD_ZONES"):
            for tmp in getattr(m, "TIMEPOINTS"):
                writer.writerow([
                    z,
                    tmp,
                    m.Regulation_Up_Violation_MW[z, tmp].value]
                )


def save_duals(m):
    m.constraint_indices["Meet_Regulation_Up_Constraint"] = \
        ["zone", "timepoint", "dual"]
