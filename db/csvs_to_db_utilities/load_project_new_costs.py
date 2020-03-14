#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project new cost data
"""

from collections import OrderedDict
from db.utilities import project_new_costs

def load_project_new_costs(io, c, subscenario_input, data_input):
    """
    Data output dictionary is {project:{period: (lifetime_yrs, annualized_real_cost_per_kw_year, annualized_real_cost_per_kwh_year)}}
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

        project_new_lifetime_costs = OrderedDict()

        for prj in data_input_subscenario['project'].unique():
            project_new_lifetime_costs[prj] = OrderedDict()

            for p in data_input_subscenario.loc[data_input_subscenario['project'] == prj]['period'].to_list():
                project_new_lifetime_costs[prj][p] = OrderedDict()

                project_lifetime_yrs = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'lifetime_yrs'].iloc[0]
                if project_lifetime_yrs != None:
                    project_lifetime_yrs = int(project_lifetime_yrs)

                annual_real_cost_kw = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'annualized_real_cost_per_kw_yr'].iloc[0]
                if annual_real_cost_kw != None:
                    annual_real_cost_kw = float(annual_real_cost_kw)

                annual_real_cost_kwh = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'annualized_real_cost_per_kwh_yr'].iloc[0]
                if annual_real_cost_kwh != None:
                    annual_real_cost_kwh = float(annual_real_cost_kwh)

                # TODO: Add the levelized_cost_per_mwh and supply_curve_scenario_id fields
                project_new_lifetime_costs[prj][p] = (project_lifetime_yrs, annual_real_cost_kw, annual_real_cost_kwh)


        project_new_costs.update_project_new_costs(
            io=io, c=c,
            project_new_cost_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_period_lifetimes_costs=project_new_lifetime_costs
        )

