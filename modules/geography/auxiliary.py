#!/usr/bin/env python

"""
Various auxiliary functions used in geography module
"""
# TODO: combine this with auxiliary functions file in operations module?

import pandas
from importlib import import_module


def load_tx_capacity_modules(required_modules):
    imported_tx_capacity_modules = dict()
    for op_m in required_modules:
        try:
            imp_op_m = \
                import_module(
                    "." + op_m,
                    package="modules.geography.transmission_capacity_types"
                )
            imported_tx_capacity_modules[op_m] = imp_op_m
            required_attributes = ["min_transmission_capacity_rule",
                                   "max_transmission_capacity_rule"]
            for a in required_attributes:
                if hasattr(imp_op_m, a):
                    pass
                else:
                    raise Exception(
                        "ERROR! No " + str(a) + " function in module "
                        + str(imp_op_m) + ".")
        except ImportError:
            print("ERROR! Transmission capacity type module " + op_m
                  + " not found.")

    return imported_tx_capacity_modules
