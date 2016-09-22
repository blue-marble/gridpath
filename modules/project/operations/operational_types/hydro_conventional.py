#!/usr/bin/env python

"""
Operations of generic storage
"""

from pyomo.environ import Var, Set, Constraint, NonNegativeReals

from modules.auxiliary.auxiliary import generator_subset_init


def add_module_specific_components(m, scenario_directory):
    """
    Add a capacity commit variable to represent the amount of capacity that is
    on.
    :param m:
    :param scenario_directory:
    :return:
    """

    m.HYDRO_CONVENTIONAL_PROJECTS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type",
                              "hydro_conventional")
    )

    m.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.HYDRO_CONVENTIONAL_PROJECTS))

    m.Hydro_Conventional_Provide_Power_MW = \
        Var(m.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    def hydro_energy_budget_rule(mod, g, h):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return sum(mod.Hydro_Conventional_Provide_Power_MW[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   for tmp in mod.TIMEPOINTS_ON_HORIZON[h]) \
            == \
            sum(mod.hydro_specified_average_power_mwa[g, h]
                * mod.number_of_hours_in_timepoint[tmp]
                for tmp in mod.TIMEPOINTS_ON_HORIZON[h])

    m.Conventional_Hydro_Energy_Budget_Constraint = \
        Constraint(m.HYDRO_SPECIFIED_OPERATIONAL_HORIZONS,
                   rule=hydro_energy_budget_rule)


def power_provision_rule(mod, g, tmp):
    """
    Power provision from conventional hydro
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Hydro_Conventional_Provide_Power_MW[g, tmp]


def max_power_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Hydro_Conventional_Provide_Power_MW[g, tmp] \
        <= mod.hydro_specified_max_power_mw[g, mod.horizon[tmp]]


def min_power_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Hydro_Conventional_Provide_Power_MW[g, tmp] \
        >= mod.hydro_specified_min_power_mw[g, mod.horizon[tmp]]


def curtailment_rule(mod, g, tmp):
    """
    This treatment does not allow curtailment
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def fuel_cost_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def startup_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def shutdown_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0
