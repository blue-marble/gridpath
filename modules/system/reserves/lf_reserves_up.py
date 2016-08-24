#!/usr/bin/env python

import os.path

from reserve_requirements import add_generic_reserve_components


def add_model_components(m):
    add_generic_reserve_components(
        m,
        reserve_violation_variable="LF_Reserves_Up_Violation",
        reserve_violation_penalty_param="lf_reserves_up_violation_penalty",
        reserve_requirement_param="lf_reserves_up_requirement_mw",
        reserve_generator_set="LF_RESERVES_UP_GENERATORS",
        generator_reserve_provision_variable="Provide_LF_Reserves_Up",
        total_reserve_provision_variable="LF_Reserves_Up_Provision",
        meet_reserve_constraint="Meet_LF_Reserves_Up_Constraint",
        objective_function_reserve_penalty_cost_component=
        "LF_Reserve_Up_Penalty_Costs"
        )


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs",
                                           "lf_reserves_up_requirement.tab"),
                     param=m.lf_reserves_up_requirement_mw
                     )


def export_results(scenario_directory, horizon, stage, m):
    for z in getattr(m, "LOAD_ZONES"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("LF_Reserves_Up_Violation[" + str(z) + ", " + str(tmp) + "]: "
                  + str(m.LF_Reserves_Up_Violation[z, tmp].value)
                  )
