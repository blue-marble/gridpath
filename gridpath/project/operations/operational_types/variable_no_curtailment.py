#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of variable generators that cannot be curtailed (dispatched down).
Cannot provide reserves.
"""

import os.path
import pandas as pd
from pyomo.environ import Param, Set, NonNegativeReals

from gridpath.auxiliary.auxiliary import generator_subset_init, is_number


def add_module_specific_components(m, d):
    """
    Variable generators require a capacity factor for each timepoint.
    :param m:
    :param d:
    :return:
    """
    # Sets and params
    m.VARIABLE_NO_CURTAILMENT_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=generator_subset_init(
            "operational_type", "variable_no_curtailment"
        )
    )

    m.VARIABLE_NO_CURTAILMENT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.VARIABLE_NO_CURTAILMENT_GENERATORS))

    # TODO: allow cap factors greater than 1?
    m.cap_factor_no_curtailment = Param(
        m.VARIABLE_NO_CURTAILMENT_GENERATOR_OPERATIONAL_TIMEPOINTS,
                         within=NonNegativeReals)


# Operations
def power_provision_rule(mod, g, tmp):
    """
    Power provision from variable non-curtailable generators is their capacity
    times the capacity factor in each timepoint
    :param mod:
    :param g:
    :param tmp:
    :return:
    """

    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.cap_factor_no_curtailment[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since no commitment, all capacity assumed online
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Capacity_MW[g, mod.period[tmp]]


# RPS
def rec_provision_rule(mod, g, tmp):
    """
    REC provision from variable non-curtailable generators is the same as
    power-provision: their capacity times the capacity factor in each timepoint
    :param mod:
    :param g:
    :param tmp:
    :return:
    """

    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.cap_factor_no_curtailment[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    No curtailment
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_curtailment_rule(mod, g, tmp):
    """
    Can't provide downward reserves, so no subhourly curtailment
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    Can't provide upward reserves, so no subhourly curtailment
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def fuel_burn_rule(mod, g, tmp, error_message):
    """
    Variable generators should not have fuel use
    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        raise (ValueError(
            "ERROR! Variable projects should not use fuel." + "\n" +
            "Check input data for project '{}'".format(g) + "\n" +
            "and change its fuel to '.' (no value).")
        )
    else:
        raise ValueError(error_message)


def startup_shutdown_rule(mod, g, tmp):
    """
    Variable generators are never started up.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! Variable generators should not incur startup/shutdown "
        "costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup/shutdown costs to '.' (no value).")
    )


def load_module_specific_data(mod, data_portal, scenario_directory,
                              horizon, stage):
    """
    Capacity factors vary by horizon and stage, so get inputs from appropriate
    directory
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # Determine list of projects
    projects = list()

    prj_op_type_df = \
        pd.read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t", usecols=["project",
                               "operational_type"]
        )

    for row in zip(prj_op_type_df["project"],
                   prj_op_type_df["operational_type"]):
        if row[1] == 'variable_no_curtailment':
            projects.append(row[0])
        else:
            pass

    # Determine subset of project-timepoints in variable profiles file
    project_timepoints = list()
    cap_factor = dict()

    prj_tmp_cf_df = \
        pd.read_csv(
            os.path.join(scenario_directory, horizon, stage, "inputs",
                         "variable_generator_profiles.tab"),
            sep="\t", usecols=["GENERATORS", "TIMEPOINTS", "cap_factor"]
        )
    for row in zip(prj_tmp_cf_df["GENERATORS"],
                   prj_tmp_cf_df["TIMEPOINTS"],
                   prj_tmp_cf_df["cap_factor"]):
        if row[0] in projects:
            project_timepoints.append((row[0], row[1]))
            cap_factor[(row[0], row[1])] = float(row[2])
        else:
            pass

    # Load data
    data_portal.data()[
        "VARIABLE_NO_CURTAILMENT_GENERATOR_OPERATIONAL_TIMEPOINTS"
    ] = {
        None: project_timepoints
    }
    data_portal.data()["cap_factor_no_curtailment"] = cap_factor
