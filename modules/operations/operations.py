#!/usr/bin/env python
import os
import csv
import sys

from pyomo.environ import *
from importlib import import_module

# from operational_types import must_run, variable, dispatchable


def determine_dynamic_components(m, inputs_directory):
    m.required_operational_modules = list()

    # TODO: get operational types from data
    m.required_operational_modules = ["must_run", "dispatchable", "variable"]


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
        print op_m
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
