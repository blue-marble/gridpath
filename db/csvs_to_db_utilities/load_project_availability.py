#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project availability csv data
"""

import numpy as np
from collections import OrderedDict
from db.utilities import project_availability


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


def load_project_availability_types(io, c, subscenario_input, data_input):
    """
    Project availability types dictionary has project as the key with availability type and the two
    exogenous and endogenous scenario ids as values
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['project_availability_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['project_availability_scenario_id'] == sc_id)]

        print("Loading project availability types")
        project_availability_types = dict()

        for j in data_input_subscenario.index:
            prj = data_input_subscenario['project'][j]
            project_availability_types[prj] = OrderedDict()
            project_availability_types[prj]["type"] = data_input_subscenario['availability_type'][j]
            if np.isnan(data_input_subscenario['exogenous_availability_scenario_id'][j]):
                project_availability_types[prj]["exogenous_availability_id"] = None
            else:
                print("exo not None")
                project_availability_types[prj]["exogenous_availability_id"] = int(data_input_subscenario[
                                                                  'exogenous_availability_scenario_id'][j])

            if np.isnan(data_input_subscenario['endogenous_availability_scenario_id'][j]):
                project_availability_types[prj]["endogenous_availability_id"] = None
            else:
                print("endo not None")
                project_availability_types[prj]["endogenous_availability_id"] = int(data_input_subscenario[
                                                                  'endogenous_availability_scenario_id'][j])


        project_availability.make_scenario_and_insert_types_and_ids(
            io=io, c=c,
            project_availability_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_types_and_char_ids=project_availability_types
        )


def load_project_availability_exogenous(io, c, subscenario_input, data_input):
    """
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    project_availability_exogenous = dict()
    project_availability_exogenous_scenarios = dict()

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['exogenous_availability_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]
        prj = subscenario_input['project'][i]

        project_availability_exogenous_scenarios[prj] = dict()
        project_availability_exogenous_scenarios[prj][sc_id] = (sc_name, sc_description)

        project_availability_exogenous[prj] = OrderedDict()
        project_availability_exogenous[prj][sc_id] = OrderedDict()

        project_availability_by_project = data_input.loc[
                (data_input['exogenous_availability_scenario_id'] == sc_id) & (data_input['project'] == prj)]

        for st_id in project_availability_by_project['stage_id'].unique():
            project_stage_availability_by_project = project_availability_by_project.loc[
                project_availability_by_project['stage_id'] == st_id, ['timepoint', 'availability_derate']]
            project_stage_availability_by_project[['timepoint']] = \
                project_stage_availability_by_project[['timepoint']].astype(int)
            project_availability_exogenous[prj][sc_id][int(st_id)] = \
                project_stage_availability_by_project.set_index('timepoint')[
                'availability_derate'].to_dict()

        project_availability.insert_project_availability_exogenous(
            io=io, c=c,
            project_avail_scenarios=project_availability_exogenous_scenarios,
            project_avail=project_availability_exogenous
        )


def load_project_availability_endogenous(io, c, subscenario_input, data_input):
    """
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    project_availability_endogenous = dict()
    project_availability_endogenous_scenarios = dict()

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['endogenous_availability_scenario_id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]
        prj = subscenario_input['project'][i]

        project_availability_endogenous_scenarios[prj] = dict()
        project_availability_endogenous_scenarios[prj][sc_id] = (sc_name, sc_description)

        data_input_subscenario = data_input.loc[
            (data_input['endogenous_availability_scenario_id'] == sc_id)
            & (data_input['project'] == prj)
        ]

        key_cols = ["project", "endogenous_availability_scenario_id"]
        value_cols = ["unavailable_hours_per_period",
                      "unavailable_hours_per_event_min",
                      "unavailable_hours_per_event_max",
                      "available_hours_between_events_min",
                      "available_hours_between_events_max"]

        df = data_input_subscenario.groupby(key_cols)[value_cols].apply(
            lambda x: x.values.tolist()[0]).to_frame().reset_index()
        project_avail = recur_dictify(df)

        # project_availability_endogenous[sc_id] = OrderedDict()
        # project_availability_endogenous[sc_id][prj] = OrderedDict()
        #
        # project_availability_by_project =
        #
        # project_availability_endogenous[sc_id][prj]
        #
        #     project_stage_availability_by_project = project_availability_by_project.loc[
        #         project_availability_by_project['stage_id'] == st_id, ['timepoint', 'availability_derate']]
        #     project_stage_availability_by_project[['timepoint']] = \
        #         project_stage_availability_by_project[['timepoint']].astype(int)
        #     project_availability_endogenous[prj][sc_id][int(st_id)] = \
        #         project_stage_availability_by_project.set_index('timepoint')[
        #         'availability_derate'].to_dict()

        project_availability.insert_project_availability_endogenous(
            io=io, c=c,
            project_avail_scenarios=project_availability_endogenous_scenarios,
            project_avail=project_avail
        )
