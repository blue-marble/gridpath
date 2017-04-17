#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import pandas as pd
import os.path

from gridpath.auxiliary.auxiliary import load_gen_storage_capacity_type_modules


def get_inputs_from_database(
        subscenarios, c, inputs_directory
):
    """

    :param subscenarios: 
    :param c: 
    :param inputs_directory: 
    :return: 
    """

    project_cap_types = \
        pd.read_csv(
            os.path.join(inputs_directory, "projects.tab"),
            sep="\t", usecols=["project",
                               "capacity_type"]
        )

    # Required modules are the unique set of generator capacity types
    # This list will be used to know which capacity type modules to load
    required_capacity_type_modules = \
        project_cap_types.capacity_type.unique()

    # Load in the required capacity type modules
    imported_capacity_type_modules = \
        load_gen_storage_capacity_type_modules(required_capacity_type_modules)

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
