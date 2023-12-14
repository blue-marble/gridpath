# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.
from gridpath.auxiliary.auxiliary import load_subtype_modules


def load_tx_capacity_type_modules(required_tx_capacity_modules):
    """
    Load a specified set of transmission capacity type modules
    :param required_tx_capacity_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_tx_capacity_modules,
        package="gridpath.transmission.capacity.capacity_types",
        required_attributes=[
            "min_transmission_capacity_rule",
            "max_transmission_capacity_rule",
        ],
    )
