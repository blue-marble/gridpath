#!/usr/bin/env python

from pyomo.environ import Param, Var, Set, Expression, Constraint, \
    NonNegativeReals


def add_generic_reserve_components(
        m,
        d,
        reserve_zone_param,
        reserve_zone_timepoint_set,
        reserve_violation_variable,
        reserve_violation_penalty_param,
        reserve_requirement_param,
        reserve_generator_set,
        generator_reserve_provision_variable,
        total_reserve_provision_expression,
        meet_reserve_constraint,
        objective_function_reserve_penalty_cost_component):
    """
    Generic treatment of reserves. This function creates the model components
    related to a particular reserve
    requirement, including
    1) the reserve zone param name
    2) the 2-dimensional set of reserve zones and timepoints for the requirement
    3) a variable for violating the requirement and a penalty for violation
    4) the reserve requirement (currently by zone and timepoint)
    5) the set of generators that can provide reserves
    6) the name of the generator-level reserve provision variable
    7) an expression aggregating generator-level provision to total provision
    8) the constraint ensuring total provision exceeds the requirement
    9) an expression for total penalty costs that may have been incurred to add
    to the objective function
    :param m:
    :param d:
    :param reserve_zone_param:
    :param reserve_zone_timepoint_set:
    :param reserve_violation_variable:
    :param reserve_violation_penalty_param:
    :param reserve_requirement_param:
    :param reserve_generator_set:
    :param generator_reserve_provision_variable:
    :param total_reserve_provision_expression:
    :param meet_reserve_constraint:
    :param objective_function_reserve_penalty_cost_component:
    :return:
    """

    # Penalty for violation
    setattr(m, reserve_violation_variable,
            Var(getattr(m, reserve_zone_timepoint_set),
                within=NonNegativeReals)
            )
    setattr(m, reserve_violation_penalty_param, Param(initialize=999999999))

    # Magnitude of the requirement
    # TODO: default to 0 for now; better to not create for load zones w/o req
    setattr(m, reserve_requirement_param,
            Param(getattr(m, reserve_zone_timepoint_set),
                  within=NonNegativeReals, default=0)
            )

    # Reserve generators operational generators in timepoint
    # This will be the intersection of the reserve generator set and the set of
    # generators operational in the timepoint
    op_set = str(reserve_generator_set)+"_OPERATIONAL_IN_TIMEPOINT"
    setattr(m, op_set,
            Set(m.TIMEPOINTS,
                initialize=lambda mod, tmp:
                getattr(mod, reserve_generator_set) &
                    mod.OPERATIONAL_PROJECTS_IN_TIMEPOINT[tmp]))

    # Reserve provision
    def total_reserve_rule(mod, z, tmp):
        return sum(getattr(mod, generator_reserve_provision_variable)[g, tmp]
                   for g in getattr(mod, op_set)[tmp]
                   if getattr(mod, reserve_zone_param)[g] == z
                   )
    setattr(m, total_reserve_provision_expression,
            Expression(getattr(m, reserve_zone_timepoint_set),
                       rule=total_reserve_rule))

    # Reserve constraints
    def meet_reserve_rule(mod, z, tmp):
        return getattr(mod, total_reserve_provision_expression)[z, tmp] \
            + getattr(mod, reserve_violation_variable)[z, tmp] \
            == getattr(mod, reserve_requirement_param)[z, tmp]

    setattr(m, meet_reserve_constraint,
            Constraint(getattr(m, reserve_zone_timepoint_set),
                       rule=meet_reserve_rule))

    # Add violation penalty costs incurred to objective function
    # TODO: this needs to be multiplied by discount rate, hours in timepoint, horizon weight, etc.
    def penalty_costs_rule(mod):
        return sum(getattr(mod, reserve_violation_variable)[z, tmp]
                   * getattr(mod, reserve_violation_penalty_param)
                   for (z, tmp) in getattr(mod, reserve_zone_timepoint_set))
    setattr(m, objective_function_reserve_penalty_cost_component,
            Expression(rule=penalty_costs_rule))

    d.total_cost_components.append(
        objective_function_reserve_penalty_cost_component)
