#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module adds an objective function to the model, minimizing total system
cost.
"""

from pyomo.environ import Objective, minimize

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    At this point, all relevant modules should have added cost components to
    *d.total_cost_components*. We sum them all up here. With the minimum set
    of functionality, the objective function will be as follows:

    :math:`minimize:` \n

    :math:`Total\_Capacity\_Costs + Total\_Variable\_OM\_Cost +
    Total\_Fuel\_Cost + Total\_Load\_Balance\_Penalty\_Costs`

    """

    # Define objective function
    def total_cost_rule(mod):

        return sum(getattr(mod, c)
                   for c in getattr(d, total_cost_components))

    m.Total_Cost = Objective(rule=total_cost_rule, sense=minimize)
