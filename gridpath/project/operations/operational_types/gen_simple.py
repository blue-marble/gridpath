#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of no-commit generators, a proxy for a perfectly flexible generator
with constant heat rate, no minimum output, and (optional) ramp rate limits.
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


def add_module_specific_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Sets
    m.DISPATCHABLE_NO_COMMIT_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type", "gen_simple")
    )

    m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_NO_COMMIT_GENERATORS))

    # Params
    # Ramp rates can be optionally specified and will default to 1 if not
    # Ramp rate units are "percent of project capacity per minute"
    m.dispatchable_no_commit_ramp_up_rate = \
        Param(m.DISPATCHABLE_NO_COMMIT_GENERATORS, within=PercentFraction,
              default=1)
    m.dispatchable_no_commit_ramp_down_rate = \
        Param(m.DISPATCHABLE_NO_COMMIT_GENERATORS, within=PercentFraction,
              default=1)

    # Variables
    m.Provide_Power_DispNoCommit_MW = Var(
        m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )

    # Expressions
    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])
    m.Dispatchable_No_Commit_Upwards_Reserves_MW = Expression(
        m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=upwards_reserve_rule)

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])
    m.Dispatchable_No_Commit_Downwards_Reserves_MW = Expression(
        m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=downwards_reserve_rule)

    # Operational constraints
    def max_power_rule(mod, g, tmp):
        """
        Power plus upward services cannot exceed capacity.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_DispNoCommit_MW[g, tmp] + \
            mod.Dispatchable_No_Commit_Upwards_Reserves_MW[g, tmp] \
            <= mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.Availability_Derate[g, tmp]
    m.DispNoCommit_Max_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=max_power_rule
        )

    def min_power_rule(mod, g, tmp):
        """
        Power minus downward services cannot be below 0 (no commitment variable).
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_DispNoCommit_MW[g, tmp] - \
            mod.Dispatchable_No_Commit_Downwards_Reserves_MW[g, tmp] \
            >= 0
    m.DispNoCommit_Min_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_power_rule
        )

    # Optional ramp constraints
    def ramp_up_rule(mod, g, tmp):
        """
        Difference between power generation of consecutive timepoints, adjusted
        for reserve provision in current and previous timepoint, has to obey
        ramp up rate limits.

        We assume that a unit has to reach its setpoint at the start of the
        timepoint; as such, the ramping between 2 timepoints is assumed to
        take place during the duration of the first timepoint, and the
        ramp rate limit is adjusted for the duration of the first timepoint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]
        ] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]
        ] \
                == "linear":
            return Constraint.Skip
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # ramp up the full operable range between timepoints, constraint won't
        # bind, so skip
        elif (mod.dispatchable_no_commit_ramp_up_rate[g] * 60
              * mod.number_of_hours_in_timepoint[mod.previous_timepoint[
                    tmp, mod.balancing_type_project[g]]]
              >= 1
              ):
            return Constraint.Skip
        else:
            return mod.Provide_Power_DispNoCommit_MW[g, tmp] \
                + mod.Dispatchable_No_Commit_Upwards_Reserves_MW[g, tmp] \
                - (mod.Provide_Power_DispNoCommit_MW[
                       g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
                   - mod.Dispatchable_No_Commit_Downwards_Reserves_MW[
                       g, mod.previous_timepoint[tmp, mod.balancing_type_project[
                           g]]]) \
                <= \
                mod.dispatchable_no_commit_ramp_up_rate[g] * 60 \
                * mod.number_of_hours_in_timepoint[
                       mod.previous_timepoint[tmp, mod.balancing_type_project[g]]] \
                * mod.Capacity_MW[g, mod.period[tmp]] \
                * mod.Availability_Derate[g, tmp]

    m.Dispatchable_No_Commit_Ramp_Up_Constraint = \
        Constraint(
            m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=ramp_up_rule
        )

    def ramp_down_rule(mod, g, tmp):
        """
        Difference between power generation of consecutive timepoints, adjusted
        for reserve provision in current and previous timepoint, has to obey
        ramp down rate limits.

        We assume that a unit has to reach its setpoint at the start of the
        timepoint; as such, the ramping between 2 timepoints is assumed to
        take place during the duration of the first timepoint, and the
        ramp rate limit is adjusted for the duration of the first timepoint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[
            mod.horizon[tmp, mod.balancing_type_project[g]]
        ] \
                and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] \
                == "linear":
            return Constraint.Skip
        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # ramp down the full operable range between timepoints, constraint
        # won't bind, so skip
        elif (mod.dispatchable_no_commit_ramp_down_rate[g] * 60
              * mod.number_of_hours_in_timepoint[
                  mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
              >= 1
              ):
            return Constraint.Skip
        else:
            return mod.Provide_Power_DispNoCommit_MW[g, tmp] \
                - mod.Dispatchable_No_Commit_Downwards_Reserves_MW[g, tmp] \
                - (mod.Provide_Power_DispNoCommit_MW[
                       g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
                   + mod.Dispatchable_No_Commit_Upwards_Reserves_MW[
                       g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]
                   ) \
                >= \
                - mod.dispatchable_no_commit_ramp_down_rate[g] * 60 \
                * mod.number_of_hours_in_timepoint[
                       mod.previous_timepoint[tmp, mod.balancing_type_project[g]]] \
                * mod.Capacity_MW[g, mod.period[tmp]] \
                * mod.Availability_Derate[g, tmp]

    m.Dispatchable_No_Commit_Ramp_Down_Constraint = \
        Constraint(
            m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=ramp_down_rule
        )


def power_provision_rule(mod, g, tmp):
    """
    Power provision from dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispNoCommit_MW[g, tmp]


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


def rec_provision_rule(mod, g, tmp):
    """
    REC provision from dispatchable generators, if eligible, is an endogenous
    variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispNoCommit_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    No 'curtailment' -- simply dispatch down
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


# TODO: ignoring subhourly behavior for dispatchable gens for now
def subhourly_curtailment_rule(mod, g, tmp):
    """
    
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


# TODO: add data check that there is indeed only 1 segment for must-run
#   generators (and therefore there is no intercept)
def fuel_burn_rule(mod, g, tmp, error_message):
    """
    Fuel burn is the product of the fuel burn slope and the power output. For
    no commit generators we assume only one average heat rate is specified
    in heat_rate_curves.tab, so the fuel burn slope is equal to the specified
    heat rate and the intercept is zero.
    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        return mod.fuel_burn_slope_mmbtu_per_mwh[g, 0] \
            * mod.Provide_Power_DispNoCommit_MW[g, tmp]
    else:
        raise ValueError(error_message)


def startup_shutdown_rule(mod, g, tmp):
    """
    No commit variables, so shouldn't happen
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] == "linear":
        return None
    else:
        return mod.Provide_Power_DispNoCommit_MW[g, tmp] - \
            mod.Provide_Power_DispNoCommit_MW[g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]


def power_delta_rule(mod, g, tmp):
    """
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp, mod.balancing_type_project[g]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[g]]] == "linear":
        pass
    else:
        return mod.Provide_Power_DispNoCommit_MW[g, tmp] - \
               mod.Provide_Power_DispNoCommit_MW[
                   g, mod.previous_timepoint[tmp, mod.balancing_type_project[g]]
               ]


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
    header = pd.read_csv(os.path.join(scenario_directory, subproblem, stage,
                                      "inputs", "projects.tab"),
                         sep="\t", header=None, nrows=1).values[0]

    optional_columns = ["ramp_up_when_on_rate",
                        "ramp_down_when_on_rate"]
    used_columns = [c for c in optional_columns if c in header]

    df = \
        pd.read_csv(
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
        data_portal.data()["dispatchable_no_commit_ramp_up_rate"] = \
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
        data_portal.data()["dispatchable_no_commit_ramp_down_rate"] = \
            ramp_down_rate


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
        minimum_duration_hours
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
        minimum_duration_hours
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
        SELECT project, load_point_mw
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, operational_type, heat_rate_curves_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = '{}') AS op_char
        USING(project)
        INNER JOIN
        (SELECT project, heat_rate_curves_scenario_id, load_point_mw
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
        "minimum_duration_hours"
    ]
    validation_errors = check_req_prj_columns(df, expected_na_columns, False,
                                          "Dispatchable_no_commit")
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "Unexpected inputs",
             error
             )
        )

    # Check that there is only one load point (constant heat rate)
    validation_errors = check_constant_heat_rate(hr_df,
                                                 "Dispatchable_no_commit")
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_HEAT_RATE_CURVES",
             "inputs_project_heat_rate_curves",
             "Too many load points",
             error
             )
        )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)
