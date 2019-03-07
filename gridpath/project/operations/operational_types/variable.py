#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of variable generators. Can be curtailed (dispatched down).
Can provide reserves.
"""
from __future__ import division
from __future__ import print_function

from builtins import next
from builtins import zip
from builtins import str
from past.utils import old_div
import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, Var, Constraint, NonNegativeReals, \
    Expression, value
import warnings

from gridpath.auxiliary.auxiliary import generator_subset_init
from gridpath.auxiliary.dynamic_components import \
    footroom_variables, headroom_variables, reserve_variable_derate_params
from gridpath.project.operations.reserves.subhourly_energy_adjustment import \
    footroom_subhourly_energy_adjustment_rule, \
    headroom_subhourly_energy_adjustment_rule


def add_module_specific_components(m, d):
    """
    Variable generators require a capacity factor for each timepoint.
    :param m:
    :param d:
    :return:
    """
    # Sets and params
    m.VARIABLE_GENERATORS = Set(within=m.PROJECTS,
                                initialize=generator_subset_init(
                                    "operational_type", "variable")
                                )

    m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.VARIABLE_GENERATORS))

    # TODO: allow cap factors greater than 1, but throw a warning?
    m.cap_factor = Param(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                         within=NonNegativeReals)

    # Variable generators treated as dispatchable (can also be curtailed and
    # provide reserves)
    m.Provide_Variable_Power_MW = \
        Var(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    def max_power_rule(mod, g, tmp):
        """
        Power provision plus upward services cannot exceed available power.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Variable_Power_MW[g, tmp] + \
            sum(
            old_div(getattr(mod, c)[g, tmp], getattr(
                mod, getattr(d, reserve_variable_derate_params)[c]
            )[g])
            for c in getattr(d, headroom_variables)[g]
        ) \
            <= mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]] \
            * mod.cap_factor[g, tmp]
    m.Variable_Max_Power_Constraint = \
        Constraint(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=max_power_rule)

    def min_power_rule(mod, g, tmp):
        """
        Power provision minus downward services cannot be less than 0.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Variable_Power_MW[g, tmp] - \
            sum(
            old_div(getattr(mod, c)[g, tmp], getattr(
                mod, getattr(d, reserve_variable_derate_params)[c]
            )[g])
            for c in getattr(d, footroom_variables)[g]
        ) \
            >= 0
    m.Variable_Min_Power_Constraint = \
        Constraint(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=min_power_rule)

    def scheduled_curtailment_expression_rule(mod, g, tmp):
        """
        Scheduled curtailment
        Assume cap factors don't incorporate availability derates, 
        so don't multply capacity by availability_derate here (will count 
        as curtailment)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.cap_factor[g, tmp] - \
            mod.Provide_Variable_Power_MW[g, tmp]

    m.Scheduled_Variable_Generator_Curtailment_MW = \
        Expression(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=scheduled_curtailment_expression_rule)

    def subhourly_curtailment_expression_rule(mod, g, tmp):
        """
        Subhourly curtailment from providing downward reserves
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return footroom_subhourly_energy_adjustment_rule(d=d, mod=mod, g=g,
                                                         tmp=tmp)

    m.Subhourly_Variable_Generator_Curtailment_MW = \
        Expression(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=subhourly_curtailment_expression_rule)

    def subhourly_delivered_energy_expression_rule(mod, g, tmp):
        """
        # Subhourly energy delivered from providing upward reserves
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return headroom_subhourly_energy_adjustment_rule(d=d, mod=mod, g=g,
                                                         tmp=tmp)

    m.Subhourly_Variable_Generator_Energy_Delivered_MW = \
        Expression(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=subhourly_delivered_energy_expression_rule)

    def total_curtailment_expression_rule(mod, g, tmp):
        """
        Available energy that was not delivered
        There's an adjustment for subhourly reserve provision:
        1) if downward reserves are provided, they will be called upon
        occasionally, so power provision will have to decrease and additional
        curtailment will be incurred;
        2) if upward reserves are provided (energy is being curtailed),
        they will be called upon occasionally, so power provision will have to
        increase and less curtailment will be incurred
        The subhourly adjustment here is a simple linear function of reserve
        
        Assume cap factors don't incorporate availability derates, 
        so don't multply capacity by availability_derate here (will count 
        as curtailment)
        
        provision.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.cap_factor[g, tmp] - \
            mod.Provide_Variable_Power_MW[g, tmp] \
            + mod.Subhourly_Variable_Generator_Curtailment_MW[g, tmp] \
            - mod.Subhourly_Variable_Generator_Energy_Delivered_MW[g, tmp]

    m.Total_Variable_Generator_Curtailment_MW = \
        Expression(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=total_curtailment_expression_rule)


# Operations
def power_provision_rule(mod, g, tmp):
    """
    Power provision from variable generators is their capacity times the
    capacity factor in each timepoint minus any upward reserves/curtailment.
    See max_power_rule above.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """

    return mod.Provide_Variable_Power_MW[g, tmp]


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
    REC provision from variable generators is a variable lesser than or
    equal to capacity times the capacity factor in each timepoint minus any
    upward reserves/curtailment. See max_power_rule above.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """

    return mod.Provide_Variable_Power_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    Variable generation can be dispatched down, i.e. scheduled below the
    available energy
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Scheduled_Variable_Generator_Curtailment_MW[g, tmp]


def subhourly_curtailment_rule(mod, g, tmp):
    """
    If providing downward reserves, variable generators will occasionally
    have to be dispatched down relative to their schedule, resulting in
    additional curtailment within the hour
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Subhourly_Variable_Generator_Curtailment_MW[g, tmp]


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    If providing upward reserves, variable generators will occasionally be
    dispatched up, so additional energy will be delivered within the hour
    relative to their schedule (less curtailment)
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Subhourly_Variable_Generator_Energy_Delivered_MW[g, tmp]


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
        raise ValueError(
            "ERROR! Variable projects should not use fuel." + "\n" +
            "Check input data for project '{}'".format(g) + "\n" +
            "and change its fuel to '.' (no value)."
        )
    else:
        raise ValueError(error_message)


def startup_shutdown_rule(mod, g, tmp):
    """
    Variable generators don't incur startup costs.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise ValueError(
        "ERROR! Variable generators should not incur startup/shutdown "
        "costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup/shutdown costs to '.' (no value)."
    )


def ramp_rule(mod, g, tmp):
    """
    Curtailment is counted as part of the ramp here
    :param mod: 
    :param g: 
    :param tmp: 
    :return: 
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        pass
    else:
        return \
            (mod.Capacity_MW[g, mod.period[tmp]]
             * mod.availability_derate[g, mod.horizon[tmp]]
             * mod.cap_factor[g, tmp]) - \
            (mod.Capacity_MW[
                 g, mod.period[mod.previous_timepoint[tmp]]
             ] * mod.availability_derate[
                g, mod.horizon[mod.previous_timepoint[tmp]]
            ] * mod.cap_factor[g, mod.previous_timepoint[tmp]]
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
    # Determine list of 'variable' projects
    projects = list()
    # Also get a list of the projects of the 'variable_no_curtailment'
    # operational_type, needed for the data check below
    # (to avoid throwing warning unnecessarily)
    var_no_curt_proj = list()

    prj_op_type_df = \
        pd.read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t", usecols=["project",
                               "operational_type"]
        )

    for row in zip(prj_op_type_df["project"],
                   prj_op_type_df["operational_type"]):
        if row[1] == 'variable':
            projects.append(row[0])
        elif row[1] == 'variable_no_curtailment':
            var_no_curt_proj.append(row[0])
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
        elif row[0] in var_no_curt_proj:
            pass
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
        "VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS"
    ] = {
        None: project_timepoints
    }
    data_portal.data()["cap_factor"] = cap_factor


def export_module_specific_results(mod, d, scenario_directory, horizon, stage):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "dispatch_variable.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "horizon_weight", "number_of_hours_in_timepoint",
                         "technology", "load_zone",
                         "power_mw", "scheduled_curtailment_mw",
                         "subhourly_curtailment_mw",
                         "subhourly_energy_delivered_mw",
                         "total_curtailment_mw"
                         ])

        for (p, tmp) in mod.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.horizon[tmp],
                tmp,
                mod.horizon_weight[mod.horizon[tmp]],
                mod.number_of_hours_in_timepoint[tmp],
                mod.technology[p],
                mod.load_zone[p],
                value(mod.Provide_Variable_Power_MW[p, tmp]),
                value(mod.Scheduled_Variable_Generator_Curtailment_MW[p, tmp]),
                value(mod.Subhourly_Variable_Generator_Curtailment_MW[p, tmp]),
                value(mod.Subhourly_Variable_Generator_Energy_Delivered_MW[
                          p, tmp]),
                value(mod.Total_Variable_Generator_Curtailment_MW[p, tmp])
            ])


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
    # Select only profiles of projects with 'variable'
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
        AND operational_type = 'variable'
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


def import_module_specific_results_to_database(
        scenario_id, c, db, results_directory
):
    """
    
    :param scenario_id: 
    :param c: 
    :param db: 
    :param results_directory: 
    :return: 
    """

    print("project dispatch variable")
    # dispatch_variable.csv
    c.execute(
        """DELETE FROM results_project_dispatch_variable
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_project_dispatch_variable"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_dispatch_variable"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        project VARCHAR(64),
        period INTEGER,
        horizon INTEGER,
        timepoint INTEGER,
        horizon_weight FLOAT,
        number_of_hours_in_timepoint FLOAT,
        load_zone VARCHAR(32),
        technology VARCHAR(32),
        power_mw FLOAT,
        scheduled_curtailment_mw FLOAT,
        subhourly_curtailment_mw FLOAT,
        subhourly_energy_delivered_mw FLOAT,
        total_curtailment_mw FLOAT,
        PRIMARY KEY (scenario_id, project, timepoint)
            );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "dispatch_variable.csv"), "r") as v_dispatch_file:
        reader = csv.reader(v_dispatch_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[7]
            technology = row[6]
            power_mw = row[8]
            scheduled_curtailment_mw = row[9]
            subhourly_curtailment_mw = row[10]
            subhourly_energy_delivered_mw = row[11]
            total_curtailment_mw = row[12]
            c.execute(
                """INSERT INTO temp_results_project_dispatch_variable"""
                + str(scenario_id) + """
                (scenario_id, project, period, horizon, timepoint,
                horizon_weight, number_of_hours_in_timepoint,
                load_zone, technology, power_mw, scheduled_curtailment_mw,
                subhourly_curtailment_mw, subhourly_energy_delivered_mw,
                total_curtailment_mw)
                VALUES ({}, '{}', {}, {}, {}, {}, {}, '{}', '{}',
                {}, {}, {}, {}, {});""".format(
                    scenario_id, project, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    load_zone, technology, power_mw, scheduled_curtailment_mw,
                    subhourly_curtailment_mw, subhourly_energy_delivered_mw,
                    total_curtailment_mw
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_dispatch_variable
        (scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw, scheduled_curtailment_mw,
        subhourly_curtailment_mw, subhourly_energy_delivered_mw,
        total_curtailment_mw)
        SELECT
        scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw, scheduled_curtailment_mw,
        subhourly_curtailment_mw, subhourly_energy_delivered_mw,
        total_curtailment_mw
        FROM temp_results_project_dispatch_variable""" + str(scenario_id) + """
        ORDER BY scenario_id, project, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_dispatch_variable"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
