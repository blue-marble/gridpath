#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Fully deliverable projects (no energy-only allowed)
"""

from pyomo.environ import Set


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    
    :param m: 
    :param d: 
    :return: 
    """
    m.FULLY_DELIVERABLE_PRM_PROJECTS = Set(
        within=m.PRM_PROJECTS,
        initialize=lambda mod:
        [p for p in mod.PRM_PROJECTS if mod.prm_type[p] == "fully_deliverable"]
    )


def elcc_eligible_capacity_rule(mod, g, p):
    """
    
    :param mod: 
    :param g: 
    :param p: 
    :return: 
    """
    return mod.Capacity_MW[g, p]
