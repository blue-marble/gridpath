#!/usr/bin/env python

"""
Describe operational constraints on the generation infrastructure.
"""
import os
import csv
import sys

from pyomo.environ import *
from importlib import import_module
import pandas


def determine_dynamic_components(m, inputs_directory):
    """
    Determine which operational type modules will be needed based on the
    operational types in the input data.
    Also determine whether to track startup and shutdown costs.
    :param m:
    :param inputs_directory:
    :return:
    """

    # Get the operational type of each generator
    dynamic_components = \
        pandas.read_csv(os.path.join(inputs_directory, "generators.tab"),
                        sep="\t", usecols=["GENERATORS",
                                           "operational_type",
                                           "startup_cost",
                                           "shutdown_cost"]
                        )

    # Required modules are the unique set of generator operational types
    # This list will be used to know which operational modules to load
    m.required_operational_modules = \
        dynamic_components.operational_type.unique()

    # If numeric values greater than for startup/shutdown costs are specified
    # for some generators, add those generators to lists that will be used to
    # initialize generators subsets for which startup/shutdown costs will be
    # tracked as well as dictionaries that will be used to initialize the
    # startup_cost and shutdown_cost params
    m.startup_cost_generators = list()  # to init STARTUP_COST_GENERATORS set
    m.startup_cost_by_generator = dict()  # to init startup_cost param
    for row in zip(dynamic_components["GENERATORS"],
                   dynamic_components["startup_cost"]):
        if is_number(row[1]) and float(row[1]) > 0:
            m.startup_cost_generators.append(row[0])
            m.startup_cost_by_generator[row[0]] = float(row[1])
        else:
            pass

    m.shutdown_cost_generators = list()  # to init SHUTDOWN_COST_GENERATORS set
    m.shutdown_cost_by_generator = dict()  # to init shutdown_cost param
    for row in zip(dynamic_components["GENERATORS"],
                   dynamic_components["shutdown_cost"]):
        if is_number(row[1]) and float(row[1]) > 0:
            m.shutdown_cost_generators.append(row[0])
            m.shutdown_cost_by_generator[row[0]] = float(row[1])
        else:
            pass


def load_operational_modules(required_modules):
    imported_operational_modules = dict()
    for op_m in required_modules:
        try:
            imp_op_m = \
                import_module(
                    "." + op_m,
                    package="modules.generation.operations.operational_types"
                )
            imported_operational_modules[op_m] = imp_op_m
            required_attributes = ["power_provision_rule",
                                   "max_power_rule", "min_power_rule"]
            for a in required_attributes:
                if hasattr(imp_op_m, a):
                    pass
                else:
                    raise("ERROR! No " + a + " function in module "
                          + imp_op_m + ".")
        except ImportError:
            print("ERROR! Operational module " + op_m + " not found.")
            sys.exit()

    return imported_operational_modules


def add_model_components(m):
    """

    :param m:
    :return:
    """

    # Import needed operational modules
    imported_operational_modules = \
        load_operational_modules(m.required_operational_modules)

    # First, add any components specific to the operational modules
    for op_m in m.required_operational_modules:
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m)

    def power_provision_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type].\
            power_provision_rule(mod, g, tmp)
    m.Power_Provision = Expression(m.GENERATORS, m.TIMEPOINTS,
                                   rule=power_provision_rule)

    def max_power_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type].\
            max_power_rule(mod, g, tmp)
    m.Max_Power_Constraint = Constraint(m.GENERATORS, m.TIMEPOINTS,
                                        rule=max_power_rule)

    def min_power_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            min_power_rule(mod, g, tmp)
    m.Min_Power_Constraint = Constraint(m.GENERATORS, m.TIMEPOINTS,
                                        rule=min_power_rule)

    # ### Aggregate power for load balance ### #
    # TODO: make this generators in the zone only when multiple zones actually
    # are implemented
    def total_generation_power_rule(m, z, tmp):
        return sum(m.Power_Provision[g, tmp] for g in m.GENERATORS)
    m.Generation_Power = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                    rule=total_generation_power_rule)

    m.energy_generation_components.append("Generation_Power")

    # ### Aggregate power costs for objective function ### #
    # Add cost to objective function
    # TODO: fix this when periods added, etc.
    def generation_cost_rule(m):
        """
        Power production cost for all generators across all timepoints
        :param m:
        :return:
        """
        return sum(m.Power_Provision[g, tmp] * m.variable_cost[g]
                   for g in m.GENERATORS for tmp in m.TIMEPOINTS)

    m.Total_Generation_Cost = Expression(rule=generation_cost_rule)
    m.total_cost_components.append("Total_Generation_Cost")

    # ### Startup and shutdown costs ### #
    m.STARTUP_COST_GENERATORS = Set(within=m.GENERATORS,
                                    initialize=m.startup_cost_generators)
    m.SHUTDOWN_COST_GENERATORS = Set(within=m.GENERATORS,
                                     initialize=m.shutdown_cost_generators)
    # Startup and shutdown cost (per unit started/shut down)
    m.startup_cost = Param(m.STARTUP_COST_GENERATORS, within=PositiveReals,
                           initialize=m.startup_cost_by_generator)
    m.shutdown_cost = Param(m.SHUTDOWN_COST_GENERATORS, within=PositiveReals,
                            initialize=m.shutdown_cost_by_generator)
    m.Startup_Cost = Var(m.STARTUP_COST_GENERATORS, m.TIMEPOINTS,
                         within=NonNegativeReals)
    m.Shutdown_Cost = Var(m.SHUTDOWN_COST_GENERATORS, m.TIMEPOINTS,
                          within=NonNegativeReals)

    def startup_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            startup_rule(mod, g, tmp)
    m.Startup_Expression = Expression(
        m.STARTUP_COST_GENERATORS, m.TIMEPOINTS,
        rule=startup_rule)

    def shutdown_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            shutdown_rule(mod, g, tmp)
    m.Shutdown_Expression = Expression(
        m.SHUTDOWN_COST_GENERATORS, m.TIMEPOINTS,
        rule=shutdown_rule)

    def startup_cost_rule(mod, g, tmp):
        """
        Startup expression is positive when more units are on in the current
        timepoint that were on in the previous timepoint. Startup_Cost is
        defined to be non-negative, so if Startup_Expression is 0 or negative
        (i.e. no units started or units shut down since the previous timepoint),
        Startup_Cost will be 0.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Startup_Cost[g, tmp] \
            >= mod.Startup_Expression[g, tmp] * mod.startup_cost[g]
    m.Startup_Cost_Constraint = Constraint(m.STARTUP_COST_GENERATORS,
                                           m.TIMEPOINTS,
                                           rule=startup_cost_rule)

    def shutdown_cost_rule(mod, g, tmp):
        """
        Shutdown expression is positive when more units were on in the previous
        timepoint that are on in the current timepoint. Shutdown_Cost is
        defined to be non-negative, so if Shutdown_Expression is 0 or negative
        (i.e. no units shut down or units started since the previous timepoint),
        Shutdown_Cost will be 0.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Shutdown_Cost[g, tmp] \
            >= mod.Shutdown_Expression[g, tmp] * mod.shutdown_cost[g]
    m.Shutdown_Cost_Constraint = Constraint(m.SHUTDOWN_COST_GENERATORS,
                                            m.TIMEPOINTS,
                                            rule=shutdown_cost_rule)

    # Add to objective function
    def total_startup_cost_rule(mod):
        """
        Sum startup costs for the objective function term.
        :param mod:
        :return:
        """
        return sum(mod.Startup_Cost[g, tmp]
                   for g in mod.STARTUP_COST_GENERATORS
                   for tmp in mod.TIMEPOINTS)
    m.Total_Startup_Cost = Expression(rule=total_startup_cost_rule)
    m.total_cost_components.append("Total_Startup_Cost")

    # Add to objective function
    def total_shutdown_cost_rule(mod):
        """
        Sum shutdown costs for the objective function term.
        :param mod:
        :return:
        """
        return sum(mod.Shutdown_Cost[g, tmp]
                   for g in mod.SHUTDOWN_COST_GENERATORS
                   for tmp in mod.TIMEPOINTS)
    m.Total_Shutdown_Cost = Expression(rule=total_shutdown_cost_rule)
    m.total_cost_components.append("Total_Shutdown_Cost")


def load_model_data(m, data_portal, inputs_directory):
    """
    Traverse required operational modules and load any module-specific data.
    :param m:
    :param data_portal:
    :param inputs_directory:
    :return:
    """
    imported_operational_modules = \
        load_operational_modules(m.required_operational_modules)
    for op_m in m.required_operational_modules:
        if hasattr(imported_operational_modules[op_m],
                   "load_module_specific_data"):
            imported_operational_modules[op_m].load_module_specific_data(
                m, data_portal, inputs_directory)
        else:
            pass


def export_results(m):
    for g in getattr(m, "GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Power_Provision[" + str(g) + ", " + str(tmp) + "]: "
                  + str(m.Power_Provision[g, tmp].expr.value)
                  )

    imported_operational_modules = \
        load_operational_modules(m.required_operational_modules)
    for op_m in m.required_operational_modules:
        if hasattr(imported_operational_modules[op_m],
                   "export_module_specific_results"):
            imported_operational_modules[op_m].export_module_specific_results(
                m)
        else:
            pass


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False