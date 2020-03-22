#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module describes the operations of generation projects that that must
produce power in all timepoints they are available; unlike the must-run
generators, however, they can vary power output between a pre-specified
minimum stable level (greater than 0) and their available capacity.

The available capacity can either be a set input (e.g. for the gen_spec
capacity_type) or a decision variable by period (e.g. for the gen_new_lin
capacity_type). This makes this operational type suitable for both production
simulation type problems and capacity expansion problems.

The optimization makes the dispatch decisions in every timepoint. Heat rate
degradation below full load is considered. Always-on projects can be allowed to
provide upward and/or downward reserves, subject to the available headroom and
footroom. Ramp limits can be optionally specified.

Costs for this operational type include fuel costs and variable O&M costs.

"""

from __future__ import division

from builtins import zip
import os.path
import pandas as pd
from pyomo.environ import Param, Set, Var, NonNegativeReals, \
    PercentFraction, Constraint, Expression

from gridpath.auxiliary.auxiliary import generator_subset_init, \
    write_validation_to_database, check_req_prj_columns
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
    | | :code:`GEN_ALWAYS_ON`                                                 |
    |                                                                         |
    | The set of generators of the :code:`gen_always_on` operational type.    |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_ALWAYS_ON_OPR_TMPS`                                        |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_always_on`        |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_ALWAYS_ON_FUEL_PRJ_OPR_TMPS`                               |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_always_on`        |
    | operational type who are also in :code:`FUEL_PRJS`, and their       |
    | operational timepoints.                                                 |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_ALWAYS_ON_OPR_TMPS_FUEL_SEG`                               |
    |                                                                         |
    | Three-dimensional set with generators of the :code:`gen_always_on`      |
    | operational type, their operational timepoints, and their fuel          |
    | segments (if the project is in :code:`FUEL_PRJS`).                  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_always_on_unit_size_mw`                                    |
    | | *Defined over*: :code:`GEN_ALWAYS_ON`                                 |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The MW size of a unit in this project (projects of the                  |
    | :code:`gen_always_on` type can represent a fleet of similar units).     |
    +-------------------------------------------------------------------------+
    | | :code:`gen_always_on_min_stable_level_fraction`                       |
    | | *Defined over*: :code:`GEN_ALWAYS_ON`                                 |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The minimum stable level of this project as a fraction of its capacity. |
    | This can also be interpreted as the minimum stable level of a unit      |
    | within this project (as the project itself can represent multiple       |
    | units with similar characteristics.                                     |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_always_on_ramp_up_rate`                                    |
    | | *Defined over*: :code:`GEN_ALWAYS_ON`                                 |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's upward ramp rate limit during operations, defined as a    |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_always_on_ramp_down_rate`                                  |
    | | *Defined over*: :code:`GEN_ALWAYS_ON`                                 |
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
    | | :code:`GenAlwaysOn_Provide_Power_MW`                                  |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_OPR_TMPS`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Power provision in MW from this project in each timepoint in which the  |
    | project is operational (capacity exists and the project is available).  |
    +-------------------------------------------------------------------------+
    | | :code:`GenAlwaysOn_Fuel_Burn_MMBTU`                                   |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_FUEL_PRJ_OPR_TMPS`               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Fuel burn in MMBTU by this project in each operational timepoint.       |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | Power                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenAlwaysOn_Max_Power_Constraint`                              |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_OPR_TMPS`                        |
    |                                                                         |
    | Limits the power plus upward reserves to the available capacity.        |
    +-------------------------------------------------------------------------+
    | | :code:`GenAlwaysOn_Min_Power_Constraint`                              |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_OPR_TMPS`                        |
    |                                                                         |
    | Power provision minus downward reserves should exceed the minimum       |
    | stable level for the project.                                           |
    +-------------------------------------------------------------------------+
    | Ramps                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenAlwaysOn_Ramp_Up_Constraint`                                |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_OPR_TMPS`                        |
    |                                                                         |
    | Limits the allowed project upward ramp based on the                     |
    | :code:`gen_always_on_ramp_up_rate`.                                     |
    +-------------------------------------------------------------------------+
    | | :code:`GenAlwaysOn_Ramp_Down_Constraint`                              |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_OPR_TMPS`                        |
    |                                                                         |
    | Limits the allowed project downward ramp based on the                   |
    | :code:`gen_always_on_ramp_down_rate`.                                   |
    +-------------------------------------------------------------------------+
    | Fuel Burn                                                               |
    +-------------------------------------------------------------------------+
    | | :code:`GenAlwaysOn_Fuel_Burn_Constraint`                              |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_OPR_TMPS_FUEL_SEG`               |
    |                                                                         |
    | Determines fuel burn from the project in each timepoint based on its    |
    | heat rate curve.                                                        |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################
    m.GEN_ALWAYS_ON = Set(
        within=m.PROJECTS,
        initialize=generator_subset_init("operational_type", "gen_always_on")
    )

    m.GEN_ALWAYS_ON_OPR_TMPS = Set(
        dimen=2, within=m.PRJ_OPR_TMPS,
        rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS
                if g in mod.GEN_ALWAYS_ON)
    )

    m.GEN_ALWAYS_ON_FUEL_PRJ_OPR_TMPS = Set(
        dimen=2, within=m.GEN_ALWAYS_ON_OPR_TMPS,
        rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GEN_ALWAYS_ON_OPR_TMPS
                if g in mod.FUEL_PRJS)
    )

    m.GEN_ALWAYS_ON_OPR_TMPS_FUEL_SEG = Set(
        dimen=3, within=m.FUEL_PRJ_SGMS_OPR_TMPS,
        rule=lambda mod:
            set((g, tmp, s) for (g, tmp, s)
                in mod.FUEL_PRJ_SGMS_OPR_TMPS
                if g in mod.GEN_ALWAYS_ON)
    )

    # Required Params
    ###########################################################################

    m.gen_always_on_unit_size_mw = Param(
        m.GEN_ALWAYS_ON, within=NonNegativeReals
    )

    m.gen_always_on_min_stable_level_fraction = Param(
        m.GEN_ALWAYS_ON, within=PercentFraction
    )

    # Optional Params
    ###########################################################################

    m.gen_always_on_ramp_up_rate = Param(
        m.GEN_ALWAYS_ON, within=PercentFraction,
        default=1
    )

    m.gen_always_on_ramp_down_rate = Param(
        m.GEN_ALWAYS_ON, within=PercentFraction,
        default=1
    )

    # Variables
    ###########################################################################

    m.GenAlwaysOn_Provide_Power_MW = Var(
        m.GEN_ALWAYS_ON_OPR_TMPS, within=NonNegativeReals
    )

    m.GenAlwaysOn_Fuel_Burn_MMBTU = Var(
        m.GEN_ALWAYS_ON_FUEL_PRJ_OPR_TMPS, within=NonNegativeReals
    )

    # Expressions
    ###########################################################################
    # TODO: the reserve rules are the same in all modules, so should be
    #  consolidated
    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])
    m.GenAlwaysOn_Upwards_Reserves_MW = Expression(
        m.GEN_ALWAYS_ON_OPR_TMPS,
        rule=upwards_reserve_rule)

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])
    m.GenAlwaysOn_Downwards_Reserves_MW = Expression(
        m.GEN_ALWAYS_ON_OPR_TMPS,
        rule=downwards_reserve_rule)

    # Constraints
    ###########################################################################

    m.GenAlwaysOn_Min_Power_Constraint = Constraint(
        m.GEN_ALWAYS_ON_OPR_TMPS,
        rule=min_power_rule
    )

    m.GenAlwaysOn_Max_Power_Constraint = Constraint(
        m.GEN_ALWAYS_ON_OPR_TMPS,
        rule=max_power_rule
    )

    m.GenAlwaysOn_Ramp_Up_Constraint = Constraint(
        m.GEN_ALWAYS_ON_OPR_TMPS,
        rule=ramp_up_rule
    )

    m.GenAlwaysOn_Ramp_Down_Constraint = Constraint(
        m.GEN_ALWAYS_ON_OPR_TMPS,
        rule=ramp_down_rule
    )

    m.GenAlwaysOn_Fuel_Burn_Constraint = Constraint(
        m.GEN_ALWAYS_ON_OPR_TMPS_FUEL_SEG,
        rule=fuel_burn_constraint_rule
    )


# Constraint Formulation Rules
###############################################################################

# Power
def min_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenAlwaysOn_Min_Power_Constraint
    **Enforced Over**: GEN_ALWAYS_ON_OPR_TMPS

    Power minus downward services cannot be below a minimum stable level.
    """
    return mod.GenAlwaysOn_Provide_Power_MW[g, tmp] \
        - mod.GenAlwaysOn_Downwards_Reserves_MW[g, tmp] \
        >= mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp] \
        * mod.gen_always_on_min_stable_level_fraction[g]


def max_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenAlwaysOn_Max_Power_Constraint
    **Enforced Over**: GEN_ALWAYS_ON_OPR_TMPS

    Power plus upward services cannot exceed capacity.
    """
    return mod.GenAlwaysOn_Provide_Power_MW[g, tmp] \
        + mod.GenAlwaysOn_Upwards_Reserves_MW[g, tmp] \
        <= mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


# Ramps
def ramp_up_rule(mod, g, tmp):
    """
    **Constraint Name**: GenAlwaysOn_Ramp_Up_Constraint
    **Enforced Over**: GEN_ALWAYS_ON_OPR_TMPS

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
    elif (mod.gen_always_on_ramp_up_rate[g] * 60
          * mod.hrs_in_tmp[mod.prev_tmp[
                tmp, mod.balancing_type_project[g]]]
          >= (1 - mod.gen_always_on_min_stable_level_fraction[g])):
        return Constraint.Skip
    else:
        return mod.GenAlwaysOn_Provide_Power_MW[g, tmp] \
            + mod.GenAlwaysOn_Upwards_Reserves_MW[g, tmp] \
            - (mod.GenAlwaysOn_Provide_Power_MW[
                   g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]]
               - mod.GenAlwaysOn_Downwards_Reserves_MW[
                   g, mod.prev_tmp[tmp, mod.balancing_type_project[
                       g]]]) \
            <= \
            mod.gen_always_on_ramp_up_rate[g] * 60 \
            * mod.hrs_in_tmp[
                   mod.prev_tmp[tmp, mod.balancing_type_project[g]]] \
            * mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.Availability_Derate[g, tmp]


def ramp_down_rule(mod, g, tmp):
    """
    **Constraint Name**: GenAlwaysOn_Ramp_Down_Constraint
    **Enforced Over**: GEN_ALWAYS_ON_OPR_TMPS

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
    elif (mod.gen_always_on_ramp_down_rate[g] * 60
          * mod.hrs_in_tmp[
              mod.prev_tmp[tmp, mod.balancing_type_project[g]]]
          >= (1 - mod.gen_always_on_min_stable_level_fraction[g])):
        return Constraint.Skip
    else:
        return mod.GenAlwaysOn_Provide_Power_MW[g, tmp] \
            - mod.GenAlwaysOn_Downwards_Reserves_MW[g, tmp] \
            - (mod.GenAlwaysOn_Provide_Power_MW[
                   g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]]
               + mod.GenAlwaysOn_Upwards_Reserves_MW[
                   g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]]
               ) \
            >= \
            - mod.gen_always_on_ramp_down_rate[g] * 60 \
            * mod.hrs_in_tmp[
                   mod.prev_tmp[tmp, mod.balancing_type_project[g]]] \
            * mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.Availability_Derate[g, tmp]


# Fuel Burn
def fuel_burn_constraint_rule(mod, g, tmp, s):
    """
    **Constraint Name**: GenAlwaysOn_Fuel_Burn_Constraint
    **Enforced Over**: GEN_ALWAYS_ON_OPR_TMPS

    Fuel burn is set by piecewise linear representation of input/output
    curve, which will capture heat rate degradation below full output.

    Note: we assume that when projects are derated for availability, the
    input/output curve is derated by the same amount. The implicit
    assumption is that when a generator is de-rated, some of its units
    are out rather than it being forced to run below minimum stable level
    at very inefficient operating points.
    """
    return mod.GenAlwaysOn_Fuel_Burn_MMBTU[g, tmp] \
        >= mod.fuel_burn_slope_mmbtu_per_mwh[g, s] \
        * mod.GenAlwaysOn_Provide_Power_MW[g, tmp] \
        + mod.fuel_burn_intercept_mmbtu_per_hr[g, s] \
        * mod.Availability_Derate[g, tmp] \
        * (mod.Capacity_MW[g, mod.period[tmp]]
           / mod.gen_always_on_unit_size_mw[g])


# Operational Type Methods
###############################################################################

def power_provision_rule(mod, g, tmp):
    """
    Power provision for always-on generators is a variable constrained to be
    between the generator's minimum stable level and its capacity.
    """
    return mod.GenAlwaysOn_Provide_Power_MW[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since there is no commitment, all capacity is assumed to be online.
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision for always-on generators, if eligible, is their power output.
    """
    return mod.GenAlwaysOn_Provide_Power_MW[g, tmp]


# TODO: ignore curtailment for now, but might need to revisit if for example
#  RPS-eligible technologies are modeled as always-on (e.g. geothermal) -- 
#  it may make more sense to model them as 'gen_var' with constant cap factor
def scheduled_curtailment_rule(mod, g, tmp):
    """
    """
    return 0


def subhourly_curtailment_rule(mod, g, tmp):
    """
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    """
    return 0


def fuel_burn_rule(mod, g, tmp, error_message):
    """
    """
    if g in mod.FUEL_PRJS:
        return mod.GenAlwaysOn_Fuel_Burn_MMBTU[g, tmp]
    else:
        raise ValueError(error_message)


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
    """
    if check_if_linear_horizon_first_timepoint(
            mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        pass
    else:
        return mod.GenAlwaysOn_Provide_Power_MW[g, tmp] - \
               mod.GenAlwaysOn_Provide_Power_MW[
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

    unit_size_mw = dict()
    min_stable_fraction = dict()
    ramp_up_rate = dict()
    ramp_down_rate = dict()
    header = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t", header=None, nrows=1
    ).values[0]

    optional_columns = ["ramp_up_when_on_rate", "ramp_down_when_on_rate"]
    used_columns = [c for c in optional_columns if c in header]

    dynamic_components = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "operational_type", "unit_size_mw",
                 "min_stable_level_fraction"] + used_columns
    )

    # Get unit size and minimum stable level
    for row in zip(dynamic_components["project"],
                   dynamic_components["operational_type"],
                   dynamic_components["unit_size_mw"],
                   dynamic_components["min_stable_level_fraction"]):
        if row[1] == "gen_always_on":
            unit_size_mw[row[0]] = float(row[2])
            min_stable_fraction[row[0]] = float(row[3])
        else:
            pass

    data_portal.data()["gen_always_on_unit_size_mw"] = unit_size_mw
    data_portal.data()["gen_always_on_min_stable_level_fraction"] = \
        min_stable_fraction
    
    # Ramp rate limits are optional; will default to 1 if not specified
    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_up_when_on_rate"]
                       ):
            if row[1] == "gen_always_on" and row[2] != ".":
                ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_always_on_ramp_up_rate"] = ramp_up_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_down_when_on_rate"]
                       ):
            if row[1] == "gen_always_on" and row[2] != ".":
                ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_always_on_ramp_down_rate"] = ramp_down_rate


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

    c = conn.cursor()
    projects = c.execute(
        """SELECT project, operational_type,
        min_stable_level, unit_size_mw,
        startup_cost_per_mw, shutdown_cost_per_mw,
        startup_fuel_mmbtu_per_mw,
        startup_plus_ramp_up_rate,
        shutdown_plus_ramp_down_rate,
        min_up_time_hours, min_down_time_hours,
        charging_efficiency, discharging_efficiency,
        minimum_duration_hours
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, operational_type,
        min_stable_level, unit_size_mw,
        startup_cost_per_mw, shutdown_cost_per_mw,
        startup_fuel_mmbtu_per_mw,
        startup_plus_ramp_up_rate,
        shutdown_plus_ramp_down_rate,
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
            "gen_always_on"
        )
    )

    df = pd.DataFrame(
        data=projects.fetchall(),
        columns=[s[0] for s in projects.description]
    )

    # Check that unit size and min stable level are specified
    # (not all operational types require this input)
    req_columns = [
        "min_stable_level",
        "unit_size_mw"
    ]
    validation_errors = check_req_prj_columns(df, req_columns, True,
                                              "gen_always_on")
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_OPERATIONAL_CHARS",
             "inputs_project_operational_chars",
             "High",
             "Missing inputs",
             error
             )
        )

    # Check that there are no unexpected operational inputs
    expected_na_columns = [
        "startup_cost_per_mw", "shutdown_cost_per_mw",
        "startup_fuel_mmbtu_per_mw",
        "startup_plus_ramp_up_rate",
        "shutdown_plus_ramp_down_rate",
        "min_up_time_hours", "min_down_time_hours",
        "charging_efficiency", "discharging_efficiency",
        "minimum_duration_hours"
    ]
    validation_errors = check_req_prj_columns(df, expected_na_columns, False,
                                              "gen_always_on")
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

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)
