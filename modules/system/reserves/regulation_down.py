#!/usr/bin/env python

import os.path

from reserve_requirements import add_generic_reserve_components


def add_model_components(m, d):
    add_generic_reserve_components(
        m,
        d,
        reserve_violation_variable="Regulation_Down_Violation_MW",
        reserve_violation_penalty_param=
        "regulation_down_violation_penalty_per_mw",
        reserve_requirement_param="regulation_down_requirement_mw",
        reserve_generator_set="REGULATION_DOWN_GENERATORS",
        generator_reserve_provision_variable="Provide_Regulation_Down_MW",
        total_reserve_provision_variable="Total_Regulation_Down_Provision_MW",
        meet_reserve_constraint="Meet_Regulation_Down_Constraint",
        objective_function_reserve_penalty_cost_component=
        "Regulation_Down_Penalty_Cost"
        )


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs",
                                           "regulation_down_requirement.tab"),
                     param=m.regulation_down_requirement_mw

                     )


def export_results(scenario_directory, horizon, stage, m):
    for z in getattr(m, "LOAD_ZONES"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Regulation_Down_Violation_MW[" + str(z) + ", "
                  + str(tmp) + "]: "
                  + str(m.Regulation_Down_Violation_MW[z, tmp].value)
                  )