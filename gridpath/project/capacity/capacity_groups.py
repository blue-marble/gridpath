#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
Minimum and maximum new and total capacity by period and project group.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Constraint, NonNegativeReals

from gridpath.auxiliary.auxiliary import \
    load_gen_storage_capacity_type_modules
from gridpath.auxiliary.dynamic_components import required_capacity_modules


def add_model_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`CAPACITY_GROUP_PERIODS`                                        |
    |                                                                         |
    | A two-dimensional set of group-period combinations for which there may  |
    | be group capacity requirements.                                         |
    +-------------------------------------------------------------------------+
    | | :code:`CAPACITY_GROUPS`                                               |
    |                                                                         |
    | The groups of projects for which there may be group capacity            |
    | requirements.                                                           |
    +-------------------------------------------------------------------------+
    | | :code:`PROJECTS_IN_CAPACITY_GROUP`                                    |
    |                                                                         |
    | The list of projects by capacity group.                                 |
    +-------------------------------------------------------------------------+

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`capacity_group_new_capacity_min`                               |
    | | *Defined over*: :code:`CAPACITY_GROUP_PERIODS`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The minimum amount of capacity (in MW) that must be built at projects   |
    | in this group in a given period.                                        |
    +-------------------------------------------------------------------------+
    | | :code:`capacity_group_new_capacity_max`                               |
    | | *Defined over*: :code:`CAPACITY_GROUP_PERIODS`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`inf`                                                |
    |                                                                         |
    | The maximum amount of capacity (in MW) that may be built at projects    |
    | in this group in a given period.                                        |
    +-------------------------------------------------------------------------+
    | | :code:`capacity_group_total_capacity_min`                             |
    | | *Defined over*: :code:`CAPACITY_GROUP_PERIODS`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The minimum amount of capacity (in MW) that must exist at projects      |
    | in this group in a given period.                                        |
    +-------------------------------------------------------------------------+
    | | :code:`capacity_group_total_capacity_max`                             |
    | | *Defined over*: :code:`CAPACITY_GROUP_PERIODS`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`inf`                                                |
    |                                                                         |
    | The maximum amount of capacity (in MW) that may exist at projects       |
    | in this group in a given period.                                        |
    +-------------------------------------------------------------------------+

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
        m.CAPACITY_GROUP_PERIODS, within=NonNegativeReals,
        default=0
    )
    m.capacity_group_new_capacity_max = Param(
        m.CAPACITY_GROUP_PERIODS, within=NonNegativeReals,
        default=float('inf')
    )
    m.capacity_group_total_capacity_min = Param(
        m.CAPACITY_GROUP_PERIODS, within=NonNegativeReals,
        default=0
    )
    m.capacity_group_total_capacity_max = Param(
        m.CAPACITY_GROUP_PERIODS, within=NonNegativeReals,
        default=float('inf')
    )

    # Import needed capacity type modules
    imported_capacity_modules = load_gen_storage_capacity_type_modules(
        getattr(d, required_capacity_modules)
    )

    def new_capacity_rule(mod, prj, prd):
        gen_cap_type = mod.capacity_type[prj]
        # The capacity type modules check if this period is a "vintage" for
        # this project and return 0 if not
        return imported_capacity_modules[gen_cap_type].new_capacity_rule(
            mod, prj, prd)

    def total_capacity_rule(mod, prj, prd):
        gen_cap_type = mod.capacity_type[prj]
        # Return the capacity type's capacity rule if the project is
        # operational in this timepoint; otherwise, return 0
        return imported_capacity_modules[gen_cap_type].capacity_rule(
            mod, prj, prd) \
            if prd in mod.OPR_PRDS_BY_PRJ[prj] \
            else 0

    # Constraints

    # Limit the min and max amount of new build in a group-period
    def new_capacity_max_rule(mod, grp, prd):
        return sum(
            new_capacity_rule(mod, prj, prd)
            for prj in mod.PROJECTS_IN_CAPACITY_GROUP[grp]
        ) <= mod.capacity_group_new_capacity_max[grp, prd]

    m.Max_Group_Build_in_Period_Constraint = Constraint(
        m.CAPACITY_GROUP_PERIODS,
        rule=new_capacity_max_rule
    )

    def new_capacity_min_rule(mod, grp, prd):
        return sum(
            new_capacity_rule(mod, prj, prd)
            for prj in mod.PROJECTS_IN_CAPACITY_GROUP[grp]
        ) >= mod.capacity_group_new_capacity_min[grp, prd]

    m.Min_Group_Build_in_Period_Constraint = Constraint(
        m.CAPACITY_GROUP_PERIODS,
        rule=new_capacity_min_rule
    )

    # Limit the min and max amount of total capacity in a group-period
    def total_capacity_max_rule(mod, grp, prd):
        return sum(
            total_capacity_rule(mod, prj, prd)
            for prj in mod.PROJECTS_IN_CAPACITY_GROUP[grp]
        ) <= mod.capacity_group_total_capacity_max[grp, prd]

    m.Max_Group_Total_Cap_in_Period_Constraint = Constraint(
        m.CAPACITY_GROUP_PERIODS,
        rule=total_capacity_max_rule
    )

    def total_capacity_min_rule(mod, grp, prd):
        return sum(
            total_capacity_rule(mod, prj, prd)
            for prj in mod.PROJECTS_IN_CAPACITY_GROUP[grp]
        ) >= mod.capacity_group_total_capacity_min[grp, prd]

    m.Min_Group_Total_Cap_in_Period_Constraint = Constraint(
        m.CAPACITY_GROUP_PERIODS,
        rule=total_capacity_min_rule
    )


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    # Only load data if the input files were written; otehrwise, we won't
    # initialize the components in this module

    req_file = os.path.join(
        scenario_directory, subproblem, stage, "inputs",
        "capacity_group_requirements.tab"
    )
    if os.path.exists(req_file):
        data_portal.load(
            filename=req_file,
            index=m.CAPACITY_GROUP_PERIODS,
            param=(m.capacity_group_new_capacity_min,
                   m.capacity_group_new_capacity_max,
                   m.capacity_group_total_capacity_min,
                   m.capacity_group_total_capacity_max)
        )
    else:
        pass

    prj_file = os.path.join(
        scenario_directory, subproblem, stage, "inputs",
        "capacity_group_projects.tab"
    )
    if os.path.exists(prj_file):
        proj_groups_df = pd.read_csv(prj_file, delimiter="\t")
        proj_groups_dict = {
            g: v["project"].tolist()
            for g, v in proj_groups_df.groupby("capacity_group")
        }
        data_portal.data()["PROJECTS_IN_CAPACITY_GROUP"] = proj_groups_dict
    else:
        pass


# Database
###############################################################################

def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """


    c1 = conn.cursor()
    cap_grp_reqs = c1.execute(
        """
        SELECT capacity_group, period,
        capacity_group_new_capacity_min, capacity_group_new_capacity_max,
        capacity_group_total_capacity_min, capacity_group_total_capacity_max
        FROM inputs_project_capacity_group_requirements
        WHERE project_capacity_group_requirement_scenario_id = {}
        """.format(subscenarios.PROJECT_CAPACITY_GROUP_REQUIREMENT_SCENARIO_ID)
    )

    c2 = conn.cursor()
    cap_grp_prj = c2.execute(
        """
        SELECT capacity_group, project
        FROM inputs_project_capacity_groups
        WHERE project_capacity_group_scenario_id = {}
        """.format(subscenarios.PROJECT_CAPACITY_GROUP_SCENARIO_ID)
    )

    return cap_grp_reqs, cap_grp_prj


def write_model_inputs(
        scenario_directory, subscenarios, subproblem, stage, conn
):
    """
    """
    cap_grp_reqs, cap_grp_prj = get_inputs_from_database(
        subscenarios, subproblem, stage, conn
    )

    # Write the input files only if a subscenario is specified
    if subscenarios.PROJECT_CAPACITY_GROUP_REQUIREMENT_SCENARIO_ID != "NULL":
        with open(os.path.join(
                scenario_directory, str(subproblem), str(stage), "inputs",
                "capacity_group_requirements.tab"
        ), "w", newline="") as req_file:
            writer = csv.writer(req_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                ["capacity_group", "period",
                 "capacity_group_new_capacity_min",
                 "capacity_group_new_capacity_max",
                 "capacity_group_total_capacity_min",
                 "capacity_group_total_capacity_max"]
            )

            for row in cap_grp_reqs:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)


    if subscenarios.PROJECT_CAPACITY_GROUP_SCENARIO_ID != "NULL":
        with open(os.path.join(
                scenario_directory, str(subproblem), str(stage), "inputs",
                "capacity_group_projects.tab"
        ), "w", newline="") as prj_file:
            writer = csv.writer(prj_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                ["capacity_group", "project"]
            )

            for row in cap_grp_prj:
                writer.writerow(row)
