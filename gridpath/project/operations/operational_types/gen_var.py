#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This modules describes the operational capabilities and constraints of
variable projects. These projects can be curtailed (dispatched down) and can
provide reserves.
"""
from __future__ import division
from __future__ import print_function

from builtins import next
from builtins import zip
from builtins import str
import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, Var, Constraint, NonNegativeReals, \
    Expression, value
import warnings

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import generator_subset_init, \
    setup_results_import
from gridpath.auxiliary.dynamic_components import \
    footroom_variables, headroom_variables, reserve_variable_derate_params
from gridpath.project.operations.reserves.subhourly_energy_adjustment import \
    footroom_subhourly_energy_adjustment_rule, \
    headroom_subhourly_energy_adjustment_rule


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    Here, we define the set of dispatchable-capacity-commit generators:
    *VARIABLE_GENERATORS* (:math:`VG`, index :math:`vg`) and use this set
    to get the subset of *PROJECT_OPERATIONAL_TIMEPOINTS* with
    :math:`g \in VG` -- the *VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS*
    (:math:`VG\_OT`).

    The main operational parameter for variable generators is their capacity
    factor, *cap_factor* \ :sub:`vg, tmp`\  defined over :math:`VG\_OT`.

    The power provision variable for dispatchable-capacity-commit generators,
    *Provide_Variable_Power_MW*, is defined over
    *VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS*.

    This operational type is curtailable, so power provision is defined to
    be less than or equal to the capacity times the capacity factor in each
    timepoint:

    For :math:`(vg, tmp) \in VG\_OT`: \n
    :math:`Provide\_Variable\_Power\_MW_{vg, tmp} \leq
    Capacity\_MW_{vg,p^{tmp}} \\times cap\_factor_{vg, tmp}`

    Advanced functionality includes allowing the variable projects to provide
    reserves; we will document this functionality once we have fully
    validated it.
    """
    # Sets and params
    m.VARIABLE_GENERATORS = Set(within=m.PROJECTS,
                                initialize=generator_subset_init(
                                    "operational_type", "gen_var")
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
            sum(getattr(mod, c)[g, tmp]
                / getattr(mod, getattr(d, reserve_variable_derate_params)[c])[g]
                for c in getattr(d, headroom_variables)[g]) \
            <= mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.Availability_Derate[g, tmp] \
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
            sum(getattr(mod, c)[g, tmp]
                / getattr(mod, getattr(d, reserve_variable_derate_params)[c])[g]
                for c in getattr(d, footroom_variables)[g]) \
            >= 0
    m.Variable_Min_Power_Constraint = \
        Constraint(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=min_power_rule)

    def scheduled_curtailment_expression_rule(mod, g, tmp):
        """
        Scheduled curtailment is the available power minus what was actually
        provided.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.Availability_Derate[g, tmp] \
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
        so don't multply capacity by Availability_Derate here (will count
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
    :param mod: the Pyomo abstract model
    :param g: the project
    :param tmp: the operational timepoint
    :return: expression for power provision by variable generators

    Power provision from variable generators is their capacity times the
    capacity factor in each timepoint minus any upward reserves/curtailment.
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
        * mod.Availability_Derate[g, tmp]


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


def power_delta_rule(mod, g, tmp):
    """
    Curtailment is counted as part of the ramp here; excludes any ramping from
    reserve provision.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            == "linear":
        pass
    else:
        return \
            (mod.Capacity_MW[g, mod.period[tmp]]
             * mod.Availability_Derate[g, tmp]
             * mod.cap_factor[g, tmp]) - \
            (mod.Capacity_MW[
                 g, mod.period[
                     mod.previous_timepoint[tmp, mod.balancing_type_project[g]]
                 ]
             ] * mod.Availability_Derate[
                g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]
            ]
             * mod.cap_factor[
                 g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]
             ]
             )


def load_module_specific_data(mod, data_portal,
                              scenario_directory, subproblem, stage):
    """
    Capacity factors vary by horizon and stage, so get inputs from appropriate
    directory
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    # Determine list of 'gen_var' projects
    projects = list()
    # Also get a list of the projects of the 'gen_var_must_take'
    # operational_type, needed for the data check below
    # (to avoid throwing warning unnecessarily)
    var_no_curt_proj = list()

    prj_op_type_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "operational_type"]
    )

    for row in zip(prj_op_type_df["project"],
                   prj_op_type_df["operational_type"]):
        if row[1] == 'gen_var':
            projects.append(row[0])
        elif row[1] == 'gen_var_must_take':
            var_no_curt_proj.append(row[0])
        else:
            pass

    # Determine subset of project-timepoints in variable profiles file
    project_timepoints = list()
    cap_factor = dict()

    prj_tmp_cf_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "inputs",
                     "variable_generator_profiles.tab"),
        sep="\t",
        usecols=["project", "timepoint", "cap_factor"]
    )
    for row in zip(prj_tmp_cf_df["project"],
                   prj_tmp_cf_df["timepoint"],
                   prj_tmp_cf_df["cap_factor"]):
        if row[0] in projects:
            project_timepoints.append((row[0], row[1]))
            cap_factor[(row[0], row[1])] = float(row[2])
        # Profile could be for a 'gen_var' project, in which case ignore
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


def export_module_specific_results(mod, d,
                                   scenario_directory, subproblem, stage):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "dispatch_variable.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "balancing_type_project", "horizon",
                         "timepoint", "timepoint_weight",
                         "number_of_hours_in_timepoint",
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
                mod.balancing_type_project[p],
                mod.horizon[tmp, mod.balancing_type_project[p]],
                tmp,
                mod.timepoint_weight[tmp],
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
        subscenarios, subproblem, stage, conn
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    # Select only profiles of projects in the portfolio
    # Select only profiles of projects with 'gen_var'
    # operational type
    # Select only profiles for timepoints from the correct temporal scenario
    # and the correct subproblem
    # Select only timepoints on periods when the project is operational
    # (periods with existing project capacity for existing projects or
    # with costs specified for new projects)
    variable_profiles = c.execute("""
        SELECT project, timepoint, cap_factor
        FROM (
        -- Select only projects from the relevant portfolio
        SELECT project
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {}
        ) as portfolio_tbl
        -- Of the projects in the portfolio, select only those that are in 
        -- this project_operational_chars_scenario_id and have 'gen_var' as 
        -- their operational_type
        INNER JOIN
        (SELECT project, variable_generator_profile_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = 'gen_var'
        ) AS op_char
        USING (project)
        -- Cross join to the timepoints in the relevant 
        -- temporal_scenario_id, subproblem_id, and stage_id
        -- Get the period since we'll need that to get only the operational 
        -- timepoints for a project via an INNER JOIN below
        CROSS JOIN
        (SELECT stage_id, timepoint, period
        FROM inputs_temporal_timepoints
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {}
        ) as tmps_tbl
        -- Now that we have the relevant projects and timepoints, get the 
        -- respective cap_factor (and no others) from 
        -- inputs_project_variable_generator_profiles through a LEFT OUTER JOIN
        LEFT OUTER JOIN
        inputs_project_variable_generator_profiles
        USING (variable_generator_profile_scenario_id, project, 
        stage_id, timepoint)
        -- We also only want timepoints in periods when the project actually 
        -- exists, so we figure out the operational periods for each of the  
        -- projects below and INNER JOIN to that
        INNER JOIN
            (SELECT project, period
            FROM (
                -- Get the operational periods for each 'existing' and 
                -- 'new' project
                SELECT project, period
                FROM inputs_project_existing_capacity
                WHERE project_existing_capacity_scenario_id = {}
                AND existing_capacity_mw > 0
                UNION
                SELECT project, period
                FROM inputs_project_new_cost
                WHERE project_new_cost_scenario_id = {}
                ) as all_operational_project_periods
            -- Only use the periods in temporal_scenario_id via an INNER JOIN
            INNER JOIN (
                SELECT period
                FROM inputs_temporal_periods
                WHERE temporal_scenario_id = {}
                ) as relevant_periods_tbl
            USING (period)
            ) as relevant_op_periods_tbl
        USING (project, period);
        """.format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            stage,
            subscenarios.PROJECT_EXISTING_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID
        )
    )

    return variable_profiles


def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # variable_profiles = get_module_specific_inputs_from_database(
    #     subscenarios, subproblem, stage, conn

    # do stuff here to validate inputs


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    variable_generator_profiles.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    variable_profiles = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

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
                               "variable_generator_profiles.tab"), "w", newline="") as \
                variable_profiles_tab_file:
            writer = csv.writer(variable_profiles_tab_file, delimiter="\t")

            # Write header
            writer.writerow(
                ["project", "timepoint", "cap_factor"]
            )
            for row in variable_profiles:
                writer.writerow(row)


def import_module_specific_results_to_database(
        scenario_id, subproblem, stage, c, db, results_directory
):
    """
    
    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c: 
    :param db: 
    :param results_directory: 
    :return: 
    """

    print("project dispatch variable")
    # dispatch_variable.csv
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_dispatch_variable",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "dispatch_variable.csv"), "r") as v_dispatch_file:
        reader = csv.reader(v_dispatch_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            balancing_type_project = row[2]
            horizon = row[3]
            timepoint = row[4]
            timepoint_weight = row[5]
            number_of_hours_in_timepoint = row[6]
            load_zone = row[8]
            technology = row[7]
            power_mw = row[9]
            scheduled_curtailment_mw = row[10]
            subhourly_curtailment_mw = row[11]
            subhourly_energy_delivered_mw = row[12]
            total_curtailment_mw = row[13]
            
            results.append(
                (scenario_id, project, period, subproblem, stage,
                    balancing_type_project, horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, power_mw,
                    scheduled_curtailment_mw, subhourly_curtailment_mw,
                    subhourly_energy_delivered_mw, total_curtailment_mw)
            )
    insert_temp_sql = """
        INSERT INTO temp_results_project_dispatch_variable{}
        (scenario_id, project, period, subproblem_id, stage_id,
        balancing_type_project, horizon, timepoint, timepoint_weight,
        number_of_hours_in_timepoint, load_zone, technology, power_mw, 
        scheduled_curtailment_mw, subhourly_curtailment_mw,
        subhourly_energy_delivered_mw, total_curtailment_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_dispatch_variable
        (scenario_id, project, period, subproblem_id, stage_id,
        balancing_type_project, horizon, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint, load_zone, technology, power_mw, 
        scheduled_curtailment_mw, subhourly_curtailment_mw,
        subhourly_energy_delivered_mw, total_curtailment_mw)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        balancing_type_project, horizon, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint, load_zone, technology, power_mw,
        scheduled_curtailment_mw, subhourly_curtailment_mw,
        subhourly_energy_delivered_mw, total_curtailment_mw
        FROM temp_results_project_dispatch_variable{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


def process_module_specific_results(db, c, subscenarios):
    """
    Aggregate scheduled curtailment
    :param db:
    :param c:
    :param subscenarios:
    :return:
    """

    print("aggregate variable curtailment")

    # Delete old aggregated variable curtailment results
    del_sql = """
        DELETE FROM results_project_curtailment_variable 
        WHERE scenario_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=del_sql,
                          data=(subscenarios.SCENARIO_ID,),
                          many=False)

    # Aggregate variable curtailment (just scheduled curtailment)
    insert_sql = """
        INSERT INTO results_project_curtailment_variable
        (scenario_id, subproblem_id, stage_id, period, horizon, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, month, hour_of_day,
        load_zone, scheduled_curtailment_mw)
        SELECT
        scenario_id, subproblem_id, stage_id, period, horizon, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, month, hour_of_day,
        load_zone, scheduled_curtailment_mw
        FROM (
            SELECT scenario_id, subproblem_id, stage_id, period, horizon, 
            timepoint, timepoint_weight, number_of_hours_in_timepoint, 
            load_zone, 
            sum(scheduled_curtailment_mw) AS scheduled_curtailment_mw
            FROM results_project_dispatch_variable
            GROUP BY subproblem_id, stage_id, timepoint, load_zone
        ) as agg_curtailment_tbl
        JOIN (
            SELECT subproblem_id, period, timepoint, month,  hour_of_day
            FROM inputs_temporal_timepoints
            WHERE temporal_scenario_id = (
                SELECT temporal_scenario_id 
                FROM scenarios
                WHERE scenario_id = ?
                )
        ) as tmp_info_tbl
        USING (subproblem_id, period, timepoint)
        WHERE scenario_id = ?
        ORDER BY subproblem_id, stage_id, load_zone, timepoint;"""

    spin_on_database_lock(
        conn=db, cursor=c, sql=insert_sql,
        data=(subscenarios.SCENARIO_ID, subscenarios.SCENARIO_ID),
        many=False
    )
