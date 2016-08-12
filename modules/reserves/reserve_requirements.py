#!/usr/bin/env python

from pyomo.environ import *


def add_generic_reserve_components(m,
                                   reserve_violation_variable,
                                   reserve_violation_penalty_param,
                                   reserve_requirement_param,
                                   reserve_generator_set,
                                   generator_reserve_provision_variable,
                                   total_reserve_provision_variable,
                                   meet_reserve_constraint,
                                   objective_function_reserve_penalty_cost_component):
    """
    Generic treatment of reserves. This function creates the model components related to a particular reserve
    requirement, including
    1) a variable for violating the requirement and a penalty for violation
    2) the reserve requirement (currently by zone and timepoint)
    3) the set of generators that can provide reserves
    4) the name of the generator-level reserve provision variable
    5) an expression aggregating generator-level provision to total provision
    6) the constraint ensuring total provision exceeds the requirement
    7) an expression for total penalty costs that may have been incurred to add to the objective function
    :param m:
    :param reserve_violation_variable:
    :param reserve_violation_penalty_param:
    :param reserve_requirement_param:
    :param reserve_generator_set:
    :param generator_reserve_provision_variable:
    :param total_reserve_provision_variable:
    :param meet_reserve_constraint:
    :param objective_function_reserve_penalty_cost_component:
    :return:
    """

    # Penalty for violation
    setattr(m, reserve_violation_variable, Var(m.LOAD_ZONES, m.TIMEPOINTS, within=NonNegativeReals))
    setattr(m, reserve_violation_penalty_param, Param(initialize=999999999))

    # Magnitude of the requirement
    setattr(m, reserve_requirement_param, Param(m.LOAD_ZONES, m.TIMEPOINTS, within=NonNegativeReals))

    # TODO: by zone eventually, not all generators
    # Reserve provision
    def total_reserve_rule(m, z, tmp):
        return sum(getattr(m, generator_reserve_provision_variable)[g, tmp] for g in getattr(m, reserve_generator_set))
    setattr(m, total_reserve_provision_variable, Expression(m.LOAD_ZONES, m.TIMEPOINTS, rule=total_reserve_rule))

    # Reserve constraints
    def meet_reserve_rule(m, z, tmp):
        return getattr(m, total_reserve_provision_variable)[z, tmp] == getattr(m, reserve_requirement_param)[z, tmp]

    setattr(m, meet_reserve_constraint, Constraint(m.LOAD_ZONES, m.TIMEPOINTS, rule=meet_reserve_rule))

    # Add violation penalty costs incurred to objective function
    def penalty_costs_rule(m):
        return sum(getattr(m, reserve_violation_variable)[z, tmp] * getattr(m, reserve_violation_penalty_param)
                   for z in m.LOAD_ZONES for tmp in m.TIMEPOINTS)
    setattr(m, objective_function_reserve_penalty_cost_component, Expression(rule=penalty_costs_rule))

    m.total_cost_components.append(objective_function_reserve_penalty_cost_component)

