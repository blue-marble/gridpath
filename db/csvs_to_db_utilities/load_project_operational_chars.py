#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

"""
Load project operational chars data
"""

from collections import OrderedDict
from db.utilities import project_operational_chars

def load_project_operational_chars(io, c, subscenario_input, data_input):
    """
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    operational_chars_integers = ['heat_rate_curves_scenario_id',
                                  'variable_om_curves_scenario_id',
                                  'startup_chars_scenario_id',
                                  'min_up_time_hours', 'min_down_time_hours',
                                  'variable_generator_profile_scenario_id',
                                  'hydro_operational_chars_scenario_id']
    operational_chars_non_integers = data_input.columns.difference(
        operational_chars_integers + ['id', 'project']).tolist()

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]

        data_input_subscenario = data_input.loc[(data_input['id'] == sc_id)]
        # Make subscenario and insert all projects into operational
        # characteristics table; we'll then update that table with the
        # operational characteristics each project needs
        project_operational_chars.make_scenario_and_insert_all_projects(
            io=io, c=c,
            project_operational_chars_scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_description=sc_description
        )

        # ### Operational chars integers ### #
        for op_chars in operational_chars_integers:
            if data_input_subscenario[op_chars].notnull().sum() != 0:
                operational_chars_dict = dict()
                operational_chars_df = data_input_subscenario.loc[:, ['project', op_chars]].dropna()
                operational_chars_df[[op_chars]] = operational_chars_df[
                    [op_chars]].astype(int)  # Otherwise they could be floats or numpy ints
                operational_chars_dict = operational_chars_df.set_index(
                    'project')[op_chars].to_dict()

                project_operational_chars.update_project_opchar_column(
                    io=io, c=c,
                    project_operational_chars_scenario_id=sc_id,
                    column=op_chars,
                    project_char=operational_chars_dict
                )

        # ### Operational chars non-integers (strings and floats) ### #
        for op_chars in operational_chars_non_integers:
            if data_input_subscenario[op_chars].notnull().sum() != 0:
                operational_chars_dict = dict()
                operational_chars_dict = data_input_subscenario.loc[:, ['project', op_chars]].dropna().set_index(
                    'project')[op_chars].to_dict()

                project_operational_chars.update_project_opchar_column(
                    io=io, c=c,
                    project_operational_chars_scenario_id=sc_id,
                    column=op_chars,
                    project_char=operational_chars_dict
                )


def load_project_variable_profiles(io, c, subscenario_input, data_input):
    """
    Data dictionary is {project:{scenario_id:{stage_id:{timepoint: cap_factor}}}}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    project_tmp_profiles = dict()
    project_tmp_profiles_scenarios = dict()

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]
        prj = subscenario_input['project'][i]

        # Check whether project key exists. This situation arises for project + subscenario id keys
        if prj not in project_tmp_profiles_scenarios:
            project_tmp_profiles_scenarios[prj] = dict()
        project_tmp_profiles_scenarios[prj][sc_id] = (sc_name, sc_description)

        # Check whether project key exists. This situation arises for project + subscenario id keys
        if prj not in project_tmp_profiles:
            project_tmp_profiles[prj] = dict()
        project_tmp_profiles[prj][sc_id] = dict()

        project_tmp_profiles_by_project = data_input.loc[
                (data_input['id'] == sc_id) & (data_input['project'] == prj)]

        for st_id in project_tmp_profiles_by_project['stage_id'].unique():
            project_tmp_profiles_by_project_stage = project_tmp_profiles_by_project.loc[
                project_tmp_profiles_by_project['stage_id'] == st_id, ['timepoint', 'cap_factor']]
            project_tmp_profiles_by_project_stage[['timepoint']] = \
                project_tmp_profiles_by_project_stage[['timepoint']].astype(int)
            project_tmp_profiles[prj][sc_id][int(st_id)] = \
                project_tmp_profiles_by_project_stage.set_index('timepoint')['cap_factor'].to_dict()

    project_operational_chars.update_project_variable_profiles(
        io=io, c=c,
        proj_profile_names=project_tmp_profiles_scenarios,
        proj_tmp_profiles=project_tmp_profiles
    )


def load_project_hydro_opchar(io, c, subscenario_input, data_input):
    """
    Data output dictionary is {project:{scenario_id:{balancing_type:{horizon:{period, avg, min, max}}}}}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """

    project_horizon_chars = dict()
    project_horizon_chars_scenarios = dict()

    for i in subscenario_input.index:
        sc_id = int(subscenario_input['id'][i])
        sc_name = subscenario_input['name'][i]
        sc_description = subscenario_input['description'][i]
        prj = subscenario_input['project'][i]

        # Check whether project key exists. This situation arises for project + subscenario id keys
        if prj not in project_horizon_chars_scenarios:
            project_horizon_chars_scenarios[prj] = dict()
        project_horizon_chars_scenarios[prj][sc_id] = (sc_name, sc_description)

        # Check whether project key exists. This situation arises for project + subscenario id keys
        if prj not in project_horizon_chars:
            project_horizon_chars[prj] = dict()
        project_horizon_chars[prj][sc_id] = dict()

        project_horizon_chars_by_project = data_input.loc[
            (data_input['id'] == sc_id) & (data_input['project'] == prj)]

        for b_type in project_horizon_chars_by_project['balancing_type_project'].unique():
            project_horizon_chars_by_project_balancing_type = project_horizon_chars_by_project.loc[
                project_horizon_chars_by_project['balancing_type_project'] == b_type, ['horizon', 'period', 'avg', 'min', 'max']]
            project_horizon_chars_by_project_balancing_type[['horizon']] = \
                project_horizon_chars_by_project_balancing_type[['horizon']].astype(int)
            project_horizon_chars_by_project_balancing_type[['period']] = \
                project_horizon_chars_by_project_balancing_type[['period']].astype(int)
            project_horizon_chars[prj][sc_id][b_type] = \
                project_horizon_chars_by_project_balancing_type[[
                    'horizon', 'period', 'avg', 'min', 'max']].set_index(['horizon']).to_dict(orient='index')

    project_operational_chars.update_project_hydro_opchar(
        io=io, c=c,
        proj_opchar_names=project_horizon_chars_scenarios,
        proj_horizon_chars=project_horizon_chars
    )


def load_project_hr_curves(io, c, subscenario_input, data_input):
    """
    Data output dictionary is {project:{heat_rate_curves_scenario_id:{load_point: average_heat_rate_mmbtu_per_mwh}}}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """
    project_hr_scenarios = [
        tuple(x) for x in subscenario_input.to_records(index=False)
    ]

    # Change the order of the columns before creating the list of tuples
    # (move subscenario_id and project to the front)
    cols = data_input.columns.tolist()
    cols = [cols[3], cols[4], cols[0], cols[1], cols[2]]
    data_input = data_input[cols]

    project_hr_chars = [
        tuple(x) for x in data_input.to_records(index=False)
    ]

    project_operational_chars.update_project_hr_curves(
        io=io, c=c,
        subs_data=project_hr_scenarios,
        proj_hr_chars=project_hr_chars
    )


def load_project_vom_curves(io, c, subscenario_input, data_input):
    """
    Data output dictionary is {project:{variable_om_curves_scenario_id:{
    load_point: average_variable_om_cost_per_mwh}}}
    :param io:
    :param c:
    :param subscenario_input:
    :param data_input:
    :return:
    """
    project_vom_scenarios = [
        tuple(x) for x in subscenario_input.to_records(index=False)
    ]

    # Change the order of the columns before creating the list of tuples
    # (move subscenario_id and project to the front)
    cols = data_input.columns.tolist()
    cols = [cols[3], cols[4], cols[0], cols[1], cols[2]]
    data_input = data_input[cols]

    project_vom_chars = [
        tuple(x) for x in data_input.to_records(index=False)
    ]

    project_operational_chars.update_project_vom_curves(
        io=io, c=c,
        subs_data=project_vom_scenarios,
        proj_vom_chars=project_vom_chars
    )


def load_project_startup_chars(io, c, subscenario_input, data_input):
    """
    Data_input is a list of tuples (project, startup_chars_scenario_id,
    down_time_cutoff_hours, startup_plus_ramp_up_rate, startup_cost_per_mw)

    :param io:
    :param c:
    :param subscenario_input:
    :param data_input: pd.DataFrame
    :return:
    """

    # subscenario_input.drop(["filename"], axis=1, inplace=True)
    project_su_scenarios = [
        tuple(x) for x in subscenario_input.to_records(index=False)
    ]

    # Change the order of the columns before creating the list of tuples
    cols = data_input.columns.tolist()
    cols = cols[-2:] + cols[:3]
    data_input = data_input[cols]
    project_su_chars = [
        tuple(x) for x in data_input.to_records(index=False)
    ]

    project_operational_chars.update_project_startup_chars(
        io=io, c=c,
        subscenario_data=project_su_scenarios,
        project_startup_chars=project_su_chars
    )
