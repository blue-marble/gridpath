#!/usr/bin/env python

"""
Various auxiliary functions used in operations module
"""


import pandas
from importlib import import_module

from pyomo.environ import value


def load_operational_modules(required_modules):
    imported_operational_modules = dict()
    for op_m in required_modules:
        try:
            imp_op_m = \
                import_module(
                    "." + op_m,
                    package="modules.operations.operational_types"
                )
            imported_operational_modules[op_m] = imp_op_m
            required_attributes = ["power_provision_rule",
                                   "max_power_rule", "min_power_rule",
                                   "fuel_cost_rule", "startup_rule",
                                   "shutdown_rule"]
            for a in required_attributes:
                if hasattr(imp_op_m, a):
                    pass
                else:
                    raise Exception(
                        "ERROR! No " + str(a) + " function in module "
                        + str(imp_op_m) + ".")
        except ImportError:
            print("ERROR! Operational type module " + op_m + " not found.")

    return imported_operational_modules


def generator_subset_init(generator_parameter, expected_type):
    """
    Initialize subsets of generators by operational type based on operational
    type flags.
    Need to return a function with the model as argument, i.e. 'lambda mod'
    because we can only iterate over the
    generators after data is loaded; then we can pass the abstract model to the
    initialization function.
    :param generator_parameter:
    :param expected_type:
    :return:
    """
    return lambda mod: \
        list(g for g in mod.GENERATORS if getattr(mod, generator_parameter)[g]
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

    :param l:
    :return:
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


def make_gen_tmp_var_df(m, gen_tmp_set, x, header):
    """

    :param m:
    :param gen_tmp_set:
    :param x:
    :param header:
    :return:
    """
    # Power

    # Created nested dictionary for each generator-timepoint
    dict_for_gen_df = {}
    for (g, tmp) in getattr(m, gen_tmp_set):
        if g not in dict_for_gen_df.keys():
            dict_for_gen_df[g] = {}
            dict_for_gen_df[g][tmp] = \
                value(getattr(m, x)[g, tmp])
        else:
            dict_for_gen_df[g][tmp] = \
                value(getattr(m, x)[g, tmp])

    # For each generator, create a dataframe with its x values
    # Create two lists, the generators and dictionaries with the timepoints as
    # keys and the values -- it is critical that the order of generators and
    # of the dictionaries with their values match
    generators = []
    timepoints = []
    for g, tmp in dict_for_gen_df.iteritems():
        generators.append(g)
        timepoints.append(pandas.DataFrame.from_dict(tmp, orient='index'))

    # Concatenate all the individual generator dataframes into a final one
    final_df = pandas.DataFrame(pandas.concat(timepoints, keys=generators))
    final_df.index.names = ["generator", "timepoint"]
    final_df.columns = [header]

    return final_df
