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

    # Set of periods, cycles, and zones
    def periods_cycles_zones_init(mod):
        result = list()
        for period in mod.PERIODS:
            # Get the relevant tx_lines (= currently operational & DC OPF)
            tx_lines = list(
                mod.TRANSMISSION_LINES_DC_OPF &
                mod.TRANSMISSION_LINES_OPERATIONAL_IN_PERIOD[period]
            )

            # Get the edges from the relevant tx_lines
            edges = [(mod.load_zone_to[tx], mod.load_zone_from[tx])
                     for tx in tx_lines]
            # TODO: make sure there are no parallel edges (or pre-process those)

            # Create a network graph from the list of lines (edges) and find
            # the elementary cycles (if any)
            G = nx.Graph()
            G.add_edges_from(edges)
            cycles = nx.cycle_basis(G)  # list with list of zones for each cycle
            for cycle_id, cycle in enumerate(cycles):
                for zone in cycle:
                    result.append((period, cycle_id, zone))
        return result
    m.PERIODS_CYCLES_ZONES = Set(
        dimen=3,
        rule=periods_cycles_zones_init,
        ordered=True
    )

    # 2-D set: Period and cycle_id of the independent cycles of the network
    # graph (the network can change between periods)
    def period_cycles(mod):
        # TODO: is there a way to remove the duplicates (p, c) more cleanly?
        return set([(p, c) for (p, c, z) in mod.PERIODS_CYCLES_ZONES])
    m.PERIODS_CYCLES = Set(dimen=2, rule=period_cycles)

    # 2-D Set of cycle IDs and operational timepoints
    # KVL constraint is indexed by this set
    m.CYCLES_OPERATIONAL_TIMEPOINTS = Set(
        dimen=2,
        rule=lambda mod:
            set((c, tmp)
                for (p, c) in mod.PERIODS_CYCLES
                for tmp in mod.TIMEPOINTS_IN_PERIOD[p]))

    # Set of ordered zones/nodes in a cycle, indexed by (period, cycle)
    # Helper set, not directly used in constraints/param indices
    def zones_by_period_cycle(mod, period, cycle):
        return [z for (p, c, z) in mod.PERIODS_CYCLES_ZONES
                if p == period and c == cycle]
    m.ZONES_IN_PERIOD_CYCLE = Set(
        m.PERIODS_CYCLES,
        rule=zones_by_period_cycle,
        ordered=True
    )

    # 3-D set of periods, cycle_ids, and transmission lines in that period-cycle
    # Tx_cycle direction is indexed by this set, and the set is also used to get
    # TRANSMISSION_LINES_IN_PERIOD_CYCLE set
    def periods_cycles_transmission_lines(mod):
        result = list()
        for p, c in mod.PERIODS_CYCLES:
            # Ordered list of zones in the current cycle
            zones = list(mod.ZONES_IN_PERIOD_CYCLE[(p, c)])

            # Relevant tx_lines
            tx_lines = list(
                mod.TRANSMISSION_LINES_DC_OPF &
                mod.TRANSMISSION_LINES_OPERATIONAL_IN_PERIOD[p]
            )

            # Get the edges from the relevant tx_lines
            edges = [(mod.load_zone_to[tx], mod.load_zone_from[tx])
                     for tx in tx_lines]

            # Get the tx lines in this cycle
            for tx_from, tx_to in zip(zones[-1:] + zones[:-1], zones):
                try:
                    index = edges.index((tx_from, tx_to))
                except:
                    try:
                        # Revert direction
                        index = edges.index((tx_to, tx_from))
                    except:
                        raise ValueError(
                            "The branch connecting {} and {} is not in the "
                            "transmission line inputs".format(
                                tx_from, tx_to
                            )
                        )
                tx_line = tx_lines[index]
                result.append((p, c, tx_line))
        return result
    m.PERIODS_CYCLES_TRANSMISSION_LINES = Set(
        dimen=3,
        within=m.PERIODS_CYCLES * m.TRANSMISSION_LINES,
        rule=periods_cycles_transmission_lines)

    # Indexed set of transmission lines in each period-cycle
    # This set is used in the KVL constraint when summing up the values
    def tx_lines_by_period_cycle(mod, period, cycle):
        """
        Figure out which tx_lines are in each period-cycle
        :param mod:
        :param period:
        :param cycle:
        :return:
        """
        txs = list(tx for (p, c, tx) in mod.PERIODS_CYCLES_TRANSMISSION_LINES
                   if c == cycle and p == period)
        return txs
    m.TRANSMISSION_LINES_IN_PERIOD_CYCLE = Set(
        m.PERIODS_CYCLES,
        initialize=tx_lines_by_period_cycle
    )

    # TODO: factor out edges operational in period as a set?
    # TODO: factor out dc opf lines operational in period as a set?

    # --- Params ---

    # The series reactance for each DC OPF transmission line
    m.reactance_ohms = Param(m.TRANSMISSION_LINES_DC_OPF)

    # The value of the cycle incidence matrix for each period-cycle-tx_line
    def tx_cycle_direction_init(mod, period, cycle, tx_line):
        zones = list(mod.ZONES_IN_PERIOD_CYCLE[(period, cycle)])
        from_to = (mod.load_zone_from[tx_line], mod.load_zone_to[tx_line])
        if from_to in zip(zones[-1:] + zones[:-1], zones):
            direction = 1
        elif from_to in zip(zones, zones[-1:] + zones[:-1]):
            direction = -1
        else:
            raise ValueError(
                "The branch connecting {} and {} is not in the "
                "transmission line inputs".format(
                    mod.load_zone_from[tx_line], mod.load_zone_to[tx_line]
                )
            )
        return direction

        # TODO: how can we normalize the cycle direction (nx returns random
        #  order) after the param is initialized?
        # # If there are more negative directions for tx lines than positive ones,
        # # revert the cycle direction (this is to standardize cycle direction)
        # if sum(tx_cycle_directions.values()) < 0:
        #     tx_cycle_directions = {(p, c, tx): -v
        #                            for (p, c, tx), v
        #                            in tx_cycle_directions.items()}
        # return tx_cycle_directions

    m.tx_cycle_direction = Param(
        m.PERIODS_CYCLES_TRANSMISSION_LINES,
        initialize=tx_cycle_direction_init
    )

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
            mod.Transmit_Power_DC_OPF_MW[l, tmp]
            * mod.tx_cycle_direction[mod.period[tmp], c, l]
            * mod.reactance_ohms[l]
            for l in mod.TRANSMISSION_LINES_IN_PERIOD_CYCLE[mod.period[tmp], c]
        ) == 0

    m.Kirchhoff_Voltage_Law_Constraint = Constraint(
        m.CYCLES_OPERATIONAL_TIMEPOINTS,
        rule=kirchhoff_voltage_law_rule
    )

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

    # TODO: need to find TRANMISSION_LINES_OPERATIONAL_IN_PERIOD here so we
    #  can figure out the cycles for each operational period. However, this set
    #  is a derived set (see capacity.py) it is not easily available.
    #  OPTION 1: move everything to add_model components and derive the tx
    #  cycle direction param. This step would just read in reactance
    #  This is what I'm currently trying
    #  OPTION 2: derive the tx_operational_periods here again from the tab
    #  files. Not ideal since we'd be doing this twice (also in capacity.py)

    # Dict of reactance by dc_opf_transmission line
    reactance_ohms = dict(zip(
        df["TRANSMISSION_LINES"],
        pd.to_numeric(df["reactance_ohms"])
    ))

    # Load data
    data_portal.data()["reactance_ohms"] = reactance_ohms


def transmit_power_rule(mod, l, tmp):
    """

    :param mod:
    :param l:
    :param tmp:
    :return:
    """
    return mod.Transmit_Power_DC_OPF_MW[l, tmp]


