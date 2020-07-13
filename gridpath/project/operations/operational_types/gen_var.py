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


import csv
import os.path
from pyomo.environ import Param, Set, Var, Constraint, NonNegativeReals, \
    Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import generator_subset_init
from gridpath.auxiliary.dynamic_components import \
    footroom_variables, headroom_variables, reserve_variable_derate_params
from gridpath.project.operations.reserves.subhourly_energy_adjustment import \
    footroom_subhourly_energy_adjustment_rule, \
    headroom_subhourly_energy_adjustment_rule
from gridpath.project.common_functions import \
    check_if_first_timepoint, check_boundary_type
from gridpath.project.operations.operational_types.common_functions import \
    update_dispatch_results_table, load_var_profile_inputs, \
    get_var_profile_inputs_from_database, write_tab_file_model_inputs, \
    validate_opchars, validate_var_profiles, load_optype_module_specific_data


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
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_var_variable_om_cost_per_mwh`                              |
    | | *Defined over*: :code:`GEN_VAR`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The variable operations and maintenance (O&M) cost for each project in  |
    | $ per MWh.                                                              |
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

    # Optional Params
    ###########################################################################

    m.gen_var_variable_om_cost_per_mwh = Param(
        m.GEN_VAR, within=NonNegativeReals,
        default=0
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
        * mod.gen_var_variable_om_cost_per_mwh[g]


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

    This rule is only used in tuning costs, so fine to skip for linked
    horizon's first timepoint.
    """
    if check_if_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ) and (
        check_boundary_type(
            mod=mod, tmp=tmp,
            balancing_type=mod.balancing_type_project[g],
            boundary_type="linear"
        ) or
        check_boundary_type(
            mod=mod, tmp=tmp,
            balancing_type=mod.balancing_type_project[g],
            boundary_type="linked"
        )
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
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Load data from projects.tab and get the list of projects of this type
    projects = load_optype_module_specific_data(
        mod=mod, data_portal=data_portal,
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, op_type="gen_var"
    )

    load_var_profile_inputs(
        data_portal, scenario_directory, subproblem, stage, "gen_var"
    )


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
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
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
    :return: cursor object with query results
    """

    return get_var_profile_inputs_from_database(
        subscenarios, subproblem, stage, conn, "gen_var"
    )


def write_module_specific_model_inputs(
        scenario_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    variable_generator_profiles.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    data = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)
    fname = "variable_generator_profiles.tab"

    write_tab_file_model_inputs(
        scenario_directory, subproblem, stage, fname, data
    )


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
            FROM inputs_temporal
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

    # Validate operational chars table inputs
    validate_opchars(subscenarios, subproblem, stage, conn, "gen_var")

    # Validate var profiles input table
    validate_var_profiles(subscenarios, subproblem, stage, conn, "gen_var")
