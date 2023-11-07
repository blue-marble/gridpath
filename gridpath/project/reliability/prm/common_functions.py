# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

from gridpath.auxiliary.auxiliary import load_subtype_modules


def load_prm_type_modules(required_prm_modules):
    """
    Load a specified set of prm type modules
    :param required_prm_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_prm_modules,
        package="gridpath.project.reliability.prm.prm_types",
        required_attributes=[
            "elcc_eligible_capacity_rule",
        ],
    )
