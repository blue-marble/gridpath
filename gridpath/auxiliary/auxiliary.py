#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Various auxiliary functions used in other modules
"""
from __future__ import print_function


from builtins import str
import datetime
from importlib import import_module
import pandas as pd

from db.common_functions import spin_on_database_lock


def load_subtype_modules(
        required_subtype_modules, package, required_attributes
):
    """
    Load subtype modules (e.g. capacity types, operational types, etc).
    This function will also check that the subtype modules have certain
    required attributes.

    :param required_subtype_modules: name of the subtype_modules to be loaded
    :param package: The name of the package the subtype modules reside in. E.g.
        capacity_type modules live in gridpath.project.capacity.capacity_types
    :param required_attributes: module attributes that are required for each of
        the specified required_subtype_modules. E.g. each capacity_type will
        need to have a "capacity_rule" attribute.
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    imported_subtype_modules = dict()
    for m in required_subtype_modules:
        try:
            imp_m = \
                import_module(
                    "." + m,
                    package=package
                )
            imported_subtype_modules[m] = imp_m
            for a in required_attributes:
                if hasattr(imp_m, a):
                    pass
                else:
                    raise Exception(
                        "ERROR! No " + str(a) + " function in subtype module "
                        + str(imp_m) + ".")
        except ImportError:
            print("ERROR! Subtype module " + m + " not found.")

    return imported_subtype_modules


def load_gen_storage_capacity_type_modules(required_capacity_modules):
    """
    Load a specified set of capacity type modules
    :param required_capacity_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_capacity_modules,
        package="gridpath.project.capacity.capacity_types",
        required_attributes=["capacity_rule", "capacity_cost_rule"]
    )


def load_reserve_type_modules(required_reserve_modules):
    """
    Load a specified set of reserve modules
    :param required_reserve_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_reserve_modules,
        package="gridpath.project.operations.reserves",
        required_attributes=[]
    )


# TODO: add curtailment rules as required?
def load_operational_type_modules(required_operational_modules):
    """
    Load a specified set of operational type modules
    :param required_operational_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_operational_modules,
        package="gridpath.project.operations.operational_types",
        required_attributes=["power_provision_rule", "startup_cost_rule",
                             "shutdown_cost_rule", "startup_fuel_burn_rule"]
    )


def load_prm_type_modules(required_prm_modules):
    """
    Load a specified set of prm type modules
    :param required_prm_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_prm_modules,
        package="gridpath.project.reliability.prm.prm_types",
        required_attributes=["elcc_eligible_capacity_rule",]
    )


def load_tx_capacity_type_modules(required_tx_capacity_modules):
    """
    Load a specified set of transmission capacity type modules
    :param required_tx_capacity_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_tx_capacity_modules,
        package="gridpath.transmission.capacity.capacity_types",
        required_attributes=["min_transmission_capacity_rule",
                             "max_transmission_capacity_rule"]
    )


def load_tx_operational_type_modules(required_tx_operational_modules):
    """
    Load a specified set of transmission operational type modules
    :param required_tx_operational_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_tx_operational_modules,
        package="gridpath.transmission.operations.operational_types",
        required_attributes=[
            "transmit_power_rule", "transmit_power_losses_lz_from_rule",
            "transmit_power_losses_lz_to_rule"
        ]
    )


def join_sets(mod, set_list):
    """
    Join sets in a list.
    If list contains only a single set, return just that set.

    :param mod:
    :param set_list:
    :return:
    """
    if len(set_list) == 0:
        return []
    elif len(set_list) == 1:
        return getattr(mod, set_list[0])
    else:
        joined_set = set()
        for s in set_list:
            for element in getattr(mod, s):
                joined_set.add(element)
    return joined_set


def generator_subset_init(generator_parameter, expected_type):
    """
    Initialize subsets of generators by subtype based on subtype flags.
    Need to return a function with the model as argument, i.e. 'lambda mod'
    because we can only iterate over the
    generators after data is loaded; then we can pass the abstract model to the
    initialization function.

    :param generator_parameter:
    :param expected_type:
    :return:
    """
    return lambda mod: \
        list(g for g in mod.PROJECTS if getattr(mod, generator_parameter)[g]
             == expected_type)


def check_list_has_single_item(l, error_msg):
    if len(l) > 1:
        raise ValueError(error_msg)
    else:
        pass


def find_list_item_position(l, item):
    """

    :param l:
    :param item:
    :return:
    """
    return [i for i, element in enumerate(l) if element == item]


def check_list_items_are_unique(l):
    """
    Check if items in a list are unique

    :param l:
    A list
    :return:
    Nothing
    """
    for item in l:
        positions = find_list_item_position(l, item)
        check_list_has_single_item(
            l=positions,
            error_msg="Service " + str(item) + " is specified more than once" +
            " in generators.tab.")


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# TODO: handle non-existing scenarios/scenario_ids
def get_scenario_id_and_name(scenario_id_arg, scenario_name_arg, c, script):
    """
    Get the scenario_id and the scenario_ name. Usually only one is given (the
    other one will be 'None'), so this functions determine the missing one from
    the one that is provided. If both are provided, this function checks whether
    they match.

    :param scenario_id_arg: 
    :param scenario_name_arg: 
    :param c: 
    :param script: 
    :return: (scenario_id, scenario_name)
    """
    if scenario_id_arg is None and scenario_name_arg is None:
        raise TypeError(
            """ERROR: Either scenario_id or scenario_name must be specified. 
            Run 'python """ + script + """'.py --help' for help."""
        )
    elif scenario_id_arg is not None and scenario_name_arg is None:
        scenario_id = scenario_id_arg
        scenario_name = c.execute(
            """SELECT scenario_name
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
    elif scenario_id_arg is None and scenario_name_arg is not None:
        scenario_name = scenario_name_arg
        scenario_id = c.execute(
            """SELECT scenario_id
               FROM scenarios
               WHERE scenario_name = '{}';""".format(scenario_name)
        ).fetchone()[0]
    else:
        # If both scenario_id and scenario_name
        scenario_name_db = c.execute(
            """SELECT scenario_name
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id_arg)
        ).fetchone()[0]
        if scenario_name_db == scenario_name_arg:
            scenario_id = scenario_id_arg
            scenario_name = scenario_name_arg
        else:
            raise ValueError("ERROR: scenario_id and scenario_name don't "
                             "match in database.")

    return scenario_id, scenario_name


def write_validation_to_database(validation_results, conn):
    """
    Writes the validation results to database. Helper function for input
    validation.
    :param validation_results: list of tuples with results from input validation.
        Each row represents an identified input validation issue.
    :param conn: database connection
    :return:
    """
    # add timestamp (ISO8601 strings, so truncate to ms)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    validation_results = [row + (timestamp,) for row in validation_results]
    c = conn.cursor()
    for row in validation_results:
        query = """
        INSERT INTO status_validation
        (scenario_id, subproblem_id, stage_id, 
        gridpath_module, related_subscenario, related_database_table, 
        issue_severity, issue_type, issue_description, timestamp)
        VALUES ({});
        """.format(','.join(['?' for item in row]))

        c.execute(query, row)

    conn.commit()


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


def check_dtypes(df, expected_dtypes):
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


def check_column_sign_positive(df, columns):
    """
    Checks whether the selected columns of a DataFrame are non-negative.
    Helper function for input validation.
    :param df: DataFrame for which to check signs. Must have a "project"
        column, and columns param must be a subset of the columns in df
    :param columns: list with columns that are expected to be non-negative
    :return: List of error messages for each column with invalid signs.
        Error message specifies the column.
    """
    result = []
    for column in columns:
        is_negative = (df[column] < 0)
        if is_negative.any():
            bad_projects = df["project"][is_negative].values
            print_bad_projects = ", ".join(bad_projects)
            result.append(
                 "Project(s) '{}': Expected '{}' >= 0"
                 .format(print_bad_projects, column)
                 )

    return result


def check_req_prj_columns(df, columns, required, category):
    """
    Checks whether the required columns of a DataFrame are not None/NA or
    whether the incompatible columns are None/NA. If required columns are
    None/NA, or if incompatible columns are not None/NA, an error message
    is returned.
    Helper function for input validation.
    :param df: DataFrame for which to check columns. Must have a "project"
        column, and columns param must be a subset of the columns in df
    :param columns: list of columns to check
    :param required: Boolean, whether the listed columns are required or
        incompatible
    :param category: project category (operational_type, capacity_type, ...)
        for which we're doing the input validation
    :return: List of error messages for each column with invalid inputs.
        Error message specifies the column.
    """
    result = []
    for column in columns:
        if required:
            invalids = pd.isna(df[column])
            error_str = "should have inputs for"
        else:
            invalids = pd.notna(df[column])
            error_str = "should not have inputs for"
        if invalids.any():
            bad_projects = df["project"][invalids].values
            print_bad_projects = ", ".join(bad_projects)
            result.append(
                "Project(s) '{}'; {} {} '{}'"
                .format(print_bad_projects, category, error_str, column)
                 )

    return result


def check_prj_column(df, column, valids):
    """
    Check that the specified column only has entries within the list of valid
    entries ("valids"). If not, an error message is returned.
    Helper function for input validation.

    Note: could be expanded to check multiple columns
    :param df: DataFrame for which to check columns. Must have a "project"
        column, and a column equal to the column param.
    :param column: string, column to check
    :param valids: list of valid entries
    :return:
    """
    results = []

    invalids = ~df[column].isin(valids)
    if invalids.any():
        bad_projects = df["project"][invalids].values
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': Invalid entry for {}"
            .format(print_bad_projects, column)
        )

    return results


def check_constant_heat_rate(df, op_type):
    """
    Check whether the projects in the DataFrame have a constant heat rate
    based on the number of load points per project in the DAtaFrame
    :param df: DataFrame for which to check constant heat rate. Must have
        "project", "load_point_fraction" columns
    :param op_type: Operational type (used in error message)
    :return:
    """

    results = []

    n_load_points = df.groupby(["project"]).size()
    invalids = (n_load_points > 1)
    if invalids.any():
        bad_projects = invalids.index[invalids]
        print_bad_projects = ", ".join(bad_projects)
        results.append(
            "Project(s) '{}': {} should have only 1 load point"
            .format(print_bad_projects, op_type)
        )

    return results


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


def check_projects_for_reserves(projects_op_type, projects_w_ba,
                                operational_type, reserve):
    """
    Check that a list of projects of a given operational_type does not show up
    in a a list of projects that can provide a given type of reserve. This is
    used when checking that a certain operational type (e.g. gen_must_run) is not
    providing a certain type of reserve (e..g regulation_up) which it shouldn't
    be able to provide.

    :param projects_op_type: list of projects with specified operational type
    :param projects_w_ba: list of projects with specified reserve ba
    :param operational_type: string, specified operational_type (e.g. gen_must_run)
        that is not able to provide the specified reserve
    :param reserve: string, specified reserve product (e.g. regulation_up)
    :return:
    """

    results = []

    # Convert list of projects to sets and check set intersection
    projects_op_type = set(projects_op_type)
    projects_w_ba = set(projects_w_ba)
    bad_projects = sorted(list(projects_w_ba & projects_op_type))

    # If there are any projects of the specified operaitonal type
    # with a reserve BA specified, create a validation error
    if bad_projects:
        print_bad_projects = ", ".join(bad_projects)
        results.append(
             "Project(s) '{}'; {} cannot provide {}".format(
                 print_bad_projects, operational_type, reserve)
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
    prj_df["startup_duration"] = prj_df["min_stable_level"] \
                             / prj_df["startup_plus_ramp_up_rate_cold"] / 60
    prj_df["shutdown_duration"] = prj_df["min_stable_level"] \
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


def setup_results_import(conn, cursor, table, scenario_id, subproblem, stage):
    """
    :param conn: the connection object
    :param cursor: the cursor object
    :param table: the results table we'll be inserting into
    :param scenario_id:
    :param subproblem:
    :param stage:

    Prepare for results import: 1) delete prior results and 2) create a
    temporary table we'll insert into first (for sorting before inserting
    into the final table)
    """
    # Delete prior results
    del_sql = """
        DELETE FROM {} 
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """.format(table)
    spin_on_database_lock(conn=conn, cursor=cursor, sql=del_sql,
                          data=(scenario_id, subproblem, stage), many=False)

    # Create temporary table, which we'll use to sort the results before
    # inserting them into our persistent table
    drop_tbl_sql = \
        """DROP TABLE IF EXISTS temp_{}{};
        """.format(table, scenario_id)
    spin_on_database_lock(conn=conn, cursor=cursor, sql=drop_tbl_sql,
                          data=(), many=False)

    # Get the CREATE statemnt for the persistent table
    tbl_sql = cursor.execute("""
        SELECT sql 
        FROM sqlite_master
        WHERE type='table'
        AND name='{}'
        """.format(table)
                             ).fetchone()[0]

    # Create a temporary table with the same structure as the persistent table
    temp_tbl_sql = \
        tbl_sql.replace(
            "CREATE TABLE {}".format(table),
            "CREATE TEMPORARY TABLE temp_{}{}".format(table, scenario_id)
        )

    spin_on_database_lock(conn=conn, cursor=cursor, sql=temp_tbl_sql,
                          data=(), many=False)
