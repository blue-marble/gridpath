#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
import pandas as pd
import warnings

from db.common_functions import spin_on_database_lock
from gridpath.project.common_functions import \
    check_if_boundary_type_and_first_timepoint, get_column_row_value, \
    check_boundary_type


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
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g],
        boundary_type="linear"
    ):
        pass  # no more relevant timepoints, keep list limited to *t*
    # If we have already reached the first timepoint in a linked horizon
    # setting, we'll immediately move on to the linked timepoints without
    # looking for a previous timepoint
    elif check_if_boundary_type_and_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g],
        boundary_type="linked"
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
                hours_from_tmp += mod.hrs_in_linked_tmp[linked_tmp]
                linked_tmp += -1
    # If we haven't reached the first timepoint of a linear or linked
    # horizon, we'll look for the previous timepoint
    else:
        # The next possible relevant timepoint is the previous timepoint,
        # so we'll check its duration (if it's longer than or equal to the
        # minimum up/down time, we'll break out of the loop immediately)
        relevant_tmp = mod.prev_tmp[tmp, mod.balancing_type_project[g]]
        hours_from_tmp = \
            mod.hrs_in_tmp[
                mod.prev_tmp[tmp, mod.balancing_type_project[g]]]

        while hours_from_tmp < min_time:
            # If we haven't exceed the minimum up/down time yet, this timepoint
            # is relevant and we add it to our list
            relevant_tmps.append(relevant_tmp)

            # In a 'linear' horizon setting, once we reach the first
            # timepoint of the horizon, we break out of the loop since there
            # are no more timepoints to consider
            if check_if_boundary_type_and_first_timepoint(
                mod=mod, tmp=relevant_tmp, balancing_type=mod.balancing_type_project[g],
                boundary_type="linear"
            ):
                break
            # In a 'circular' horizon setting, once we reach timepoint *t*,
            # we break out of the loop since there are no more timepoints to
            # consider (we have already added all horizon timepoints as
            # relevant)
            elif check_boundary_type(
                mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g],
                boundary_type="circular"
            ) and relevant_tmp == tmp:
                break
            # TODO: only allow the first horizon of a subproblem to have
            #  linked timepoints
            # In a 'linked' horizon setting, once we reach the first
            # timepoint of the horizon, we'll start adding the linked
            # timepoints until we reach the target min time
            elif check_if_boundary_type_and_first_timepoint(
                mod=mod, tmp=relevant_tmp, balancing_type=mod.balancing_type_project[g],
                boundary_type="linked"
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
                        hours_from_tmp += mod.hrs_in_linked_tmp[linked_tmp]
                        linked_tmp += -1
                # Break out from the outer while loop when done with the
                # linked timepoints
                break
            # Otherwise, we move on to the relevant timepoint's previous
            # timepoint and will add that timepoint's duration to
            # hours_from_tmp
            else:
                hours_from_tmp += \
                    mod.hrs_in_tmp[
                        mod.prev_tmp[
                            relevant_tmp, mod.balancing_type_project[g]
                        ]
                    ]
                relevant_tmp = mod.prev_tmp[
                    relevant_tmp, mod.balancing_type_project[g]]

    return relevant_tmps, relevant_linked_tmps


def update_dispatch_results_table(
     db, c, results_directory, scenario_id, subproblem, stage, results_file
):
    results = []
    with open(os.path.join(results_directory, results_file), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)

        header = next(reader)

        for row in reader:
            project = row[0]
            period = row[1]
            balancing_type = row[2]
            horizon = row[3]
            timepoint = row[4]
            timepoint_weight = row[5]
            n_hours_in_tmp = row[6]
            technology = row[7]
            load_zone = row[8]
            power = row[9]
            scheduled_curtailment_mw = get_column_row_value(
                header, "scheduled_curtailment_mw", row)
            subhourly_curtailment_mw = get_column_row_value(
                header,"subhourly_curtailment_mw", row)
            subhourly_energy_delivered_mw = get_column_row_value(
                header, "subhourly_energy_delivered_mw", row)
            total_curtailment_mw = get_column_row_value(
                header, "total_curtailment_mw", row)
            committed_mw = get_column_row_value(header, "committed_mw", row)
            committed_units = get_column_row_value(header, "committed_units", row)
            started_units = get_column_row_value(header, "started_units", row)
            stopped_units = get_column_row_value(header, "stopped_units", row)
            synced_units = get_column_row_value(header, "synced_units", row)
            auxiliary_consumption = get_column_row_value(
                header, "auxiliary_consumption_mw", row)
            gross_power = get_column_row_value(header, "gross_power_mw", row)

            results.append(
                (scheduled_curtailment_mw, subhourly_curtailment_mw,
                 subhourly_energy_delivered_mw, total_curtailment_mw,
                 committed_mw, committed_units, started_units,
                 stopped_units, synced_units, auxiliary_consumption,
                 gross_power,
                 scenario_id, project, period, subproblem, stage, timepoint)
            )

    # Update the results table with the module-specific results
    update_sql = """
        UPDATE results_project_dispatch
        SET scheduled_curtailment_mw = ?,
        subhourly_curtailment_mw = ?,
        subhourly_energy_delivered_mw = ?,
        total_curtailment_mw = ?,
        committed_mw = ?,
        committed_units = ?,
        started_units = ?,
        stopped_units = ?,
        synced_units = ?,
        auxiliary_consumption_mw = ?,
        gross_power_mw = ?
        WHERE scenario_id = ?
        AND project = ?
        AND period = ?
        AND subproblem_id = ?
        AND stage_id = ?
        AND timepoint = ?;
        """

    spin_on_database_lock(conn=db, cursor=c, sql=update_sql, data=results)


def get_optype_inputs_as_df(
        scenario_directory, subproblem, stage, op_type,
        required_columns, optional_columns
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
            scenario_directory, subproblem, stage, "inputs", "projects.tab"
        ),
        sep="\t", header=None, nrows=1
    ).values[0]

    # Get the columns for the optional params (it's OK if they don't exist)
    used_columns = [c for c in optional_columns if c in header]

    # Read in the appropriate columns for the operational type from
    # projects.tab
    df = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage),
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "operational_type"]
            + required_columns + used_columns

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

    for row in zip(df["project"],
                   df[column_name]):
        [prj, param_val] = row
        # Add to the param dictionary if a value is specified
        # Otherwise, we'll use the default value (or Pyomo will throw an
        # error if no default value)
        if param_val != ".":
            param_dict[prj] = cast_as_type(row[1])
        else:
            pass

    return param_dict


def get_optype_param_requirements(op_type):
    """
    :param op_type: string
    :return: two dictionaries of the required and optional projects.tab
        columns for the operational type with their types as values

    Read in the required and optional columns for an operational type. Make
    a dictionary for each with the types for each as values. We need the
    types to cast when loading into Pyomo.
    """

    df = pd.read_csv(
        os.path.join(os.path.dirname(__file__),
                     "opchar_param_requirements.csv"),
        sep=",",
        dtype=str
    )
    # df.set_index('ID').T.to_dict('list')
    required_columns = \
        df.loc[df[op_type] == "required"][["char", "type"]]
    required_columns_dict = dict(
        zip(required_columns["char"], required_columns["type"])
    )
    optional_columns = \
        df.loc[df[op_type] == "optional"][["char", "type"]]
    optional_columns_dict = dict(
        zip(optional_columns["char"], optional_columns["type"])
    )

    return required_columns_dict, optional_columns_dict


def get_types_dict():
    """
    :return: type name read in as string to type method mapping
    """
    return {
        "str": str,
        "float": float,
        "int": int
    }


def load_optype_module_specific_data(
        mod, data_portal, scenario_directory, subproblem, stage, op_type):
    """

    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param op_type:
    :return:
    """
    # String to method dicionary for types
    types_dict = get_types_dict()

    # Get the required and optional columns with their types
    required_columns_types, optional_columns_types = \
        get_optype_param_requirements(op_type=op_type)

    # Load in the inputs dataframe for the op type module
    op_type_df = get_optype_inputs_as_df(
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, op_type=op_type,
        required_columns=[r for r in required_columns_types.keys()],
        optional_columns=[o for o in optional_columns_types.keys()]
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
    for opt in optional_columns_types.keys():
        type_method = types_dict[optional_columns_types[opt]]
        try:
            data_portal.data()["{}_{}".format(op_type, opt)] = \
                get_param_dict(
                    df=op_type_df, column_name=opt, cast_as_type=type_method
                )
        # These columns are optional, so it's OK if we don't find them
        except KeyError:
            pass

    return op_type_projects


def write_tab_file_model_inputs(
        scenario_directory, subproblem, stage, fname, data,
        replace_nulls=False
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

    out_file = os.path.join(scenario_directory, str(subproblem), str(stage),
                            "inputs", fname)
    f_exists = os.path.isfile(out_file)
    append_mode = "a" if f_exists else "w"

    with open(out_file, append_mode, newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # If file doesn't exist, write header first
        if not f_exists:
            cols = [s[0] for s in data.description]
            writer.writerow(cols)

        for row in data:
            if replace_nulls:
                row = ["." if i is None else i for i in row]
            writer.writerow(row)


def load_var_profile_inputs(
        data_portal, scenario_directory, subproblem, stage, op_type):
    """
    Capacity factors vary by horizon and stage, so get inputs from appropriate
    directory.

    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param op_type:
    :return:
    """

    var_op_types = ["gen_var_must_take", "gen_var"]
    other_var_op_types = set(var_op_types) - set([op_type])
    assert op_type in var_op_types

    # Determine projects of this op_type and other var op_types
    # TODO: re-factor getting projects of certain op-type?
    prj_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "operational_type"]
    )
    op_type_prjs = prj_df[prj_df["operational_type"] == op_type]["project"]
    other_var_op_type_prjs = prj_df[prj_df["operational_type"].isin(
        other_var_op_types)]["project"]
    var_prjs = list(op_type_prjs) + list(other_var_op_type_prjs)

    # Read in the cap factors, filter for projects with the correct op_type
    # and convert to dictionary
    cf_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "inputs",
                     "variable_generator_profiles.tab"),
        sep="\t",
        usecols=["project", "timepoint", "cap_factor"],
        dtype={"cap_factor": float}
    )
    op_type_cf_df = cf_df[cf_df["project"].isin(op_type_prjs)]
    cap_factor = op_type_cf_df.set_index(["project", "timepoint"])[
        "cap_factor"].to_dict()

    # Throw warning if profile exists for a project not in projects.tab
    # (as 'gen_var' or 'gen_var_must_take')
    # TODO: this will throw warning twice, once for gen_var and once for
    #  gen_var_must_take
    # TODO: move this to validation instead?
    invalid_prjs = cf_df[~cf_df["project"].isin(var_prjs)]["project"].unique()
    for prj in invalid_prjs:
        warnings.warn(
            """WARNING: Profiles are specified for '{}' in 
            variable_generator_profiles.tab, but '{}' is not in 
            projects.tab.""".format(prj, prj)
        )

    # Load data
    data_portal.data()["{}_cap_factor".format(op_type)] = cap_factor


def get_var_profile_inputs_from_database(
        subscenarios, subproblem, stage, conn, op_type
):
    """
    Select only profiles of projects in the portfolio
    Select only profiles of projects with 'op_type' operational type
    Select only profiles for timepoints from the correct temporal scenario
    and the correct subproblem
    Select only timepoints on periods when the project is operational
    (periods with existing project capacity for existing projects or
    with costs specified for new projects)

    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :param op_type:
    :return: cursor object with query results
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage

    c = conn.cursor()
    variable_profiles = c.execute("""
        SELECT project, timepoint, cap_factor
        FROM (
        -- Select only projects from the relevant portfolio
        SELECT project
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {}
        ) as portfolio_tbl
        -- Of the projects in the portfolio, select only those that are in 
        -- this project_operational_chars_scenario_id and have 'op_type' as 
        -- their operational_type
        INNER JOIN
        (SELECT project, variable_generator_profile_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = '{}'
        ) AS op_char
        USING (project)
        -- Cross join to the timepoints in the relevant 
        -- temporal_scenario_id, subproblem_id, and stage_id
        -- Get the period since we'll need that to get only the operational 
        -- timepoints for a project via an INNER JOIN below
        CROSS JOIN
        (SELECT stage_id, timepoint, period
        FROM inputs_temporal_timepoints
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {}
        ) as tmps_tbl
        -- Now that we have the relevant projects and timepoints, get the 
        -- respective cap_factor (and no others) from 
        -- inputs_project_variable_generator_profiles through a LEFT OUTER JOIN
        LEFT OUTER JOIN
        inputs_project_variable_generator_profiles
        USING (variable_generator_profile_scenario_id, project, 
        stage_id, timepoint)
        -- We also only want timepoints in periods when the project actually 
        -- exists, so we figure out the operational periods for each of the  
        -- projects below and INNER JOIN to that
        INNER JOIN
            (SELECT project, period
            FROM (
                -- Get the operational periods for each 'existing' and 
                -- 'new' project
                SELECT project, period
                FROM inputs_project_specified_capacity
                WHERE project_specified_capacity_scenario_id = {}
                UNION
                SELECT project, vintage AS period
                FROM inputs_project_new_cost
                WHERE project_new_cost_scenario_id = {}
                ) as all_operational_project_periods
            -- Only use the periods in temporal_scenario_id via an INNER JOIN
            INNER JOIN (
                SELECT period
                FROM inputs_temporal_periods
                WHERE temporal_scenario_id = {}
                ) as relevant_periods_tbl
            USING (period)
            ) as relevant_op_periods_tbl
        USING (project, period);
        """.format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            op_type,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage,
            subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID
        )
    )

    return variable_profiles


def load_hydro_opchars(data_portal, scenario_directory, subproblem,
                       stage, op_type, projects):
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

    project_horizons = list()
    avg = dict()
    min = dict()
    max = dict()

    prj_hor_opchar_df = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                     "hydro_conventional_horizon_params.tab"),
        sep="\t",
        usecols=["project", "horizon", "average_power_fraction",
                 "min_power_fraction", "max_power_fraction"]
    )
    for row in zip(prj_hor_opchar_df["project"],
                   prj_hor_opchar_df["horizon"],
                   prj_hor_opchar_df["average_power_fraction"],
                   prj_hor_opchar_df["min_power_fraction"],
                   prj_hor_opchar_df["max_power_fraction"]):
        if row[0] in projects:
            project_horizons.append((row[0], row[1]))
            avg[(row[0], row[1])] = float(row[2])
            min[(row[0], row[1])] = float(row[3])
            max[(row[0], row[1])] = float(row[4])
        else:
            pass

    # Load data
    data_portal.data()["{}_OPR_HRZS".format(op_type.upper())] = \
        {None: project_horizons}
    data_portal.data()["{}_average_power_fraction".format(op_type)] = avg
    data_portal.data()["{}_min_power_fraction".format(op_type)] = min
    data_portal.data()["{}_max_power_fraction".format(op_type)] = max


def get_hydro_inputs_from_database(
        subscenarios, subproblem, stage, conn, op_type
):
    """
    Get the hydro-specific operational characteristics from the
    inputs_project_hydro_operational_chars input table.

    Select only budgets/min/max of projects in the portfolio
    Select only budgets/min/max of projects with 'op_type'
    Select only budgets/min/max for horizons from the correct temporal
    scenario and subproblem
    Select only horizons on periods when the project is operational
    (periods with existing project capacity for existing projects or
    with costs specified for new projects)

    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :param op_type:
    :return: cursor object with query results
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage

    c = conn.cursor()
    # TODO: should we ensure that the project balancing type and the horizon
    #  length type match (e.g. by joining on them being equal here)
    hydro_chars = c.execute(
        """SELECT project, horizon, average_power_fraction, min_power_fraction,
        max_power_fraction
        FROM (
            -- Select only projects from the relevant portfolio
            SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}
        ) as portfolio_tbl
        -- Of the projects in the portfolio, select only those that are in 
        -- this project_operational_chars_scenario_id and have 'op_type' as 
        -- their operational_type
        INNER JOIN
            (SELECT project, hydro_operational_chars_scenario_id
            FROM inputs_project_operational_chars
            WHERE project_operational_chars_scenario_id = {}
            AND operational_type = '{}') AS op_char
        USING (project)
        -- Cross join to the horizons in the relevant 
        -- temporal_scenario_id, and subproblem_id
        CROSS JOIN
            (SELECT horizon
            FROM inputs_temporal_horizons
            WHERE temporal_scenario_id = {}
            AND subproblem_id = {})
        -- Now that we have the relevant projects and horizons, get the 
        -- respective hydro opchars (and no others) from 
        -- inputs_project_hydro_operational_chars through a LEFT OUTER JOIN
        LEFT OUTER JOIN
            inputs_project_hydro_operational_chars
        USING (hydro_operational_chars_scenario_id, project, horizon)
        -- We also only want horizons in periods when the project actually 
        -- exists, so we figure out the operational periods for each of the  
        -- projects below and INNER JOIN to that
        INNER JOIN
            -- Get the operational periods for each 'existing' and 
            -- 'new' project
            (SELECT project, period
            FROM (
                SELECT project, period
                FROM inputs_project_specified_capacity
                WHERE project_specified_capacity_scenario_id = {}
                UNION
                SELECT project, vintage AS period
                FROM inputs_project_new_cost                
                WHERE project_new_cost_scenario_id = {}
            ) as all_operational_project_periods
            -- Only use the periods in temporal_scenario_id via an INNER JOIN
            INNER JOIN
                (SELECT period
                FROM inputs_temporal_periods
                WHERE temporal_scenario_id = {}
                ) as relevant_periods_tbl
            USING (period)
            ) as relevant_op_periods_tbl
        using (project, period);
        """.format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            op_type,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID,

        )
    )

    return hydro_chars


def load_startup_chars(data_portal, scenario_directory, subproblem,
                       stage, op_type, projects):
    """

    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param op_type:
    :param projects:`
    :return:
    """

    # TODO: change the name of the startup_cost_per_mw,
    #  gen_commit_bin_startup_plus_ramp_up_rate, and
    #  gen_commit_bin_down_time_cutoff_hours to include "by_ll" or something
    #  like that, and re-add these same params for a simple treatment to
    #  gen_commit_bin and gen_commit_lin
    # Startup characteristics
    df = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage),
                     "inputs", "startup_chars.tab"),
        sep="\t"
    )

    # Note: the rank function requires at least one numeric input in the
    # down_time_cutoff_hours column (can't be all NULL/None).
    if len(df) > 0:
        df["startup_type_id"] = df.groupby("project")[
            "down_time_cutoff_hours"].rank()

    startup_ramp_projects = set()
    startup_ramp_projects_types = list()
    down_time_cutoff_hours_dict = dict()
    startup_plus_ramp_up_rate_dict = dict()
    startup_cost_dict = dict()

    for i, row in df.iterrows():
        project = row["project"]
        startup_type_id = row["startup_type_id"]
        down_time_cutoff_hours = row["down_time_cutoff_hours"]
        startup_plus_ramp_up_rate = row["startup_plus_ramp_up_rate"]
        startup_cost = row["startup_cost_per_mw"]

        if down_time_cutoff_hours != "." and startup_plus_ramp_up_rate != "." \
                and project in projects:
            startup_ramp_projects.add(project)
            startup_ramp_projects_types.append((project, startup_type_id))
            down_time_cutoff_hours_dict[(project, startup_type_id)] = \
                float(down_time_cutoff_hours)
            startup_plus_ramp_up_rate_dict[(project, startup_type_id)] = \
                float(startup_plus_ramp_up_rate)
            startup_cost_dict[(project, startup_type_id)] = \
                float(startup_cost)

    if startup_ramp_projects:
        data_portal.data()["{}_STR_RMP_PRJS".format(op_type.upper())] = \
            {None: startup_ramp_projects}
        data_portal.data()["{}_STR_RMP_PRJS_TYPES".format(op_type.upper())] = \
            {None: startup_ramp_projects_types}
        data_portal.data()["{}_down_time_cutoff_hours".format(op_type)] = \
            down_time_cutoff_hours_dict
        data_portal.data()["{}_startup_plus_ramp_up_rate".format(op_type)] = \
            startup_plus_ramp_up_rate_dict
        data_portal.data()["{}_startup_cost_per_mw".format(op_type)] = \
            startup_cost_dict


def get_startup_chars_inputs_from_database(
        subscenarios, subproblem, stage, conn, op_type):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :param op_type:
    :return: cursor object with query results
    """

    c = conn.cursor()
    # TODO: should we align this better with heat rates (queries and input
    #  validations are slightly different).
    startup_chars = c.execute(
        """
        SELECT project, 
        down_time_cutoff_hours, startup_plus_ramp_up_rate, startup_cost_per_mw
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, startup_chars_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = '{}') AS op_char
        USING(project)
        INNER JOIN
        inputs_project_startup_chars
        USING(project, startup_chars_scenario_id)
        WHERE project_portfolio_scenario_id = {}
        AND startup_chars_scenario_id is not Null
        """.format(subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                   op_type,
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID)
    )

    return startup_chars


def check_for_tmps_to_link(
    scenario_directory, subproblem, stage
):
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
            os.path.join(scenario_directory, "linked_subproblems_map.csv"),
            sep=","
        )

        # Figure out which timepoints we'll be linking to the next subproblem
        # Stages must match in the linked subproblems
        # These are subset of all TMPS in the current subproblem
        tmps_to_link_df = map_df.loc[
            (map_df["subproblem"] == int(subproblem)) &
            (map_df["stage"] == (1 if stage == "" else int(stage)))
            ]
        tmps_to_link = tmps_to_link_df["timepoint"].tolist()
        tmp_linked_tmp_dict = \
            tmps_to_link_df.set_index("timepoint")["linked_timepoint"]\
            .to_dict()

        return tmps_to_link, tmp_linked_tmp_dict
    except FileNotFoundError:
        return [], {}
