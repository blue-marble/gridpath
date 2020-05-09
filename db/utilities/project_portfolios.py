#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Project portfolios
"""
from db.common_functions import spin_on_database_lock


def update_project_portfolios(
    conn, subscenario_data, inputs_data
):
    """
    :param conn:
    :param subscenario_data:
    :param inputs_data:
    """
    c = conn.cursor()
    # Subscenario
    subs_sql = """
        INSERT OR IGNORE INTO subscenarios_project_portfolios
        (project_portfolio_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=subs_sql,
                          data=subscenario_data)

    # Insert data
    inputs_sql = """
        INSERT OR IGNORE INTO inputs_project_portfolios
         (project_portfolio_scenario_id, project, specified, new_build, 
         capacity_type)
         VALUES (?, ?, ?, ?, ?);
        """
    spin_on_database_lock(conn=conn, cursor=c, sql=inputs_sql,
                          data=inputs_data)

    c.close()


if __name__ == "__main__":
    pass
