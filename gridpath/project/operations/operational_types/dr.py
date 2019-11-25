#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This modules describes the operations of generic shiftable load.

There are two operational variables: shift load up (add load) and shift load
down (subtract load). These cannot exceed the power capacity of the project
and must meet an energy balance constraint on each horizon (no efficiency
loss implemented).

Full documentation to be added.
"""

from pyomo.environ import Var, Set, Constraint, NonNegativeReals

from gridpath.auxiliary.auxiliary import generator_subset_init


def add_module_specific_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.SHIFTABLE_LOAD_GENERIC_PROJECTS = Set(
        within=m.PROJECTS,
        initialize=generator_subset_init("operational_type",
                                         "dr")
    )

    m.SHIFTABLE_LOAD_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.SHIFTABLE_LOAD_GENERIC_PROJECTS))

    m.SHIFTABLE_LOAD_GENERIC_PROJECT_OPERATIONAL_HORIZONS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, mod.horizon[tmp, mod.balancing_type_project[g]]) for (g, tmp) in
                mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.SHIFTABLE_LOAD_GENERIC_PROJECTS))

    # Variables
    # Add load (i.e. negative power)
    m.Generic_Shiftable_Load_Shift_Up_MW = \
        Var(m.SHIFTABLE_LOAD_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)
    # Remove load (i.e. positive power)
    m.Generic_Shiftable_Load_Shift_Down_MW = \
        Var(m.SHIFTABLE_LOAD_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals
            )

    # Constraints
    def max_shift_up_rule(mod, l, tmp):
        """
        Can't exceed power capacity
        :param mod: 
        :param l: 
        :param tmp: 
        :return: 
        """
        return mod.Generic_Shiftable_Load_Shift_Up_MW[l, tmp] <= \
            mod.Capacity_MW[l, mod.period[tmp]]
    
    m.Generic_Shiftable_Load_Max_Shift_Up_Constraint = Constraint(
        m.SHIFTABLE_LOAD_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=max_shift_up_rule
    )

    def max_shift_down_rule(mod, l, tmp):
        """
        Can't exceed power capacity
        :param mod: 
        :param l: 
        :param tmp: 
        :return: 
        """
        return mod.Generic_Shiftable_Load_Shift_Down_MW[l, tmp] <= \
            mod.Capacity_MW[l, mod.period[tmp]]

    m.Generic_Shiftable_Load_Max_Shift_Down_Constraint = Constraint(
        m.SHIFTABLE_LOAD_GENERIC_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=max_shift_down_rule
    )

    def energy_balance_rule(mod, l, h):
        """
        No efficiency losses
        :param mod:
        :param l:
        :param h:
        :return:
        """
        return sum(
            mod.Generic_Shiftable_Load_Shift_Up_MW[l, tmp]
            for tmp in mod.TIMEPOINTS_ON_HORIZON[h]
        ) == sum(
            mod.Generic_Shiftable_Load_Shift_Down_MW[l, tmp]
            for tmp in mod.TIMEPOINTS_ON_HORIZON[h]
        )

    m.Generic_Shiftable_Load_Energy_Balance_Constraint = Constraint(
        m.SHIFTABLE_LOAD_GENERIC_PROJECT_OPERATIONAL_HORIZONS,
        rule=energy_balance_rule
    )

    def energy_budget_rule(mod, l, h):
        """
        Total energy that can be shifted on each horizon
        Get the period for the total capacity from the first timepoint of the
        horizon
        :param mod:
        :param l:
        :param h:
        :return:
        """
        return sum(
            mod.Generic_Shiftable_Load_Shift_Up_MW[l, tmp] *
            mod.number_of_hours_in_timepoint[tmp]
            for tmp in mod.TIMEPOINTS_ON_HORIZON[h]
        ) == mod.Energy_Capacity_MWh[
            l, mod.period[mod.first_horizon_timepoint[h]]
        ]

    m.Generic_Shiftable_Load_Energy_Budget_Constraint = Constraint(
        m.SHIFTABLE_LOAD_GENERIC_PROJECT_OPERATIONAL_HORIZONS,
        rule=energy_budget_rule
    )


def power_provision_rule(mod, l, tmp):
    """
    Shiftable load
    :param mod:
    :param l:
    :param tmp:
    :return:
    """
    return -mod.Generic_Shiftable_Load_Shift_Up_MW[l, tmp] \
        + mod.Generic_Shiftable_Load_Shift_Down_MW[l, tmp]


def fuel_burn_rule(mod, g, tmp, error_message):
    """

    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        raise ValueError(

            "ERROR! Shiftable load projects should not use fuel." + "\n" +
            "Check input data for project '{}'".format(g) + "\n" +
            "and change its fuel to '.' (no value)."
        )
    else:
        raise ValueError(error_message)


def startup_rule(mod, g, tmp, l):
    """
    :param mod:
    :param g:
    :param tmp:
    :param l:
    :return:
    """
    raise ValueError(
        "ERROR! Shiftable load projects should not incur startup "
        "costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup/shutdown costs to '.' (no value)."
    )


def shutdown_rule(mod, g, tmp):
    """
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise ValueError(
        "ERROR! Shiftable load projects should not incur shutdown "
        "costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup/shutdown costs to '.' (no value)."
    )


def power_delta_rule(mod, l, tmp):
    """
    :param mod:
    :param l:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[
        mod.horizon[tmp, mod.balancing_type_project[l]]] \
            and mod.boundary[mod.horizon[tmp, mod.balancing_type_project[l]]] == \
            "linear":
        pass
    else:
        return (mod.Generic_Shiftable_Load_Shift_Up_MW[l, tmp]
                - mod.Generic_Shiftable_Load_Shift_Down_MW[l, tmp]) - \
            (mod.Generic_Shiftable_Load_Shift_Up_MW[
                 l, mod.previous_timepoint[tmp, mod.balancing_type_project[l]]
             ]
                - mod.Generic_Shiftable_Load_Shift_Down_MW[
                 l, mod.previous_timepoint[tmp, mod.balancing_type_project[l]]
             ])
