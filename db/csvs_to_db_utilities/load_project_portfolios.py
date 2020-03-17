#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project portfolios data
"""

from db.utilities import project_portfolios

def load_project_portfolios(io, c, subscenario_input, data_input):
    """
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['id'] == sc_id)]

        project_capacity_types = dict()
        project_capacity_types = data_input_subscenario[['project', 'capacity_type']].dropna().set_index(
            'project')['capacity_type'].to_dict()

        project_portfolios.update_project_portfolios(
            io=io, c=c,
            project_portfolio_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_cap_types=project_capacity_types
        )
