#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project local capacity chars
"""

from collections import OrderedDict
from db.utilities import project_local_capacity_chars


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


def load_project_local_capacity_chars(io, c, subscenario_input, data_input):
    """
    Data output dictionary is {project: (local_capacity_fraction,
    min_duration_for_full_capacity_credit_hours)}
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
        value_cols = ["local_capacity_fraction",
                      "min_duration_for_full_capacity_credit_hours"]

        df = data_input_subscenario.groupby(key_cols)[value_cols].apply(
            lambda x: x.values.tolist()[0]).to_frame().reset_index()
        prj_local_capacity_chars = recur_dictify(df)

        project_local_capacity_chars.insert_project_local_capacity_chars(
            io=io, c=c,
            project_local_capacity_chars_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            project_local_capacity_chars=prj_local_capacity_chars
        )
