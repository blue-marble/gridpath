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
    m.GENERATORS = Set()
    m.load_zone = Param(m.GENERATORS, within=m.LOAD_ZONES)
    m.capacity_type = Param(m.GENERATORS)

    m.capacity_type_operational_period_sets = []

    m.required_capacity_modules = d.required_capacity_modules
    # Import needed operational modules
    imported_capacity_modules = \
        load_capacity_modules(m.required_capacity_modules)

    # First, add any components specific to the operational modules
    for op_m in m.required_capacity_modules:
        imp_op_m = imported_capacity_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m)

    def join_cap_type_operational_period_sets(mod):
        """
        Join the sets we need to make the GENERATOR_OPERATIONAL_PERIODS
        super set; if list contains only a single set, return just that set
        :param mod:
        :return:
        """
        if len(mod.capacity_type_operational_period_sets) == 1:
            return getattr(mod, mod.capacity_type_operational_period_sets[0])
        else:
            return reduce(lambda x, y: getattr(mod, x) | getattr(mod, y),
                          mod.capacity_type_operational_period_sets)

    m.GENERATOR_OPERATIONAL_PERIODS = \
        Set(dimen=2,
            initialize=join_cap_type_operational_period_sets)

    m.OPERATIONAL_PERIODS_BY_GENERATOR = \
        Set(m.GENERATORS,
            rule=lambda mod, gen: set(
                p for (g, p) in mod.GENERATOR_OPERATIONAL_PERIODS if
                g == gen)
            )

    def gen_op_tmps_init(mod):
        gen_tmps = set()
        for g in mod.GENERATORS:
            for p in mod.OPERATIONAL_PERIODS_BY_GENERATOR[g]:
                for tmp in mod.TIMEPOINTS_IN_PERIOD[p]:
                    gen_tmps.add((g, tmp))
        return gen_tmps
    m.GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, rule=gen_op_tmps_init)

    def op_gens_by_tmp(mod, tmp):
        """
        Figure out which generators are operational in each timepoint
        :param mod:
        :param tmp:
        :return:
        """
        gens = list(
            g for (g, t) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS if t == tmp)
        return gens

    m.OPERATIONAL_GENERATORS_IN_TIMEPOINT = \
        Set(m.TIMEPOINTS, initialize=op_gens_by_tmp)

    def capacity_rule(mod, g, p):
        gen_cap_type = mod.capacity_type[g]
        return imported_capacity_modules[gen_cap_type].\
            capacity_rule(mod, g, p)

    m.Capacity_MW = Expression(m.GENERATOR_OPERATIONAL_PERIODS,
                               rule=capacity_rule)


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "generators.tab"),
                     index=m.GENERATORS,
                     select=("GENERATORS", "load_zone", "capacity_type"),
                     param=(m.load_zone, m.capacity_type)
                     )

    imported_capacity_modules = \
        load_capacity_modules(m.required_capacity_modules)
    for op_m in m.required_capacity_modules:
        if hasattr(imported_capacity_modules[op_m],
                   "load_module_specific_data"):
            imported_capacity_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, horizon, stage)
        else:
            pass


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


# TODO: could be consolidated with same function in
# generation.operations.sets_and_params
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