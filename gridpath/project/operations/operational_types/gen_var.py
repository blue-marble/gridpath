#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This operational type describes generator projects whose power output is equal
to a pre-specified fraction of their available capacity (a capacity factor
parameter) in every timepoint, e.g. a wind farm with variable output depending
on local weather. Curtailment (dispatch down) is allowed. GridPath includes
experimental features to allow these generators to provide upward and/or
downward reserves.

Costs for this operational type include variable O&M costs.

"""
from __future__ import division
from __future__ import print_function

from builtins import zip

import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, Var, Constraint, NonNegativeReals, \
    Expression, value
import warnings

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import generator_subset_init
from gridpath.auxiliary.dynamic_components import \
    footroom_variables, headroom_variables, reserve_variable_derate_params
from gridpath.project.operations.reserves.subhourly_energy_adjustment import \
    footroom_subhourly_energy_adjustment_rule, \
    headroom_subhourly_energy_adjustment_rule
from gridpath.project.common_functions import \
    check_if_linear_horizon_first_timepoint
from gridpath.project.operations.operational_types.common_functions import \
    update_dispatch_results_table


def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_VAR`                                                       |
    |                                                                         |
    | The set of generators of the :code:`gen_var` operational type.          |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_VAR_OPR_TMPS`                                              |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_var`              |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_var_cap_factor`                                            |
    | | *Defined over*: :code:`GEN_VAR`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's power output in each operational timepoint as a fraction  |
    | of its available capacity (i.e. the capacity factor).                   |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`GenVar_Provide_Power_MW`                                       |
    | | *Defined over*: :code:`GEN_VAR_OPR_TMPS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Power provision in MW from this project in each timepoint in which the  |
    | project is operational (capacity exists and the project is available).  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`GenVar_Subhourly_Curtailment_MW`                               |
    | | *Defined over*: :code:`GEN_VAR_OPR_TMPS`                              |
    |                                                                         |
    | Sub-hourly curtailment (in MW) from providing downward reserves.        |
    +-------------------------------------------------------------------------+
    | | :code:`GenVar_Subhourly_Energy_Delivered_MW`                          |
    | | *Defined over*: :code:`GEN_VAR_OPR_TMPS`                              |
    |                                                                         |
    | Sub-hourly energy delivered (in MW) from providing upward reserves.     |
    +-------------------------------------------------------------------------+
    | | :code:`GenVar_Scheduled_Curtailment_MW`                               |
    | | *Defined over*: :code:`GEN_VAR_OPR_TMPS`                              |
    |                                                                         |
    | The available power minus what was actually provided (in MW).           |
    +-------------------------------------------------------------------------+
    | | :code:`GenVar_Total_Curtailment_MW`                                   |
    | | *Defined over*: :code:`GEN_VAR_OPR_TMPS`                              |
    |                                                                         |
    | Scheduled curtailment (in MW) plus an upward adjustment for additional  |
    | curtailment when providing downward reserves, and a downward adjustment |
    | adjustment for a reduction in curtailment when providing upward         |
    | reserves, to account for sub-hourly dispatch when providing reserves.   |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | Power                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenVar_Max_Power_Constraint`                                   |
    | | *Defined over*: :code:`GEN_VAR_OPR_TMPS`                              |
    |                                                                         |
    | Limits the power plus upward reserves in each timepoint based on the    |
    | :code:`gen_var_cap_factor` and the available capacity.                  |
    +-------------------------------------------------------------------------+
    | | :code:`GenVar_Min_Power_Constraint`                                   |
    | | *Defined over*: :code:`GEN_VAR_OPR_TMPS`                              |
    |                                                                         |
    | Power provision minus downward reserves should exceed zero.             |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################
    m.GEN_VAR = Set(
        within=m.PROJECTS,
        initialize=generator_subset_init("operational_type", "gen_var"))

    m.GEN_VAR_OPR_TMPS = Set(
        dimen=2, within=m.PRJ_OPR_TMPS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS
            if g in mod.GEN_VAR)
    )

    # Required Params
    ###########################################################################

    # TODO: allow cap factors greater than 1, but throw a warning?
    m.gen_var_cap_factor = Param(
        m.GEN_VAR_OPR_TMPS,
        within=NonNegativeReals
    )

    # Variables
    ###########################################################################

    m.GenVar_Provide_Power_MW = Var(
        m.GEN_VAR_OPR_TMPS,
        within=NonNegativeReals
    )

    # Expressions
    ###########################################################################

    def upwards_reserve_rule(mod, g, tmp):
        """
        Gather all headroom variables, and de-rate the total reserves offered
        to account for the fact that gen_var output is uncertain.
        """
        return sum(
            getattr(mod, c)[g, tmp]
            / getattr(mod, getattr(d, reserve_variable_derate_params)[c])[g]
            for c in getattr(d, headroom_variables)[g]
        )

    m.GenVar_Upwards_Reserves_MW = Expression(
        m.GEN_VAR_OPR_TMPS,
        rule=upwards_reserve_rule
    )

    def downwards_reserve_rule(mod, g, tmp):
        """
        Gather all footroom variables, and de-rate the total reserves offered
        to account for the fact that gen_var output is uncertain.
        """
        return sum(
            getattr(mod, c)[g, tmp]
            / getattr(mod, getattr(d, reserve_variable_derate_params)[c])[g]
            for c in getattr(d, footroom_variables)[g]
        )

    m.GenVar_Downwards_Reserves_MW = Expression(
        m.GEN_VAR_OPR_TMPS,
        rule=downwards_reserve_rule
    )

    def subhourly_curtailment_expression_rule(mod, g, tmp):
        """
        Sub-hourly curtailment from providing downward reserves.
        """
        return footroom_subhourly_energy_adjustment_rule(d, mod, g, tmp)

    m.GenVar_Subhourly_Curtailment_MW = Expression(
        m.GEN_VAR_OPR_TMPS,
        rule=subhourly_curtailment_expression_rule
    )

    def subhourly_delivered_energy_expression_rule(mod, g, tmp):
        """
        Sub-hourly energy delivered from providing upward reserves.
        """
        return headroom_subhourly_energy_adjustment_rule(d, mod, g, tmp)

    m.GenVar_Subhourly_Energy_Delivered_MW = Expression(
        m.GEN_VAR_OPR_TMPS,
        rule=subhourly_delivered_energy_expression_rule
    )

    m.GenVar_Scheduled_Curtailment_MW = Expression(
        m.GEN_VAR_OPR_TMPS,
        rule=scheduled_curtailment_expression_rule
    )

    m.GenVar_Total_Curtailment_MW = Expression(
        m.GEN_VAR_OPR_TMPS,
        rule=total_curtailment_expression_rule
    )

    # Constraints
    ###########################################################################

    m.GenVar_Max_Power_Constraint = Constraint(
        m.GEN_VAR_OPR_TMPS,
        rule=max_power_rule
    )

    m.GenVar_Min_Power_Constraint = Constraint(
        m.GEN_VAR_OPR_TMPS,
        rule=min_power_rule
    )


# Expression Methods
###############################################################################

def scheduled_curtailment_expression_rule(mod, g, tmp):
    """
    **Expression Name**: GenVar_Scheduled_Curtailment_MW
    **Defined Over**: GEN_VAR_OPR_TMPS

    Scheduled curtailment is the available power minus what was actually
    provided.
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp] \
        * mod.gen_var_cap_factor[g, tmp] \
        - mod.GenVar_Provide_Power_MW[g, tmp]


def total_curtailment_expression_rule(mod, g, tmp):
    """
    **Expression Name**: GenVar_Total_Curtailment_MW
    **Defined Over**: GEN_VAR_OPR_TMPS

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
    so don't multiply capacity by Availability_Derate here (will count
    as curtailment).
    """

    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.gen_var_cap_factor[g, tmp] \
        - mod.GenVar_Provide_Power_MW[g, tmp] \
        + mod.GenVar_Subhourly_Curtailment_MW[g, tmp] \
        - mod.GenVar_Subhourly_Energy_Delivered_MW[g, tmp]


# Constraint Formulation Rules
###############################################################################

def max_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenVar_Max_Power_Constraint
    **Enforced Over**: GEN_VAR_OPR_TMPS

    Power provision plus upward services cannot exceed available power, which
    is equal to the available capacity multiplied by the capacity factor.
    """
    return mod.GenVar_Provide_Power_MW[g, tmp] \
        + mod.GenVar_Upwards_Reserves_MW[g, tmp] \
        <= mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp] \
        * mod.gen_var_cap_factor[g, tmp]


def min_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenVar_Min_Power_Constraint
    **Enforced Over**: GEN_VAR_OPR_TMPS

    Power provision minus downward services cannot be less than zero.
    """
    return mod.GenVar_Provide_Power_MW[g, tmp] \
        - mod.GenVar_Downwards_Reserves_MW[g, tmp] \
        >= 0


# Operational Type Methods
###############################################################################

def power_provision_rule(mod, g, tmp):
    """
    Power provision from variable generators is their capacity times the
    capacity factor in each timepoint minus any upward reserves/curtailment.
    """

    return mod.GenVar_Provide_Power_MW[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since no commitment, all capacity assumed online
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision from variable generators is a variable lesser than or
    equal to capacity times the capacity factor in each timepoint minus any
    upward reserves/curtailment. See max_power_rule above.
    """
    return mod.GenVar_Provide_Power_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    Variable generation can be dispatched down, i.e. scheduled below the
    available energy
    """
    return mod.GenVar_Scheduled_Curtailment_MW[g, tmp]


def subhourly_curtailment_rule(mod, g, tmp):
    """
    If providing downward reserves, variable generators will occasionally
    have to be dispatched down relative to their schedule, resulting in
    additional curtailment within the hour
    """
    return mod.GenVar_Subhourly_Curtailment_MW[g, tmp]


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    If providing upward reserves, variable generators will occasionally be
    dispatched up, so additional energy will be delivered within the hour
    relative to their schedule (less curtailment)
    """
    return mod.GenVar_Subhourly_Energy_Delivered_MW[g, tmp]


def fuel_burn_rule(mod, g, tmp):
    """
    Variable generators should not have fuel use.
    """
    if g in mod.FUEL_PRJS:
        raise ValueError(
            "ERROR! gen_var projects should not use fuel." + "\n" +
            "Check input data for project '{}'".format(g) + "\n" +
            "and change its fuel to '.' (no value)."
        )
    else:
        return 0


def variable_om_cost_rule(mod, g, tmp):
    """
    """
    return mod.GenVar_Provide_Power_MW[g, tmp] \
        * mod.variable_om_cost_per_mwh[g]


def startup_cost_rule(mod, g, tmp):
    """
    Since there is no commitment, there is no concept of starting up.
    """
    return 0


def shutdown_cost_rule(mod, g, tmp):
    """
    Since there is no commitment, there is no concept of shutting down.
    """
    return 0


def startup_fuel_burn_rule(mod, g, tmp):
    """
    Since there is no commitment, there is no concept of starting up.
    """
    return 0


def power_delta_rule(mod, g, tmp):
    """
    Curtailment is counted as part of the ramp here; excludes any ramping from
    reserve provision.
    """
    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        pass
    else:
        return \
            (mod.Capacity_MW[g, mod.period[tmp]]
             * mod.Availability_Derate[g, tmp]
             * mod.gen_var_cap_factor[g, tmp]) \
            - (mod.Capacity_MW[g, mod.period[mod.prev_tmp[
                tmp, mod.balancing_type_project[g]]]]
               * mod.Availability_Derate[g, mod.prev_tmp[
                tmp, mod.balancing_type_project[g]]]
               * mod.gen_var_cap_factor[g, mod.prev_tmp[
                tmp, mod.balancing_type_project[g]]])


# Inputs-Outputs
###############################################################################

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
    var_must_take_prjs = list()

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
            var_must_take_prjs.append(row[0])
        else:
            pass

    # Determine subset of project-timepoints in variable profiles file
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
            cap_factor[(row[0], row[1])] = float(row[2])
        # Profile could be for a 'gen_var' project, in which case ignore
        elif row[0] in var_must_take_prjs:
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
    data_portal.data()["gen_var_cap_factor"] = cap_factor


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
        writer.writerow(["project", "period", "balancing_type_project",
                         "horizon", "timepoint", "timepoint_weight",
                         "number_of_hours_in_timepoint",
                         "technology", "load_zone",
                         "power_mw", "scheduled_curtailment_mw",
                         "subhourly_curtailment_mw",
                         "subhourly_energy_delivered_mw",
                         "total_curtailment_mw"
                         ])

        for (p, tmp) in mod.GEN_VAR_OPR_TMPS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.balancing_type_project[p],
                mod.horizon[tmp, mod.balancing_type_project[p]],
                tmp,
                mod.tmp_weight[tmp],
                mod.hrs_in_tmp[tmp],
                mod.technology[p],
                mod.load_zone[p],
                value(mod.GenVar_Provide_Power_MW[p, tmp]),
                value(mod.GenVar_Scheduled_Curtailment_MW[p, tmp]),
                value(mod.GenVar_Subhourly_Curtailment_MW[p, tmp]),
                value(mod.GenVar_Subhourly_Energy_Delivered_MW[p, tmp]),
                value(mod.GenVar_Total_Curtailment_MW[p, tmp])
            ])


# Database
###############################################################################

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
                FROM inputs_project_specified_capacity
                WHERE project_specified_capacity_scenario_id = {}
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
            subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID
        )
    )

    return variable_profiles


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
            writer = csv.writer(variable_profiles_tab_file, delimiter="\t", lineterminator="\n")
            for row in variable_profiles:
                writer.writerow(row)
    # If variable_generator_profiles.tab does not exist, write header first,
    # then add profiles data
    else:
        with open(os.path.join(inputs_directory,
                               "variable_generator_profiles.tab"), "w", newline="") as \
                variable_profiles_tab_file:
            writer = csv.writer(variable_profiles_tab_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                ["project", "timepoint", "cap_factor"]
            )
            for row in variable_profiles:
                writer.writerow(row)


def import_module_specific_results_to_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """
    
    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c: 
    :param db: 
    :param results_directory:
    :param quiet:
    :return: 
    """
    if not quiet:
        print("project dispatch variable")

    update_dispatch_results_table(
        db=db, c=c, results_directory=results_directory,
        scenario_id=scenario_id, subproblem=subproblem, stage=stage,
        results_file="dispatch_variable.csv"
    )


def process_module_specific_results(db, c, subscenarios, quiet):
    """
    Aggregate scheduled curtailment
    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
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
        (scenario_id, subproblem_id, stage_id, period, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, month, hour_of_day,
        load_zone, scheduled_curtailment_mw)
        SELECT
        scenario_id, subproblem_id, stage_id, period, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, month, hour_of_day,
        load_zone, scheduled_curtailment_mw
        FROM (
            SELECT scenario_id, subproblem_id, stage_id, period, 
            timepoint, timepoint_weight, number_of_hours_in_timepoint, 
            load_zone, 
            sum(scheduled_curtailment_mw) AS scheduled_curtailment_mw
            FROM results_project_dispatch
            WHERE operational_type = 'gen_var'
            GROUP BY scenario_id, subproblem_id, stage_id, timepoint, load_zone
        ) as agg_curtailment_tbl
        JOIN (
            SELECT subproblem_id, stage_id, timepoint, month, hour_of_day
            FROM inputs_temporal_timepoints
            WHERE temporal_scenario_id = (
                SELECT temporal_scenario_id 
                FROM scenarios
                WHERE scenario_id = ?
                )
        ) as tmp_info_tbl
        USING (subproblem_id, stage_id, timepoint)
        WHERE scenario_id = ?
        ORDER BY subproblem_id, stage_id, load_zone, timepoint;"""

    spin_on_database_lock(
        conn=db, cursor=c, sql=insert_sql,
        data=(subscenarios.SCENARIO_ID, subscenarios.SCENARIO_ID),
        many=False
    )


# Validation
###############################################################################

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
