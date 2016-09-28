#!/usr/bin/env python

import csv
import os.path
from pyomo.environ import Param, Var, Set, Expression, Constraint, \
    NonNegativeReals


def generic_add_model_components(
        m,
        d,
        reserve_zone_set,
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
    1) the reserve zone set name
    2) the reserve zone param name
    3) the 2-dimensional set of reserve zones and timepoints for the requirement
    4) a variable for violating the requirement and a penalty for violation
    5) the reserve requirement (currently by zone and timepoint)
    6) the set of generators that can provide reserves
    7) the name of the generator-level reserve provision variable
    8) an expression aggregating generator-level provision to total provision
    9) the constraint ensuring total provision exceeds the requirement
    10) an expression for total penalty costs that may have been incurred to add
    to the objective function
    :param m:
    :param d:
    :param reserve_zone_set:
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

    # BA-timepoint combinations with requirement
    setattr(m, reserve_zone_timepoint_set,
            Set(dimen=2,
                within = getattr(m, reserve_zone_set) * m.TIMEPOINTS
                )
            )
    # Penalty for violation
    setattr(m, reserve_violation_variable,
            Var(getattr(m, reserve_zone_timepoint_set),
                within=NonNegativeReals)
            )
    setattr(m, reserve_violation_penalty_param,
            Param(getattr(m, reserve_zone_set),
                  within=NonNegativeReals))

    # Magnitude of the requirement by reserve zone and timepoint
    setattr(m, reserve_requirement_param,
            Param(getattr(m, reserve_zone_timepoint_set),
                  within=NonNegativeReals)
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
    def total_reserve_rule(mod, ba, tmp):
        return sum(getattr(mod, generator_reserve_provision_variable)[g, tmp]
                   for g in getattr(mod, op_set)[tmp]
                   if getattr(mod, reserve_zone_param)[g] == ba
                   )
    setattr(m, total_reserve_provision_expression,
            Expression(getattr(m, reserve_zone_timepoint_set),
                       rule=total_reserve_rule))

    # Reserve constraints
    def meet_reserve_rule(mod, ba, tmp):
        return getattr(mod, total_reserve_provision_expression)[ba, tmp] \
            + getattr(mod, reserve_violation_variable)[ba, tmp] \
            == getattr(mod, reserve_requirement_param)[ba, tmp]

    setattr(m, meet_reserve_constraint,
            Constraint(getattr(m, reserve_zone_timepoint_set),
                       rule=meet_reserve_rule))

    # Add violation penalty costs incurred to objective function
    # TODO: this needs to be multiplied by hours in timepoint andhorizon weight
    def penalty_costs_rule(mod):
        return sum(getattr(mod, reserve_violation_variable)[ba, tmp]
                   * getattr(mod, reserve_violation_penalty_param)[ba]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (ba, tmp)
                   in getattr(mod, reserve_zone_timepoint_set)
                   )
    setattr(m, objective_function_reserve_penalty_cost_component,
            Expression(rule=penalty_costs_rule))

    d.total_cost_components.append(
        objective_function_reserve_penalty_cost_component)


def generic_load_model_data(m, d, data_portal,
                            scenario_directory, horizon, stage,
                            ba_list_filename,
                            reserve_violation_penalty_param,
                            requirement_filename,
                            reserve_zone_timepoint_set,
                            reserve_requirement_param):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param ba_list_filename:
    :param reserve_violation_penalty_param:
    :param requirement_filename:
    :param reserve_zone_timepoint_set:
    :param reserve_requirement_param:
    :return:
    """

    data_portal.load(filename=os.path.join(scenario_directory, "inputs",
                                           ba_list_filename),
                     param=getattr(m, reserve_violation_penalty_param)
                     )

    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs",
                                           requirement_filename),
                     index=getattr(m, reserve_zone_timepoint_set),
                     param=getattr(m, reserve_requirement_param)
                     )


def generic_export_results(scenario_directory, horizon, stage, m, d,
                           filename,
                           column_name,
                           reserve_zone_timepoint_set,
                           reserve_violation_variable
                           ):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :param filename:
    :param column_name:
    :param reserve_zone_timepoint_set:
    :param reserve_violation_variable:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           filename), "wb") \
            as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["zone", "timepoint",
                         column_name]
                        )
        for (ba, tmp) in getattr(m, reserve_zone_timepoint_set):
            writer.writerow([
                ba,
                tmp,
                getattr(m, reserve_violation_variable)[ba, tmp].value]
            )


def generic_save_duals(m, reserve_constraint_name):
    """

    :param m:
    :param reserve_constraint_name:
    :return:
    """
    m.constraint_indices[reserve_constraint_name] = \
        ["zone", "timepoint", "dual"]
