#!/usr/bin/env python

import os.path
from pandas import read_csv


def determine_dynamic_components(d, scenario_directory, horizon, stage):
    """

    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    project_dynamic_data = \
        read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t", usecols=["project",
                               "capacity_type",
                               "operational_type"]
        )

    # Required modules are the unique set of generator capacity types
    # This list will be used to know which operational modules to load
    d.required_capacity_modules = \
        project_dynamic_data.capacity_type.unique()

    # Required operational modules
    # Will be determined based on operational_types specified in the data
    # (in projects.tab)
    d.required_operational_modules = \
        project_dynamic_data.operational_type.unique()

    # From here on, the dynamic components will be further populated by the
    # modules
    # Reserve variables
    # Will be determined based on whether the user has specified the
    # respective reserve module AND based on whether a reserve zone is
    # specified for a project in projects.tab
    # We need to make the dictionaries first; it is the lists for each key
    # that are populated by the modules
    d.headroom_variables = \
        {r: [] for r in project_dynamic_data.project}
    d.footroom_variables = \
        {r: [] for r in project_dynamic_data.project}
