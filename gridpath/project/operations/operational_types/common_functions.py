# Copyright 2016-2024 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import os.path
import pandas as pd
import warnings

from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.project.common_functions import (
    check_if_boundary_type_and_first_timepoint,
    check_boundary_type,
)
from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    validate_req_cols,
    validate_missing_inputs,
    validate_values,
    validate_column_monotonicity,
)


def determine_relevant_timepoints(mod, g, tmp, min_time):
    """
    :param mod:
    :param g:
    :param tmp:
    :param min_time:
    :return: the relevant timepoints to look at for the minimum up/down time
        constraints

    We need to figure out how far back we need to look,
    i.e. which timepoints we need to consider when capacity could have
    been turned on/off that must still be on/off in the current timepoint *t*.

    Any capacity that was turned on/off between t and t-1 must still be
    on/off in t, so timepoint *t* is a relevant timepoint.

    Capacity must also still be on/off if it was turned on/off less than its
    up/down time ago, i.e. if it was turned on/off between timepoints that
    are within the min up/down time from the beginning of the current
    timepoint. Once we reach a timepoint whose duration takes us to a
    point in time that is removed from the beginning of timepoint *t* by a
    time greater than or equal to the min_time, that timepoint is not
    relevant anymore and we have completed our list of relevant timepoints.

    In a simple case, let's assume all timepoints have durations of 1 hour.
    Timepoint t-1 is removed from the start of timepoint *t* by an hour,
    timepoint t-2 by 2 hours, timepoint t-3 by 3 hours, etc. Therefore, if
    if a generator has a 4-hour minimum up time and was started up in t-3 (
    i.e. between t-4 and t-3), then it must still be on in the current
    timepoint. If it was started up in t-4, it has already been up for 4
    hours by the time timepoint *t* begins, so it can be turned off. The
    relevant timepoints are therefore t-1, t-2, and t-3; we do not need to
    constrain capacity turned on/off in t-4 or farther in the past.

    If t-2 has duration of 2-hours, on the other hand, the total duration of
    the previous three timepoints would be 4 hours and the generator turned
    on in t-3 should therefore be allowed to turn off in the current
    timepoint *t*. In this case, the relevant timepoints would be t-1 and
    t-2. By the time we reach t-3, we will have reached the 4-hour minimum
    up/down time, so t-3 will not be relevant for the minimum up time
    constraint in timepoint *t*.
    """

    # The first possible relevant timepoint is the current timepoint
    relevant_tmps = [tmp]
    relevant_linked_tmps = []
    # The first possible linked timepoint is 0
    linked_tmp = 0

    # If we have already reached the first timepoint of a horizon in a
    # linear boundary type we'll just pass, as there are no more relevant
    # timepoints to add
    if check_if_boundary_type_and_first_timepoint(
        mod=mod,
        tmp=tmp,
        balancing_type=mod.balancing_type_project[g],
        boundary_type="linear",
    ):
        pass  # no more relevant timepoints, keep list limited to *t*
    # If we have already reached the first timepoint in a linked horizon
    # setting, we'll immediately move on to the linked timepoints without
    # looking for a previous timepoint
    elif check_if_boundary_type_and_first_timepoint(
        mod=mod,
        tmp=tmp,
        balancing_type=mod.balancing_type_project[g],
        boundary_type="linked",
    ):
        # Add the first linked timepoint's duration to hours_from_tmp
        hours_from_tmp = mod.hrs_in_linked_tmp[linked_tmp]
        # If we haven't exceeded the min time yet, the first linked
        # timepoint is relevant, so we'll add it and move on to the
        # next one
        while hours_from_tmp < min_time:
            relevant_linked_tmps.append(linked_tmp)
            # If this is the furthest linked timepoint, break out of
            # the linked timepoints loop; otherwise, move on to the next
            # linked timepoint
            if linked_tmp == mod.furthest_linked_tmp:
                break
            else:
                linked_tmp += -1
                hours_from_tmp += mod.hrs_in_linked_tmp[linked_tmp]
    # If we haven't reached the first timepoint of a linear or linked
    # horizon, we'll look for the previous timepoint
    else:
        # The next possible relevant timepoint is the previous timepoint,
        # so we'll check its duration (if it's longer than or equal to the
        # minimum up/down time, we'll break out of the loop immediately)
        relevant_tmp = mod.prev_tmp[tmp, mod.balancing_type_project[g]]
        hours_from_tmp = mod.hrs_in_tmp[
            mod.prev_tmp[tmp, mod.balancing_type_project[g]]
        ]

        while hours_from_tmp < min_time:
            # If we haven't exceed the minimum up/down time yet, this timepoint
            # is relevant and we add it to our list
            relevant_tmps.append(relevant_tmp)

            # In a 'linear' horizon setting, once we reach the first
            # timepoint of the horizon, we break out of the loop since there
            # are no more timepoints to consider
            if check_if_boundary_type_and_first_timepoint(
                mod=mod,
                tmp=relevant_tmp,
                balancing_type=mod.balancing_type_project[g],
                boundary_type="linear",
            ):
                break
            # In a 'circular' horizon setting, once we reach timepoint *t*,
            # we break out of the loop since there are no more timepoints to
            # consider (we have already added all horizon timepoints as
            # relevant)
            elif (
                check_boundary_type(
                    mod=mod,
                    tmp=tmp,
                    balancing_type=mod.balancing_type_project[g],
                    boundary_type="circular",
                )
                and relevant_tmp == tmp
            ):
                break
            # TODO: only allow the first horizon of a subproblem to have
            #  linked timepoints
            # In a 'linked' horizon setting, once we reach the first
            # timepoint of the horizon, we'll start adding the linked
            # timepoints until we reach the target min time
            elif check_if_boundary_type_and_first_timepoint(
                mod=mod,
                tmp=relevant_tmp,
                balancing_type=mod.balancing_type_project[g],
                boundary_type="linked",
            ):
                # Add the first linked timepoint's duration to hours_from_tmp
                hours_from_tmp += mod.hrs_in_linked_tmp[linked_tmp]
                # If we haven't exceeded the min time yet, the first linked
                # timepoint is relevant, so we'll add it and move on to the
                # next one
                while hours_from_tmp < min_time:
                    relevant_linked_tmps.append(linked_tmp)
                    # If this is the furthest linked timepoint, break out of
                    # the linked timepoints loop; otherwise, move on to the
                    # next linked timepoint
                    if linked_tmp == mod.furthest_linked_tmp:
                        break
                    else:
                        linked_tmp += -1
                        hours_from_tmp += mod.hrs_in_linked_tmp[linked_tmp]
                # Break out from the outer while loop when done with the
                # linked timepoints
                break
            # Otherwise, we move on to the relevant timepoint's previous
            # timepoint and will add that timepoint's duration to
            # hours_from_tmp
            else:
                hours_from_tmp += mod.hrs_in_tmp[
                    mod.prev_tmp[relevant_tmp, mod.balancing_type_project[g]]
                ]
                relevant_tmp = mod.prev_tmp[relevant_tmp, mod.balancing_type_project[g]]

    return relevant_tmps, relevant_linked_tmps


def get_optype_inputs_as_df(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    op_type,
    required_columns,
    optional_columns,
):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param op_type:
    :param required_columns:
    :param optional_columns:
    :return: the project dataframe filtered for the operational type and
        with the appropriate columns for the operational type

    Create a dataframe for the operational type from the projects.tab file.
    This dataframe takes only the rows with projects of this operational
    type and only the columns required or optional for the operational type.
    """

    # Figure out which headers we have
    header = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        sep="\t",
        header=None,
        nrows=1,
    ).values[0]

    # Get the columns for the optional params (it's OK if they don't exist)
    used_columns = [c for c in optional_columns if c in header]

    # Read in the appropriate columns for the operational type from
    # projects.tab
    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        sep="\t",
        usecols=["project", "operational_type"] + required_columns + used_columns,
    )

    # Filter for the operational type
    optype_df = df.loc[df["operational_type"] == op_type]

    return optype_df


def get_param_dict(df, column_name, cast_as_type):
    """
    :param df: the project-params dataframe
    :param column_name: string, column name of the parameter to look for
    :param cast_as_type: the type for the parameter
    :return: dictionary, {project: param_value}

    Create a dictionary for the parameter to load into Pyomo.
    """
    param_dict = dict()

    for row in zip(df["project"], df[column_name]):
        [prj, param_val] = row
        # Add to the param dictionary if a value is specified
        # Otherwise, we'll use the default value (or Pyomo will throw an
        # error if no default value)
        if param_val != ".":
            param_dict[prj] = cast_as_type(row[1])

    return param_dict


def get_optype_param_requirements(op_type):
    """
    :param op_type: string
    :return: three dictionaries of the required, optional, and other
        projects.tab columns for the operational type with their types as
        values.

    Read in the required, optional, and other columns for an operational
    type. Make a dictionary for each with the types for each as values. We
    need the types to cast when loading into Pyomo. "other" columns are columns
    that are neither required nor optional and for which we don't expect any
    inputs for for that operational type.
    """

    df = pd.read_csv(
        os.path.join(os.path.dirname(__file__), "opchar_param_requirements.csv"),
        sep=",",
        dtype=str,
    )
    # df.set_index('ID').T.to_dict('list')
    required_columns = df.loc[df[op_type] == "required"][["char", "type"]]
    required_columns_dict = dict(
        zip(required_columns["char"], required_columns["type"])
    )
    optional_columns = df.loc[df[op_type] == "optional"][["char", "type"]]
    optional_columns_dict = dict(
        zip(optional_columns["char"], optional_columns["type"])
    )
    other_columns = df.loc[~df[op_type].isin(["optional", "required"])][
        ["char", "type"]
    ]
    other_columns_dict = dict(zip(other_columns["char"], other_columns["type"]))

    return required_columns_dict, optional_columns_dict, other_columns_dict


def get_types_dict():
    """
    :return: type name read in as string to type method mapping
    """
    return {"str": str, "float": float, "int": int}


def load_optype_model_data(
    mod,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    op_type,
):
    """

    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param op_type:
    :return:
    """
    # String to method dictionary for types
    types_dict = get_types_dict()

    # Get the required and optional columns with their types
    required_columns_types, optional_columns_types, _ = get_optype_param_requirements(
        op_type=op_type
    )

    # Load in the inputs dataframe for the op type module
    op_type_df = get_optype_inputs_as_df(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        op_type=op_type,
        required_columns=[r for r in required_columns_types.keys()],
        optional_columns=[o for o in optional_columns_types.keys()],
    )

    # Get the list of projects of this operational type
    # We'll return this at the end, as some operational types use the list
    # after calling this function
    op_type_projects = op_type_df["project"].to_list()

    # Load required param data into the Pyomo DataPortal
    # This requires that the param name consist of the operational type
    # name, an underscore, and the column name
    for req in required_columns_types.keys():
        type_method = types_dict[required_columns_types[req]]
        data_portal.data()["{}_{}".format(op_type, req)] = get_param_dict(
            df=op_type_df, column_name=req, cast_as_type=type_method
        )

    # Load optional param data into the Pyomo DataPortal
    # Ignore if relevant columns are not found in the dataframe
    # TODO: figure out how to flag what gets loaded at the module level vs
    #  what we can load downstream
    for opt in optional_columns_types.keys():
        type_method = types_dict[optional_columns_types[opt]]
        try:
            data_portal.data()["{}_{}".format(op_type, opt)] = get_param_dict(
                df=op_type_df, column_name=opt, cast_as_type=type_method
            )
        # These columns are optional, so it's OK if we don't find them
        except KeyError:
            pass

    return op_type_projects


def write_tab_file_model_inputs(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    fname,
    data,
    replace_nulls=False,
):
    """
    Write inputs to tab-delimited file in appropriate directory

    TODO: could use this function in many more modules where we write to file
     but need to make sure db column names and tab file column names are
     consistent

    :param scenario_directory: string, the scenario directory
    :param subproblem: the active subproblem, set to "" if only 1 subproblem
    :param stage: the active stage, set to " if only 1 stage
    :param fname: the filename (with the .tab file extension)
    :param data: cursor object with query results
    :param replace_nulls: Booolean, whether the replace Nulls with "."
    :return:
    """

    out_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        fname,
    )
    f_exists = os.path.isfile(out_file)
    append_mode = "a" if f_exists else "w"

    # Only write if we have data
    data_list = [row for row in data.fetchall()]
    if data_list:
        with open(out_file, append_mode, newline="") as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")

            # If file doesn't exist, write header first
            if not f_exists:
                cols = [s[0] for s in data.description]
                writer.writerow(cols)

            for row in data_list:
                if replace_nulls:
                    row = ["." if i is None else i for i in row]
                writer.writerow(row)


def load_var_profile_inputs(
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    op_type,
    tab_filename="variable_generator_profiles.tab",
    param_name="cap_factor",
):
    """
    Capacity factors vary by horizon and stage, so get inputs from appropriate
    directory.

    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param op_type:
    :param tab_filename: defaults to "variable_generator_profiles.tab"
    :param param_name: defaults to "cap_factor"
    :return:
    """

    var_op_types = [
        "gen_var_must_take",
        "gen_var",
        "gen_var_stor_hyb",
        "energy_profile",
        "load_component_modifier",
        "load_component_shift",
    ]
    other_var_op_types = set(var_op_types) - set([op_type])
    assert op_type in var_op_types

    # Determine projects of this op_type and other var op_types
    # TODO: re-factor getting projects of certain op-type?
    prj_df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        sep="\t",
        usecols=["project", "operational_type"],
    )
    op_type_prjs = prj_df[prj_df["operational_type"] == op_type]["project"]
    other_var_op_type_prjs = prj_df[
        prj_df["operational_type"].isin(other_var_op_types)
    ]["project"]
    var_prjs = list(op_type_prjs) + list(other_var_op_type_prjs)

    # Read in the cap factors, filter for projects with the correct op_type
    # and convert to dictionary
    cf_df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            tab_filename,
        ),
        sep="\t",
        usecols=["project", "timepoint", param_name],
        dtype={param_name: float},
    )
    op_type_cf_df = cf_df[cf_df["project"].isin(op_type_prjs)]
    param_value = op_type_cf_df.set_index(["project", "timepoint"])[
        param_name
    ].to_dict()

    # Throw warning if profile exists for a project not in projects.tab
    # (as 'gen_var' or 'gen_var_must_take')
    # TODO: this will throw warning twice, once for gen_var and once for
    #  gen_var_must_take
    # TODO: move this to validation instead?
    invalid_prjs = cf_df[~cf_df["project"].isin(var_prjs)]["project"].unique()
    for prj in invalid_prjs:
        warnings.warn(
            f"""WARNING: Profiles are specified for '{prj}' in 
            {tab_filename}, but '{prj}' is not in 
            projects.tab."""
        )

    # Load data
    data_portal.data()[f"{op_type}_{param_name}"] = param_value


# TODO: scenario setup tables; run slow queries only once, then select from
#  smaller table for iterations/subproblems


# TODO: consolidate with horizon equivalent methods below
TIMEPOINT_INDEX_QUERY_PARAMS = {
    "select_columns": "timepoint",
    "index_columns": "timepoint",
    "index_join_table": "inputs_temporal",
    "index_columns_join_table": "timepoint",
}

BT_HRZ_INDEX_QUERY_PARAMS = {
    "select_columns": "balancing_type_project, horizon",
    "index_columns": "balancing_type_project, horizon",
    "index_join_table": "inputs_temporal_horizon_timepoints",
    "index_columns_join_table": "balancing_type_horizon, horizon",
}


def get_prj_temporal_index_opr_inputs_from_db(
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
    op_type,
    table,
    subscenario_id_column,
    data_column,
    opr_index_dict=None,
):
    """
    Determine appropriate iterations for projects and get those inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :param op_type:
    :return: cursor object with query results
    """
    if opr_index_dict is None:
        opr_index_dict = TIMEPOINT_INDEX_QUERY_PARAMS

    all_projects_sql = str()
    # Check for no iterations projects
    no_iterations_project_sql = make_iteration_subset_project_list_query(
        conn=conn,
        subscenarios=subscenarios,
        table=table,
        data_columns=data_column,
        subscenario_id_column=subscenario_id_column,
        op_type=op_type,
        subproblem=subproblem,
        stage=stage,
        varies_by_weather_iteration=0,
        varies_by_hydro_iteration=0,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        opr_index_dict=opr_index_dict,
    )
    all_projects_sql += no_iterations_project_sql

    # Check for weather iterations projects
    if no_iterations_project_sql != "":
        all_projects_sql += " UNION "

    weather_iterations_project_sql = make_iteration_subset_project_list_query(
        conn=conn,
        subscenarios=subscenarios,
        table=table,
        data_columns=data_column,
        subscenario_id_column=subscenario_id_column,
        op_type=op_type,
        subproblem=subproblem,
        stage=stage,
        varies_by_weather_iteration=1,
        varies_by_hydro_iteration=0,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        opr_index_dict=opr_index_dict,
    )
    all_projects_sql += weather_iterations_project_sql

    # Check of hydro iterations projects
    if weather_iterations_project_sql != "":
        all_projects_sql += " UNION "
    hydro_iterations_project_sql = make_iteration_subset_project_list_query(
        conn=conn,
        subscenarios=subscenarios,
        table=table,
        data_columns=data_column,
        subscenario_id_column=subscenario_id_column,
        op_type=op_type,
        subproblem=subproblem,
        stage=stage,
        varies_by_weather_iteration=0,
        varies_by_hydro_iteration=1,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        opr_index_dict=opr_index_dict,
    )
    all_projects_sql += hydro_iterations_project_sql

    # Check for weather and hydro iterations projects
    if hydro_iterations_project_sql != "":
        all_projects_sql += " UNION "
    weather_and_hydro_iterations_project_sql = make_iteration_subset_project_list_query(
        conn=conn,
        subscenarios=subscenarios,
        table=table,
        data_columns=data_column,
        subscenario_id_column=subscenario_id_column,
        op_type=op_type,
        subproblem=subproblem,
        stage=stage,
        varies_by_weather_iteration=1,
        varies_by_hydro_iteration=1,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        opr_index_dict=opr_index_dict,
    )
    all_projects_sql += weather_and_hydro_iterations_project_sql

    if all_projects_sql[-7:] == " UNION ":
        all_projects_sql = all_projects_sql[: len(all_projects_sql) - 7]

    c = conn.cursor()

    prj_tmp_data = c.execute(all_projects_sql)

    return prj_tmp_data


def get_prj_indx_inputs_with_iterations_sql(
    subscenarios,
    opr_index_dict,
    inputs_table,
    data_columns,
    subscenario_id_column,
    op_type,
    subproblem,
    stage,
    project_filter,
    weather_iteration_to_use,
    hydro_iteration_to_use,
):
    """
    Select only profiles of projects in the portfolio
    Select only profiles of projects with 'op_type' operational type
    Select only profiles for timepoints from the correct temporal scenario
    and the correct subproblem
    Select only timepoints on periods when the project is operational
    (periods with existing project capacity for existing projects or
    with costs specified for new projects)
    """

    select_columns = opr_index_dict["select_columns"]
    index_columns = opr_index_dict["index_columns"]
    index_join_table = opr_index_dict["index_join_table"]
    index_columns_join_table = opr_index_dict["index_columns_join_table"]

    optype_filter = (
        f"""AND operational_type = '{op_type}'""" if op_type != "all" else ""
    )
    sql = f"""
        SELECT project, {select_columns}, {data_columns}
        FROM {inputs_table}
        -- Portfolio projects only
        WHERE project IN (
            SELECT project FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
        )
        -- Optype projects from this opchar ID only
        AND project IN (
            SELECT project
            FROM inputs_project_operational_chars
            WHERE project_operational_chars_scenario_id = {subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID}
            {optype_filter}
        )
        -- Relevant optype opchar ID
        AND (project, {subscenario_id_column}) IN (
            SELECT project, {subscenario_id_column}
            FROM inputs_project_operational_chars
            WHERE project_operational_chars_scenario_id = {subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID}
            {project_filter}
        )
        -- Relevant temporal index
        AND ({index_columns}) IN (
            SELECT {index_columns_join_table}
            FROM {index_join_table}
            WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
            AND subproblem_id = {subproblem}
            AND stage_id = {stage}
        )
        AND weather_iteration = {weather_iteration_to_use}
        AND hydro_iteration = {hydro_iteration_to_use}
        """

    return sql


def make_iteration_subset_project_list_query(
    conn,
    subscenarios,
    table,
    data_columns,
    subscenario_id_column,
    op_type,
    subproblem,
    stage,
    varies_by_weather_iteration,
    varies_by_hydro_iteration,
    weather_iteration,
    hydro_iteration,
    opr_index_dict,
):
    c = conn.cursor()
    projects_list = c.execute(
        f"""
        SELECT project, {subscenario_id_column}
        FROM {table}_iterations
        WHERE varies_by_weather_iteration = {varies_by_weather_iteration}
        AND varies_by_hydro_iteration = {varies_by_hydro_iteration}
        ;
        """
    ).fetchall()
    if projects_list:
        project_str = make_project_str(projects_list=projects_list)
        sql = get_prj_indx_inputs_with_iterations_sql(
            subscenarios=subscenarios,
            opr_index_dict=opr_index_dict,
            inputs_table=table,
            data_columns=data_columns,
            subscenario_id_column=subscenario_id_column,
            op_type=op_type,
            subproblem=subproblem,
            stage=stage,
            project_filter=f"AND (project, {subscenario_id_column}) in {project_str}",
            weather_iteration_to_use=(
                weather_iteration if varies_by_weather_iteration else 0
            ),
            hydro_iteration_to_use=hydro_iteration if varies_by_hydro_iteration else 0,
        )
    else:
        sql = ""

    return sql


def make_project_str(projects_list):
    project_str = "("
    list_len = len(projects_list)
    n = 1
    for prj in projects_list:
        project_str += f"{prj}"
        if n < list_len:
            project_str += ", "
        else:
            project_str += ")"
        n += 1

    return project_str


##


def validate_var_profiles(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
    op_type,
):
    """

    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :param op_type:
    :return:
    """
    var_profiles = get_prj_temporal_index_opr_inputs_from_db(
        subscenarios=subscenarios,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        conn=conn,
        op_type="gen_var",
        table="inputs_project_variable_generator_profiles",
        subscenario_id_column="variable_generator_profile_scenario_id",
        data_column="cap_factor",
    )

    # Convert input data into pandas DataFrame
    df = cursor_to_df(var_profiles)

    value_cols = ["cap_factor"]

    # Check for missing inputs
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_variable_generator_profiles",
        severity="High",
        errors=validate_missing_inputs(df, value_cols, ["project", "timepoint"]),
    )

    # Check for sign (should be percent fraction)
    cap_factor_validation_error = write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_variable_generator_profiles",
        severity="Low",
        errors=validate_values(df, ["cap_factor"], min=0, max=1),
    )

    return cap_factor_validation_error


def load_hydro_opchars(
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    op_type,
    projects,
):
    """
    Load hydro operational data from hydro-specific input files
    Determine subset of project-horizons in hydro budgets file

    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param op_type:
    :param projects:
    :return:
    """

    project_bt_horizons = list()
    avg = dict()
    min = dict()
    max = dict()

    prj_hor_opchar_df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "hydro_conventional_horizon_params.tab",
        ),
        sep="\t",
        usecols=[
            "project",
            "balancing_type_project",
            "horizon",
            "average_power_fraction",
            "min_power_fraction",
            "max_power_fraction",
        ],
    )
    for row in zip(
        prj_hor_opchar_df["project"],
        prj_hor_opchar_df["balancing_type_project"],
        prj_hor_opchar_df["horizon"],
        prj_hor_opchar_df["average_power_fraction"],
        prj_hor_opchar_df["min_power_fraction"],
        prj_hor_opchar_df["max_power_fraction"],
    ):
        if row[0] in projects:
            project_bt_horizons.append((row[0], row[1], row[2]))
            avg[(row[0], row[1], row[2])] = float(row[3])
            min[(row[0], row[1], row[2])] = float(row[4])
            max[(row[0], row[1], row[2])] = float(row[5])

    # Load data
    data_portal.data()["{}_OPR_BT_HRZS".format(op_type.upper())] = {
        None: project_bt_horizons
    }
    data_portal.data()["{}_average_power_fraction".format(op_type)] = avg
    data_portal.data()["{}_min_power_fraction".format(op_type)] = min
    data_portal.data()["{}_max_power_fraction".format(op_type)] = max


def validate_hydro_opchars(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
    op_type,
):
    """

    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :param op_type:
    :return:
    """

    hydro_chars = get_prj_temporal_index_opr_inputs_from_db(
        subscenarios=subscenarios,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        conn=conn,
        op_type="gen_hydro_must_take",
        table="inputs_project_hydro_operational_chars",
        subscenario_id_column="hydro_operational_chars_scenario_id",
        data_column="average_power_fraction, min_power_fraction, " "max_power_fraction",
        opr_index_dict=BT_HRZ_INDEX_QUERY_PARAMS,
    )

    # Convert input data into pandas DataFrame
    df = cursor_to_df(hydro_chars)
    value_cols = ["min_power_fraction", "average_power_fraction", "max_power_fraction"]

    # Check for missing inputs
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_hydro_operational_chars",
        severity="High",
        errors=validate_missing_inputs(df, value_cols, ["project", "horizon"]),
    )

    # Check for sign (should be percent fraction)
    hydro_opchar_fraction_error = write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_hydro_operational_chars",
        severity="Low",
        errors=validate_values(df, value_cols, min=0, max=1),
    )

    # Check min <= avg <= sign
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_hydro_operational_chars",
        severity="Mid",
        errors=validate_column_monotonicity(
            df=df, cols=value_cols, idx_col=["project", "horizon"]
        ),
    )

    return hydro_opchar_fraction_error


def load_startup_chars(
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    op_type,
    projects,
):
    """

    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param op_type:
    :param projects:
    :return:
    """

    startup_chars_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "startup_chars.tab",
    )

    if os.path.exists(startup_chars_file):
        df = pd.read_csv(startup_chars_file, sep="\t")

        # Note: the rank function requires at least one numeric input in the
        # down_time_cutoff_hours column (can't be all NULL/None).
        if len(df) > 0:
            df["startup_type_id"] = df.groupby("project")[
                "down_time_cutoff_hours"
            ].rank()

        startup_ramp_projects = set()
        startup_ramp_projects_types = list()
        down_time_cutoff_hours_dict = dict()
        startup_plus_ramp_up_rate_dict = dict()

        for i, row in df.iterrows():
            project = row["project"]
            startup_type_id = row["startup_type_id"]
            down_time_cutoff_hours = row["down_time_cutoff_hours"]
            startup_plus_ramp_up_rate = row["startup_plus_ramp_up_rate"]

            if (
                down_time_cutoff_hours != "."
                and startup_plus_ramp_up_rate != "."
                and project in projects
            ):
                startup_ramp_projects.add(project)
                startup_ramp_projects_types.append((project, startup_type_id))
                down_time_cutoff_hours_dict[(project, startup_type_id)] = float(
                    down_time_cutoff_hours
                )
                startup_plus_ramp_up_rate_dict[(project, startup_type_id)] = float(
                    startup_plus_ramp_up_rate
                )

        if startup_ramp_projects:
            data_portal.data()[
                "{}_down_time_cutoff_hours".format(op_type)
            ] = down_time_cutoff_hours_dict
            data_portal.data()[
                "{}_startup_plus_ramp_up_rate_by_st".format(op_type)
            ] = startup_plus_ramp_up_rate_dict


def check_for_tmps_to_link(scenario_directory, subproblem, stage):
    """
    :param scenario_directory: str
    :param subproblem: str
    :param stage: str
    :return:

    If there's a linked_subproblems_map CSV file, check which of the current
    subproblem TMPS we should export results for to link to the next
    subproblem and pass that; otherwise, pass empty list.
    """
    try:
        map_df = pd.read_csv(
            os.path.join(scenario_directory, "linked_subproblems_map.csv"), sep=","
        )

        # Figure out which timepoints we'll be linking to the next subproblem
        # Stages must match in the linked subproblems
        # These are subset of all TMPS in the current subproblem
        tmps_to_link_df = map_df.loc[
            (map_df["subproblem"] == int(subproblem))
            & (map_df["stage"] == (1 if stage == "" else int(stage)))
        ]
        tmps_to_link = tmps_to_link_df["timepoint"].tolist()
        tmp_linked_tmp_dict = tmps_to_link_df.set_index("timepoint")[
            "linked_timepoint"
        ].to_dict()

        return tmps_to_link, tmp_linked_tmp_dict
    except FileNotFoundError:
        return [], {}


def get_optype_inputs_from_db(scenario_id, subscenarios, conn, op_type):
    """

    :param subscenarios:
    :param conn:
    :param op_type:
    :return:
    """

    # TODO: consolidate this with what happens in projects.init so we only
    #  hard-code the list of project opchars once.
    #  Also remove min/max duration since not really an opchar?
    cols = [
        "project",
        "variable_om_cost_per_mwh",
        "operational_type",
        "min_stable_level_fraction",
        "unit_size_mw",
        "startup_cost_per_mw",
        "shutdown_cost_per_mw",
        "startup_fuel_mmbtu_per_mw",
        "startup_plus_ramp_up_rate",
        "shutdown_plus_ramp_down_rate",
        "ramp_up_when_on_rate",
        "ramp_down_when_on_rate",
        "min_up_time_hours, min_down_time_hours",
        "allow_startup_shutdown_power",
        "storage_efficiency",
        "charging_efficiency",
        "discharging_efficiency",
        "charging_capacity_multiplier",
        "discharging_capacity_multiplier",
        "minimum_duration_hours",
        "maximum_duration_hours",
        "max_losses_in_hrz_frac_stor_energy_capacity",
        "aux_consumption_frac_capacity",
        "aux_consumption_frac_power",
        "powerunithour_per_fuelunit",
        "partial_availability_threshold",
        "powerhouse",
        "generator_efficiency",
        "linked_load_component",
        "efficiency_factor",
        "energy_requirement_factor",
    ]

    sql = """SELECT {}
        FROM inputs_project_portfolios
        INNER JOIN
        inputs_project_operational_chars
        USING (project)
        WHERE project_portfolio_scenario_id = {}
        AND project_operational_chars_scenario_id = {}
        AND operational_type = '{}';
        """.format(
        ",".join(cols),
        subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
        op_type,
    )

    df = pd.read_sql(sql, conn)

    return df


def validate_opchars(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
    op_type,
):
    """

    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :param op_type:
    :return:
    """

    # TODO: deal with fuel and variable O&M column, which are nor optional nor
    #  required for any?

    # Get the opchar inputs for this operational type
    df = get_optype_inputs_from_db(scenario_id, subscenarios, conn, op_type)

    # Get the required, optional, and other columns with their types
    (
        required_columns_types,
        optional_columns_types,
        other_columns_types,
    ) = get_optype_param_requirements(op_type=op_type)
    req_cols = required_columns_types.keys()
    na_cols = other_columns_types.keys()

    # Check that required inputs are present
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="High",
        errors=validate_req_cols(df, req_cols, True, op_type),
    )

    # Check that other (not required or optional) inputs are not present
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="Low",
        errors=validate_req_cols(df, na_cols, False, op_type),
    )

    # TODO: do data-type and numeric non-negativity checking here rather than
    #  in project.init?

    # Return the opchar df (sometimes used for further validations)
    return df
