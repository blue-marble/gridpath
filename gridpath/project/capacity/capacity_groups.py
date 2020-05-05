#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
Minimum and maximum capacity by period and project group.
"""

import os.path
import pandas as pd
from pyomo.environ import Set, Param, Constraint, NonNegativeReals

from gridpath.auxiliary.auxiliary import \
    load_gen_storage_capacity_type_modules
from gridpath.auxiliary.dynamic_components import required_capacity_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Sets
    m.CAPACITY_GROUP_PERIODS = Set(dimen=2)

    m.CAPACITY_GROUPS = Set(
        rule=lambda mod: set([g for (g, p) in mod.CAPACITY_GROUP_PERIODS])
    )

    m.PROJECTS_IN_CAPACITY_GROUP = Set(
        m.CAPACITY_GROUPS, within=m.PROJECTS
    )

    # Params
    m.capacity_group_new_capacity_min = Param(
        m.CAPACITY_GROUP_PERIODS, within=NonNegativeReals
    )
    m.capacity_group_new_capacity_max = Param(
        m.CAPACITY_GROUP_PERIODS, within=NonNegativeReals
    )
    m.capacity_group_total_capacity_min = Param(
        m.CAPACITY_GROUP_PERIODS, within=NonNegativeReals
    )
    m.capacity_group_total_capacity_max = Param(
        m.CAPACITY_GROUP_PERIODS, within=NonNegativeReals
    )

    # Import needed capacity type modules
    imported_capacity_modules = load_gen_storage_capacity_type_modules(
        getattr(d, required_capacity_modules)
    )

    def new_capacity_rule(mod, prj, prd):
        gen_cap_type = mod.capacity_type[prj]
        return imported_capacity_modules[gen_cap_type].new_capacity_rule(
            mod, prj, prd)

    # Constraints

    # Limit the amount of new build in a period
    def new_capacity_limits_rule(mod, grp, prd):
        return sum(
            new_capacity_rule(mod, prj, prd)
            for prj in mod.PROJECTS_IN_CAPACITY_GROUP[grp]
        ) <= mod.capacity_group_new_capacity_max[grp, prd]

    m.Max_Group_Build_in_Period_Constraint = Constraint(
        m.CAPACITY_GROUP_PERIODS,
        rule=new_capacity_limits_rule
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    data_portal.load(filename=os.path.join(
        scenario_directory, subproblem, stage, "inputs",
        "capacity_group_requirements.tab"
    ),
        index=m.CAPACITY_GROUP_PERIODS,
        param=(m.capacity_group_new_capacity_min,
               m.capacity_group_new_capacity_max,
               m.capacity_group_total_capacity_min,
               m.capacity_group_total_capacity_max)
    )

    proj_groups_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "inputs",
                     "capacity_group_projects.tab"),
        delimiter="\t"
    )
    proj_groups_dict = {
        g: v["project"].tolist()
        for g, v in proj_groups_df.groupby("capacity_group")
    }
    data_portal.data()["PROJECTS_IN_CAPACITY_GROUP"] = proj_groups_dict
