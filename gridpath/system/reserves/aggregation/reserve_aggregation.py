#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from builtins import str
from pyomo.environ import Set, Expression


def generic_add_model_components(
        m,
        d,
        reserve_zone_param,
        reserve_zone_set,
        reserve_generator_set,
        generator_reserve_provision_variable,
        total_reserve_provision_expression
):
    """
    Generic treatment of reserves. This function creates model components
    related to a particular reserve requirement, including
    1) an expression aggregating generator-level provision to total provision
    :param m:
    :param d:
    :param reserve_zone_param:
    :param reserve_zone_set:
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
            Set(m.TMPS,
                initialize=lambda mod, tmp:
                getattr(mod, reserve_generator_set) &
                    mod.OPR_PRJS_IN_TMP[tmp]))

    # Reserve provision
    def total_reserve_rule(mod, ba, tmp):
        return sum(getattr(mod, generator_reserve_provision_variable)[g, tmp]
                   for g in getattr(mod, op_set)[tmp]
                   if getattr(mod, reserve_zone_param)[g] == ba
                   )
    setattr(m, total_reserve_provision_expression,
            Expression(getattr(m, reserve_zone_set), m.TMPS,
                       rule=total_reserve_rule))
