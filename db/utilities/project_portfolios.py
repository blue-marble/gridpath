#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Project portfolios
"""


def update_project_portfolios(
        io, c,
        project_portfolio_scenario_id,
        scenario_name,
        scenario_description,
        project_cap_types
):
    print("project portfolios")

    # Subscenario
    c.execute(
        """INSERT INTO subscenarios_project_portfolios
        (project_portfolio_scenario_id, name, description)
        VALUES ({}, '{}', '{}');""".format(
            project_portfolio_scenario_id, scenario_name, scenario_description
        )
    )
    io.commit()

    for project in project_cap_types.keys():
        c.execute(
            """INSERT INTO inputs_project_portfolios
             (project_portfolio_scenario_id, project, capacity_type)
             VALUES ({}, '{}', '{}');""".format(
                project_portfolio_scenario_id, project,
                project_cap_types[project]
            )
        )
    io.commit()


if __name__ == "__main__":
    pass
