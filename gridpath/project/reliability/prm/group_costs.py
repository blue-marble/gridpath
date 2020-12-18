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


import os.path
import pandas as pd
from pyomo.environ import Set, Expression, Param

from gridpath.auxiliary.auxiliary import join_sets
from gridpath.project.reliability.prm.common_functions import \
    load_prm_type_modules
from gridpath.auxiliary.dynamic_components import prm_cost_group_sets, \
    prm_cost_group_prm_type


def add_model_components(m, d, subproblem_stage_directory):
    """

    :param m:
    :param d:
    :return:
    """

    m.PRM_COST_GROUPS = Set(
            initialize=lambda mod:
            join_sets(mod, getattr(d, prm_cost_group_sets))
            )

    def group_prm_type_init(mod, group):
        """
        Figure out the PRM type of each group
        :param mod:
        :param group:
        :return:
        """
        for group_set in getattr(d, prm_cost_group_sets):
            for element in getattr(mod, group_set):
                if element == group:
                    return getattr(d, prm_cost_group_prm_type)[group_set]

    m.group_prm_type = Param(
        m.PRM_COST_GROUPS, within=["energy_only_allowed"],
        initialize=lambda mod, g: group_prm_type_init(mod, g)
    )

    # Import all possible PRM modules
    project_df = pd.read_csv(
        os.path.join(subproblem_stage_directory,
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "prm_type"]
    )
    required_prm_modules = [
        prm_type for prm_type in project_df.prm_type.unique() if
        prm_type != "."
    ]

    imported_prm_modules = load_prm_type_modules(required_prm_modules)

    # For each PRM project type, get the group costs
    def group_cost_rule(mod, group, p):
        prm_type = mod.group_prm_type[group]
        return imported_prm_modules[prm_type]. \
            group_cost_rule(mod, group, p)

    m.PRM_Group_Costs = Expression(
        m.PRM_COST_GROUPS, m.PERIODS,
        rule=group_cost_rule
    )
