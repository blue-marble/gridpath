#!/usr/bin/env python

"""
Various auxiliary functions used in capacity module
"""
# TODO: combine this with auxiliary functions file in operations module?

from importlib import import_module
import pandas
from pyomo.environ import value


def load_capacity_modules(required_modules):
    imported_capacity_modules = dict()
    for op_m in required_modules:
        try:
            imp_op_m = \
                import_module(
                    "." + op_m,
                    package=
                    "modules.capacity.generation_and_storage.capacity_types"
                )
            imported_capacity_modules[op_m] = imp_op_m
            required_attributes = ["capacity_rule", "capacity_cost_rule"]
            for a in required_attributes:
                if hasattr(imp_op_m, a):
                    pass
                else:
                    raise Exception(
                        "ERROR! No " + str(a) + " function in module "
                        + str(imp_op_m) + ".")
        except ImportError:
            print("ERROR! Capacity type module " + op_m + " not found.")

    return imported_capacity_modules


def make_gen_period_var_df(m, gen_period_set, x, header):
    """

    :param m:
    :param gen_period_set:
    :param x:
    :param header:
    :return:
    """
    # Created nested dictionary for each generator-timepoint
    dict_for_gen_df = {}
    for (g, p) in getattr(m, gen_period_set):
        if g not in dict_for_gen_df.keys():
            dict_for_gen_df[g] = {}
            try:
                dict_for_gen_df[g][p] = value(getattr(m, x)[g, p])
            except ValueError:
                dict_for_gen_df[g][p] = None
                print(
                    """WARNING: the following capacity variable was
                    not initialized: """ + "\n" + str(x) + "\n"
                    + "Check if " + str(p) + "is a period in the study.")
        else:
            try:
                dict_for_gen_df[g][p] = value(getattr(m, x)[g, p])
            except ValueError:
                dict_for_gen_df[g][p] = None
                print(
                    """WARNING: the following capacity variable was
                    not initialized: """ + "\n" + str(x) + "\n"
                    + "Check if " + str(p) + "is a period in the study.")

    # For each generator, create a dataframe with its x values
    # Create two lists, the generators and dictionaries with the timepoints as
    # keys and the values -- it is critical that the order of generators and
    # of the dictionaries with their values match
    generators = []
    periods = []
    for g, tmp in dict_for_gen_df.iteritems():
        generators.append(g)
        periods.append(pandas.DataFrame.from_dict(tmp, orient='index'))

    # Concatenate all the individual generator dataframes into a final one
    final_df = pandas.DataFrame(pandas.concat(periods, keys=generators))
    final_df.index.names = ["generator", "period"]
    final_df.columns = [header]

    return final_df
