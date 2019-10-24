#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This is a line-level module that adds to the formulation components that
describe the amount of power flowing on each line, subject to DC OPF
constraints. The DC OPF constraints are based on the Kirchhoff approach laid
out in Horsch et al. (2018).

Note: transmission operational types can optionally be mixed and matched.
If there are any non-dc_opf_transmission operational types, they will simply
not be considered when setting up the network constraints laid out in this
module.

Source: Horsch et al. (2018). Linear Optimal Power Flow Using Cycle Flows
"""

from __future__ import print_function

import networkx as nx
import os
import pandas as pd

from pyomo.environ import Set, Var, Constraint, Reals, Param


def add_module_specific_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # --- Sets ---

    # DC OPF transmission lines
    m.TRANSMISSION_LINES_DC_OPF = Set(
        within=m.TRANSMISSION_LINES,
        rule=lambda mod: set(l for l in mod.TRANSMISSION_LINES if
                             mod.tx_operational_type[l] ==
                             "dc_opf_transmission")
    )

    # DC OPF operational timepoints
    m.TX_DC_OPF_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2, within=m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod:
            set((l, tmp) for (l, tmp) in mod.TRANSMISSION_OPERATIONAL_TIMEPOINTS
                if l in mod.TRANSMISSION_LINES_DC_OPF))

    # Independent cycles which form a basis for cycles of the graph network
    m.CYCLES = Set()

    # 2-D set of transmission lines and independent cycles it belongs to
    m.TRANSMISSION_LINE_CYCLES = Set(within=m.TRANSMISSION_LINES * m.CYCLES)

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
    #  by checking for each cycle which tx_lines are included, and checking
    #  the transmission operational timepoints for those tx_lines
    #  --> seems like this would be a complex, slow operation
    m.CYCLES_OPERATIONAL_TIMEPOINTS = Set(initialize=m.CYCLES * m.TIMEPOINTS)

    # --- Params ---

    # The series reactance for each DC OPF transmission line
    m.reactance_ohms = Param(m.TRANSMISSION_LINES_DC_OPF)
    # The value of the cycle incidence matrix for each tx_line and cycle
    m.tx_cycle_direction = Param(m.TRANSMISSION_LINE_CYCLES)

    # --- Decision variables ---

    m.Transmit_Power_DC_OPF_MW = Var(m.TX_DC_OPF_OPERATIONAL_TIMEPOINTS,
                                     within=Reals)

    # --- Constraints ---

    def kirchhoff_voltage_law_rule(mod, c, tmp):
        """
        The sum of all potential difference across branches around all cycles
        in the network must be zero. In DC power flow we assume all voltage
        magnitudes are kept at nominal value and the voltage angle differences
        across branches is small enough that we can approximate the sinus of
        the angle with the angle itself, i.e. sin(theta) ~ theta.
        We can therefore write KVL in terms of voltage angles as follows:

        ..math:: \\sum_{l} C_{l,c} * \theta_{l} = 0   \\forall c = 1,...,L-N+1

        Using the linearized relationship between voltage angle
        differences across branches and the line flow, :math:`\theta_{l} = x_{l}
        * f_{l}`, we can factor out the voltage angles and write KVL purely in
        terms of line flows and line reactances:

        .. math:: C_{l,c} * x_{l} * f_{l} = 0   \\forall c = 1,...,L-N+1

        The latter equation is enforced in this constraint.

        Note: While most power flow formulations normalize all inputs to per
        unit (p.u.) we can safely avoid that here since the normalization
        factors out in the equation, and it is really just about the relative
        magnitude of the reactance of the lines.

        Source: Horsch et al. (2018). Linear Optimal Power Flow Using Cycle
        Flows
        :param mod:
        :param c: basic cycle in the network
        :param tmp:
        :return:
        """

        return sum(
            mod.Transmit_Power_DC_OPF_MW[l, tmp] * mod.tx_cycle_direction[l, c]
            * mod.reactance_ohms[l]
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
        Line flows cannot exceed the minimum line rating
        :param mod:
        :param l:
        :param tmp:
        :return:
        """
        return mod.Transmit_Power_DC_OPF_MW[l, tmp] \
            >= mod.Transmission_Min_Capacity_MW[l, mod.period[tmp]]

    m.Min_Transmit_DC_OPF_Constraint = \
        Constraint(m.TX_DC_OPF_OPERATIONAL_TIMEPOINTS,
                   rule=min_transmit_rule)

    def max_transmit_rule(mod, l, tmp):
        """
        Line flows cannot exceed the maximum line rating
        :param mod:
        :param l:
        :param tmp:
        :return:
        """
        return mod.Transmit_Power_DC_OPF_MW[l, tmp] \
            <= mod.Transmission_Max_Capacity_MW[l, mod.period[tmp]]

    m.Max_Transmit_DC_OPF_Constraint = \
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
                 "tx_operational_type", "reactance_ohms"]
    )
    df = df[df["tx_operational_type"] == "dc_opf_transmission"].reset_index()
    df["reactance_ohms"] = pd.to_numeric(df["reactance_ohms"])

    # create a network graph from the list of lines (edges) and find
    # the elementary cycles (if any)
    G = nx.Graph()
    # TODO: make sure there are no parallel edges (or pre-process those)
    edges = list(zip(df['load_zone_from'], df['load_zone_to']))
    G.add_edges_from(edges)
    cycles = nx.cycle_basis(G)  # list with list of nodes for each cycle

    cycle_set = []  # list of cycle_ids
    tx_lines_cycles = []  # list of tuples with (tx_line, cycle_id)
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

    # If there are more negative directions for tx lines than positive ones,
    # revert the cycle direction (this is to standardize cycle direction)
    if sum(tx_cycle_directions.values()) < 0:
        tx_cycle_directions = {(tx, c): -v
                               for (tx, c), v in tx_cycle_directions.items()}

    # Dict of reactance by dc_opf_transmission line
    reactance_ohms = dict(zip(df["TRANSMISSION_LINES"], df["reactance_ohms"]))

    # Load data
    data_portal.data()["CYCLES"] = {None: cycle_set}
    data_portal.data()["TRANSMISSION_LINE_CYCLES"] = {None: tx_lines_cycles}
    data_portal.data()["tx_cycle_direction"] = tx_cycle_directions
    data_portal.data()["reactance_ohms"] = reactance_ohms


def transmit_power_rule(mod, l, tmp):
    """

    :param mod:
    :param l:
    :param tmp:
    :return:
    """
    return mod.Transmit_Power_DC_OPF_MW[l, tmp]
