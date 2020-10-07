#!/usr/bin/env python
# Copyright 2016-2020 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
