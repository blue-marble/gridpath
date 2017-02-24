#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Various auxiliary functions used in other modules
"""

from importlib import import_module
import os.path
import pandas as pd
from pyomo.environ import value


def load_subtype_modules(
        required_subtype_modules, package, required_attributes):
    """
    Load subtype modules (e.g. capacity types, operational types, etc).
    This function will also check that the subtype module have certain
    required attributes.
    :param required_subtype_modules:
    :param package:
    :param required_attributes:
    :return:
    """
    imported_subtype_modules = dict()
    for op_m in required_subtype_modules:
        try:
            imp_op_m = \
                import_module(
                    "." + op_m,
                    package=package
                )
            imported_subtype_modules[op_m] = imp_op_m
            for a in required_attributes:
                if hasattr(imp_op_m, a):
                    pass
                else:
                    raise Exception(
                        "ERROR! No " + str(a) + " function in subtype module "
                        + str(imp_op_m) + ".")
        except ImportError:
            print("ERROR! Subtype module " + op_m + " not found.")

    return imported_subtype_modules


def load_gen_storage_capacity_type_modules(required_capacity_modules):
    return load_subtype_modules(
            required_capacity_modules,
            "gridpath.project.capacity.capacity_types",
            ["capacity_rule", "capacity_cost_rule"]
        )


def load_reserve_type_modules(required_reserve_modules):
    return load_subtype_modules(
        required_reserve_modules,
        "gridpath.project.operations.reserves",
        []
         )


# TODO: add curtailment rules as required?
def load_operational_type_modules(required_operational_modules):
    return load_subtype_modules(
        required_operational_modules,
        "gridpath.project.operations.operational_types",
        ["power_provision_rule", "fuel_burn_rule",
         "startup_rule", "shutdown_rule"]
         )


def load_tx_capacity_type_modules(required_tx_capacity_modules):
    return load_subtype_modules(
            required_tx_capacity_modules,
            "gridpath.transmission.capacity.capacity_types",
            ["min_transmission_capacity_rule",
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


def make_project_time_var_df(m, project_time_set, var, index, header):
    """
    Create a pandas dataframe with the two-dimensional project_time_set as a
    two-column index and the values of x, a variable indexed by
    project_time_set, as the value column. A 'project' can be a generator,
    a storage project, a transmission line, etc. 'Time' can be timepoints,
    periods, etc.
    :param m:
    The abstract model
    :param project_time_set:
    A two-dimensional set of project (e.g. generator, transmission line, etc.)
    and temporal index (e.g. timepoint, period, etc.)
    :param var:
    The variable indexed by project_time_set that we will get values for
    :param index:
    The names of the DataFrame columns we'll index by
    :param header:
    The header of the value column of the DataFrame we'll create
    :return:
    Nothing
    """

    # Create a multi-index from the relevant project-time set
    multi_index = pd.MultiIndex.from_tuples(
        tuples=[(p, time) for (p, time) in getattr(m, project_time_set)],
        names=index
    )
    results_df = pd.DataFrame(
        index=multi_index, columns=[header]
    )

    # Populate indexed dataframe with the variable results values
    for indx in multi_index:
        try:
            results_df[header][indx] = value(getattr(m, var)[indx])
        except ValueError:
            results_df[header][indx] = None
            print(
                "WARNING: The following variable was not initialized: "
                + "\n" + str(var) + "\n"
                + "The uninitialized index of set " + project_time_set
                + " is (" + str((indx)) + ")."
            )

    return results_df


def check_if_technology_column_exists(problem_directory):
    """

    :param problem_directory:
    :return:
    """
    try:
        # If this works, we'll continue; otherwise, we'll skip summarizing
        # results
        pd.read_csv(os.path.join(problem_directory, "inputs", "projects.tab"),
                    sep="\t", usecols=["technology"])
        return True
    except ValueError:
        return False