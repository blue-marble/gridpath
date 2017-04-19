#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
PRM projects and the zone they contribute to
"""
import os.path
from pyomo.environ import Param, Set


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # First figure out which projects we need to track for PRM contribution
    m.PRM_PROJECTS = Set(within=m.PROJECTS)
    m.prm_zone = Param(m.PRM_PROJECTS, within=m.PRM_ZONES)

    m.PRM_PROJECTS_BY_PRM_ZONE = \
        Set(m.PRM_ZONES, within=m.PRM_PROJECTS,
            initialize=lambda mod, prm_z:
            [p for p in mod.PRM_PROJECTS
             if mod.prm_zone[p] == prm_z])

    # Get operational carbon cap projects - timepoints combinations
    m.PRM_PROJECT_OPERATIONAL_PERIODS = Set(
        within=m.PROJECT_OPERATIONAL_PERIODS,
        rule=lambda mod: [(prj, p) for (prj, p) in
                          mod.PROJECT_OPERATIONAL_PERIODS
                          if prj in mod.PRM_PROJECTS]
    )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     select=("project", "prm_zone"),
                     param=(m.prm_zone,)
                     )

    data_portal.data()['PRM_PROJECTS'] = {
        None: data_portal.data()['prm_zone'].keys()
    }
