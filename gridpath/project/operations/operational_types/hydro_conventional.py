#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of generic storage
"""

import os.path
from pyomo.environ import Var, Set, Param, Constraint, NonNegativeReals

from gridpath.auxiliary.auxiliary import generator_subset_init
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables


def add_module_specific_components(m, d):
    """
    Add a capacity commit variable to represent the amount of capacity that is
    on.
    :param m:
    :return:
    """
    # Sets and params
    m.HYDRO_CONVENTIONAL_PROJECTS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type",
                              "hydro_conventional")
    )

    m.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_HORIZONS = \
        Set(dimen=2)

    m.hydro_specified_average_power_mwa = \
        Param(m.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)
    m.hydro_specified_min_power_mw = \
        Param(m.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)
    m.hydro_specified_max_power_mw = \
        Param(m.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)

    m.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.HYDRO_CONVENTIONAL_PROJECTS))

    # Variables
    m.Hydro_Conventional_Provide_Power_MW = \
        Var(m.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    # Operational constraints
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
        Constraint(m.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_HORIZONS,
                   rule=hydro_energy_budget_rule)

    def max_power_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Hydro_Conventional_Provide_Power_MW[g, tmp] + \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, headroom_variables)[g]) \
               <= mod.hydro_specified_max_power_mw[g, mod.horizon[tmp]]
    m.Hydro_Conventional_Max_Power_Constraint = \
        Constraint(
            m.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=max_power_rule
        )

    def min_power_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Hydro_Conventional_Provide_Power_MW[g, tmp] - \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, footroom_variables)[g]) \
            >= mod.hydro_specified_min_power_mw[g, mod.horizon[tmp]]
    m.Hydro_Conventional_Min_Power_Constraint = \
        Constraint(
            m.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=min_power_rule
        )


def power_provision_rule(mod, g, tmp):
    """
    Power provision from conventional hydro
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Hydro_Conventional_Provide_Power_MW[g, tmp]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision from conventional hydro if eligible
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Hydro_Conventional_Provide_Power_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    This treatment does not allow curtailment
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0

# TODO: ignoring subhourly behavior for hydro for now
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


def load_module_specific_data(m,
                              data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(filename=
                     os.path.join(scenario_directory, horizon,
                                  "inputs",
                                  "hydro_conventional_horizon_params.tab"),
                     index=
                     m.HYDRO_CONVENTIONAL_PROJECT_OPERATIONAL_HORIZONS,
                     select=("hydro_project", "horizon",
                             "hydro_specified_average_power_mwa",
                             "hydro_specified_min_power_mw",
                             "hydro_specified_max_power_mw"),
                     param=(m.hydro_specified_average_power_mwa,
                            m.hydro_specified_min_power_mw,
                            m.hydro_specified_max_power_mw)
                     )
