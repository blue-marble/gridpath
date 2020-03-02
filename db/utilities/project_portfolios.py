#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Project portfolios
"""
from db.common_functions import spin_on_database_lock


def update_project_portfolios(
        io, c,
        project_portfolio_scenario_id,
        scenario_name,
        scenario_description,
        project_cap_types
):

    # Subscenario
    subs_data = [(project_portfolio_scenario_id, scenario_name,
                  scenario_description)]
    subs_sql = """
        INSERT INTO subscenarios_project_portfolios
        (project_portfolio_scenario_id, name, description)
        VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=subs_sql, data=subs_data)

    # Insert data
    inputs_data = []
    for project in list(project_cap_types.keys()):
        inputs_data.append(
            (project_portfolio_scenario_id, project,
             project_cap_types[project])
        )
    inputs_sql = """
        INSERT INTO inputs_project_portfolios
         (project_portfolio_scenario_id, project, capacity_type)
         VALUES (?, ?, ?);
        """
    spin_on_database_lock(conn=io, cursor=c, sql=inputs_sql, data=inputs_data)


if __name__ == "__main__":
    pass
