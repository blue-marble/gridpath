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
    :param m:
    :param inputs_directory:
    :return:
    """

    # Generator capabilities
    m.headroom_variables = dict()
    m.footroom_variables = dict()

    with open(os.path.join(inputs_directory, "generators.tab"), "rb") \
            as generation_capacity_file:
        generation_capacity_reader = csv.reader(generation_capacity_file,
                                                delimiter="\t")
        headers = generation_capacity_reader.next()
        # Check that columns are not repeated
        check_list_items_are_unique(headers)
        for row in generation_capacity_reader:
            # Get generator name; we have checked that columns names are unique
            # so can expect a single-item list here and get 0th element
            generator = row[find_list_item_position(headers, "GENERATORS")[0]]
            # All generators get the following variables
            m.headroom_variables[generator] = list()
            m.footroom_variables[generator] = list()
            # In addition, some generators get the variables associated with
            # provision of other services (e.g. reserves) if flagged
            # Generators that can provide upward load-following reserves
            if int(row[find_list_item_position(headers,
                                               "lf_reserves_up")[0]]
                   ):
                m.headroom_variables[generator].append(
                    "Provide_LF_Reserves_Up")
            # Generators that can provide upward regulation
            if int(row[find_list_item_position(headers, "regulation_up")[0]]
                   ):
                m.headroom_variables[generator].append(
                    "Provide_Regulation_Up")
            # Generators that can provide downward load-following reserves
            if int(row[find_list_item_position(headers, "lf_reserves_down")[0]]
                   ):
                m.footroom_variables[generator].append(
                    "Provide_LF_Reserves_Down")
            # Generators that can provide downward regulation
            if int(row[find_list_item_position(headers, "regulation_down")[0]]
                   ):
                m.footroom_variables[generator].append(
                    "Provide_Regulation_Down")

    # TODO: ugly; make this more uniform with the loading of data above rather
    # than having two separate methods
    # Get the operational type of each generator
    dynamic_components = \
        pandas.read_csv(os.path.join(inputs_directory, "generators.tab"),
                        sep="\t", usecols=["GENERATORS",
                                           "operational_type"]
                        )

    # Required modules are the unique set of generator operational types
    # This list will be used to know which operational modules to load
    m.required_operational_modules = \
        dynamic_components.operational_type.unique()


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

    # TODO: figure out how to flag which generators get this variable
    # Generators that can vary power output
    m.Provide_Power = Var(m.DISPATCHABLE_GENERATORS,
                          m.TIMEPOINTS,
                          within=NonNegativeReals)

    # Headroom and footroom services
    m.Provide_LF_Reserves_Up = Var(m.LF_RESERVES_UP_GENERATORS, m.TIMEPOINTS,
                                   within=NonNegativeReals)
    m.Provide_Regulation_Up = Var(m.REGULATION_UP_GENERATORS, m.TIMEPOINTS,
                                  within=NonNegativeReals)
    m.Provide_LF_Reserves_Down = Var(m.LF_RESERVES_DOWN_GENERATORS,
                                     m.TIMEPOINTS,
                                     within=NonNegativeReals)
    m.Provide_Regulation_Down = Var(m.REGULATION_DOWN_GENERATORS, m.TIMEPOINTS,
                                    within=NonNegativeReals)

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

    for g in getattr(m, "LF_RESERVES_UP_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print(
            "Provide_LF_Reserves_Up[" + str(g) + ", " + str(tmp) + "]: "
            + str(m.Provide_LF_Reserves_Up[g, tmp].value)
            )

    for g in getattr(m, "REGULATION_UP_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print(
            "Provide_Regulation_Up[" + str(g) + ", " + str(tmp) + "]: "
            + str(m.Provide_Regulation_Up[g, tmp].value)
            )

    for g in getattr(m, "LF_RESERVES_DOWN_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print(
            "Provide_LF_Reserves_Down[" + str(g) + ", " + str(tmp) + "]: "
            + str(m.Provide_LF_Reserves_Down[g, tmp].value)
            )

    for g in getattr(m, "REGULATION_DOWN_GENERATORS"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print(
            "Provide_Regulation_Down[" + str(g) + ", " + str(tmp) + "]: "
            + str(m.Provide_Regulation_Down[g, tmp].value)
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
