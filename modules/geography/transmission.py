#!/usr/bin/env python

import os.path
from pandas import read_csv
from pyomo.environ import Set, Param, Var, Constraint, Expression, Reals

from auxiliary import load_tx_capacity_modules


def determine_dynamic_components(d, scenario_directory, horizon, stage):
    """

    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # Get the capacity type of each generator
    dynamic_components = \
        read_csv(os.path.join(scenario_directory, "inputs",
                              "transmission_lines.tab"),
                 sep="\t", usecols=["TRANSMISSION_LINES", "tx_capacity_type"]
                 )

    # Required modules are the unique set of generator operational types
    # This list will be used to know which operational modules to load
    d.required_tx_capacity_modules = \
        dynamic_components.tx_capacity_type.unique()


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    m.TRANSMISSION_LINES = Set()
    m.tx_capacity_type = Param(m.TRANSMISSION_LINES)
    m.load_zone_from = Param(m.TRANSMISSION_LINES)
    m.load_zone_to = Param(m.TRANSMISSION_LINES)

    # Capacity-type modules will populate this list if called
    # List will be used to initialize TRANSMISSION_OPERATIONAL_PERIODS
    m.tx_capacity_type_operational_period_sets = []

    m.required_tx_capacity_modules = d.required_tx_capacity_modules
    # Import needed transmission capacity modules
    imported_tx_capacity_modules = \
        load_tx_capacity_modules(m.required_tx_capacity_modules)

    # First, add any components specific to the transmission capacity modules
    for op_m in m.required_tx_capacity_modules:
        imp_op_m = imported_tx_capacity_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m)

    def join_tx_cap_type_operational_period_sets(mod):
        """
        Join the sets we need to make the TRANSMISSION_OPERATIONAL_PERIODS
        super set; if list contains only a single set, return just that set
        :param mod:
        :return:
        """
        if len(mod.tx_capacity_type_operational_period_sets) == 0:
            return []
        elif len(mod.tx_capacity_type_operational_period_sets) == 1:
            return getattr(mod, mod.tx_capacity_type_operational_period_sets[0])

        else:
            return reduce(lambda x, y: getattr(mod, x) | getattr(mod, y),
                          mod.tx_capacity_type_operational_period_sets)

    m.TRANSMISSION_OPERATIONAL_PERIODS = \
        Set(dimen=2,
            initialize=join_tx_cap_type_operational_period_sets)

    def transmission_min_capacity_rule(mod, tx, p):
        tx_cap_type = mod.tx_capacity_type[tx]
        return imported_tx_capacity_modules[tx_cap_type]. \
            min_transmission_capacity_rule(mod, tx, p)

    m.Transmission_Min_Capacity_MW = \
        Expression(m.TRANSMISSION_OPERATIONAL_PERIODS,
                   rule=transmission_min_capacity_rule)

    def transmission_max_capacity_rule(mod, tx, p):
        tx_cap_type = mod.tx_capacity_type[tx]
        return imported_tx_capacity_modules[tx_cap_type]. \
            max_transmission_capacity_rule(mod, tx, p)

    m.Transmission_Max_Capacity_MW = \
        Expression(m.TRANSMISSION_OPERATIONAL_PERIODS,
                   rule=transmission_max_capacity_rule)

    # ### Transmission operations ### #

    # Define various sets to be used in transmission operations module
    m.OPERATIONAL_PERIODS_BY_TRANSMISSION_LINE = \
        Set(m.TRANSMISSION_LINES,
            rule=lambda mod, tx: set(
                p for (l, p) in mod.TRANSMISSION_OPERATIONAL_PERIODS if
                l == tx)
            )

    def tx_op_tmps_init(mod):
        tx_tmps = set()
        for tx in mod.TRANSMISSION_LINES:
            for p in mod.OPERATIONAL_PERIODS_BY_TRANSMISSION_LINE[tx]:
                for tmp in mod.TIMEPOINTS_IN_PERIOD[p]:
                    tx_tmps.add((tx, tmp))
        return tx_tmps
    m.TRANSMISSION_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, rule=tx_op_tmps_init)

    m.Transmit_Power_MW = Var(m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
                              within=Reals)

    def min_transmit_rule(mod, l, tmp):
        """

        :param mod:
        :param l:
        :param tmp:
        :return:
        """
        return mod.Transmit_Power_MW[l, tmp] \
            >= mod.Transmission_Min_Capacity_MW[l, mod.period[tmp]]

    m.Min_Transmit_Constraint = \
        Constraint(m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
                   rule=min_transmit_rule)

    def max_transmit_rule(mod, l, tmp):
        """

        :param mod:
        :param l:
        :param tmp:
        :return:
        """
        return mod.Transmit_Power_MW[l, tmp] \
            <= mod.Transmission_Max_Capacity_MW[l, mod.period[tmp]]

    m.Max_Transmit_Constraint = \
        Constraint(m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
                   rule=max_transmit_rule)

    # Add to load balance
    def total_transmission_to_rule(mod, z, tmp):
        return sum(mod.Transmit_Power_MW[tx, tmp]
                   for tx in mod.TRANSMISSION_LINES
                   if mod.load_zone_to[tx] == z)
    m.Transmission_to_Zone_MW = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                           rule=total_transmission_to_rule)
    d.load_balance_production_components.append("Transmission_to_Zone_MW")

    def total_transmission_from_rule(mod, z, tmp):
        return sum(mod.Transmit_Power_MW[tx, tmp]
                   for tx in mod.TRANSMISSION_LINES
                   if mod.load_zone_from[tx] == z)
    m.Transmission_from_Zone_MW = Expression(m.LOAD_ZONES, m.TIMEPOINTS,
                                             rule=total_transmission_from_rule)
    d.load_balance_consumption_components.append("Transmission_from_Zone_MW")


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory, "inputs",
                                           "transmission_lines.tab"),
                     select=("TRANSMISSION_LINES", "tx_capacity_type",
                             "load_zone_from", "load_zone_to"),
                     index=m.TRANSMISSION_LINES,
                     param=(m.tx_capacity_type,
                            m.load_zone_from, m.load_zone_to)
                     )

    imported_tx_capacity_modules = \
        load_tx_capacity_modules(m.required_tx_capacity_modules)
    for op_m in m.required_tx_capacity_modules:
        if hasattr(imported_tx_capacity_modules[op_m],
                   "load_module_specific_data"):
            imported_tx_capacity_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, horizon, stage)
        else:
            pass



def export_results(scenario_directory, horizon, stage, m):
    for tx in getattr(m, "TRANSMISSION_LINES"):
        for tmp in getattr(m, "TIMEPOINTS"):
            print("Transmit_Power_MW[" + str(tx) + ", " + str(tmp) + "]: "
                  + str(m.Transmit_Power_MW[tx, tmp].value)
                  )