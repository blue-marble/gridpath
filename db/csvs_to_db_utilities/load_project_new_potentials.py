#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project new cost data
"""

from collections import OrderedDict
from db.utilities import project_new_potentials

def load_project_new_potentials(io, c, subscenario_input, data_input):
    """
    Data output dictionary is {project:{period: (minimum_cumulative_new_build_mw,
    minimum_cumulative_new_build_mwh, maximum_cumulative_new_build_mw, maximum_cumulative_new_build_mwh)}}
    Convert values to floats else they show up as blobs in sql db
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['project_new_potential_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['project_new_potential_scenario_id'] == sc_id)]

        project_new_potential_capacities = OrderedDict()

        for prj in data_input_subscenario['project'].unique():
            project_new_potential_capacities[prj] = OrderedDict()

            for p in data_input_subscenario.loc[data_input_subscenario['project'] == prj]['period'].to_list():
                project_new_potential_capacities[prj][p] = OrderedDict()

                min_cum_new_build_mw = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'minimum_cumulative_new_build_mw'].iloc[0]
                if min_cum_new_build_mw != None:
                    min_cum_new_build_mw = float(min_cum_new_build_mw)

                max_cum_new_build_mw = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'maximum_cumulative_new_build_mw'].iloc[0]
                if max_cum_new_build_mw != None:
                    max_cum_new_build_mw = float(max_cum_new_build_mw)

                min_cum_new_build_mwh = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'minimum_cumulative_new_build_mwh'].iloc[0]
                if min_cum_new_build_mwh != None:
                    min_cum_new_build_mwh = float(min_cum_new_build_mwh)

                max_cum_new_build_mwh = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'maximum_cumulative_new_build_mwh'].iloc[0]
                if max_cum_new_build_mwh != None:
                    max_cum_new_build_mwh = float(max_cum_new_build_mwh)

                project_new_potential_capacities[prj][p] = (min_cum_new_build_mw, min_cum_new_build_mwh,
                                                             max_cum_new_build_mw, max_cum_new_build_mwh)


        project_new_potentials.update_project_potentials(
            io=io, c=c,
            project_new_potential_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_period_potentials=project_new_potential_capacities
        )
