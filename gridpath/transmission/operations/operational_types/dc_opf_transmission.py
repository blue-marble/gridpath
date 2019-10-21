#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This is a line-level module that adds to the formulation components that
describe the amount of power flowing on each line.
"""

from __future__ import print_function

import networkx as nx
import os
import pandas as pd

from pyomo.environ import Set, Var, Constraint, Reals, Param

# TODO: figure out how to scale reactance inputs and add unit to name
# TODO: manually check calcs for the example problem
# TODO: check example with multiple periods
# TODO: check example with new build transmissions
# TODO: check example mixing and matching transmission types
# TODO: check example when there are no cycles (e.g. 2 zones)
#   --> should skip constraint
# TODO: test run_end_to_end and set up db structures if needed

# TODO: make this work with new build and vintages and periods?
#  this means that the cycles can change by period (would this work?!)


def add_module_specific_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Set: DC OPF transmission lines
    m.TRANSMISSION_LINES_DC_OPF = Set(
        within=m.TRANSMISSION_LINES,
        rule=lambda mod: set(l for l in mod.TRANSMISSION_LINES if
                             mod.tx_operational_type[l] ==
                             "dc_opf_transmission")
    )

    # Set: DC OPF operational timepoints
    m.TX_DC_OPF_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2, within=m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
            set((l, tmp) for (l, tmp) in mod.TRANSMISSION_OPERATIONAL_TIMEPOINTS
                if l in mod.TRANSMISSION_LINES_DC_OPF))

    # Params
    # TODO: might need to derive/process this from other inputs (p.u.?)
    m.reactance = Param(m.TRANSMISSION_LINES_DC_OPF)

    # Decision variable: transmitted power flow
    m.Transmit_Power_DC_OPF_MW = Var(m.TX_DC_OPF_OPERATIONAL_TIMEPOINTS,
                                     within=Reals)

    # Set of cycles which form a basis for cycles of the graph network
    m.CYCLES = Set()

    m.TRANSMISSION_LINE_CYCLES = Set(within=m.TRANSMISSION_LINES * m.CYCLES)
    m.tx_cycle_direction = Param(m.TRANSMISSION_LINE_CYCLES)

    # Indexed set of transmission lines in cycle
    def tx_lines_by_cycle(mod, cycle):
        """
        Figure out which tx_lines are in each cycle
        :param mod:
        :param cycle:
        :return:
        """
        txs = list(tx for (tx, c) in mod.TRANSMISSION_LINE_CYCLES if c == cycle)
        return txs
    m.TRANSMISSION_LINES_IN_CYCLE = Set(m.CYCLES, initialize=tx_lines_by_cycle)

    # 2-D Set of cycles and operational timepoints
    # TODO: shouldn't this smartly select only the timepoints that are relevant
    #  by checking for each cycle which transmission is included, and checking
    #  the transmission operational timepoints for that transmission
    #  --> seems like this would be a complex, slow operation
    m.CYCLES_OPERATIONAL_TIMEPOINTS = Set(initialize=m.CYCLES * m.TIMEPOINTS)

    def kirchhoff_voltage_law_rule(mod, c, tmp):
        """
        See constraint (4) in Horsch et al. (2018)
        :param mod:
        :param c: elementary cycle in the graph network
        :param tmp:
        :return:
        """

        return sum(
            mod.Transmit_Power_DC_OPF_MW[l, tmp] * mod.tx_cycle_direction[l, c]
            * mod.reactance[l]
            for l in mod.TRANSMISSION_LINES_IN_CYCLE[c]
        ) == 0

    m.Kirchhoff_Voltage_Law_Constraint = Constraint(
        m.CYCLES_OPERATIONAL_TIMEPOINTS,
        rule=kirchhoff_voltage_law_rule
    )

    # TODO: should these move to operations.py since all transmission op_types
    #  have this constraint?
    def min_transmit_rule(mod, l, tmp):
        """

        :param mod:
        :param l:
        :param tmp:
        :return:
        """
        return mod.Transmit_Power_DC_OPF_MW[l, tmp] \
               >= mod.Transmission_Min_Capacity_MW[l, mod.period[tmp]]

    m.Min_Transmit_Constraint = \
        Constraint(m.TX_DC_OPF_OPERATIONAL_TIMEPOINTS,
                   rule=min_transmit_rule)

    def max_transmit_rule(mod, l, tmp):
        """

        :param mod:
        :param l:
        :param tmp:
        :return:
        """
        return mod.Transmit_Power_DC_OPF_MW[l, tmp] \
               <= mod.Transmission_Max_Capacity_MW[l, mod.period[tmp]]

    m.Max_Transmit_Constraint = \
        Constraint(m.TX_DC_OPF_OPERATIONAL_TIMEPOINTS,
                   rule=max_transmit_rule)


def load_module_specific_data(m, data_portal, scenario_directory,
                              subproblem, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Get the DC OPF lines
    df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "inputs",
                     "transmission_lines.tab"),
        sep="\t",
        usecols=["TRANSMISSION_LINES", "load_zone_from", "load_zone_to",
                 "tx_operational_type", "reactance"]
    )
    df = df[df["tx_operational_type"] == "dc_opf_transmission"]

    # create a network graph from the list of edges and find elementary cycles
    G = nx.Graph()
    # TODO: make sure there are no parallel edges (or pre-process those)
    edges = list(zip(df['load_zone_from'], df['load_zone_to']))
    G.add_edges_from(edges)
    cycles = nx.cycle_basis(G)  # list with list of nodes for each cycle

    cycle_set = []
    tx_lines_cycles = []
    tx_cycle_directions = {}  # indexed by tx_line and cycle
    for i, cycle in enumerate(cycles):
        cycle_set.append(i)
        for tx_from, tx_to in zip(cycle[-1:] + cycle[:-1], cycle):
            try:
                index = edges.index((tx_from, tx_to))
                tx_direction = 1
            except ValueError:
                try:
                    # revert the direction
                    index = edges.index((tx_to, tx_from))
                    tx_direction = -1
                except ValueError:
                    raise ValueError("The branch connecting {} and {} is not"
                                     "in the transmission line inputs".format(
                                        tx_from, tx_to))
            tx_line = df.loc[index, "TRANSMISSION_LINES"]
            tx_lines_cycles.append((tx_line, i))
            tx_cycle_directions[(tx_line, i)] = tx_direction

    print(tx_lines_cycles)
    print(tx_cycle_directions)

    # Dict of reactance by dc opf line
    reactance = dict(zip(df["TRANSMISSION_LINES"], df["reactance"]))

    # Load data
    data_portal.data()["CYCLES"] = {None: cycle_set}
    data_portal.data()["TRANSMISSION_LINE_CYCLES"] = {None: tx_lines_cycles}
    data_portal.data()["tx_cycle_direction"] = tx_cycle_directions
    data_portal.data()["reactance"] = reactance


def transmit_power_rule(mod, l, tmp):
    """

    :param mod:
    :param l:
    :param tmp:
    :return:
    """
    return mod.Transmit_Power_DC_OPF_MW[l, tmp]
