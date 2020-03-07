#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This operational type describes the operations of hydro generation
projects and is like the *gen_hydro* operational type except that the power
output is must-take, i.e. curtailment is not allowed.

"""

from __future__ import print_function

from builtins import next
from builtins import zip
from builtins import str
import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Param, Constraint, \
    Expression, NonNegativeReals, PercentFraction, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import generator_subset_init, \
    setup_results_import
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
    | | :code:`GEN_HYDRO_MUST_TAKE`                                           |
    |                                                                         |
    | The set of generators of the :code:`gen_hydro_must_take` operational    |
    | type.                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_HYDRO_MUST_TAKE_OPR_HRZS`                                  |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_hydro_must_take`  |
    | operational type and their operational horizons.                        |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_HYDRO_MUST_TAKE_OPR_TMPS`                                  |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_hydro_must_take`  |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_hydro_must_take_max_power_fraction`                        |
    | | *Defined over*: :code:`GEN_HYDRO_MUST_TAKE_OPR_HRZS`                  |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The project's maximum power output in each operational horizon as a     |
    | fraction of its available capacity.                                     |
    +-------------------------------------------------------------------------+
    | | :code:`gen_hydro_must_take_min_power_fraction`                        |
    | | *Defined over*: :code:`GEN_HYDRO_MUST_TAKE_OPR_HRZS`                  |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The project's minimum power output in each operational horizon as a     |
    | fraction of its available capacity.                                     |
    +-------------------------------------------------------------------------+
    | | :code:`gen_hydro_must_take_average_power_fraction`                    |
    | | *Defined over*: :code:`GEN_HYDRO_MUST_TAKE_OPR_HRZS`                  |
    | | *Within*: :code:`PercentFraction`                                     |
    |                                                                         |
    | The project's avarage power output in each operational horizon as a     |
    | fraction of its available capacity. This can be interpreted as the      |
    | project's average capacity factor or plant load factor.                 |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_hydro_must_take_ramp_up_rate`                              |
    | | *Defined over*: :code:`GEN_HYDRO_MUST_TAKE`                           |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's upward ramp rate limit during operations, defined as a    |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_hydro_must_take_ramp_down_rate`                            |
    | | *Defined over*: :code:`GEN_HYDRO_MUST_TAKE`                           |
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
    | | :code:`GenHydroMustTake_Provide_Power_MW`                             |
    | | *Defined over*: :code:`GEN_HYDRO_MUST_TAKE_OPR_TMPS`                  |
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
    | | :code:`GenHydroMustTake_Max_Power_Constraint`                         |
    | | *Defined over*: :code:`GEN_HYDRO_MUST_TAKE_OPR_HRZS`                  |
    |                                                                         |
    | Limits the power plus upward reserves based on the                      |
    | :code:`gen_hydro_must_take_max_power_fraction` and the available        |
    | capacity.                                                               |
    +-------------------------------------------------------------------------+
    | | :code:`GenHydroMustTake_Min_Power_Constraint`                         |
    | | *Defined over*: :code:`GEN_HYDRO_MUST_TAKE_OPR_HRZS`                  |
    |                                                                         |
    | Power provision minus downward reserves should exceed a certain level   |
    | based on the :code:`gen_hydro_must_take_min_power_fraction` and the     |
    | available capacity.                                                     |
    +-------------------------------------------------------------------------+
    | | :code:`GenHydroMustTake_Energy_Budget_Constraint`                     |
    | | *Defined over*: :code:`GEN_HYDRO_MUST_TAKE_OPR_HRZS`                  |
    |                                                                         |
    | The project's average capacity factor in each operational horizon,      |
    | should match the specified                                              |
    | :code:`gen_hydro_must_take_average_power_fraction`.                     |
    +-------------------------------------------------------------------------+
    | Ramps                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`GenHydroMustTake_Ramp_Up_Constraint`                           |
    | | *Defined over*: :code:`GEN_HYDRO_MUST_TAKE_OPR_TMPS`                  |
    |                                                                         |
    | Limits the allowed project upward ramp based on the                     |
    | :code:`gen_hydro_must_take_ramp_up_rate`.                               |
    +-------------------------------------------------------------------------+
    | | :code:`GenHydroMustTake_Ramp_Down_Constraint`                         |
    | | *Defined over*: :code:`GEN_HYDRO_MUST_TAKE_OPR_TMPS`                  |
    |                                                                         |
    | Limits the allowed project downward ramp based on the                   |
    | :code:`gen_hydro_must_take_ramp_down_rate`.                             |
    +-------------------------------------------------------------------------+

    """
    # Sets
    ###########################################################################

    m.GEN_HYDRO_MUST_TAKE = Set(
        within=m.PROJECTS,
        initialize=generator_subset_init("operational_type", "gen_hydro_must_take")
    )

    m.GEN_HYDRO_MUST_TAKE_OPR_HRZS = Set(dimen=2)

    m.GEN_HYDRO_MUST_TAKE_OPR_TMPS = Set(
        dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
        set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
            if g in mod.GEN_HYDRO_MUST_TAKE)
    )

    # Required Params
    ###########################################################################

    m.gen_hydro_must_take_max_power_fraction = Param(
        m.GEN_HYDRO_MUST_TAKE_OPR_HRZS,
        within=PercentFraction
    )

    m.gen_hydro_must_take_min_power_fraction = Param(
        m.GEN_HYDRO_MUST_TAKE_OPR_HRZS,
        within=PercentFraction
    )

    m.gen_hydro_must_take_average_power_fraction = Param(
        m.GEN_HYDRO_MUST_TAKE_OPR_HRZS,
        within=PercentFraction
    )

    # Optional Params
    ###########################################################################

    m.gen_hydro_must_take_ramp_up_rate = Param(
        m.GEN_HYDRO_MUST_TAKE,
        within=PercentFraction, default=1
    )

    m.gen_hydro_must_take_ramp_down_rate = Param(
        m.GEN_HYDRO_MUST_TAKE,
        within=PercentFraction, default=1
    )

    # Variables
    ###########################################################################

    m.GenHydroMustTake_Provide_Power_MW = Var(
        m.GEN_HYDRO_MUST_TAKE_OPR_TMPS,
        within=NonNegativeReals
    )

    # Expressions
    ###########################################################################

    def upwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, headroom_variables)[g])

    m.GenHydroMustTake_Upwards_Reserves_MW = Expression(
        m.GEN_HYDRO_MUST_TAKE_OPR_TMPS,
        rule=upwards_reserve_rule)

    def downwards_reserve_rule(mod, g, tmp):
        return sum(getattr(mod, c)[g, tmp]
                   for c in getattr(d, footroom_variables)[g])

    m.GenHydroMustTake_Downwards_Reserves_MW = Expression(
        m.GEN_HYDRO_MUST_TAKE_OPR_TMPS,
        rule=downwards_reserve_rule)

    # Constraints
    ###########################################################################

    m.GenHydroMustTake_Max_Power_Constraint = Constraint(
        m.GEN_HYDRO_MUST_TAKE_OPR_TMPS,
        rule=max_power_rule
    )

    m.GenHydroMustTake_Min_Power_Constraint = Constraint(
        m.GEN_HYDRO_MUST_TAKE_OPR_TMPS,
        rule=min_power_rule
    )

    m.GenHydroMustTake_Energy_Budget_Constraint = Constraint(
        m.GEN_HYDRO_MUST_TAKE_OPR_HRZS,
        rule=energy_budget_rule
    )

    m.GenHydroMustTake_Ramp_Up_Constraint = Constraint(
        m.GEN_HYDRO_MUST_TAKE_OPR_TMPS,
        rule=ramp_up_rule
    )

    m.GenHydroMustTake_Ramp_Down_Constraint = Constraint(
        m.GEN_HYDRO_MUST_TAKE_OPR_TMPS,
        rule=ramp_down_rule
    )


# Constraint Formulation Rules
###############################################################################

def max_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenHydroMustTake_Max_Power_Constraint
    **Enforced Over**: GEN_HYDRO_MUST_TAKE_OPR_HRZS

    Power plus upward reserves shall not exceed the maximum power output.
    The maximum power output (fraction) is a user input that is specified
    by horizon. If the unit is unavailable, it will be further de-rated.

    Example: The maximum power is 90% of the installed capacity in horizon
    1, which represents a winter week. If the installed capacity during the
    timepoint (period) of interest (which can be a user input or a decision
    variable, depending on the capacity type) is 1,000 MW and the project is
    fully available, the project's maximum power output is 900 MW.
    """
    return mod.GenHydroMustTake_Provide_Power_MW[g, tmp] \
        + mod.GenHydroMustTake_Upwards_Reserves_MW[g, tmp] \
        <= mod.gen_hydro_must_take_max_power_fraction[
            g, mod.horizon[tmp, mod.balancing_type_project[g]]] \
        * mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def min_power_rule(mod, g, tmp):
    """
    **Constraint Name**: GenHydroMustTake_Min_Power_Constraint
    **Enforced Over**: GEN_HYDRO_MUST_TAKE_OPR_HRZS

    Power minus downward reserves must exceed the minimum power output.
    The minimum power output (fraction) is a user input that is specified
    by horizon. If the unit is unavailable, it will be further de-rated.

    Example: The minimum power is 30% of the installed capacity in horizon
    1, which represents a winter week. If the installed capacity during the
    timepoint (period) of interest (which can be a user input or a decision
    variable, depending on the capacity type) is 1,000 MW and the project is
    fully available, the project's minimum power output is 300 MW.
    """
    return mod.GenHydroMustTake_Provide_Power_MW[g, tmp] \
        - mod.GenHydroMustTake_Downwards_Reserves_MW[g, tmp] \
        >= mod.gen_hydro_must_take_min_power_fraction[
            g, mod.horizon[tmp, mod.balancing_type_project[g]]] \
        * mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def energy_budget_rule(mod, g, h):
    """
    **Constraint Name**: GenHydroMustTake_Energy_Budget_Constraint
    **Enforced Over**: GEN_HYDRO_MUST_TAKE_OPR_HRZS

    The sum of hydro energy output within a horizon must match the horizon's
    hydro energy budget. The budget is calculated by multiplying the
    user-specified average power fraction (i.e. the average capacity factor)
    for that horizon with the product of the matching period's installed
    capacity (which can be a user input or a decision variable, depending on
    the capacity type), the number of hours in that horizon, and any
    availability derates if applicable.

    WARNING: If there are any availability derates, this means the effective
    average power fraction (and associated energy budget) will be lower than
    the user-specified input!

    Example: The average power fraction is 50% of the installed capacity in
    horizon 1, which represents a winter week. If the installed capacity
    during the period of interest is 1,000 MW, there are 168 hours in
    the horizon (1 week), and the unit is fully available, the hydro budget
    for this horizon is 0.5 * 1,000 MW * 168 h = 84,000 MWh.
    If the unit were unavailable for half of the timepoints in that horizon,
    the budget would be half, i.e. 42,000 MWh, even though the average power
    fraction is the same!
    """
    return sum(mod.GenHydroMustTake_Provide_Power_MW[g, tmp]
               * mod.number_of_hours_in_timepoint[tmp]
               for tmp in mod.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON[
                   mod.balancing_type_project[g], h]) \
        == sum(mod.gen_hydro_must_take_average_power_fraction[g, h]
               * mod.Capacity_MW[g, mod.period[tmp]]
               * mod.Availability_Derate[g, tmp]
               * mod.number_of_hours_in_timepoint[tmp]
               for tmp in mod.TIMEPOINTS_ON_BALANCING_TYPE_HORIZON[
                   mod.balancing_type_project[g], h])


def ramp_up_rule(mod, g, tmp):
    """
    **Constraint Name**: GenHydroMustTake_Ramp_Up_Constraint
    **Enforced Over**: GEN_HYDRO_MUST_TAKE_OPR_TMPS

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
    # If you can ramp up the the total project's capacity within the
    # previous timepoint, skip the constraint (it won't bind)
    elif mod.gen_hydro_must_take_ramp_up_rate[g] * 60 \
            * mod.number_of_hours_in_timepoint[
        mod.previous_timepoint[tmp, mod.balancing_type_project[g]]] \
            >= 1:
        return Constraint.Skip
    else:
        return (mod.GenHydroMustTake_Provide_Power_MW[g, tmp]
                + mod.GenHydroMustTake_Upwards_Reserves_MW[g, tmp]) \
               - (mod.GenHydroMustTake_Provide_Power_MW[
                      g, mod.previous_timepoint[
                          tmp, mod.balancing_type_project[g]]]
                  - mod.GenHydroMustTake_Downwards_Reserves_MW[
                      g, mod.previous_timepoint[
                          tmp, mod.balancing_type_project[g]]]) \
               <= \
               mod.gen_hydro_must_take_ramp_up_rate[g] * 60 \
               * mod.number_of_hours_in_timepoint[
                   mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]\
               * mod.Capacity_MW[g, mod.period[tmp]] \
               * mod.Availability_Derate[g, tmp]


def ramp_down_rule(mod, g, tmp):
    """
    **Constraint Name**: GenHydroMustTake_Ramp_Down_Constraint
    **Enforced Over**: GEN_HYDRO_MUST_TAKE_OPR_TMPS

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
    # If you can ramp down the the total project's capacity within the
    # previous timepoint, skip the constraint (it won't bind)
    elif mod.gen_hydro_must_take_ramp_down_rate[g] * 60 \
            * mod.number_of_hours_in_timepoint[
        mod.previous_timepoint[tmp, mod.balancing_type_project[g]]] \
            >= 1:
        return Constraint.Skip
    else:
        return (mod.GenHydroMustTake_Provide_Power_MW[g, tmp]
                - mod.GenHydroMustTake_Downwards_Reserves_MW[g, tmp]) \
               - (mod.GenHydroMustTake_Provide_Power_MW[
                      g, mod.previous_timepoint[
                          tmp, mod.balancing_type_project[g]]]
                  + mod.GenHydroMustTake_Upwards_Reserves_MW[
                      g, mod.previous_timepoint[
                          tmp, mod.balancing_type_project[g]]]) \
               >= \
               - mod.gen_hydro_must_take_ramp_down_rate[g] * 60 \
               * mod.number_of_hours_in_timepoint[
                   mod.previous_timepoint[tmp, mod.balancing_type_project[g]]]\
               * mod.Capacity_MW[g, mod.period[tmp]] \
               * mod.Availability_Derate[g, tmp]


# Operational Type Methods
###############################################################################

def power_provision_rule(mod, g, tmp):
    """
    Power provision from must-take hydro.
    """
    return mod.GenHydroMustTake_Provide_Power_MW[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since there is no commitment, all is capacity assumed to be online.
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.Availability_Derate[g, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision from must-take hydro if eligible.
    """
    return mod.GenHydroMustTake_Provide_Power_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    """
    return 0


# TODO: ignoring subhourly behavior for hydro for now
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
    if g in mod.FUEL_PROJECTS:
        raise ValueError(
            "ERROR! gen_hydro_must_take projects should not use fuel." + "\n" +
            "Check input data for project '{}'".format(g) + "\n" +
            "and change its fuel to '.' (no value)."
        )
    else:
        raise ValueError(error_message)


def startup_shutdown_rule(mod, g, tmp):
    """
    """
    raise ValueError(
        "ERROR! gen_hydro_must_take projects should not incur startup/shutdown"
        " costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup/shutdown costs to '.' (no value)."
    )


def power_delta_rule(mod, g, tmp):
    """
    """
    if check_if_linear_horizon_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g]
    ):
        pass
    else:
        return mod.GenHydroMustTake_Provide_Power_MW[g, tmp] \
            - mod.GenHydroMustTake_Provide_Power_MW[g, mod.previous_timepoint[
                tmp, mod.balancing_type_project[g]]]


# Input-Output
###############################################################################

def load_module_specific_data(m, data_portal,
                              scenario_directory, subproblem, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    # Determine list of projects
    projects = list()

    prj_op_type_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "operational_type"]
    )

    for row in zip(prj_op_type_df["project"],
                   prj_op_type_df["operational_type"]):
        if row[1] == 'gen_hydro_must_take':
            projects.append(row[0])
        else:
            pass

    # Determine subset of project-horizons in hydro budgets file
    project_horizons = list()
    avg = dict()
    min = dict()
    max = dict()

    prj_hor_opchar_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "inputs",
                     "hydro_conventional_horizon_params.tab"),
        sep="\t",
        usecols=["project", "horizon", "hydro_average_power_fraction",
                 "hydro_min_power_fraction", "hydro_max_power_fraction"]
    )
    for row in zip(prj_hor_opchar_df["project"],
                   prj_hor_opchar_df["horizon"],
                   prj_hor_opchar_df["hydro_average_power_fraction"],
                   prj_hor_opchar_df["hydro_min_power_fraction"],
                   prj_hor_opchar_df["hydro_max_power_fraction"]):
        if row[0] in projects:
            project_horizons.append((row[0], row[1]))
            avg[(row[0], row[1])] = float(row[2])
            min[(row[0], row[1])] = float(row[3])
            max[(row[0], row[1])] = float(row[4])
        else:
            pass

    # Load data
    data_portal.data()["GEN_HYDRO_MUST_TAKE_OPR_HRZS"] = \
        {None: project_horizons}
    data_portal.data()["gen_hydro_must_take_average_power_fraction"] = avg
    data_portal.data()["gen_hydro_must_take_min_power_fraction"] = min
    data_portal.data()["gen_hydro_must_take_max_power_fraction"] = max

    # Ramp rate limits are optional; will default to 1 if not specified
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
        usecols=["project", "operational_type"] + used_columns
    )

    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_up_when_on_rate"]
                       ):
            if row[1] == "gen_hydro_must_take" and row[2] != ".":
                ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_hydro_must_take_ramp_up_rate"] = ramp_up_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_down_when_on_rate"]
                       ):
            if row[1] == "gen_hydro_must_take" and row[2] != ".":
                ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()["gen_hydro_must_take_ramp_down_rate"] = \
            ramp_down_rate


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
    # Select only budgets/min/max of projects in the portfolio
    # Select only budgets/min/max of projects with 'gen_hydro_must_take'
    # Select only budgets/min/max for horizons from the correct temporal
    # scenario and subproblem
    # Select only horizons on periods when the project is operational
    # (periods with existing project capacity for existing projects or
    # with costs specified for new projects)
    # TODO: should we ensure that the project balancing type and the horizon
    #  length type match (e.g. by joining on them being equal here)
    hydro_chars = c.execute(
        """SELECT project, horizon, average_power_fraction, min_power_fraction,
        max_power_fraction
        FROM inputs_project_portfolios
        INNER JOIN
        (SELECT project, hydro_operational_chars_scenario_id
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {}
        AND operational_type = 'gen_hydro_must_take') AS op_char
        USING (project)
        CROSS JOIN
        (SELECT horizon
        FROM inputs_temporal_horizons
        WHERE temporal_scenario_id = {}
        AND subproblem_id = {})
        LEFT OUTER JOIN
        inputs_project_hydro_operational_chars
        USING (hydro_operational_chars_scenario_id, project, horizon)
        INNER JOIN
        (SELECT project, period
        FROM
        (SELECT project, period
        FROM inputs_project_existing_capacity
        INNER JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {})
        USING (period)
        WHERE project_existing_capacity_scenario_id = {}
        AND existing_capacity_mw > 0) as existing
        UNION
        SELECT project, period
        FROM inputs_project_new_cost
        INNER JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {})
        USING (period)
        WHERE project_new_cost_scenario_id = {})
        USING (project, period)
        WHERE project_portfolio_scenario_id = {}
        """.format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subproblem,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_EXISTING_CAPACITY_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    return hydro_chars


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    hydro_conventional_horizon_params.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    hydro_chars = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # If hydro_conventional_horizon_params.tab file already exists,
    # append rows to it
    if os.path.isfile(os.path.join(inputs_directory,
                                   "hydro_conventional_horizon_params.tab")
                      ):
        with open(os.path.join(inputs_directory,
                               "hydro_conventional_horizon_params.tab"),
                  "a") as hydro_chars_tab_file:
            writer = csv.writer(hydro_chars_tab_file, delimiter="\t", lineterminator="\n")
            for row in hydro_chars:
                writer.writerow(row)
    # If hydro_conventional_horizon_params.tab does not exist, write header
    # first, then add inputs data
    else:
        with open(os.path.join(inputs_directory,
                               "hydro_conventional_horizon_params.tab"),
                  "w", newline="") as hydro_chars_tab_file:
            writer = csv.writer(hydro_chars_tab_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                ["project", "horizon",
                 "hydro_average_power_fraction",
                 "hydro_min_power_fraction",
                 "hydro_max_power_fraction"]
            )
            for row in hydro_chars:
                writer.writerow(row)


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

    # hydro_chars = get_module_specific_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

    # do stuff here to validate inputs
