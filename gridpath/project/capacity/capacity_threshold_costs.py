#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Describe costs incurred when total capacity across groups of projects exceeds 
a pre-specified threshold
These currently include transmission/interconnection costs incurred after a 
certain amount of capacity from a group of projects is installed
"""

import csv
import os.path
from pyomo.environ import Set, Param, Var, Constraint, NonNegativeReals, \
    Expression, value


def add_model_components(m, d):
    """
    Sum up all operational costs and add to the objective function.
    :param m:
    :param d:
    :return:
    """

    m.CAPACITY_THRESHOLD_GROUPS = Set()
    m.capacity_threshold_mw = Param(
        m.CAPACITY_THRESHOLD_GROUPS, within=NonNegativeReals
    )
    m.capacity_threshold_cost_per_mw = Param(
        m.CAPACITY_THRESHOLD_GROUPS, within=NonNegativeReals,
        default=0
    )

    m.CAPACITY_THRESHOLD_GROUP_PROJECTS = Set(
        dimen=2, within=m.CAPACITY_THRESHOLD_GROUPS * m.PROJECTS
    )

    m.PROJECTS_BY_CAPACITY_THRESHOLD_GROUP = Set(
        m.CAPACITY_THRESHOLD_GROUPS, within=m.PROJECTS,
        initialize=
        lambda mod, g: [p for (group, p) in
                        mod.CAPACITY_THRESHOLD_GROUP_PROJECTS
                        if group == g]
    )

    def capacity_of_threshold_group_rule(mod, g, p):
        """
        Total capacity of projects in each threshold group
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        return sum(mod.Capacity_MW[prj, p]
                   for prj in mod.PROJECTS_BY_CAPACITY_THRESHOLD_GROUP[g]
                   if (prj, p) in mod.PROJECT_OPERATIONAL_PERIODS
                   )

    m.Threshold_Group_Capacity_MW = Expression(
        m.CAPACITY_THRESHOLD_GROUPS, m.PERIODS,
        rule=capacity_of_threshold_group_rule
    )

    m.Capacity_Threshold_Cost = Var(
        m.CAPACITY_THRESHOLD_GROUPS, m.PERIODS,
        within=NonNegativeReals
    )

    def capacity_threshold_cost_constraint_rule(mod, g, p):
        """
        Costs incurred if total capacity built in threshold group is 
        higher than the threshold; otherwise, the cost can be set to 0 (and 
        in fact has to be set to 0 since Capacity_Threshold_Cost must be 
        non-negative)
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        if mod.capacity_threshold_cost_per_mw[g] == 0:
            return Constraint.Skip
        else:
            return mod.Capacity_Threshold_Cost[g, p] \
                >= \
                (mod.Threshold_Group_Capacity_MW[g, p]
                 - mod.capacity_threshold_mw[g]) \
                * mod.capacity_threshold_cost_per_mw[g]

    m.Capacity_Threshold_Cost_Constraint = Constraint(
        m.CAPACITY_THRESHOLD_GROUPS, m.PERIODS,
        rule=capacity_threshold_cost_constraint_rule
    )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """
    Optionally load data for costs incurred only when a capacity threshold 
    is reached; if file is not found, sets in this modules will be empty and 
    params will have default values of 0
    :param m: 
    :param d: 
    :param data_portal: 
    :param scenario_directory: 
    :param horizon: 
    :param stage: 
    :return: 
    """
    group_projects_file = os.path.join(
        scenario_directory, horizon, stage, "inputs",
        "capacity_threshold_group_projects.tab"
    )

    if os.path.exists(group_projects_file):
        data_portal.load(
            filename=group_projects_file,
            set=m.CAPACITY_THRESHOLD_GROUP_PROJECTS
        )
    else:
        pass

    group_threshold_costs_file = os.path.join(
        scenario_directory, horizon, stage, "inputs",
        "capacity_threshold_group_costs.tab"
    )
    if os.path.exists(group_threshold_costs_file):
        data_portal.load(
            filename=group_threshold_costs_file,
            index=m.CAPACITY_THRESHOLD_GROUPS,
            param=(m.capacity_threshold_mw, m.capacity_threshold_cost_per_mw)
        )
    else:
        pass


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    # Total capacity for all projects
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "costs_capacity_thresholds.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["capacity_threshold_group", "period",
                         "capacity_threshold_mw",
                         "capacity_threshold_cost_per_mw",
                         "total_capacity_built_mw",
                         "capacity_threshold_cost"])
        for g in m.CAPACITY_THRESHOLD_GROUPS:
            for p in m.PERIODS:
                writer.writerow([
                    g,
                    p,
                    m.capacity_threshold_mw[g],
                    m.capacity_threshold_cost_per_mw[g],
                    value(m.Threshold_Group_Capacity_MW[g, p]),
                    value(m.Capacity_Threshold_Cost[g, p])
                ])


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    # Threshold groups with threshold and cost
    group_threshold_costs = c.execute(
        """SELECT capacity_threshold_group, capacity_threshold_mw, 
        capacity_threshold_cost_per_mw
        FROM inputs_project_capacity_threshold_costs
        WHERe capacity_threshold_cost_scenario_id = {}""".format(
            subscenarios.CAPACITY_THRESHOLD_COST_SCENARIO_ID
        )
    ).fetchall()

    with open(os.path.join(inputs_directory,
                           "capacity_threshold_group_costs.tab"), "w") as \
            capacity_threshold_costs_file:
        writer = csv.writer(capacity_threshold_costs_file, delimiter="\t")

        # Write header
        writer.writerow(["capacity_threshold_group",
                         "capacity_threshold_mw",
                         "capacity_threshold_cost_per_mw"])

        # Input data
        for row in group_threshold_costs:
            writer.writerow(row)

    # Projects by group
    project_capacity_threshold_interconnection_cost_groups = c.execute(
        """SELECT interconnection_capacity_threshold_group, project
        FROM inputs_project_portfolios
        LEFT OUTER JOIN inputs_project_load_zones
        USING (project)
        WHERE load_zone_scenario_id = {}
        AND project_load_zone_scenario_id = {}
        AND project_portfolio_scenario_id = {}
        AND interconnection_capacity_threshold_group IS NOT NULL
        ORDER BY interconnection_capacity_threshold_group, project""".format(
            subscenarios.LOAD_SCENARIO_ID,
            subscenarios.PROJECT_LOAD_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    with open(os.path.join(inputs_directory,
                           "capacity_threshold_group_projects.tab"), "w") as \
            group_projects_file:
        writer = csv.writer(group_projects_file, delimiter="\t")

        # Write header
        writer.writerow(["capacity_threshold_group", "project"])

        # Input data
        for row in project_capacity_threshold_interconnection_cost_groups:
            writer.writerow(row)

    # TODO: append to this input file if other types of thresholds are
    # implemented
