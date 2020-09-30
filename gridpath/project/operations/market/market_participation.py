#!/usr/bin/env python
# Copyright 2020 Blue Marble Analytics LLC. All rights reserved.

"""
Define the market participation components for projects.
"""

import csv
import os.path
from pyomo.environ import Set, Param, Var, NonNegativeReals, Constraint


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    """
    m.MARKET_HUB_PRJS = Set(within=m.PROJECTS)

    m.market_hub = Param(m.MARKET_HUB_PRJS, within=m.MARKET_HUBS)

    m.MARKET_HUB_PRJ_OPR_TMPS = Set(
        dimen=2,
        initialize=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS
            if g in mod.MARKET_HUB_PRJS)
    )

    m.Sell_Power = Var(
        m.MARKET_HUB_PRJ_OPR_TMPS,
        within=NonNegativeReals
    )

    # TODO: should the buy variable be project or perhaps by load zone?
    m.Buy_Power = Var(
        m.MARKET_HUB_PRJ_OPR_TMPS,
        within=NonNegativeReals
    )

    def max_sales_by_project(mod, prj, tmp):
        """
        A project can't sell more power than produced at the project.
        """
        return mod.Sell_Power[prj, tmp] <= mod.Produce_Power_MW[prj, tmp]

    m.Max_Sales_By_Project_Constraint = Constraint(
        m.MARKET_HUB_PRJ_OPR_TMPS, rule=max_sales_by_project
    )


def load_model_data(
    m, d, data_portal, scenario_directory, subproblem, stage
):
    data_portal.load(
        filename=os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs",
            "projects.tab"
        ),
        select=("project", "market_hub",),
        param=(m.market_hub,)
    )

    data_portal.data()[m.MARKET_HUB_PRJS] = {
        None: list(data_portal.data()[m.market_hub].keys())
    }


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()

    project_market_hubs = c.execute(
        """
        SELECT project, market_hub
        FROM
        -- Get projects from portfolio only
        (SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = ?
        ) as prj_tbl
        LEFT OUTER JOIN 
        -- Get BAs for those projects
        (SELECT project, market_hub
            FROM inputs_project_market_hubs
            WHERE project_market_hub_scenario_id = ?
        ) as prj_ba_tbl
        USING (project)
        -- Filter out projects whose market hub is not one included in our 
        -- market_hub_scenario_id
        WHERE market_hub in (
            SELECT market_hub
                FROM inputs_geography_market_hubs
                WHERE market_hub_scenario_id = ?
        );
        """,
        (subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
         subscenarios.LOAD_ZONE_MARKET_HUB_SCENARIO_ID,
         subscenarios.MARKET_HUB_SCENARIO_ID)
    )

    return project_market_hubs


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection

    Get inputs from database and write out the model input
    projects.tab file (to be precise, amend it).
    """
    # TODO: the appending to the projects.tab file should be factored out as
    #  it is used by a number of modules
    project_market_hubs = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Make a dict for easy access
    prj_mh_dict = dict()
    for (prj, mh) in project_market_hubs:
        prj_mh_dict[str(prj)] = "." if mh is None else (str(mh))

    # Add params to projects file
    with open(
            os.path.join(
                scenario_directory, str(subproblem), str(stage), "inputs",
                "projects.tab"
            ), "r"
    ) as f_in:
        reader = csv.reader(f_in, delimiter="\t", lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("market_hub")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_mh_dict.keys()):
                row.append(prj_mh_dict[row[0]])
            # If project not specified, specify no BA
            else:
                row.append(".")

            # Add resulting row to new_rows list
            new_rows.append(row)

    with open(
            os.path.join(
                scenario_directory, str(subproblem), str(stage), "inputs",
                "projects.tab"
            ), "w", newline=""
    ) as f_out:
        writer = csv.writer(f_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)
