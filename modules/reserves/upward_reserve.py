from pyomo.environ import *
from reserve_requirements import add_generic_reserve_components


def add_model_components(m):
    add_generic_reserve_components(
        m,
        reserve_violation_variable="Upward_Reserve_Violation",
        reserve_violation_penalty_param="upward_reserve_violation_penalty",
        reserve_requirement_param="upward_reserve_requirement_mw",
        reserve_generator_set="RESERVE_GENERATORS",
        generator_reserve_provision_variable="Upward_Reserve",
        total_reserve_provision_variable="Upward_Reserve_Provision",
        meet_reserve_constraint="Meet_Upward_Reserve_Constraint",
        objective_function_reserve_penalty_cost_component="Reserve_Penalty_Costs"
        )


def export_results(m):
    for z in getattr(m, "LOAD_ZONES"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Upward_Reserve_Violation[" + str(z) + ", " + str(tmp) + "]: "
                  + str(m.Upward_Reserve_Violation[z, tmp].value)
                  )