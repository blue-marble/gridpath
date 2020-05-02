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
import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, Var, NonNegativeReals, \
    PercentFraction, Constraint, Expression, value

from gridpath.auxiliary.auxiliary import generator_subset_init, \
    write_validation_to_database, check_req_prj_columns
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables
from gridpath.project.common_functions import \
    check_if_boundary_type_and_first_timepoint, check_if_first_timepoint, \
    check_boundary_type
from gridpath.project.operations.operational_types.common_functions import \
    load_optype_module_specific_data, check_for_tmps_to_link


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
    | operational type who are also in :code:`FUEL_PRJS`, and their           |
    | operational timepoints.                                                 |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_ALWAYS_ON_OPR_TMPS_FUEL_SEG`                               |
    |                                                                         |
    | Three-dimensional set with generators of the :code:`gen_always_on`      |
    | operational type, their operational timepoints, and their fuel          |
    | segments (if the project is in :code:`FUEL_PRJS`).                      |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_ALWAYS_ON_VOM_PRJS_OPR_TMPS_SGMS`                          |
    |                                                                         |
    | Three-dimensional set describing projects, their variable O&M cost      |
    | curve segment IDs, and the timepoints in which the project could be     |
    | operational. The variable O&M cost constraint is applied over this set. |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_COMMIT_ALWAYS_ON_LINKED_TMPS`                              |
    |                                                                         |
    | Two-dimensional set with generators of the :code:`gen_always_on`        |
    | operational type and their linked timepoints.                           |
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
    | | :code:`gen_always_on_ramp_up_when_on_rate`                            |
    | | *Defined over*: :code:`GEN_ALWAYS_ON`                                 |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's upward ramp rate limit during operations, defined as a    |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_always_on_ramp_down_when_on_rate`                          |
    | | *Defined over*: :code:`GEN_ALWAYS_ON`                                 |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`1`                                                  |
    |                                                                         |
    | The project's downward ramp rate limit during operations, defined as a  |
    | fraction of its capacity per minute.                                    |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Linked Input Params                                                     |
    +=========================================================================+
    | | :code:`gen_always_on_linked_power`                                    |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_LINKED_TMPS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's power provision in the linked timepoints.                 |
    +-------------------------------------------------------------------------+
    | | :code:`gen_always_on_linked_upwards_reserves`                         |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_LINKED_TMPS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's upward reserve provision in the linked timepoints.        |
    +-------------------------------------------------------------------------+
    | | :code:`gen_always_on_linked_downwards_reserves`                       |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_LINKED_TMPS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's downward reserve provision in the linked timepoints.      |
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
    | | :code:`GenAlwaysOn_Variable_OM_Cost_By_LL`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_OPR_TMPS`                        |
    |                                                                         |
    | Variable O&M cost for this project in each operational timepoint. Note: |
    | This is only the piecewise linear component of the variable O&M cost,   |
    | determined by the variable O&M cost curve inputs. Most projects won't   |
    | use this and instead simply have a :code:`variable_om_cost_per_mwh`     |
    | rate specified that is constant for all loading points. Both components |
    | are additive so users could use both if needed. See                     |
    | :code:`variable_om_cost_rule` for more info.                            |
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
    | :code:`gen_always_on_ramp_up_when_on_rate`.                             |
    +-------------------------------------------------------------------------+
    | | :code:`GenAlwaysOn_Ramp_Down_Constraint`                              |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_OPR_TMPS`                        |
    |                                                                         |
    | Limits the allowed project downward ramp based on the                   |
    | :code:`gen_always_on_ramp_down_when_on_rate`.                           |
    +-------------------------------------------------------------------------+
    | Fuel Burn                                                               |
    +-------------------------------------------------------------------------+
    | | :code:`GenAlwaysOn_Fuel_Burn_Constraint`                              |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_OPR_TMPS_FUEL_SEG`               |
    |                                                                         |
    | Determines fuel burn from the project in each timepoint based on its    |
    | heat rate curve.                                                        |
    +-------------------------------------------------------------------------+
    | Variable O&M                                                            |
    +-------------------------------------------------------------------------+
    | | :code:`GenAlwaysOn_Variable_OM_Constraint`                            |
    | | *Defined over*: :code:`GEN_ALWAYS_ON_VOM_PRJS_OPR_TMPS_SGMS`          |
    |                                                                         |
    | Determines variable O&M cost from the project in each timepoint based   |
    | on its variable O&M cost curve.                                         |
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

    m.GEN_ALWAYS_ON_VOM_PRJS_OPR_TMPS_SGMS = Set(
        dimen=3,
        within=m.VOM_PRJS_OPR_TMPS_SGMS,
        rule=lambda mod:
        set((g, tmp, s) for (g, tmp, s)
            in mod.VOM_PRJS_OPR_TMPS_SGMS
            if g in mod.GEN_ALWAYS_ON)
    )

    m.GEN_ALWAYS_ON_LINKED_TMPS = Set(dimen=2)

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

    m.gen_always_on_ramp_up_when_on_rate = Param(
        m.GEN_ALWAYS_ON, within=PercentFraction,
        default=1
    )

    m.gen_always_on_ramp_down_when_on_rate = Param(
        m.GEN_ALWAYS_ON, within=PercentFraction,
        default=1
    )

    # Linked Params
    ###########################################################################

    m.gen_always_on_linked_power = Param(
        m.GEN_ALWAYS_ON_LINKED_TMPS,
        within=NonNegativeReals
    )

    m.gen_always_on_linked_upwards_reserves = Param(
        m.GEN_ALWAYS_ON_LINKED_TMPS,
        within=NonNegativeReals
    )

    m.gen_always_on_linked_downwards_reserves = Param(
        m.GEN_ALWAYS_ON_LINKED_TMPS,
        within=NonNegativeReals
    )

    # Variables
    ###########################################################################

    m.GenAlwaysOn_Provide_Power_MW = Var(
        m.GEN_ALWAYS_ON_OPR_TMPS, within=NonNegativeReals
    )

    m.GenAlwaysOn_Fuel_Burn_MMBTU = Var(
        m.GEN_ALWAYS_ON_FUEL_PRJ_OPR_TMPS, within=NonNegativeReals
    )

    m.GenAlwaysOn_Variable_OM_Cost_By_LL = Var(
        m.GEN_ALWAYS_ON_OPR_TMPS,
        within=NonNegativeReals
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

    # Variable O&M
    m.GenAlwaysOn_Variable_OM_Constraint = Constraint(
        m.GEN_ALWAYS_ON_VOM_PRJS_OPR_TMPS_SGMS,
        rule=variable_om_cost_constraint_rule
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
    if check_if_boundary_type_and_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g],
        boundary_type="linear"
    ):
        return Constraint.Skip
    else:
        if check_if_boundary_type_and_first_timepoint(
            mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g],
            boundary_type="linked"
        ):
            prev_tmp_hrs_in_tmp = mod.hrs_in_linked_tmp[0]
            prev_tmp_power = \
                mod.gen_always_on_linked_power[g, 0]
            prev_tmp_downwards_reserves = \
                mod.gen_always_on_linked_downwards_reserves[g, 0]
        else:
            prev_tmp_hrs_in_tmp = mod.hrs_in_tmp[
                    mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
            prev_tmp_power = \
                mod.GenAlwaysOn_Provide_Power_MW[
                    g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
                ]
            prev_tmp_downwards_reserves = \
                mod.GenAlwaysOn_Downwards_Reserves_MW[
                    g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
                ]

        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # ramp up the full operable range between timepoints, constraint won't
        # bind, so skip
        if (mod.gen_always_on_ramp_up_when_on_rate[g] * 60
                * prev_tmp_hrs_in_tmp
                >= (1 - mod.gen_always_on_min_stable_level_fraction[g])):
            return Constraint.Skip
        else:
            return mod.GenAlwaysOn_Provide_Power_MW[g, tmp] \
                + mod.GenAlwaysOn_Upwards_Reserves_MW[g, tmp] \
                - (prev_tmp_power - prev_tmp_downwards_reserves) \
                <= \
                mod.gen_always_on_ramp_up_when_on_rate[g] * 60 \
                * prev_tmp_hrs_in_tmp \
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
    if check_if_boundary_type_and_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g],
        boundary_type="linear"
    ):
        return Constraint.Skip
    else:
        if check_if_boundary_type_and_first_timepoint(
            mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g],
            boundary_type="linked"
        ):
            prev_tmp_hrs_in_tmp = mod.hrs_in_linked_tmp[0]
            prev_tmp_power = \
                mod.gen_always_on_linked_power[g, 0]
            prev_tmp_upwards_reserves = \
                mod.gen_always_on_linked_upwards_reserves[g, 0]
        else:
            prev_tmp_hrs_in_tmp = mod.hrs_in_tmp[
                mod.prev_tmp[tmp, mod.balancing_type_project[g]]
            ]
            prev_tmp_power = \
                mod.GenAlwaysOn_Provide_Power_MW[
                    g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
                ]
            prev_tmp_upwards_reserves = \
                mod.GenAlwaysOn_Upwards_Reserves_MW[
                    g, mod.prev_tmp[tmp, mod.balancing_type_project[g]]
                ]

        # If ramp rate limits, adjusted for timepoint duration, allow you to
        # ramp down the full operable range between timepoints, constraint
        # won't bind, so skip
        if (mod.gen_always_on_ramp_down_when_on_rate[g] * 60
            * prev_tmp_hrs_in_tmp
                >= (1 - mod.gen_always_on_min_stable_level_fraction[g])):
            return Constraint.Skip
        else:
            return mod.GenAlwaysOn_Provide_Power_MW[g, tmp] \
                - mod.GenAlwaysOn_Downwards_Reserves_MW[g, tmp] \
                - (prev_tmp_power + prev_tmp_upwards_reserves) \
                >= \
                - mod.gen_always_on_ramp_down_when_on_rate[g] * 60 \
                * prev_tmp_hrs_in_tmp \
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
        >= mod.fuel_burn_slope_mmbtu_per_mwh[g, mod.period[tmp], s] \
        * mod.GenAlwaysOn_Provide_Power_MW[g, tmp] \
        + mod.fuel_burn_intercept_mmbtu_per_mw_hr[g, mod.period[tmp], s] \
        * mod.Availability_Derate[g, tmp] \
        * mod.Capacity_MW[g, mod.period[tmp]]


def variable_om_cost_constraint_rule(mod, g, tmp, s):
    """
    **Constraint Name**: GenAlwaysOn_Variable_OM_Constraint
    **Enforced Over**: GEN_ALWAYS_ON_VOM_PRJS_OPR_TMPS_SGMS

    Variable O&M cost by loading level is set by piecewise linear
    representation of the input/output curve (variable O&M cost vs. loading
    level).

    Note: we assume that when projects are derated for availability, the
    input/output curve is derated by the same amount. The implicit
    assumption is that when a generator is de-rated, some of its units
    are out rather than it being forced to run below minimum stable level
    at very costly operating points.
    """
    return mod.GenAlwaysOn_Variable_OM_Cost_By_LL[g, tmp] \
        >= mod.vom_slope_cost_per_mwh[g, mod.period[tmp], s] \
        * mod.GenAlwaysOn_Provide_Power_MW[g, tmp] \
        + mod.vom_intercept_cost_per_mw_hr[g, mod.period[tmp], s] \
        * mod.Availability_Derate[g, tmp] \
        * mod.Capacity_MW[g, mod.period[tmp]]


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


def fuel_burn_rule(mod, g, tmp):
    """
    """
    if g in mod.FUEL_PRJS:
        return mod.GenAlwaysOn_Fuel_Burn_MMBTU[g, tmp]
    else:
        return 0


def variable_om_cost_rule(mod, g, tmp):
    """
    Variable O&M cost has two components which are additive:
    1. A fixed variable O&M rate (cost/MWh) that doesn't change with loading
       levels: :code:`variable_om_cost_per_mwh`.
    2. A variable variable O&M rate that changes with the loading level,
       similar to the heat rates. The idea is to represent higher variable cost
       rates at lower loading levels. This is captured in the
       :code:`GenAlwaysOn_Variable_OM_Cost_By_LL` decision variable. If no
       variable O&M curve inputs are provided, this component will be zero.

    Most users will only use the first component, which is specified in the
    operational characteristics table.  Only operational types with
    commitment decisions can have the second component.
    """
    return mod.GenAlwaysOn_Provide_Power_MW[g, tmp] \
        * mod.variable_om_cost_per_mwh[g] \
        + mod.GenAlwaysOn_Variable_OM_Cost_By_LL[g, tmp]


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
    load_optype_module_specific_data(
        mod=mod, data_portal=data_portal,
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, op_type="gen_always_on"
    )

    # Linked timepoint params
    linked_inputs_filename = os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs",
            "gen_always_on_linked_timepoint_params.tab"
        )
    if os.path.exists(linked_inputs_filename):
        data_portal.load(
            filename=linked_inputs_filename,
            index=mod.GEN_ALWAYS_ON_LINKED_TMPS,
            param=(
                mod.gen_always_on_linked_power,
                mod.gen_always_on_linked_upwards_reserves,
                mod.gen_always_on_linked_downwards_reserves
            )
        )
    else:
        pass


def export_module_specific_results(
        mod, d, scenario_directory, subproblem, stage
):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    # If there's a linked_subproblems_map CSV file, check which of the
    # current subproblem TMPS we should export results for to link to the
    # next subproblem
    tmps_to_link, tmp_linked_tmp_dict = check_for_tmps_to_link(
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage
    )

    # If the list of timepoints to link is not empty, write the linked
    # timepoint results for this module in the next subproblem's input
    # directory
    if tmps_to_link:
        next_subproblem = str(int(subproblem) + 1)

        # Export params by project and timepoint
        with open(os.path.join(
                scenario_directory, next_subproblem, stage, "inputs",
                "gen_always_on_linked_timepoint_params.tab"
        ), "w", newline=""
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")
            writer.writerow(
                ["project", "linked_timepoint",
                 "linked_provide_power",
                 "linked_upward_reserves",
                 "linked_downward_reserves"]
            )
            for (p, tmp) in sorted(mod.GEN_ALWAYS_ON_OPR_TMPS):
                if tmp in tmps_to_link:
                    writer.writerow([
                        p,
                        tmp_linked_tmp_dict[tmp],
                        value(mod.GenAlwaysOn_Provide_Power_MW[p, tmp]),
                        value(mod.GenAlwaysOn_Upwards_Reserves_MW[p, tmp]),
                        value(mod.GenAlwaysOn_Downwards_Reserves_MW[p, tmp])
                    ])

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
        minimum_duration_hours, maximum_duration_hours
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
        minimum_duration_hours, maximum_duration_hours
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
        "minimum_duration_hours", "maximum_duration_hours"
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
