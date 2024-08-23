# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

from gridpath.auxiliary.auxiliary import load_subtype_modules


def load_operational_type_modules(required_operational_modules):
    """
    Load a specified set of operational type modules
    :param required_operational_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_operational_modules,
        package="gridpath.project.operations.operational_types",
        required_attributes=[],
    )
