#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project prm data
"""

from db.utilities import project_prm


def load_project_prm(io, c, subscenario_input, data_input):
    """
    Input subscenario dictionary and data in pandas dataframe
    Load data in sql database for all subscenarios
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    for i in subscenario_input.index:
        prj_sc_id = int(subscenario_input['id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        df = data_input.loc[(data_input['id'] ==
                            prj_sc_id)]

        proj_prm_type = dict(zip(df["project"], df["prm_type"]))
        proj_elcc_simple_fraction = dict(
            zip(df["project"], df["elcc_simple_fraction"])
        )
        proj_elcc_surface = dict(
            zip(df["project"], df["contributes_to_elcc_surface"])
        )
        proj_min_duration_for_full = dict(
            zip(df["project"],
                df["min_duration_for_full_capacity_credit_hours"])
        )
        proj_deliv_group = dict(
            zip(df["project"], df["deliverability_group"])
        )

        project_prm.project_elcc_chars(
            io=io, c=c,
            project_elcc_chars_scenario_id=prj_sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description,
            proj_prm_type=proj_prm_type,
            proj_elcc_simple_fraction=proj_elcc_simple_fraction,
            proj_elcc_surface=proj_elcc_surface,
            proj_min_duration_for_full=proj_min_duration_for_full,
            proj_deliv_group=proj_deliv_group
        )
