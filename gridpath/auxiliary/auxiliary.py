# Copyright 2016-2023 Blue Marble Analytics LLC.
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

"""
Various auxiliary functions used in other modules
"""

from importlib import import_module
import os.path
import pandas as pd
import traceback


def get_required_subtype_modules(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    which_type,
    prj_or_tx="project",
):
    """
    Get a list of unique types from projects.tab.
    """
    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "{}s.tab".format(prj_or_tx),
        ),
        sep="\t",
    )

    required_modules = df[which_type].unique()

    return required_modules


def load_subtype_modules(required_subtype_modules, package, required_attributes):
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
            imp_m = import_module("." + m, package=package)
            imported_subtype_modules[m] = imp_m
            for a in required_attributes:
                if not hasattr(imp_m, a):
                    raise Exception(
                        "ERROR! No "
                        + str(a)
                        + " function in subtype module "
                        + str(imp_m)
                        + "."
                    )
        except ImportError:
            print("ERROR! Unable to import subtype module " + m + ".")
            traceback.print_exc()

    return imported_subtype_modules


def join_sets(mod, set_name_list):
    """
    Join sets in a list.
    If list contains only a single set, return just that set.

    :param mod:
    :param set_name_list:
    :return:
    """
    if len(set_name_list) == 0:
        return []
    elif len(set_name_list) == 1:
        return getattr(mod, set_name_list[0])
    else:
        joined_set = []
        for s in set_name_list:
            for element in getattr(mod, s):
                joined_set.append(element)
    return joined_set


def subset_init_by_param_value(mod, set_name, param_name, param_value):
    """
    Initialize subset based on a param value.

    :param set_name:
    :param param_name:
    :param param_value:
    :return:
    """
    return list(
        i for i in getattr(mod, set_name) if getattr(mod, param_name)[i] == param_value
    )


def subset_init_by_set_membership(mod, superset, index, membership_set):
    """
    Initialize subset based on membership in another set.
    """
    return list(
        index_tuple
        for index_tuple in getattr(mod, superset)
        if index_tuple[index] in membership_set
    )


def check_list_has_single_item(l, error_msg):
    if len(l) > 1:
        raise ValueError(error_msg)


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
            error_msg="Service "
            + str(item)
            + " is specified more than once"
            + " in generators.tab.",
        )


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def cursor_to_df(cursor):
    """
    Convert the cursor object with query results into a pandas DataFrame.
    :param cursor: cursor object with query result
    :return:
    """
    df = pd.DataFrame(
        data=cursor.fetchall(), columns=[s[0] for s in cursor.description]
    )
    return df


def check_for_integer_subdirectories(main_directory):
    """
    :param main_directory: directory where we'll look for subdirectories
    :return: True or False depending on whether subdirectories are found

    Check for subdirectories and return list. Only take subdirectories
    that can be cast to integer (this will exclude other directories
    such as "pass_through_inputs", "inputs", "results", "logs", and so on).
    We do rely on order downstream, so make sure these are sorted.
    """
    subdirectories = sorted(
        [d for d in next(os.walk(main_directory))[1] if is_integer(d)], key=int
    )

    # There are subdirectories if the list isn't empty
    return subdirectories


def check_for_starting_string_subdirectories(main_directory, starting_string):
    subdirectories = sorted(
        [d for d in next(os.walk(main_directory))[1] if d.startswith(starting_string)],
    )

    # There are subdirectories if the list isn't empty
    return subdirectories


def is_integer(n):
    """
    Check if a value can be cast to integer.
    """
    try:
        int(n)
        return True
    except ValueError:
        return False
