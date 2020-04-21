#!/usr/bin/env python
# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
import pandas as pd

from db.common_functions import spin_on_database_lock
from gridpath.project.common_functions import \
    check_if_first_timepoint, get_column_row_value, check_boundary_type


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
    print(g, tmp, min_time)

    # The first possible relevant timepoint is the current timepoint
    relevant_tmps = [tmp]
    relevant_linked_tmps = []
    # The first possible linked timepoint is 0
    linked_tmp = 0

    # If we have already reached the first timepoint of a horizon in a
    # linear or linked horizon setting, we'll either just pass (linear
    # horizon) or move on to the linked timepoints (linked horizon) without
    # looking for a previous timepoint
    if check_if_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        if check_boundary_type(
            mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g],
            boundary_type="linear"
        ):
            pass  # no more relevant timepoints, keep list limited to *t*
        if check_boundary_type(
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
                # the linked timepoints loop and set the
                # done_with_linked_tmps flag to True; otherwise,
                # move on to the next linked timepoint
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
            if mod.boundary[
                mod.balancing_type_project[g],
                mod.horizon[tmp, mod.balancing_type_project[g]]
            ] \
                    == "linear" \
                    and relevant_tmp == \
                    mod.first_hrz_tmp[
                        mod.balancing_type_project[g],
                        mod.horizon[tmp, mod.balancing_type_project[g]]
                    ]:
                break
            # In a 'circular' horizon setting, once we reach timepoint *t*,
            # we break out of the loop since there are no more timepoints to
            # consider (we have already added all horizon timepoints as
            # relevant)
            elif mod.boundary[
                mod.balancing_type_project[g],
                mod.horizon[tmp, mod.balancing_type_project[g]]
            ] \
                    == "circular" \
                    and relevant_tmp == tmp:
                break
            # TODO: only allow the first horizon of a subproblem to have
            #  linked timepoints
            # In a 'linked' horizon setting, once we reach the first
            # timepoint of the horizon, we'll start adding the linked
            # timepoints until we reach the target min time
            elif mod.boundary[
                mod.balancing_type_project[g],
                mod.horizon[tmp, mod.balancing_type_project[g]]
            ] \
                    == "linked" \
                    and relevant_tmp == \
                    mod.first_hrz_tmp[
                        mod.balancing_type_project[g],
                        mod.horizon[tmp, mod.balancing_type_project[g]]
                    ]:
                # Add the first linked timepoint's duration to hours_from_tmp
                hours_from_tmp += mod.hrs_in_linked_tmp[linked_tmp]
                # If we haven't exceeded the min time yet, the first linked
                # timepoint is relevant, so we'll add it and move on to the
                # next one
                while hours_from_tmp < min_time:
                    relevant_linked_tmps.append(linked_tmp)
                    # If this is the furthest linked timepoint, break out of
                    # the linked timepoints loop and set the
                    # done_with_linked_tmps flag to True; otherwise,
                    # move on to the next linked timepoint
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
        sep=","
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
