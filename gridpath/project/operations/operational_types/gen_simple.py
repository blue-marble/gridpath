#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This operational type describes generators that can vary their output
between zero and full capacity in every timepoint in which they are available
(i.e. they have a power output variable but no commitment variables associated
with them).

The heat rate of these generators does not degrade below full load and they
can be allowed to provide upward and/or downward reserves subject to
available headroom and footroom. Ramp limits can be optionally specified.

Costs for this operational type include fuel costs, variable O&M costs, and
startup and shutdown costs.

"""

import os
import pandas as pd
from pyomo.environ import Set, Var, Constraint, NonNegativeReals, Param, \
    PercentFraction, Expression

from gridpath.auxiliary.auxiliary import generator_subset_init,\
    write_validation_to_database, check_req_prj_columns, \
    check_constant_heat_rate
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.common_functions import \
    check_if_linear_horizon_first_timepoint


def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_SIMPLE`                                                    |
    |                                                                         |
    | The set of generators of the :code:`gen_simple` operational type.       |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_SIMPLE_OPR_TMPS`                                           |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_simple`           |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_simple_ramp_up_rate`                                       |
    | | *Defined over*: :code:`GEN_SIMPLE`                                    |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's upward ramp rate limit during operations, defined as a    |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_simple_ramp_down_rate`                                     |
    | | *Defined over*: :code:`GEN_SIMPLE`                                    |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's downward ramp rate limit during operations, defined as a  |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`GenSimple_Provide_Power_MW`                                    |
    | | *Defined over*: :code:`GEN_SIMPLE_OPR_TMPS`                           |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Power provision in MW from this project in each timepoint in which the  |
    | project is operational (capacity exists and the project is available).  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | Power                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenSimple_Max_Power_Constraint`                                |
    | | *Defined over*: :code:`GEN_SIMPLE_OPR_TMPS`                           |
    |                                                                         |
    | Limits the power plus upward reserves to the available capacity.        |
    +-------------------------------------------------------------------------+
    | | :code:`GenSimple_Min_Power_Constraint`                                |
    | | *Defined over*: :code:`GEN_SIMPLE_OPR_TMPS`                           |
    |                                                                         |
    | Power provision minus downward reserves should exceed the minimum       |
    | stable level for the project.                                           |
    +-------------------------------------------------------------------------+
    | Ramps                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenSimple_Ramp_Up_Constraint`                                  |
    | | *Defined over*: :code:`GEN_SIMPLE_OPR_TMPS`                           |
    |                                                                         |
    | Limits the allowed project upward ramp based on the                     |
    | :code:`gen_simple_ramp_up_rate`.                                        |
    +-------------------------------------------------------------------------+
    | | :code:`GenSimple_Ramp_Down_Constraint`                                |
    | | *Defined over*: :code:`GEN_SIMPLE_OPR_TMPS`                           |
    |                                                                         |
    | Limits the allowed project downward ramp based on the                   |
    | :code:`gen_simple_ramp_down_rate`.                                      |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.GEN_SIMPLE = Set(
        within=m.PROJECTS,
        initialize=generator_subset_init("operational_type", "gen_simple")
    )

    m.GEN_SIMPLE_OPR_TMPS = Set(
        dimen=2, within=m.PRJ_OPR_TMPS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS
            if g in mod.GEN_SIMPLE)
    )

    # Optional Params
    ###########################################################################

    m.gen_simple_ramp_up_rate = Param(
        m.GEN_SIMPLE, within=PercentFraction,
        default=1
    )
    m.gen_simple_ramp_down_rate = Param(
        m.GEN_SIMPLE, within=PercentFraction,
        default=1
    )

    # Variables
    ###########################################################################

    m.GenSimple_Provide_Power_MW = Var(
        m.GEN_SIMPLE_OPR_TMPS,
        within=NonNegativeReals
    )

    # Expressions
    ###########################################################################

    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])
    m.GenSimple_Upwards_Reserves_MW = Expression(
        m.GEN_SIMPLE_OPR_TMPS,
        rule=upwards_reserve_rule
    )

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])
    m.GenSimple_Downwards_Reserves_MW = Expression(
        m.GEN_SIMPLE_OPR_TMPS,
        rule=downwards_reserve_rule
    )

    # Constraints
    ###########################################################################

    m.GenSimple_Max_Power_Constraint = Constraint(
        m.GEN_SIMPLE_OPR_TMPS,
        rule=max_power_rule
    )

    m.GenSimple_Min_Power_Constraint = Constraint(
        m.GEN_SIMPLE_OPR_TMPS,
        rule=min_power_rule
    )

    m.GenSimple_Ramp_Up_Constraint = Constraint(
        m.GEN_SIMPLE_OPR_TMPS,
        rule=ramp_up_rule
    )

    m.GenSimple_Ramp_Down_Constraint = Constraint(
        m.GEN_SIMPLE_OPR_TMPS,
        rule=ramp_down_rule
    )


# Constraint Formulation Rules
###############################################################################

# Power
def max_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenSimple_Max_Power_Constraint
    **Enforced Over**: GEN_SIMPLE_OPR_TMPS

    Power plus upward services cannot exceed capacity.
    """
    return mod.GenSimple_Provide_Power_MW[g, tmp] \
        + mod.GenSimple_Upwards_Reserves_MW[g, tmp] \
        <= mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def min_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenSimple_Min_Power_Constraint
    **Enforced Over**: GEN_SIMPLE_OPR_TMPS

    Power minus downward services cannot be below zero.
    """
    return mod.GenSimple_Provide_Power_MW[g, tmp] \
        - mod.GenSimple_Downwards_Reserves_MW[g, tmp] \
        >= 0


# Ramps
def ramp_up_rule(mod, g, tmp):
    """
    **Constraint Name**: GenSimple_Ramp_Up_Constraint
    **Enforced Over**: GEN_SIMPLE_OPR_TMPS

    Difference between power generation of consecutive timepoints, adjusted
    for reserve provision in current and previous timepoint, has to obey
    ramp up rate limits.

    We assume that a unit has to reach its setpoint at the start of the
    timepoint; as such, the ramping between 2 timepoints is assumed to
    take place during the duration of the first timepoint, and the
    ramp rate limit is adjusted for the duration of the first timepoint.
    """
    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    # If ramp rate limits, adjusted for timepoint duration, allow you to
    # ramp up the full operable range between timepoints, constraint won't
    # bind, so skip
    elif (mod.gen_simple_ramp_up_rate[g] * 60
          * mod.hrs_in_tmp[mod.prev_tmp[
                tmp, mod.balancing_type_project[g]]]
          >= 1):
        return Constraint.Skip
    else:
        return mod.GenSimple_Provide_Power_MW[g, tmp] \
            + mod.GenSimple_Upwards_Reserves_MW[g, tmp] \
            - (mod.GenSimple_Provide_Power_MW[
                   g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]]
               - mod.GenSimple_Downwards_Reserves_MW[
                   g, mod.prev_tmp[tmp, mod.balancing_type_project[
                       g]]]) \
            <= \
            mod.gen_simple_ramp_up_rate[g] * 60 \
            * mod.hrs_in_tmp[
                   mod.prev_tmp[tmp, mod.balancing_type_project[g]]] \
            * mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.Availability_Derate[g, tmp]


def ramp_down_rule(mod, g, tmp):
    """
    **Constraint Name**: GenSimple_Ramp_Down_Constraint
    **Enforced Over**: GEN_SIMPLE_OPR_TMPS

    Difference between power generation of consecutive timepoints, adjusted
    for reserve provision in current and previous timepoint, has to obey
    ramp down rate limits.

    We assume that a unit has to reach its setpoint at the start of the
    timepoint; as such, the ramping between 2 timepoints is assumed to
    take place during the duration of the first timepoint, and the
    ramp rate limit is adjusted for the duration of the first timepoint.
    """
    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        return Constraint.Skip
    # If ramp rate limits, adjusted for timepoint duration, allow you to
    # ramp down the full operable range between timepoints, constraint
    # won't bind, so skip
    elif (mod.gen_simple_ramp_down_rate[g] * 60
          * mod.hrs_in_tmp[
              mod.prev_tmp[tmp, mod.balancing_type_project[g]]]
          >= 1):
        return Constraint.Skip
    else:
        return mod.GenSimple_Provide_Power_MW[g, tmp] \
            - mod.GenSimple_Downwards_Reserves_MW[g, tmp] \
            - (mod.GenSimple_Provide_Power_MW[
                   g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]]
               + mod.GenSimple_Upwards_Reserves_MW[
                   g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]]
               ) \
            >= \
            - mod.gen_simple_ramp_down_rate[g] * 60 \
            * mod.hrs_in_tmp[
                   mod.prev_tmp[tmp, mod.balancing_type_project[g]]] \
            * mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.Availability_Derate[g, tmp]


# Operational Type Methods
###############################################################################

def power_provision_rule(mod, g, tmp):
    """
    Power provision from simple generators is an endogenous variable.
    """
    return mod.GenSimple_Provide_Power_MW[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since there is no commitment, all capacity is assumed to be online.
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision from simple generators, if eligible, is an endogenous
    variable.
    """
    return mod.GenSimple_Provide_Power_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    No 'curtailment' -- simply dispatch down
    """
    return 0


# TODO: ignoring subhourly behavior for dispatchable gens for now
def subhourly_curtailment_rule(mod, g, tmp):
    """
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    """
    return 0


# TODO: add data check that there is indeed only 1 segment for must-run
#   generators (and therefore there is no intercept)
def fuel_burn_rule(mod, g, tmp):
    """
    Fuel burn is the product of the fuel burn slope and the power output. For
    simple generators we assume only one average heat rate is specified in
    heat_rate_curves.tab, so the fuel burn slope is equal to the specified
    heat rate and the intercept is zero.
    """
    if g in mod.FUEL_PRJS:
        return mod.fuel_burn_slope_mmbtu_per_mwh[g, 0] \
            * mod.GenSimple_Provide_Power_MW[g, tmp]
    else:
        return 0


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


def variable_om_cost_rule(mod, g, tmp):
    """
    """
    return mod.GenSimple_Provide_Power_MW[g, tmp] \
        * mod.variable_om_cost_per_mwh[g]


def startup_fuel_burn_rule(mod, g, tmp):
    """
    Since there is no commitment, there is no concept of starting up.
    """
    return 0


def power_delta_rule(mod, g, tmp):
    """
    """
    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        pass
    else:
        return mod.GenSimple_Provide_Power_MW[g, tmp] - \
               mod.GenSimple_Provide_Power_MW[
                   g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
               ]


# Input-Output
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

    ramp_up_rate = dict()
    ramp_down_rate = dict()
    header = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t", header=None, nrows=1
    ).values[0]

    optional_columns = ["ramp_up_when_on_rate", "ramp_down_when_on_rate"]
    used_columns = [c for c in optional_columns if c in header]

    df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "operational_type"] + used_columns
    )

    # Ramp rate limits are optional; will default to 1 if not specified
    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(df["project"],
                       df["operational_type"],
                       df["ramp_up_when_on_rate"]
                       ):
            if row[1] == "gen_simple" and row[2] != ".":
                ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_simple_ramp_up_rate"] = \
            ramp_up_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(df["project"],
                       df["operational_type"],
                       df["ramp_down_when_on_rate"]
                       ):
            if row[1] == "gen_simple" and row[2] != ".":
                ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_simple_ramp_down_rate"] = \
            ramp_down_rate


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

    validation_results = []

    # Read in inputs to be validated
    c1 = conn.cursor()
    projects = c1.execute(
        """SELECT project, operational_type,
        fuel, min_stable_level, unit_size_mw,
        startup_cost_per_mw, shutdown_cost_per_mw,
        startup_fuel_mmbtu_per_mw,
        startup_plus_ramp_up_rate,
        shutdown_plus_ramp_down_rate,
        ramp_up_when_on_rate,
        ramp_down_when_on_rate,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours, maximum_duration_hours
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, operational_type,
        fuel, min_stable_level, unit_size_mw,
        startup_cost_per_mw, shutdown_cost_per_mw,
        startup_fuel_mmbtu_per_mw,
        startup_plus_ramp_up_rate,
        shutdown_plus_ramp_down_rate,
        ramp_up_when_on_rate,
        ramp_down_when_on_rate,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours, maximum_duration_hours
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}) as prj_chars
        USING (project)
        WHERE project_portfolio_scenario_id = {}
        AND operational_type = '{}'""".format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            "gen_simple"
        )
    )

    c2 = conn.cursor()
    heat_rates = c2.execute(
        """
        SELECT project, load_point_fraction
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, operational_type, heat_rate_curves_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = '{}') AS op_char
        USING(project)
        INNER JOIN
        (SELECT project, heat_rate_curves_scenario_id, load_point_fraction
        FROM inputs_project_heat_rate_curves) as heat_rates
        USING(project, heat_rate_curves_scenario_id)
        WHERE project_portfolio_scenario_id = {}
        """.format(subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
                   "gen_simple",
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
                   )
    )

    # Convert inputs to dataframe
    df = pd.DataFrame(
        data=projects.fetchall(),
        columns=[s[0] for s in projects.description]
    )
    hr_df = pd.DataFrame(
        data=heat_rates.fetchall(),
        columns=[s[0] for s in heat_rates.description]
    )

    # Check that there are no unexpected operational inputs
    expected_na_columns = [
        "min_stable_level",
        "unit_size_mw",
        "startup_cost_per_mw", "shutdown_cost_per_mw",
        "startup_fuel_mmbtu_per_mw",
        "startup_plus_ramp_up_rate",
        "shutdown_plus_ramp_down_rate",
        "min_up_time_hours", "min_down_time_hours",
        "charging_efficiency", "discharging_efficiency",
        "minimum_duration_hours", "maximum_duration_hours"
    ]
    validation_errors = check_req_prj_columns(df, expected_na_columns, False,
                                              "gen_simple")
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "Low",
             "Unexpected inputs",
             error
             )
        )

    # Check that there is only one load point (constant heat rate)
    validation_errors = check_constant_heat_rate(hr_df,
                                                 "gen_simple")
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_HEAT_RATE_CURVES",
             "inputs_project_heat_rate_curves",
             "Mid",
             "Too many load points",
             error
             )
        )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)
