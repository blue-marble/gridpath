#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Existing/planned project capacities
"""

from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


def update_project_new_costs(
        io, c,
        project_new_cost_scenario_id,
        scenario_name,
        scenario_description,
        project_period_lifetimes_costs
):
    # Subscenarios
    subs_data = [(project_new_cost_scenario_id, scenario_name, scenario_description)]
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_new_cost
         (project_new_cost_scenario_id, name, description)
         VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert inputs
    inputs_data = []
    for project in list(project_period_lifetimes_costs.keys()):
        for period in list(project_period_lifetimes_costs[project].keys()):
            inputs_data.append(
                (project_new_cost_scenario_id,
                 project,
                 period,
                 project_period_lifetimes_costs[project][period][0],
                 project_period_lifetimes_costs[project][period][1],
                 'NULL'
                 if project_period_lifetimes_costs[project][period][2] is None
                 else project_period_lifetimes_costs[project][period][2])
            )
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_new_cost
        (project_new_cost_scenario_id, project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr,
        annualized_real_cost_per_kwh_yr)
        VALUES (?, ?, ?, ?, ?, ?);
        """

    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)
