#!/usr/bin/env python

"""
Various auxiliary functions used in capacity module
"""
# TODO: combine this with auxiliary functions file in operations module?

import pandas
from importlib import import_module


def load_capacity_modules(required_modules):
    imported_capacity_modules = dict()
    for op_m in required_modules:
        try:
            imp_op_m = \
                import_module(
                    "." + op_m,
                    package="modules.generation.capacity.capacity_types"
                )
            imported_capacity_modules[op_m] = imp_op_m
            required_attributes = ["capacity_rule"]
            for a in required_attributes:
                if hasattr(imp_op_m, a):
                    pass
                else:
                    raise("ERROR! No " + a + " function in module "
                          + imp_op_m + ".")
        except ImportError:
            print("ERROR! Capacity type module " + op_m + " not found.")

    return imported_capacity_modules
