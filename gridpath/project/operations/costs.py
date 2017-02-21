#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Describe operational costs.
"""
from pandas import read_csv
import os.path
from pyomo.environ import Var, Set, Param, Expression, Constraint, \
    NonNegativeReals, PositiveReals

from gridpath.auxiliary.dynamic_components import required_operational_modules, \
    total_cost_components
from gridpath.auxiliary.auxiliary import load_operational_type_modules, is_number


def add_model_components(m, d):
    """
    Sum up all operational costs and add to the objective function.
    :param m:
    :param d:
    :return:
    """

    # Generators that incur startup/shutdown costs
    m.STARTUP_COST_PROJECTS = Set(within=m.PROJECTS)
    m.startup_cost_per_unit = Param(m.STARTUP_COST_PROJECTS,
                                    within=PositiveReals)

    m.SHUTDOWN_COST_PROJECTS = Set(within=m.PROJECTS)
    m.shutdown_cost_per_unit = Param(m.SHUTDOWN_COST_PROJECTS,
                                     within=PositiveReals)

    # TODO: implement check for which generator types can have fuels
    # Fuels and heat rates
    m.FUEL_PROJECTS = Set(within=m.PROJECTS)
    m.fuel = Param(m.FUEL_PROJECTS, within=m.FUELS)
    m.minimum_input_mmbtu_per_hr = Param(m.FUEL_PROJECTS)
    m.inc_heat_rate_mmbtu_per_mwh = Param(m.FUEL_PROJECTS)

    m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.FUEL_PROJECTS))

    m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.STARTUP_COST_PROJECTS))

    m.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.SHUTDOWN_COST_PROJECTS))

    # ### Aggregate operational costs for objective function ### #
    # Add cost to objective function
    def variable_om_cost_rule(m, g, tmp):
        """
        Power production cost for each generator.
        :param m:
        :return:
        """
        return m.Power_Provision_MW[g, tmp] * m.variable_om_cost_per_mwh[g]

    m.Variable_OM_Cost = Expression(m.PROJECT_OPERATIONAL_TIMEPOINTS,
                                    rule=variable_om_cost_rule)

    # Power production variable costs
    def total_variable_om_cost_rule(mod):
        """
        Power production cost for all generators across all timepoints
        :param mod:
        :return:
        """
        return sum(mod.Variable_OM_Cost[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS)

    m.Total_Variable_OM_Cost = Expression(rule=total_variable_om_cost_rule)
    getattr(d, total_cost_components).append("Total_Variable_OM_Cost")

    # From here, the operational modules determine how the model components are
    # formulated
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # ### Fuel cost ### #
    def fuel_cost_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            fuel_cost_rule(mod, g, tmp)

    m.Fuel_Cost = Expression(m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS,
                             rule=fuel_cost_rule)

    def total_fuel_cost_rule(mod):
        """
        Power production cost for all generators across all timepoints
        :param mod:
        :return:
        """
        return sum(mod.Fuel_Cost[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp) in mod.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS)

    m.Total_Fuel_Cost = Expression(rule=total_fuel_cost_rule)
    getattr(d, total_cost_components).append("Total_Fuel_Cost")

    # ### Startup and shutdown costs ### #
    def startup_rule(mod, g, tmp):
        """
        Track units started up from timepoint to timepoint; get appropriate
        expression from the generator's operational module.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            startup_rule(mod, g, tmp)
    m.Startup_Expression = Expression(
        m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=startup_rule)

    def shutdown_rule(mod, g, tmp):
        """
        Track units shut down from timepoint to timepoint; get appropriate
        expression from the generator's operational module.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            shutdown_rule(mod, g, tmp)
    m.Shutdown_Expression = Expression(
        m.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_rule)
    m.Startup_Cost = Var(m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS,
                         within=NonNegativeReals)
    m.Shutdown_Cost = Var(m.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS,
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
    m.Startup_Cost_Constraint = \
        Constraint(m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS,
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
    m.Shutdown_Cost_Constraint = Constraint(
        m.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_cost_rule)

    # Startup and shutdown costs
    def total_startup_cost_rule(mod):
        """
        Sum startup costs for the objective function term.
        :param mod:
        :return:
        """
        return sum(mod.Startup_Cost[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp)
                   in mod.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS)
    m.Total_Startup_Cost = Expression(rule=total_startup_cost_rule)
    getattr(d, total_cost_components).append("Total_Startup_Cost")

    def total_shutdown_cost_rule(mod):
        """
        Sum shutdown costs for the objective function term.
        :param mod:
        :return:
        """
        return sum(mod.Shutdown_Cost[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   * mod.number_years_represented[mod.period[tmp]]
                   * mod.discount_factor[mod.period[tmp]]
                   for (g, tmp)
                   in mod.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS)
    m.Total_Shutdown_Cost = Expression(rule=total_shutdown_cost_rule)
    getattr(d, total_cost_components).append("Total_Shutdown_Cost")


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # STARTUP_COST_PROJECTS
    def determine_startup_cost_projects():
        """
        If numeric values greater than 0 for startup costs are specified
        for some generators, add those generators to the
        STARTUP_COST_PROJECTS subset and initialize the respective startup
        cost param value
        :param mod:
        :return:
        """
        startup_cost_projects = list()
        startup_cost_per_unit = dict()

        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project",
                                   "startup_cost"]
                )
        for row in zip(dynamic_components["project"],
                       dynamic_components["startup_cost"]):
            if is_number(row[1]) and float(row[1]) > 0:
                startup_cost_projects.append(row[0])
                startup_cost_per_unit[row[0]] = float(row[1])
            else:
                pass

        return startup_cost_projects, startup_cost_per_unit

    data_portal.data()["STARTUP_COST_PROJECTS"] = {
        None: determine_startup_cost_projects()[0]
    }

    data_portal.data()["startup_cost_per_unit"] = \
        determine_startup_cost_projects()[1]

    # SHUTDOWN_COST_PROJECTS
    def determine_shutdown_cost_projects():
        """
        If numeric values greater than 0 for shutdown costs are specified
        for some generators, add those generators to the
        SHUTDOWN_COST_PROJECTS subset and initialize the respective shutdown
        cost param value
        :param mod:
        :return:
        """

        shutdown_cost_projects = list()
        shutdown_cost_per_unit = dict()

        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project",
                                   "shutdown_cost"]
                )
        for row in zip(dynamic_components["project"],
                       dynamic_components["shutdown_cost"]):
            if is_number(row[1]) and float(row[1]) > 0:
                shutdown_cost_projects.append(row[0])
                shutdown_cost_per_unit[row[0]] = float(row[1])
            else:
                pass

        return shutdown_cost_projects, shutdown_cost_per_unit

    data_portal.data()["SHUTDOWN_COST_PROJECTS"] = {
        None: determine_shutdown_cost_projects()[0]
    }

    data_portal.data()["shutdown_cost_per_unit"] = \
        determine_shutdown_cost_projects()[1]

    # FUEL_PROJECTS
    def determine_fuel_projects():
        """
        E.g. generators that use coal, gas, uranium
        :param mod:
        :return:
        """
        fuel_projects = list()
        fuel = dict()
        minimum_input_mmbtu_per_hr = dict()
        inc_heat_rate_mmbtu_per_mwh = dict()

        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project",
                                   "fuel",
                                   "minimum_input_mmbtu_per_hr",
                                   "inc_heat_rate_mmbtu_per_mwh"]
                )

        for row in zip(dynamic_components["project"],
                       dynamic_components["fuel"],
                       dynamic_components["minimum_input_mmbtu_per_hr"],
                       dynamic_components["inc_heat_rate_mmbtu_per_mwh"]):
            if row[1] != ".":
                fuel_projects.append(row[0])
                fuel[row[0]] = row[1]
                minimum_input_mmbtu_per_hr[row[0]] = float(row[2])
                inc_heat_rate_mmbtu_per_mwh[row[0]] = float(row[3])
            else:
                pass

        return fuel_projects, fuel, minimum_input_mmbtu_per_hr, \
               inc_heat_rate_mmbtu_per_mwh

    data_portal.data()["FUEL_PROJECTS"] = {
        None: determine_fuel_projects()[0]
    }

    data_portal.data()["fuel"] = determine_fuel_projects()[1]
    data_portal.data()["minimum_input_mmbtu_per_hr"] = \
        determine_fuel_projects()[2]
    data_portal.data()["inc_heat_rate_mmbtu_per_mwh"] = \
        determine_fuel_projects()[3]
