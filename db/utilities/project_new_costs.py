#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Existing/planned project capacities
"""

from db.common_functions import spin_on_database_lock

from db.common_functions import spin_on_database_lock


def update_project_new_costs(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:

    """
    c = conn.cursor()

    # Subscenarios
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_new_cost
         (project_new_cost_scenario_id, name, description)
         VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert inputs
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_new_cost
        (project_new_cost_scenario_id, project, vintage, lifetime_yrs,
        annualized_real_cost_per_mw_yr,
        annualized_real_cost_per_mwh_yr)
        VALUES (?, ?, ?, ?, ?, ?);
        """

    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()
