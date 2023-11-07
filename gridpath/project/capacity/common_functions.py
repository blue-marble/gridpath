# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

from gridpath.auxiliary.auxiliary import load_subtype_modules


def load_project_capacity_type_modules(required_capacity_modules, prj_or_tx="project"):
    """
    Load a specified set of capacity type modules
    :param required_capacity_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_capacity_modules,
        package=f"gridpath.{prj_or_tx}.capacity.capacity_types",
        required_attributes=[],
    )
