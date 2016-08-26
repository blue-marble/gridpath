#!/usr/bin/env python

"""
Describe operational costs.
"""
from pyomo.environ import *


def add_model_components(m, d):
    """
    Sum up all operational costs and add to the objective function.
    :param m:
    :param d:
    :return:
    """

    # ### Aggregate power costs for objective function ### #
    # Add cost to objective function
    # TODO: fix this when periods added, etc.
    def generation_cost_rule(m, g, tmp):
        """
        Power production cost for each generator.
        :param m:
        :return:
        """
        return m.Power_Provision_MW[g, tmp] * m.variable_cost_per_mwh[g]

    m.Generation_Cost = Expression(m.GENERATORS, m.TIMEPOINTS,
                                   rule=generation_cost_rule)

    # ### Startup and shutdown costs ### #
    m.Startup_Cost = Var(m.STARTUP_COST_GENERATORS, m.TIMEPOINTS,
                         within=NonNegativeReals)
    m.Shutdown_Cost = Var(m.SHUTDOWN_COST_GENERATORS, m.TIMEPOINTS,
                          within=NonNegativeReals)

    def startup_cost_rule(mod, g, tmp):
        """
        Startup expression is positive when more units are on in the current
        timepoint that were on in the previous timepoint. Startup_Cost is
        defined to be non-negative, so if Startup_Expression is 0 or negative
        (i.e. no units started or units shut down since the previous timepoint),
        Startup_Cost will be 0.
        If horizon is circular, the last timepoint of the horizon is the
        previous_timepoint for the first timepoint if the horizon;
        if the horizon is linear, no previous_timepoint is defined for the first
        timepoint of the horizon, so skip constraint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        else:
            return mod.Startup_Cost[g, tmp] \
                >= mod.Startup_Expression[g, tmp] \
                * mod.startup_cost_per_unit[g]
    m.Startup_Cost_Constraint = Constraint(m.STARTUP_COST_GENERATORS,
                                           m.TIMEPOINTS,
                                           rule=startup_cost_rule)

    def shutdown_cost_rule(mod, g, tmp):
        """
        Shutdown expression is positive when more units were on in the previous
        timepoint that are on in the current timepoint. Shutdown_Cost is
        defined to be non-negative, so if Shutdown_Expression is 0 or negative
        (i.e. no units shut down or units started since the previous timepoint),
        Shutdown_Cost will be 0.
        If horizon is circular, the last timepoint of the horizon is the
        previous_timepoint for the first timepoint if the horizon;
        if the horizon is linear, no previous_timepoint is defined for the first
        timepoint of the horizon, so skip constraint.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        else:
            return mod.Shutdown_Cost[g, tmp] \
                >= mod.Shutdown_Expression[g, tmp] \
                * mod.shutdown_cost_per_unit[g]
    m.Shutdown_Cost_Constraint = Constraint(m.SHUTDOWN_COST_GENERATORS,
                                            m.TIMEPOINTS,
                                            rule=shutdown_cost_rule)
