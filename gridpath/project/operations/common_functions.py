# Copyright 2016-2020 Blue Marble Analytics LLC. All rights reserved.
import pandas as pd

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


def create_dispatch_results_optype_df(results_columns, data):
    df = pd.DataFrame(
        columns=[
            "project",
            "timepoint",
        ]
        + results_columns,
        data=data,
    ).set_index(["project", "timepoint"])

    return df
