#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from pyomo.environ import Set, Expression


def generic_add_model_components(
        m,
        d,
        reserve_zone_param,
        reserve_zone_timepoint_set,
        reserve_generator_set,
        generator_reserve_provision_variable,
        total_reserve_provision_expression
):
    """
    Generic treatment of reserves. This function creates model components
    related to a particular reserve requirement, including
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
    :param reserve_zone_param:
    :param reserve_zone_timepoint_set:
    :param reserve_generator_set:
    :param generator_reserve_provision_variable:
    :param total_reserve_provision_expression:
    :return:
    """

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
