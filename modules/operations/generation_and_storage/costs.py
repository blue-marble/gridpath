#!/usr/bin/env python

"""
Describe operational costs.
"""
from pandas import read_csv
import os.path

from pyomo.environ import Var, Set, Param, Expression, Constraint, \
    NonNegativeReals, PositiveReals, BuildAction

from modules.auxiliary.auxiliary import load_operational_type_modules, is_number


def add_model_components(m, d, scenario_directory, horizon, stage):
    """
    Sum up all operational costs and add to the objective function.
    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # The components below will be initialized via Pyomo's BuildAction function
    # See:
    # software.sandia.gov/downloads/pub/pyomo/PyomoOnlineDocs.html#BuildAction

    def determine_startup_cost_generators(mod):
        """
        If numeric values greater than 0 for startup costs are specified
        for some generators, add those generators to the
        STARTUP_COST_GENERATORS subset and initialize the respective startup
        cost param value
        :param mod:
        :return:
        """
        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "generators.tab"),
                sep="\t", usecols=["GENERATORS",
                                   "startup_cost"]
                )
        for row in zip(dynamic_components["GENERATORS"],
                       dynamic_components["startup_cost"]):
            if is_number(row[1]) and float(row[1]) > 0:
                mod.STARTUP_COST_GENERATORS.add(row[0])
                mod.startup_cost_per_unit[row[0]] = float(row[1])
            else:
                pass

    # Generators that incur startup/shutdown costs
    m.STARTUP_COST_GENERATORS = Set(within=m.GENERATORS, initialize=[])
    m.startup_cost_per_unit = Param(m.STARTUP_COST_GENERATORS,
                                    within=PositiveReals, mutable=True,
                                    initialize={})
    m.StartupCostGeneratorsBuild = BuildAction(
        rule=determine_startup_cost_generators)

    def determine_shutdown_cost_generators(mod):
        """
        If numeric values greater than 0 for shutdown costs are specified
        for some generators, add those generators to the
        SHUTDOWON_COST_GENERATORS subset and initialize the respective shutdown
        cost param value
        :param mod:
        :return:
        """
        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "generators.tab"),
                sep="\t", usecols=["GENERATORS",
                                   "shutdown_cost"]
                )
        for row in zip(dynamic_components["GENERATORS"],
                       dynamic_components["shutdown_cost"]):
            if is_number(row[1]) and float(row[1]) > 0:
                mod.SHUTDOWN_COST_GENERATORS.add(row[0])
                mod.shutdown_cost_per_unit[row[0]] = float(row[1])
            else:
                pass

    m.SHUTDOWN_COST_GENERATORS = Set(within=m.GENERATORS, initialize=[])
    m.shutdown_cost_per_unit = Param(m.SHUTDOWN_COST_GENERATORS,
                                     within=PositiveReals, mutable=True,
                                     initialize={})
    m.ShutdownCostGeneratorsBuild = BuildAction(
        rule=determine_shutdown_cost_generators)

    # TODO: implement check for which generator types can have fuels
    # Fuels and heat rates
    def determine_fuel_generators(mod):
        """
        E.g. generators that use coal, gas, uranium
        :param mod:
        :return:
        """
        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "generators.tab"),
                sep="\t", usecols=["GENERATORS",
                                   "fuel",
                                   "minimum_input_mmbtu_per_hr",
                                   "inc_heat_rate_mmbtu_per_mwh"]
                )

        for row in zip(dynamic_components["GENERATORS"],
                       dynamic_components["fuel"],
                       dynamic_components["minimum_input_mmbtu_per_hr"],
                       dynamic_components["inc_heat_rate_mmbtu_per_mwh"]):
            if row[1] != ".":
                mod.FUEL_GENERATORS.add(row[0])
                mod.fuel[row[0]] = row[1]
                mod.minimum_input_mmbtu_per_hr[row[0]] = float(row[2])
                mod.inc_heat_rate_mmbtu_per_mwh[row[0]] = float(row[3])
            else:
                pass

    m.FUEL_GENERATORS = Set(within=m.GENERATORS, initialize=[])
    m.fuel = Param(m.FUEL_GENERATORS, within=m.FUELS, mutable=True,
                   initialize={})
    m.minimum_input_mmbtu_per_hr = Param(m.FUEL_GENERATORS, mutable=True,
                                         initialize={})

    m.inc_heat_rate_mmbtu_per_mwh = Param(m.FUEL_GENERATORS, mutable=True,
                                          initialize={})
    m.FuelGeneratorsBuild = BuildAction(rule=determine_fuel_generators)

    m.FUEL_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.FUEL_GENERATORS))

    m.STARTUP_COST_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.STARTUP_COST_GENERATORS))

    m.SHUTDOWN_COST_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS
                if g in mod.SHUTDOWN_COST_GENERATORS))

    # ### Aggregate operational costs for objective function ### #
    # Add cost to objective function
    # TODO: fix this when periods added, etc.
    def variable_om_cost_rule(m, g, tmp):
        """
        Power production cost for each generator.
        :param m:
        :return:
        """
        return m.Power_Provision_MW[g, tmp] * m.variable_om_cost_per_mwh[g]

    m.Variable_OM_Cost = Expression(m.GENERATOR_OPERATIONAL_TIMEPOINTS,
                                    rule=variable_om_cost_rule)

    # Power production variable costs
    # TODO: fix this when periods added, etc.
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
                   for (g, tmp) in mod.GENERATOR_OPERATIONAL_TIMEPOINTS)

    m.Total_Variable_OM_Cost = Expression(rule=total_variable_om_cost_rule)
    d.total_cost_components.append("Total_Variable_OM_Cost")

    # From here, the operational modules determine how the model components are
    # formulated
    m.required_operational_modules = d.required_operational_modules
    # Import needed operational modules
    imported_operational_modules = load_operational_type_modules(m)

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

    m.Fuel_Cost = Expression(m.FUEL_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
                   for (g, tmp) in mod.FUEL_GENERATOR_OPERATIONAL_TIMEPOINTS)

    m.Total_Fuel_Cost = Expression(rule=total_fuel_cost_rule)
    d.total_cost_components.append("Total_Fuel_Cost")

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
        m.STARTUP_COST_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
        m.SHUTDOWN_COST_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=shutdown_rule)
    m.Startup_Cost = Var(m.STARTUP_COST_GENERATOR_OPERATIONAL_TIMEPOINTS,
                         within=NonNegativeReals)
    m.Shutdown_Cost = Var(m.SHUTDOWN_COST_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
        Constraint(m.STARTUP_COST_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
        m.SHUTDOWN_COST_GENERATOR_OPERATIONAL_TIMEPOINTS,
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
                   in mod.STARTUP_COST_GENERATOR_OPERATIONAL_TIMEPOINTS)
    m.Total_Startup_Cost = Expression(rule=total_startup_cost_rule)
    d.total_cost_components.append("Total_Startup_Cost")

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
                   in mod.SHUTDOWN_COST_GENERATOR_OPERATIONAL_TIMEPOINTS)
    m.Total_Shutdown_Cost = Expression(rule=total_shutdown_cost_rule)
    d.total_cost_components.append("Total_Shutdown_Cost")
