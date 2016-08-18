#!/usr/bin/env python

from pyomo.environ import *


def add_model_components(m):
    def total_cost_rule(m):

        return sum(getattr(m, component)
                   for component in m.total_cost_components)

    m.Total_Cost = Objective(rule=total_cost_rule, sense=minimize)