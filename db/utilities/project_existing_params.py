#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Existing/planned project capacities
"""
from __future__ import print_function

from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


def update_project_capacities(
        io, c,
        project_existing_capacity_scenario_id,
        scenario_name,
        scenario_description,
        project_capacities
):
    """
    
    :param io: 
    :param c: 
    :param project_existing_capacity_scenario_id: 
    :param scenario_name: 
    :param scenario_description: 
    :param project_capacities: 
    :return: 
    """
    print("project existing capacities")

    # Subscenario
    subs_data = [(project_existing_capacity_scenario_id, scenario_name,
            scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_project_existing_capacity
         (project_existing_capacity_scenario_id, name, description)
         VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for project in list(project_capacities.keys()):
        for period in list(project_capacities[project].keys()):
            inputs_data.append(
                (project_existing_capacity_scenario_id, project, period,
                 project_capacities[project][period][0],
                 'NULL' if project_capacities[project][period][1] is None
                 else project_capacities[project][period][1])
            )
    inputs_sql = """
        INSERT INTO inputs_project_existing_capacity
        (project_existing_capacity_scenario_id, project, period,
        existing_capacity_mw, existing_capacity_mwh)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


def update_project_fixed_costs(
        io, c,
        project_existing_fixed_cost_scenario_id,
        scenario_name,
        scenario_description,
        project_fixed_costs
):
    """

    :param io:
    :param c:
    :param project_existing_fixed_cost_scenario_id:
    :param scenario_name:
    :param scenario_description:
    :param project_fixed_costs:
    :return:
    """
    print("project existing fixed costs")

    # Subscenario
    subs_data = [(project_existing_fixed_cost_scenario_id, scenario_name,
                  scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_project_existing_fixed_cost
         (project_existing_fixed_cost_scenario_id, name, description)
         VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for project in list(project_fixed_costs.keys()):
        for period in list(project_fixed_costs[project].keys()):
            inputs_data.append(
                (project_existing_fixed_cost_scenario_id, project, period,
                 project_fixed_costs[project][period][0],
                 'NULL' if project_fixed_costs[project][period][1] is None
                 else project_fixed_costs[project][period][1])
            )
    inputs_sql = """
        INSERT INTO inputs_project_existing_fixed_cost
        (project_existing_fixed_cost_scenario_id, project, period,
        annual_fixed_cost_per_kw_year, annual_fixed_cost_per_kwh_year)
        VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


if __name__ == '__main__':
    pass
