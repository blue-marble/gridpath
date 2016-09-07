#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, Expression, Boolean
from pandas import read_csv

from auxiliary import load_capacity_modules


def determine_dynamic_components(d, scenario_directory, horizon, stage):
    """

    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # Get the capacity type of each generator
    dynamic_components = \
        read_csv(os.path.join(scenario_directory, "inputs", "generators.tab"),
                 sep="\t", usecols=["GENERATORS", "capacity_type"]
                 )

    # Required modules are the unique set of generator operational types
    # This list will be used to know which operational modules to load
    d.required_capacity_modules = \
        dynamic_components.capacity_type.unique()


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    m.required_capacity_modules = d.required_capacity_modules
    # Import needed operational modules
    imported_capacity_modules = \
        load_capacity_modules(m.required_capacity_modules)

    def capacity_rule(mod, g, p):
        gen_cap_type = mod.capacity_type[g]
        return imported_capacity_modules[gen_cap_type].\
            capacity_rule(mod, g, p)

    m.Capacity_MW = Expression(m.GENERATOR_OPERATIONAL_PERIODS,
                               rule=capacity_rule)


def export_results(scenario_directory, horizon, stage, m):
    """
    Export operations results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :return:
    """

    m.module_specific_df = []

    imported_capacity_modules = \
        load_capacity_modules(m.required_capacity_modules)
    for op_m in m.required_capacity_modules:
        if hasattr(imported_capacity_modules[op_m],
                   "export_module_specific_results"):
            imported_capacity_modules[
                op_m].export_module_specific_results(
                m)
        else:
            pass
