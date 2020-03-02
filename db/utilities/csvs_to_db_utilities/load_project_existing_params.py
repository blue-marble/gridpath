#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project existing capacities and cost data
"""

from collections import OrderedDict
from db.utilities import project_existing_params

def load_project_existing_capacities(io, c, subscenario_input, data_input):
    """
    Data output dictionary is {project:{period: (existing_capacity_mw, existing_capacity_mwh)}}
    Convert values to floats else they show up as blobs in sql db
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['project_existing_capacity_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['project_existing_capacity_scenario_id'] == sc_id)]

        project_existing_capacities = OrderedDict()

        for prj in data_input_subscenario['project'].unique():
            project_existing_capacities[prj] = OrderedDict()

            for p in data_input_subscenario.loc[data_input_subscenario['project'] == prj]['period'].to_list():
                project_existing_capacities[prj][p] = OrderedDict()

                project_existing_capacity_mw = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'existing_capacity_mw'].iloc[0]
                if project_existing_capacity_mw != None:
                    project_existing_capacity_mw = float(project_existing_capacity_mw)

                project_existing_capacity_mwh = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'existing_capacity_mwh'].iloc[0]
                if project_existing_capacity_mwh != None:
                    project_existing_capacity_mwh = float(project_existing_capacity_mwh)

                project_existing_capacities[prj][p] = (project_existing_capacity_mw, project_existing_capacity_mwh)

        project_existing_params.update_project_capacities(
            io=io, c=c,
            project_existing_capacity_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_capacities=project_existing_capacities
        )


def load_project_existing_fixed_costs(io, c, subscenario_input, data_input):
    """
    Data output dictionary is {project:{period: (annual_fixed_cost_per_kw_year, annual_fixed_cost_per_kwh_year)}}
    Convert values to floats else they show up as blobs in sql db
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['project_existing_fixed_cost_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['project_existing_fixed_cost_scenario_id'] == sc_id)]

        project_existing_fixed_costs = OrderedDict()

        for prj in data_input_subscenario['project'].unique():
            project_existing_fixed_costs[prj] = OrderedDict()

            for p in data_input_subscenario.loc[data_input_subscenario['project'] == prj]['period'].to_list():
                project_existing_fixed_costs[prj][p] = OrderedDict()

                annual_fixed_cost_kw = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'annual_fixed_cost_per_kw_year'].iloc[0]
                if annual_fixed_cost_kw != None:
                    annual_fixed_cost_kw = float(annual_fixed_cost_kw)

                annual_fixed_cost_kwh = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'annual_fixed_cost_per_kwh_year'].iloc[0]
                if annual_fixed_cost_kw != None:
                    annual_fixed_cost_kwh = float(annual_fixed_cost_kwh)

                project_existing_fixed_costs[prj][p] = (annual_fixed_cost_kw, annual_fixed_cost_kwh)

        project_existing_params.update_project_fixed_costs(
            io=io, c=c,
            project_existing_fixed_cost_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_fixed_costs=project_existing_fixed_costs
        )