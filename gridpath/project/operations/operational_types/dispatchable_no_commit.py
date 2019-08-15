#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of no-commit generators, a proxy for a perfectly flexible generator
with constant heat rate, no minimum output, and no ramp rate limits.
"""

import pandas as pd
from pyomo.environ import Set, Var, Constraint, NonNegativeReals

from gridpath.auxiliary.auxiliary import generator_subset_init,\
    write_validation_to_database, check_prj_columns, check_constant_heat_rate
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
        generator_subset_init("operational_type", "dispatchable_no_commit")
    )

    m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_NO_COMMIT_GENERATORS))

    # Variables
    m.Provide_Power_DispNoCommit_MW = Var(
        m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )

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
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, headroom_variables)[g]) \
            <= mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]]
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
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, footroom_variables)[g]) \
            >= 0
    m.DispNoCommit_Min_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_power_rule
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
        * mod.availability_derate[g, mod.horizon[tmp]]


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
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        return None
    else:
        return mod.Provide_Power_DispNoCommit_MW[g, tmp] - \
            mod.Provide_Power_DispNoCommit_MW[g, mod.previous_timepoint[tmp]]


def power_delta_rule(mod, g, tmp):
    """
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        pass
    else:
        return mod.Provide_Power_DispNoCommit_MW[g, tmp] - \
               mod.Provide_Power_DispNoCommit_MW[
                   g, mod.previous_timepoint[tmp]
               ]


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
            "dispatchable_no_commit"
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
                   "dispatchable_no_commit",
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
        "ramp_up_when_on_rate",
        "ramp_down_when_on_rate",
        "min_up_time_hours", "min_down_time_hours",
        "charging_efficiency", "discharging_efficiency",
        "minimum_duration_hours"
    ]
    validation_errors = check_prj_columns(df, expected_na_columns, False,
                                          "Dispatchable_no_commit")
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
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
             __name__,
             "PROJECT_HEAT_RATE_CURVES",
             "inputs_project_heat_rate_curves",
             "Too many load points",
             error
             )
        )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)
