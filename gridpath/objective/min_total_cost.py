#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from pyomo.environ import Objective, minimize

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d):
    """
    Aggregate costs and components to objective function.
    :param m:
    :param d:
    :return:
    """

    # Define objective function
    def total_cost_rule(mod):

        return sum(getattr(mod, c)
                   for c in getattr(d, total_cost_components))

    m.Total_Cost = Objective(rule=total_cost_rule, sense=minimize)