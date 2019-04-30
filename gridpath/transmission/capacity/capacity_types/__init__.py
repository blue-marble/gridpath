#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.transmission.capacity.capacity_types** package contains
modules to describe the various ways in which transmission-line capacity can be
treated in the optimization problem, e.g. as specified, available to be
built, available to be retired, etc.
"""

import pandas as pd
import os.path

from gridpath.auxiliary.auxiliary import load_tx_capacity_type_modules


def get_inputs_from_database(
        subscenarios, c, inputs_directory
):
    """

    :param subscenarios: 
    :param c: 
    :param inputs_directory: 
    :return: 
    """

    tx_cap_types = \
        pd.read_csv(
            os.path.join(inputs_directory, "transmission_lines.tab"),
            sep="\t", usecols=["TRANSMISSION_LINES",
                               "tx_capacity_type"]
        )

    # Required modules are the unique set of transmission capacity types
    # This list will be used to know which capacity type modules to load
    required_capacity_type_modules = \
        tx_cap_types.tx_capacity_type.unique()

    # Load in the required capacity type modules
    imported_capacity_type_modules = \
        load_tx_capacity_type_modules(required_capacity_type_modules)

    # Get module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "get_module_specific_inputs_from_database"):
            imported_capacity_type_modules[op_m]. \
                get_module_specific_inputs_from_database(
                subscenarios, c, inputs_directory
            )
        else:
            pass
