#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Various input validation functions used in other modules
"""

import datetime
import numpy as np
import pandas as pd

from db.common_functions import spin_on_database_lock


def _get_idx_col(df):
    if "project" in df.columns:
        return "project"
    elif "transmission_line" in df.columns:
        return "transmission_line"
    else:
        raise IOError(
            "df should contain 'project' or 'transmission_line' column"
        )


def write_validation_to_database(conn, scenario_id, subproblem_id, stage_id,
                                 gridpath_module, db_table, severity, errors):
    """
    Write all validations in the `errors` list and the associated meta-data
    (scenario_id, subproblem, stage, etc.) to the status_validation
    database table.

    :param conn: The database connection
    :param scenario_id: The scenario ID of the scenario that is being validated
    :param subproblem_id: The active subproblem ID that is being validated
    :param stage_id: The active stage ID that is being validated
    :param gridpath_module: The gridpath_module that performed the validation
    :param db_table: The database table that contains the validation errors
    :param severity: The severity of the validation error
    :param errors: The list of validation errors to be written to database,
    with each error a string describing the issue.
    :return:
    """

    # If there are no validation errors to write, simply exit here
    if not errors:
        return

    # add timestamp (ISO8601 strings, so truncate to ms)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    rows = [(scenario_id, subproblem_id, stage_id, gridpath_module, db_table,
             severity, error, timestamp) for error in errors]
    c = conn.cursor()
    sql = """
    INSERT INTO status_validation
    (scenario_id, subproblem_id, stage_id, 
    gridpath_module, db_table, severity, description, time_stamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """
    spin_on_database_lock(conn, c, sql, rows)
    c.close()


def get_expected_dtypes(conn, tables):
    """
    Goes through each listed table and creates a dictionary that maps each
    column name to an expected datatype. If the tables have duplicate column
    names, the last table will define the expected datatype (generally datatypes
    are the same for columns in different tables with the same name so this
    shouldn't be an issue).
    :param conn: database connection
    :param tables: list of database tables for which to collect datatypes
    :return: dictionary with table columns and expected datatype category
        ('numeric' or 'string')
    """

    # Map SQLITE types to either numeric or string
    # Based on '3.1 Determination of column affinity':
    # https://www.sqlite.org/datatype3.html
    numeric_types = ["BOOLEAN", "DATE", "DATETIME", "DECIMAL", "DOUB", "FLOA",
                     "INT", "NUMERIC", "REAL", "TIME"]
    string_types = ["BLOB", "CHAR", "CLOB", "STRING", "TEXT"]

    def get_type_category(detailed_type):
        if any(numeric_type in detailed_type for numeric_type in numeric_types):
            return "numeric"
        elif any(string_type in detailed_type for string_type in string_types):
            return "string"
        else:
            raise ValueError("Encountered unknown SQLite type: type {}"
                             .format(detailed_type))

    expected_dtypes = {}
    for table in tables:
        # Get the expected datatypes from the table info (pragma)
        table_info = conn.execute("""PRAGMA table_info({})""".format(table))
        df = pd.DataFrame(
            data=table_info.fetchall(),
            columns=[s[0] for s in table_info.description]
        )

        df["type_category"] = df["type"].map(get_type_category)
        dtypes_dict = dict(zip(df.name, df.type_category))
        expected_dtypes.update(dtypes_dict)

    return expected_dtypes


def get_projects_by_reserve(subscenarios, conn):
    """
    Get a list of projects that can provide reserves for each applicable
    reserve type. Whether a project can provide a certain reserve type is
    dependent on whether the project has a reserve zone specified for that
    reserve type.

    :param subscenarios:
    :param conn:
    :return: result, dictionary of list of projects by reserve type
    """

    result = {}
    c = conn.cursor()
    reserves = [r[0] for r in c.execute(
        """SELECT reserve_type FROM mod_reserve_types"""
    ).fetchall()]

    for reserve in reserves:
        # Get set of projects with a reserve BA specified
        table = "inputs_project_" + reserve + "_bas"
        ba_column = reserve + "_ba"
        ba_id = reserve + "_ba_scenario_id"
        project_ba_id = "project_" + reserve + "_ba_scenario_id"

        # If the subscenario_ids are specified, get the projects
        if getattr(subscenarios, ba_id.upper()) and \
                getattr(subscenarios, project_ba_id.upper()):
            c = conn.cursor()
            prjs_w_ba = c.execute(
                """SELECT project
                FROM {}
                WHERE {} IS NOT NULL
                AND {} = {}
                """.format(
                    table,
                    ba_column,
                    project_ba_id, getattr(subscenarios, project_ba_id.upper())
                )
            )

            result[reserve] = [p[0] for p in prjs_w_ba.fetchall()]

    return result


# TODO: further generalize this by joining on opchars so "col" can also be
#  any column in opchars, e.g. so we can select fuel projects for instance?
def get_projects(conn, subscenarios, col, col_value):
    """
    Get projects for which the column value of "col" is equal to "col_value".
    E.g. "get the projects of operational type gen_commit_lin".
    :param conn: database connection
    :param subscenarios: Subscenarios class objects
    :param col: str
    :param col_value: str
    :return: List of projects that meet the criteria
    """

    c = conn.cursor()
    projects = c.execute(
        """SELECT project
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {}
        AND {} = '{}';""".format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            col,
            col_value
        )
    )
    projects = [p[0] for p in projects]  # convert to list
    return projects


def validate_dtypes(df, expected_dtypes):
    """
    Checks whether the inputs for a DataFrame are in the expected datatype.
    Helper function for input validation.
    :param df: DataFrame for which to check data types
    :param expected_dtypes: dictionary with expected datatype ("numeric" or
        "string" for each column.
    :return: List of error messages for each column with invalid datatypes.
        Error message specifies the column and the expected data type.
        List of columns with erroneous data types.
    """

    result = []
    columns = []
    for column in df.columns:
        if pd.isna(df[column]).all():
            pass
        elif expected_dtypes[column] == "numeric" \
                and not pd.api.types.is_numeric_dtype(df[column]):
            result.append(
                "Invalid data type for column '{}'; expected numeric".format(
                    column
                )
            )
            columns.append(column)
        elif expected_dtypes[column] == "string" \
                and not pd.api.types.is_string_dtype(df[column]):
            result.append(
                 "Invalid data type for column '{}'; expected string".format(
                     column
                 )
            )
            columns.append(column)

    # Alternative that avoids pd.api.types:
    # numeric_columns = [k for k, v in expected_dtypes.items() if v == "numeric"]
    # string_columns = [k for k, v in expected_dtypes.items() if v == "string"]
    # is_number = np.vectorize(lambda x: np.issubdtype(x, np.number))
    # numeric_bool = is_number(df[numeric_columns].dtypes)
    # any_bad_dtypes = not numeric_bool.all()
    # if any_bad_dtypes:
    #     bad_columns = numeric_columns[np.invert(numeric_bool)]

    return result, columns


def validate_signs(df, columns, sign):
    """
    Checks whether the selected columns of a DataFrame have the correct sign,
    e.g. whether all entries are positive numbers.
    Helper function for input validation.
    :param df: DataFrame for which to check signs. Must have a 'project'
        or 'transmission_line' column, and 'columns' param must be a subset
        of the columns in df
    :param columns: list with columns that are expected to be non-negative
    :param sign: str, specifies the expected sign for the columns. Option are
        'positive', 'nonnegative', 'negative', 'nonpositive', 'pctfraction',
        'pctfraction_nonzero'.
    :return: List of error messages for each column with invalid inputs.
        Error message specifies the column and the expected sign.
    """
    assert sign in ["positive", "nonnegative", "negative", "nonpositive",
                    "pctfraction", "pctfraction_nonzero"]

    idx_col = _get_idx_col(df)
    result = []
    for column in columns:
        if sign == "positive":
            invalids = (df[column] <= 0)
            expected = "> 0"
        elif sign == "nonnegative":
            invalids = (df[column] < 0)
            expected = ">= 0"
        elif sign == "negative":
            invalids = (df[column] >= 0)
            expected = "< 0"
        elif sign == "nonpositive":
            invalids = (df[column] > 0)
            expected = "<= 0"
        elif sign == "pctfraction":
            invalids = (df[column] < 0) | (df[column] > 1)
            expected = "within [0, 1]"
        elif sign == "pctfraction_nonzero":
            invalids = (df[column] <= 0) | (df[column] > 1)
            expected = "within (0, 1]"

        if invalids.any():
            bad_idxs = df[idx_col][invalids].values
            print_bad_idxs = ", ".join(bad_idxs)
            result.append(
                "{}(s) '{}': Expected '{}' {}"
                .format(idx_col, print_bad_idxs, column, expected)
            )

    return result


def validate_req_cols(df, columns, required, category):
    """
    Checks whether the required columns of a DataFrame are not None/NA or
    whether the incompatible columns are None/NA. If required columns are
    None/NA, or if incompatible columns are not None/NA, an error message
    is returned.
    Helper function for input validation.
    :param df: DataFrame for which to check columns. Must have a "project" or
        "transmission_line" column, and columns param must be a subset of
        the columns in df
    :param columns: list of columns to check
    :param required: Boolean, whether the listed columns are required or
        incompatible
    :param category: project category (operational_type, capacity_type, ...)
        for which we're doing the input validation
    :return: List of error messages for each column with invalid inputs.
        Error message specifies the column.
    """
    idx_col = _get_idx_col(df)
    result = []
    for column in columns:
        if required:
            invalids = pd.isna(df[column])
            error_str = "should have inputs for"
        else:
            invalids = pd.notna(df[column])
            error_str = "should not have inputs for"
        if invalids.any():
            bad_idxs = df[idx_col][invalids].values
            print_bad_idxs = ", ".join(bad_idxs)
            result.append(
                "{}(s) '{}'; {} {} '{}'"
                .format(idx_col, print_bad_idxs, category, error_str, column)
                 )

    return result


def validate_columns(df, columns, valids=[], invalids=[]):
    """
    Check that the specified column(s) only have entries within the list of
    valid entries and no entries within the list of invalids. If not, an error
    message is returned, specifying which column indexes are in violation.

    Examples:
     - check that a DataFrame with project and fuels only has valid fuels
       specified for each project.
     - check that a DataFrame with project, cap-type, and op-type does not have
       any incompatible combinations of cap-type and op-type.

    Note: this function differs from validate_idxs() in that we are checking
    data column(s) (e.g. op-type), not an index (e.g. project). validate_idxs()
    also checks that entries contain a set of required entries, which is
    different from checking that all entries are within a set of valid entries.

    :param df: DataFrame for which to check columns. Must have a "project"
        or "transmission_line" column, and contain the specified column(s).
    :param columns: str or list of str, columns to check
    :param valids: list of valid entries, defaults to []. If multiple columns
        specified, should be list of tuples.
    :param invalids: list of valid entries, defaults to []. If multiple columns
        specified, should be list of tuples.
    :return: List of error messages for each entry with invalid inputs.
    """
    idx_col = _get_idx_col(df)
    results = []

    # If checking for combination of columns, combine into tuple for lookup
    if isinstance(columns, list):
        df["lookup"] = list(zip(*[df[c] for c in columns]))
    elif isinstance(columns, str):
        df["lookup"] = df[columns]
    else:
        raise ValueError("Columns should be string or list of strings")

    # Entries are invalid if they are either not in the provided list of valid
    # entries (if any), or if they are in the provided list of invalid entries
    falses = pd.Series([False] * len(df))
    valids_mask = ~df["lookup"].isin(valids) if valids else falses
    invalids_mask = df["lookup"].isin(invalids) if invalids else falses
    mask = valids_mask | invalids_mask

    if mask.any():
        bad_idxs = df[idx_col][mask].values
        print_bad_idxs = ", ".join(bad_idxs)
        print_valid = " Valid options are {}.".format(valids) if valids else ""
        print_invalid = " Invalid options are {}.".format(invalids) if invalids else ""
        end_msg = print_valid + print_invalid
        results.append(
            "{}(s) '{}': Invalid entry for {}.{}"
            .format(idx_col, print_bad_idxs, columns, end_msg)
        )
    return results


# TODO: could also feed in df instead of actual_idxs, and derive label?
def validate_idxs(actual_idxs, req_idxs=[], invalid_idxs=[],
                  idx_label="project", msg=""):
    """
    Check that actual list of indexes contains all required indexes and none
    of the invalid indexes. If any required indexes are missing, or any invalid
    indexes are present, return an error message specifying the missing or
    invalid index, its label, and an optional clarifying message. The indexes
    can be lists of anything, but generally a list of strings or tuples.

    Example: check that the list of projects with binary build size inputs
    (actual_idxs) contains all binary new build projects (required_idxs)

    :param actual_idxs: list, the indexes to check
    :param req_idxs: list, the required indexes, defaults to empty list
    :param invalid_idxs: list, the invalid indexes, defaults to empty list
    :param idx_label: str, the index label, defaults to "project"
    :param msg: str, optional error message clarification.
    :return:
    """

    results = []

    missing_idxs = sorted(list(set(req_idxs) - set(actual_idxs)))
    if len(missing_idxs) > 0:
        results.append(
            "Missing required inputs for {}: {}. {}"
            .format(idx_label, missing_idxs, msg)
        )

    invalids = sorted(list(set(actual_idxs) & set(invalid_idxs)))
    if len(invalids) > 0:
        results.append(
            "Invalid inputs for {}: {}. {}"
            .format(idx_label, invalids, msg)
        )

    return results


def validate_single_input(df, idx_col="project", msg=""):
    """
    Check whether there is only 1 input per index.

    Example: check that there is only 1 load point per project in the heat
    rate inputs DataFrame.

    :param df: DataFrame to check. Must have column idx_col.
    :param idx_col: str, the index column, defaults to "project".
    :param msg: str, optional error message clarification.
    :return: List of error messages for each index with invalid inputs.
    """

    results = []

    n_inputs = df.groupby([idx_col]).size()
    invalids = (n_inputs > 1)
    if invalids.any():
        bad_idxs = invalids.index[invalids]
        print_bad_idxs = ", ".join(bad_idxs)
        results.append(
            "{}(s) '{}': Too many inputs! Maximum 1 input per {}. {}"
            .format(idx_col, print_bad_idxs, idx_col, msg)
        )

    return results


def validate_fuel_vs_heat_rates(hr_df):
    """
    Make sure projects with fuel have a heat rate scenario specified.
    Conversely, if no fuel is specified, make sure there is no heat rate
    scenario specified.
    :param hr_df:
    :return:
    """
    results = []

    hr_curve_mask = pd.notna(hr_df["heat_rate_curves_scenario_id"])
    fuel_mask = pd.notna(hr_df["fuel"])

    invalids = fuel_mask & ~hr_curve_mask
    if invalids.any():
        bad_projects = hr_df["project"][invalids]
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': Missing heat_rate_curves_scenario_id"
            .format(print_bad_projects)
        )

    invalids = ~fuel_mask & hr_curve_mask
    if invalids.any():
        bad_projects = pd.unique(hr_df["project"][invalids])
        print_bad_projects = ", ".join(bad_projects)
        results.append(
             "Project(s) '{}': No fuel specified so no heat rate expected"
             .format(print_bad_projects)
        )

    return results


def validate_heat_rate_curves(hr_df):
    """
    1. Check that specified heat rate scenarios actually have inputs in the
       heat rate curves table
    2. Check that specified heat rate curves inputs are valid:
        - strictly increasing load points
        - increasing total fuel burn
        - convex fuel burn curve
    :param hr_df:
    :return:
    """
    results = []

    fuel_mask = pd.notna(hr_df["fuel"])
    hr_curve_mask = pd.notna(hr_df["heat_rate_curves_scenario_id"])
    load_point_mask = pd.notna(hr_df["load_point_fraction"])

    # Check for missing inputs in heat rates curves table
    invalids = hr_curve_mask & ~load_point_mask
    if invalids.any():
        bad_projects = hr_df["project"][invalids]
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': Expected at least one load point"
            .format(print_bad_projects)
        )

    # Check that each project has convex heat rates etc.
    relevant_mask = fuel_mask & load_point_mask
    hr_df = hr_df[relevant_mask]
    for project in hr_df["project"].unique():
        for period in hr_df[hr_df["project"] == project]["period"].unique():
            # read in the power setpoints and average heat rates
            hr_slice = hr_df[(hr_df["project"] == project)
                             & (hr_df["period"] == period)]
            hr_slice = hr_slice.sort_values(by=["load_point_fraction"])
            load_points = hr_slice["load_point_fraction"].values
            heat_rates = hr_slice["average_heat_rate_mmbtu_per_mwh"].values

            if len(load_points) > 1:
                incr_loads = np.diff(load_points)

                if np.any(incr_loads == 0):
                    # note: primary key should already prohibit this
                    results.append(
                        "Project(s) '{}': load points can not be identical"
                        .format(project)
                    )

                else:
                    fuel_burn = load_points * heat_rates
                    incr_fuel_burn = np.diff(fuel_burn)
                    slopes = incr_fuel_burn / incr_loads

                    if np.any(incr_fuel_burn <= 0):
                        results.append(
                            "Project(s) '{}': Total fuel burn should increase "
                            "with increasing load"
                            .format(project)
                        )
                    if np.any(np.diff(slopes) <= 0):
                        results.append(
                            "Project(s) '{}': Fuel burn should be convex, "
                            "i.e. marginal heat rate should increase with "
                            "increading load"
                            .format(project)
                        )

    return results


def validate_vom_curves(vom_df):
    """
    1. Check that specified variable O&M scenarios actually have inputs in the
       variable O&M curves table
    2. Check that specified variable O&M curves inputs are valid:
        - strictly increasing load points
        - increasing total variable O&M cost
        - convex variable O&M curve
    :param vom_df:
    :return:
    """
    results = []

    vom_curve_mask = pd.notna(vom_df["variable_om_curves_scenario_id"])
    load_point_mask = pd.notna(vom_df["load_point_fraction"])

    # Check for missing inputs in heat rates curves table
    invalids = vom_curve_mask & ~load_point_mask
    if invalids.any():
        bad_projects = vom_df["project"][invalids]
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': Expected at least one load point"
            .format(print_bad_projects)
        )

    # Check that each project has convex variable O&M rates etc.
    vom_df = vom_df[load_point_mask]
    for project in vom_df["project"].unique():
        for period in vom_df[vom_df["project"] == project]["period"].unique():
            # read in the power setpoints and average variable O&M
            vom_slice = vom_df[(vom_df["project"] == project)
                               & (vom_df["period"] == period)]
            vom_slice = vom_slice.sort_values(by=["load_point_fraction"])
            load_points = vom_slice["load_point_fraction"].values
            vom = vom_slice["average_variable_om_cost_per_mwh"].values

            if len(load_points) > 1:
                incr_loads = np.diff(load_points)

                if np.any(incr_loads == 0):
                    # note: primary key should already prohibit this
                    results.append(
                        "Project(s) '{}': load points can not be identical"
                        .format(project)
                    )

                else:
                    vom_cost = load_points * vom
                    incr_vom_cost = np.diff(vom_cost)
                    slopes = incr_vom_cost / incr_loads

                    if np.any(incr_vom_cost <= 0):
                        results.append(
                            "Project(s) '{}': Total variable O&M cost should "
                            "increase with increasing load"
                            .format(project)
                        )
                    if np.any(np.diff(slopes) <= 0):
                        results.append(
                            "Project(s) '{}': Variable O&M cost should be "
                            "convex, i.e. variable O&M rate should increase "
                            "with increasing load"
                            .format(project)
                        )

    return results


def validate_startup_shutdown_rate_inputs(prj_df, su_df, hrs_in_tmp):
    """
    TODO: additional checks:
     - check for excessively slow startup ramps which would wrap around the
       horizon and disallow any startups
     - Check that non lin/bin commit types have no shutdown trajectories
       --> ramp should be large enough (but check shouldn't be here!)
     - could also add type checking here (resp. int and float?)
     - Check that non lin/bin commit types have no shutdown trajectories
       --> ramp should be large enough (but check shouldn't be here!)
     - Check that there are only gen_lin and gen_bin types in startup_chars
       (depends on what happens to cap commit module); would have to check
       this in cross module validation

    :param prj_df: DataFrame with project_chars (see projects.tab)
    :param su_df: DataFrame with startup_chars (project, cutoff, ramp rate)
    :param hrs_in_tmp:
    :return:
    """

    results = []

    if len(su_df) == 0:
        return results

    if pd.isna(su_df["down_time_cutoff_hours"]).any():
        return (["Down_time_cutoff_hours should be specified for each "
                 "project listed in the startup_chars table. If the unit is"
                 "has no minimum down time and is quick-start, either remove "
                 "the project from the table or set the cutoff to zero."])
    # 0. Prepare DataFrame

    # Split su_df in df with hottest starts and df with coldest starts
    su_df_hot = su_df.groupby("project").apply(
        lambda grp: grp.nsmallest(1, columns=["down_time_cutoff_hours"])
    ).reset_index(drop=True).rename(
        columns={"down_time_cutoff_hours": "down_time_cutoff_hours_hot",
                 "startup_plus_ramp_up_rate": "startup_plus_ramp_up_rate_hot"})
    su_df_cold = su_df.groupby("project").apply(
        lambda grp: grp.nlargest(1, columns=["down_time_cutoff_hours"])
    ).reset_index(drop=True).rename(
        columns={"down_time_cutoff_hours": "down_time_cutoff_hours_cold",
                 "startup_plus_ramp_up_rate":
                     "startup_plus_ramp_up_rate_cold"})

    # Calculate number of startup types and null values for each project
    su_count = su_df.groupby("project").size().reset_index(name="n_types")
    su_count_series = su_count.set_index("project")["n_types"]  # DF to Series
    cutoff_na_count = su_df.groupby("project")["down_time_cutoff_hours"].apply(
        lambda grp: grp.isnull().sum())  # pd.Series (index = project)
    ramp_na_count = su_df.groupby("project")[
        "startup_plus_ramp_up_rate"].apply(
        lambda grp: grp.isnull().sum())  # pd.Series (index = project)

    # Join DataFrames (left join since not all projects have startup chars,
    # but we still want to operational chars such as shutdown ramp rates)
    prj_df = prj_df.merge(su_df_hot, on="project", how="left")
    prj_df = prj_df.merge(su_df_cold, on="project", how="left")
    prj_df = prj_df.merge(su_count, on="project", how="left")
    # TODO: consider not doing left join so we skip any projects that are not
    #  in startup chars? (but then you can't check shutdown_chars alone)

    # Add missing columns and populate with defaults
    if "min_down_time_hours" not in prj_df.columns:
        prj_df["min_down_time_hours"] = 0
    # if "startup_plus_ramp_up_rate" not in prj_df.columns:
    #     prj_df["startup_plus_ramp_up_rate"] = 1
    if "shutdown_plus_ramp_down_rate" not in prj_df.columns:
        prj_df["shutdown_plus_ramp_down_rate"] = 1
    if "startup_fuel_mmbtu_per_mw" not in prj_df.columns:
        prj_df["startup_fuel_mmbtu_per_mw"] = 0

    # Replace any NA/None with defaults
    prj_df.fillna(
        value={"min_down_time_hours": 0,
               "down_time_cutoff_hours_hot": 0,
               "down_time_cutoff_hours_cold": 0,
               "startup_plus_ramp_up_rate_hot": 1,
               "startup_plus_ramp_up_rate_cold": 1,
               "n_types": 0,
               "shutdown_plus_ramp_down_rate": 1,
               "startup_fuel_mmbtu_per_mw": 0},
        inplace=True
    )

    # Calculate (coldest) startup and shutdown duration
    prj_df["startup_duration"] = prj_df["min_stable_level_fraction"] \
                             / prj_df["startup_plus_ramp_up_rate_cold"] / 60
    prj_df["shutdown_duration"] = prj_df["min_stable_level_fraction"] \
                              / prj_df["shutdown_plus_ramp_down_rate"] / 60
    prj_df["startup_plus_shutdown_duration"] = \
        prj_df["startup_duration"] + prj_df["shutdown_duration"]

    # 1. Calculate Masks (True/False Arrays)
    trajectories_fit_mask = (prj_df["startup_plus_shutdown_duration"]
                             > prj_df["min_down_time_hours"])
    down_time_mask = prj_df["min_down_time_hours"] > 0
    ramp_rate_mask = ((prj_df["startup_plus_ramp_up_rate_cold"] < 1) |
                      (prj_df["startup_plus_ramp_up_rate_hot"] < 1) |
                      (prj_df["shutdown_plus_ramp_down_rate"] < 1))
    startup_fuel_mask = prj_df["startup_fuel_mmbtu_per_mw"] > 0
    startup_trajectory_mask = prj_df["startup_duration"] > hrs_in_tmp
    shutdown_trajectory_mask = prj_df["shutdown_duration"] > hrs_in_tmp
    down_time_mismatch_mask = (prj_df["min_down_time_hours"]
                               != prj_df["down_time_cutoff_hours_hot"])
    cutoff_na_mask = (cutoff_na_count > 0)
    ramp_na_mask = (ramp_na_count > 0)
    all_ramp_na_mask = (ramp_na_count == su_count_series)

    # 2. Check startup and shutdown ramp duration fit within min down time
    # (to avoid overlap of startup and shutdown trajectory)
    # Invalid projects are projects with a non-fitting trajectory, with a
    # specified down time and/or a specified startup or shutdown rate
    # and at least a startup or shutdown trajectory (i.e. across multiple tmps)
    invalids = (trajectories_fit_mask
                & (down_time_mask | ramp_rate_mask)
                & (startup_trajectory_mask | shutdown_trajectory_mask))
    if invalids.any():
        bad_projects = prj_df[invalids]["project"]
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': Startup ramp duration plus shutdown ramp duration"
            " should be less than the minimum down time. Make sure the minimum"
            " down time is long enough to fit the (coldest) trajectories!"
                .format(print_bad_projects)
        )

    # 2. Check that startup fuel and startup trajectories are not combined
    invalids = startup_fuel_mask & startup_trajectory_mask
    if invalids.any():
        bad_projects = prj_df[invalids]["project"]
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': Cannot have both startup_fuel inputs and a startup "
            "trajectory that takes multiple timepoints as this will double "
            "count startup fuel consumption. Please adjust startup ramp rate or"
            " startup fuel consumption inputs"
                .format(print_bad_projects)
        )

    # 3. Check that down time cutoff is in line with min down time
    invalids = down_time_mismatch_mask
    if invalids.any():
        bad_projects = prj_df[invalids]["project"]
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': down_time_cutoff_hours of hottest start should "
            "match project's minimum_down_time_hours. If there is no minimum "
            "down time, set cutoff to zero."
                .format(print_bad_projects)
        )

    # 4. Check that only gen_commit_lin/bin have inputs in startup_chars
    invalids = (prj_df["n_types"] > 0) & (~prj_df["operational_type"].isin([
        "gen_commit_lin", "gen_commit_bin"]))
    if invalids.any():
        bad_projects = prj_df[invalids]["project"]
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': Only projects of the gen_commit_lin or "
            "gen_commit_bin operational type can have startup_chars inputs."
                .format(print_bad_projects)
        )

    # 5. Check that ramp rate is specified for all or none
    invalids = ramp_na_mask & ~all_ramp_na_mask
    if invalids.any():
        bad_projects = ramp_na_count[invalids].index
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': startup_plus_ramp_up_rate should be specified "
            "for each startup type or for none of them."
                .format(print_bad_projects)
        )
    elif all_ramp_na_mask.any():
        bad_projects = ramp_na_count[all_ramp_na_mask].index
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': startup_plus_ramp_up_rate is not specified in. "
            "project_startup_chars. Model will assume there are no startup "
            "ramp rate limits."
                .format(print_bad_projects)
        )

    # 6. Check that cutoff and ramp rate are in right order
    if ~cutoff_na_mask.any() and ~ramp_na_mask.any():
        rank_cutoff = su_df.groupby("project")["down_time_cutoff_hours"].rank()
        rank_ramp = su_df.groupby("project")["startup_plus_ramp_up_rate"].rank(
            ascending=False)

        invalids = rank_cutoff != rank_ramp
        if invalids.any():
            bad_projects = su_df[invalids]["project"].unique()
            print_bad_projects = ", ".join(bad_projects)
            results.append(
                "Project(s) '{}': Startup ramp rate should decrease with "
                "increasing down time cutoff (colder starts are slower)."
                    .format(print_bad_projects)
            )

    # TODO: test whether some startup types are quick-start and others are not
    # TODO: should validation flag a down time mismatch when there is just one
    #  cold start? (right now it always enforces a down time match and does
    #  not accept no inputs for down time cutoff, even though a simple case
    #  for a fast-start unit might not need this input).

    return results


