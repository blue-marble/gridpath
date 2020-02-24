#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project availability csv data
"""

import numpy as np
from collections import OrderedDict
from db.utilities import project_availability

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

