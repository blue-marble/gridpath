#!/usr/bin/env python

import os.path
from pandas import read_csv
from pyomo.environ import Set, Param, NonNegativeReals

from modules.auxiliary.dynamic_components import required_capacity_modules, \
    required_operational_modules, headroom_variables, footroom_variables


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
    setattr(d, required_capacity_modules,
            project_dynamic_data.capacity_type.unique()
            )

    # Required operational modules
    # Will be determined based on operational_types specified in the data
    # (in projects.tab)
    setattr(d, required_operational_modules,
            project_dynamic_data.operational_type.unique()
            )

    # From here on, the dynamic components will be further populated by the
    # modules
    # Reserve variables
    # Will be determined based on whether the user has specified the
    # respective reserve module AND based on whether a reserve zone is
    # specified for a project in projects.tab
    # We need to make the dictionaries first; it is the lists for each key
    # that are populated by the modules
    setattr(d, headroom_variables,
            {r: [] for r in project_dynamic_data.project}
            )
    setattr(d, footroom_variables,
            {r: [] for r in project_dynamic_data.project}
            )


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.PROJECTS = Set()
    m.load_zone = Param(m.PROJECTS, within=m.LOAD_ZONES)
    m.capacity_type = Param(m.PROJECTS)
    m.operational_type = Param(m.PROJECTS)

    # Variable O&M cost
    # TODO: all projects have this for now; is that what makes the most sense?
    m.variable_om_cost_per_mwh = Param(m.PROJECTS, within=NonNegativeReals)


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     index=m.PROJECTS,
                     select=("project", "load_zone", "capacity_type",
                             "operational_type", "variable_om_cost_per_mwh"),
                     param=(m.load_zone, m.capacity_type,
                            m.operational_type, m.variable_om_cost_per_mwh)
                     )