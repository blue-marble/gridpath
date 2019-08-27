#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Various auxiliary functions used in other modules
"""
from __future__ import print_function


from builtins import str
from builtins import object
import datetime
from importlib import import_module
import os.path
import sys
import pandas as pd


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
        required_attributes=["power_provision_rule", "startup_shutdown_rule"]
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


class Logging(object):
    """
    Log output to both standard output and a log file. This will be 
    accomplished by assigning this class to sys.stdout.
    """

    def __init__(self, logs_dir):
        """
        Assign sys.stdout and a log file as output destinations

        :param logs_dir: 
        """
        self.terminal = sys.stdout
        self.log_file_path = \
            os.path.join(
                logs_dir, datetime.datetime.now().strftime(
                                              '%Y-%m-%d_%H-%M-%S') + ".log"
            )
        self.log_file = open(self.log_file_path, "w", buffering=1)

    def __getattr__(self, attr):
        """
        Default to sys.stdout when calling attributes for this class

        :param attr: 
        :return: 
        """
        return getattr(self.terminal, attr)

    def write(self, message):
        """
        Output to both terminal and a log file. The print statement will
        call the write() method of any object you assign to sys.stdout
        (in this case the Logging object)

        :param message: 
        :return: 
        """
        self.terminal.write(message)
        self.log_file.write(message)

    def flush(self):
        """
        Flush both the terminal and the log file

        :return: 
        """
        self.terminal.flush()
        self.log_file.flush()


def get_scenario_id_and_name(scenario_id_arg, scenario_name_arg, c, script):
    """
    huh

    :param scenario_id_arg: 
    :param scenario_name_arg: 
    :param c: 
    :param script: 
    :return: 
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
    c = conn.cursor()
    for row in validation_results:
        query = """INSERT into mod_input_validation
                (scenario_id, subproblem_id, stage_id, 
                gridpath_module, related_subscenario, related_database_table, 
                issue_type, issue_description)
                VALUES ({});""".format(','.join(['?' for item in row]))

        c.execute(query, row)

    conn.commit()


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
        "project", "load_point_mw" columns
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


def check_projects_for_reserves(projects, operational_type, subscenarios,
                                subproblem, stage, conn):
    """
    Check that a list of projects of a given operational_type does not show up
    in any of the inputs_project_reserve_bas tables since the operational type
    can't provide any reserves (e.g. must_run).
    :param operational_type:
    :param projects:
    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """
    validation_results = []

    reserves = ["frequency_response", "spinning_reserves",
                "lf_reserves_down", "lf_reserves_up",
                "regulation_up", "regulation_down"]
    for reserve in reserves:
        # Get set of projects with a reserve BA specified and set of must_run
        table = "inputs_project_" + reserve + "_bas"
        ba_column = reserve + "_ba"
        ba_id = reserve + "_ba_scenario_id"
        project_ba_id = "project_" + reserve + "_ba_scenario_id"

        # If the subscenario_ids are specified, do the input validation
        if getattr(subscenarios, ba_id.upper()) and \
                getattr(subscenarios, project_ba_id.upper()):
            c = conn.cursor()
            prjs_w_ba = c.execute(
                """SELECT project
                FROM {}
                WHERE {} IS NOT NULL
                AND {} = {}
                AND {} = {}
                """.format(
                    table,
                    ba_column,
                    ba_id, getattr(subscenarios, ba_id.upper()),
                    project_ba_id, getattr(subscenarios, project_ba_id.upper())
                )
            )
            prjs_w_ba = set([p[0] for p in prjs_w_ba.fetchall()])
            must_run_projects = set(projects)

            # If there are any projects with a reserve BA specified,
            # create a validation error
            bad_projects = prjs_w_ba & must_run_projects  # intersection of sets
            if bad_projects:
                print_bad_projects = ", ".join(bad_projects)
                validation_results.append(
                    (subscenarios.SCENARIO_ID,
                     subproblem,
                     stage,
                     __name__,
                     project_ba_id.upper(),
                     table,
                     "Invalid {} BA inputs".format(reserve),
                     "Project(s) '{}'; {} cannot provide {}".format(
                         print_bad_projects, operational_type, reserve)
                     )
                )

    return validation_results
