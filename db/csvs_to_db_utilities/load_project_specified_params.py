#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project existing capacities and cost data
"""

from collections import OrderedDict
from db.utilities import project_specified_params

def load_project_specified_capacities(io, c, subscenario_input, data_input):
    """
    Data output dictionary is {project:{period: (specified_capacity_mw, specified_capacity_mwh)}}
    Convert values to floats else they show up as blobs in sql db
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

        project_specified_capacities = OrderedDict()

        for prj in data_input_subscenario['project'].unique():
            project_specified_capacities[prj] = OrderedDict()

            for p in data_input_subscenario.loc[data_input_subscenario['project'] == prj]['period'].to_list():
                project_specified_capacities[prj][p] = OrderedDict()

                project_specified_capacity_mw = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'specified_capacity_mw'].iloc[0]
                if project_specified_capacity_mw != None:
                    project_specified_capacity_mw = float(project_specified_capacity_mw)

                project_specified_capacity_mwh = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'specified_capacity_mwh'].iloc[0]
                if project_specified_capacity_mwh != None:
                    project_specified_capacity_mwh = float(project_specified_capacity_mwh)

                project_specified_capacities[prj][p] = (project_specified_capacity_mw, project_specified_capacity_mwh)

        project_specified_params.update_project_capacities(
            io=io, c=c,
            project_specified_capacity_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_capacities=project_specified_capacities
        )


def load_project_specified_fixed_costs(io, c, subscenario_input, data_input):
    """
    Data output dictionary is {project:{period: (annual_fixed_cost_per_mw_year, annual_fixed_cost_per_mwh_year)}}
    Convert values to floats else they show up as blobs in sql db
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

        project_specified_fixed_costs = OrderedDict()

        for prj in data_input_subscenario['project'].unique():
            project_specified_fixed_costs[prj] = OrderedDict()

            for p in data_input_subscenario.loc[data_input_subscenario['project'] == prj]['period'].to_list():
                project_specified_fixed_costs[prj][p] = OrderedDict()

                annual_fixed_cost_mw = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'annual_fixed_cost_per_mw_year'].iloc[0]
                if annual_fixed_cost_mw != None:
                    annual_fixed_cost_mw = float(annual_fixed_cost_mw)

                annual_fixed_cost_mwh = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'annual_fixed_cost_per_mwh_year'].iloc[0]
                if annual_fixed_cost_mw != None:
                    annual_fixed_cost_mwh = float(annual_fixed_cost_mwh)

                project_specified_fixed_costs[prj][p] = (annual_fixed_cost_mw, annual_fixed_cost_mwh)

        project_specified_params.update_project_fixed_costs(
            io=io, c=c,
            project_specified_fixed_cost_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_fixed_costs=project_specified_fixed_costs
        )
