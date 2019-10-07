#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module describes the operations of must-run generators. These
generators can provide power but not reserves.
"""

import warnings
import pandas as pd
from pyomo.environ import Constraint, Set

from gridpath.auxiliary.auxiliary import generator_subset_init, \
    write_validation_to_database, check_req_prj_columns, \
    check_constant_heat_rate, get_projects_by_reserve, \
    check_projects_for_reserves
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to


    """

    # TODO: do we need this set or can we remove it
    m.MUST_RUN_GENERATORS = Set(within=m.PROJECTS,
                                initialize=generator_subset_init(
                                    "operational_type", "must_run")
                                )

    # TODO: do we need this set or can we remove it?
    m.MUST_RUN_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.MUST_RUN_GENERATORS))

    # TODO: remove this constraint once input validation is in place that
    #  does not allow specifying a reserve_zone if 'must_run' type
    def no_upwards_reserve_rule(mod, g, tmp):
        if getattr(d, headroom_variables)[g]:
            warnings.warn(
                """project {} is of the 'must_run' operational type and should 
                not be assigned any upward reserve BAs since it cannot provide 
                upward reserves. Please replace the upward reserve BA for 
                project {} with '.' (no value) in projects.tab. Model will add  
                constraint to ensure project {} cannot provide upward reserves
                """.format(g, g, g)
            )
            return sum(getattr(mod, c)[g, tmp]
                       for c in getattr(d, headroom_variables)[g]) == 0
        else:
            return Constraint.Skip
    m.Must_Run_No_Upwards_Reserves_Constraint = Constraint(
            m.MUST_RUN_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=no_upwards_reserve_rule)

    # TODO: remove this constraint once input validation is in place that
    #  does not allow specifying a reserve_zone if 'must_run' type
    def no_downwards_reserve_rule(mod, g, tmp):
        if getattr(d, footroom_variables)[g]:
            warnings.warn(
                """project {} is of the 'must_run' operational type and should 
                not be assigned any downward reserve BAs since it cannot provide 
                upwards reserves. Please replace the downward reserve BA for 
                project {} with '.' (no value) in projects.tab. Model will add  
                constraint to ensure project {} cannot provide downward reserves
                """.format(g, g, g)
            )
            return sum(getattr(mod, c)[g, tmp]
                       for c in getattr(d, footroom_variables)[g]) == 0
        else:
            return Constraint.Skip
    m.Must_Run_No_Downwards_Reserves_Constraint = Constraint(
            m.MUST_RUN_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=no_downwards_reserve_rule)


def power_provision_rule(mod, g, tmp):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param tmp: the operational timepoint
    :return: expression for power provision by must-run generators

    Power provision for must run generators is simply their capacity in all
    timepoints when they are operational.
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Maintenance_Derate[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since no commitment, all capacity assumed online
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Maintenance_Derate[g, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision for must-run generators, if eligible, is their capacity.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Maintenance_Derate[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    Can't dispatch down and curtailment not allowed
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_curtailment_rule(mod, g, tmp):
    """
    Can't provide reserves
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    Can't provide reserves
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def fuel_burn_rule(mod, g, tmp, error_message):
    """
    Output doesn't vary, so this is a constant
    Return 0 if must-run generator with no fuel (e.g. geothermal); these
    should not have been given a fuel or labeled carbonaceous in the first
    place
    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        return mod.fuel_burn_slope_mmbtu_per_mwh[g, 0] \
            * mod.Power_Provision_MW[g, tmp]
    else:
        raise ValueError(error_message)


def startup_shutdown_rule(mod, g, tmp):
    """
    Must-run generators are never started up or shut down
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise ValueError(
        "ERROR! Must-run generators should not incur startup/shutdown "
        "costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup/shutdown costs to '.' (no value)."
    )


def power_delta_rule(mod, g, tmp):
    """
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


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
            "must_run"
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
                   "must_run",
                   subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
                   )
    )

    # Convert inputs to data frame
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
    validation_errors = check_req_prj_columns(df, expected_na_columns, False,
                                              "Must_run")
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
    validation_errors = check_constant_heat_rate(hr_df, "Must_run")
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

    # Check that the project does not show up in any of the
    # inputs_project_reserve_bas tables since must_run can't provide any
    # reserves
    projects_by_reserve = get_projects_by_reserve(subscenarios, conn)
    for reserve, projects in projects_by_reserve.items():
        project_ba_id = "project_" + reserve + "_ba_scenario_id"
        table = "inputs_project_" + reserve + "_bas"
        validation_errors = check_projects_for_reserves(
            projects_op_type=df["project"],
            projects_w_ba=projects,
            operational_type="must_run",
            reserve=reserve
        )
        for error in validation_errors:
            validation_results.append(
                (subscenarios.SCENARIO_ID,
                 subproblem,
                 stage,
                 __name__,
                 project_ba_id.upper(),
                 table,
                 "Invalid {} BA inputs".format(reserve),
                 error
                 )
            )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)
