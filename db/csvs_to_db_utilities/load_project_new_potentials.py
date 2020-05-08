#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project new cost data
"""

from collections import OrderedDict
from db.utilities import project_new_potentials


# TODO: move to common_functions, also used in load_transmission_new_costs
def recur_dictify(frame):
    """
    Converts DataFrame to nested dictionary using recursion.
    :param frame:
    :return:
    """
    if len(frame.columns) == 1:
        if frame.values.size == 1:
            return frame.values[0][0]
        return frame.values.squeeze()
    grouped = frame.groupby(frame.columns[0])
    d = {k: recur_dictify(g.iloc[:, 1:]) for k, g in grouped}
    return d


def load_project_new_potentials(io, c, subscenario_input, data_input):
    """
    Data output dictionary is {project:{period: (min_cumulative_new_build_mw,
    min_cumulative_new_build_mwh, max_cumulative_new_build_mw, max_cumulative_new_build_mwh)}}
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

        project_new_potential_capacities = OrderedDict()

        for prj in data_input_subscenario['project'].unique():
            project_new_potential_capacities[prj] = OrderedDict()

            for p in data_input_subscenario.loc[data_input_subscenario['project'] == prj]['period'].to_list():
                project_new_potential_capacities[prj][p] = OrderedDict()

                min_cum_new_build_mw = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'min_cumulative_new_build_mw'].iloc[0]
                if min_cum_new_build_mw != None:
                    min_cum_new_build_mw = float(min_cum_new_build_mw)

                max_cum_new_build_mw = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'max_cumulative_new_build_mw'].iloc[0]
                if max_cum_new_build_mw != None:
                    max_cum_new_build_mw = float(max_cum_new_build_mw)

                min_cum_new_build_mwh = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'min_cumulative_new_build_mwh'].iloc[0]
                if min_cum_new_build_mwh != None:
                    min_cum_new_build_mwh = float(min_cum_new_build_mwh)

                max_cum_new_build_mwh = data_input_subscenario.loc[
                                                           (data_input_subscenario['project'] == prj) & (
                                                                   data_input_subscenario[
                                                                       'period'] == p), 'max_cumulative_new_build_mwh'].iloc[0]
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


def load_project_new_binary_build_sizes(io, c, subscenario_input, data_input):
    """
    Data output dictionary is {project: (binary_build_size_mw,
    binary_build_size_mwh)}
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

        key_cols = ["project"]
        value_cols = ["binary_build_size_mw", "binary_build_size_mwh"]

        df = data_input_subscenario.groupby(key_cols)[value_cols].apply(
            lambda x: x.values.tolist()[0]).to_frame().reset_index()
        project_new_binary_build_sizes = recur_dictify(df)

        project_new_potentials.update_project_binary_build_sizes(
            io=io, c=c,
            project_new_binary_build_size_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_new_binary_build_sizes=project_new_binary_build_sizes
        )
