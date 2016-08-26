#!/usr/bin/env python

import os.path

from reserve_requirements import add_generic_reserve_components


def add_model_components(m, d):
    add_generic_reserve_components(
        m,
        d,
        reserve_violation_variable="Regulation_Up_Violation_MW",
        reserve_violation_penalty_param="regulation_up_violation_penalty_mw",
        reserve_requirement_param="regulation_up_requirement_mw",
        reserve_generator_set="REGULATION_UP_GENERATORS",
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
    for z in getattr(m, "LOAD_ZONES"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Regulation_Up_Violation_MW[" + str(z) + ", "
                  + str(tmp) + "]: "
                  + str(m.Regulation_Up_Violation_MW[z, tmp].value)
                  )