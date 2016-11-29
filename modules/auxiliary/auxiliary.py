#!/usr/bin/env python

"""
Various auxiliary functions used in other modules
"""


import pandas
from importlib import import_module

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
            "modules.project.capacity.capacity_types",
            ["capacity_rule", "capacity_cost_rule"]
        )


def load_reserve_type_modules(required_reserve_modules):
    return load_subtype_modules(
        required_reserve_modules,
        "modules.project.operations.reserves",
        []
         )


def load_operational_type_modules(required_operational_modules):
    return load_subtype_modules(
        required_operational_modules,
        "modules.project.operations.operational_types",
        ["power_provision_rule","max_power_rule", "min_power_rule",
         "fuel_cost_rule", "startup_rule", "shutdown_rule"]
         )


def load_tx_capacity_type_modules(required_tx_capacity_modules):
    return load_subtype_modules(
            required_tx_capacity_modules,
            "modules.transmission.capacity.capacity_types",
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
    The DataFrame columns we'll index by
    :param header:
    The header of the value column of the DataFrame we'll create
    :return:
    Nothing
    """

    # Created nested dictionary for each generator-temporal combo
    dict_for_project_df = {}
    for (r, time) in getattr(m, project_time_set):
        if r not in dict_for_project_df.keys():
            dict_for_project_df[r] = {}
            try:
                dict_for_project_df[r][time] = value(getattr(m, var)[r, time])
            except ValueError:
                dict_for_project_df[r][time] = None
                print(
                    "WARNING: The following variable was not initialized: "
                    + "\n" + str(var) + "\n"
                    + "The uninitialized index of set " + project_time_set
                    + " is (" + str((r, time)) + ")."
                )
        else:
            try:
                dict_for_project_df[r][time] = value(getattr(m, var)[r, time])
            except ValueError:
                dict_for_project_df[r][time] = None
                print(
                    "WARNING: The following variable was not initialized: "
                    + "\n" + str(var) + "\n"
                    + "The uninitialized index of set " + project_time_set
                    + " is (" + str((r, time)) + ")."
                )

    # For each generator, create a dataframe with the variable (x) values
    # Create two lists, the generators and dictionaries with the timepoints as
    # keys and the values -- it is critical that the order of generators and
    # of the dictionaries with their values match, as we will concatenate based
    # on that order below
    generators = []
    times = []
    for r, tmp in dict_for_project_df.iteritems():
        generators.append(r)
        times.append(pandas.DataFrame.from_dict(tmp, orient='index'))

    # Concatenate all the individual generator dataframes into a final one
    final_df = pandas.DataFrame(pandas.concat(times, keys=generators))
    final_df.index.names = index
    final_df.columns = [header]

    return final_df
