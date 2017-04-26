#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of variable generators that cannot be curtailed (dispatched down).
Cannot provide reserves.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, NonNegativeReals
import warnings

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
        * mod.availability_derate[g, mod.horizon[tmp]] \
        * mod.cap_factor_no_curtailment[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since no commitment, all capacity assumed online
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.availability_derate[g, mod.horizon[tmp]]


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
        * mod.availability_derate[g, mod.horizon[tmp]] \
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


def ramp_rule(mod, g, tmp):
    """
    Exogenously defined ramp for variable generators (no curtailment)
    :param mod: 
    :param g: 
    :param tmp: 
    :return: 
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        pass
    else:
        return (mod.Capacity_MW[g, mod.period[tmp]]
                * mod.availability_derate[g, mod.horizon[tmp]]
                * mod.cap_factor_no_curtailment[g, tmp]) - \
               (mod.Capacity_MW[
                    g, mod.period[mod.previous_timepoint[tmp]]
                ]
                * mod.availability_derate[g, mod.horizon[
                   mod.previous_timepoint[tmp]]
                ]
                * mod.cap_factor_no_curtailment[
                    g, mod.previous_timepoint[tmp]
                    ]
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
    # Also get a list of the projects of the 'variable' operational_type,
    # needed for the data check below (to avoid throwing warning unnecessarily)
    var_proj = list()

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
        elif row[1] == 'variable':
            var_proj.append(row[0])
        else:
            pass

    # Determine subset of project-timepoints in variable profiles file
    project_timepoints = list()
    cap_factor = dict()

    prj_tmp_cf_df = \
        pd.read_csv(
            os.path.join(scenario_directory, horizon, stage, "inputs",
                         "variable_generator_profiles.tab"),
            sep="\t", usecols=["project", "timepoint", "cap_factor"]
        )
    for row in zip(prj_tmp_cf_df["project"],
                   prj_tmp_cf_df["timepoint"],
                   prj_tmp_cf_df["cap_factor"]):
        if row[0] in projects:
            project_timepoints.append((row[0], row[1]))
            cap_factor[(row[0], row[1])] = float(row[2])
        # Profile could be for a 'variable' project, in which case ignore
        elif row[0] in var_proj:
            pass
        # Throw warning if profile exists for a project not in projects.tab
        # (as 'variable' or 'variable_no_curtailment')
        else:
            warnings.warn(
                """WARNING: Profiles are specified for '{}' in 
                variable_generator_profiles.tab, but '{}' is not in 
                projects.tab.""".format(
                    row[0], row[0]
                )
            )

    # Load data
    data_portal.data()[
        "VARIABLE_NO_CURTAILMENT_GENERATOR_OPERATIONAL_TIMEPOINTS"
    ] = {
        None: project_timepoints
    }
    data_portal.data()["cap_factor_no_curtailment"] = cap_factor


def get_module_specific_inputs_from_database(
        subscenarios, c, inputs_directory
):
    """
    Write profiles to variable_generator_profiles.tab
    If file does not yet exist, write header first
    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # Select only profiles of projects in the portfolio
    # Select only profiles of projects with 'variable_no_curtailment'
    # operational type
    # Select only profiles for timepoints from the correct timepoint
    # scenario
    # Select only timepoints on periods when the project is operational
    # (periods with existing project capacity for existing projects or
    # with costs specified for new projects)
    variable_profiles = c.execute(
        """SELECT project, timepoint, cap_factor
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, variable_generator_profile_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = 'variable_no_curtailment'
        ) AS op_char
        USING (project)
        CROSS JOIN
        (SELECT timepoint, period
        FROM inputs_temporal_timepoints
        WHERE timepoint_scenario_id = {})
        LEFT OUTER JOIN
        inputs_project_variable_generator_profiles
        USING (variable_generator_profile_scenario_id, project, timepoint)
        INNER JOIN
        (SELECT project, period
        FROM
        (SELECT project, period
        FROM inputs_project_existing_capacity
        INNER JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE timepoint_scenario_id = {})
        USING (period)
        WHERE project_existing_capacity_scenario_id = {}
        AND existing_capacity_mw > 0) as existing
        UNION
        SELECT project, period
        FROM inputs_project_new_cost
        INNER JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE timepoint_scenario_id = {})
        USING (period)
        WHERE project_new_cost_scenario_id = {})
        USING (project, period)
        WHERE project_portfolio_scenario_id = {}""".format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.TIMEPOINT_SCENARIO_ID,
            subscenarios.TIMEPOINT_SCENARIO_ID,
            subscenarios.PROJECT_EXISTING_CAPACITY_SCENARIO_ID,
            subscenarios.TIMEPOINT_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    # If variable_generator_profiles.tab file already exists, append rows to it
    if os.path.isfile(os.path.join(inputs_directory,
                                   "variable_generator_profiles.tab")
                      ):
        with open(os.path.join(inputs_directory,
                               "variable_generator_profiles.tab"), "a") as \
                variable_profiles_tab_file:
            writer = csv.writer(variable_profiles_tab_file, delimiter="\t")
            for row in variable_profiles:
                writer.writerow(row)
    # If variable_generator_profiles.tab does not exist, write header first,
    # then add profiles data
    else:
        with open(os.path.join(inputs_directory,
                               "variable_generator_profiles.tab"), "w") as \
                variable_profiles_tab_file:
            writer = csv.writer(variable_profiles_tab_file, delimiter="\t")

            # Write header
            writer.writerow(
                ["project", "timepoint", "cap_factor"]
            )
            for row in variable_profiles:
                writer.writerow(row)
