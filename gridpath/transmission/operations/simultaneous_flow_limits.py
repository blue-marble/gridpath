#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Set, Param, Constraint, NonNegativeReals, \
    Integers, Expression, value


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.SIMULTANEOUS_FLOW_LIMIT_GROUP_PERIODS = Set(dimen=2)
    m.simultaneous_flow_limit_mw = Param(
        m.SIMULTANEOUS_FLOW_LIMIT_GROUP_PERIODS, within=NonNegativeReals
    )

    m.SIMULTANEOUS_FLOW_LIMIT_GROUP_TIMEPOINTS = Set(
        dimen=2,
        rule=lambda mod:
        set((g, tmp)
            for (g, p) in mod.SIMULTANEOUS_FLOW_LIMIT_GROUP_PERIODS
            for tmp in mod.TIMEPOINTS_IN_PERIOD[p]
            )
    )
    m.SIMULTANEOUS_FLOW_GROUPS = Set(
        rule=lambda mod:
        set(group for (group, period) in
            mod.SIMULTANEOUS_FLOW_LIMIT_GROUP_PERIODS)
    )

    m.SIMULTANEOUS_FLOW_GROUP_LINES = Set(
        dimen=2, within=m.SIMULTANEOUS_FLOW_GROUPS * m.TRANSMISSION_LINES
    )

    m.simultaneous_flow_direction = Param(
        m.SIMULTANEOUS_FLOW_GROUP_LINES, within=Integers,
        validate=lambda mod, v, g, l: v in [-1, 1]
    )

    m.TRANSMISSION_LINES_BY_SIMULTANEOUS_FLOW_GROUP = Set(
        m.SIMULTANEOUS_FLOW_GROUPS,
        rule=lambda mod, g:
        set(tx_line for (group, tx_line)
            in mod.SIMULTANEOUS_FLOW_GROUP_LINES if group == g)
    )

    def simultaneous_flow_expression_rule(mod, g, tmp):
        """
        Total flow on lines in each group
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return sum(mod.Transmit_Power_MW[tx_line, tmp] *
                   mod.simultaneous_flow_direction[g, tx_line]
                   for tx_line in
                   mod.TRANSMISSION_LINES_BY_SIMULTANEOUS_FLOW_GROUP[g]
                   if (tx_line, tmp) in
                   mod.TRANSMISSION_OPERATIONAL_TIMEPOINTS)
    m.Simultaneous_Flow_MW = Expression(
        m.SIMULTANEOUS_FLOW_LIMIT_GROUP_TIMEPOINTS,
        rule=simultaneous_flow_expression_rule
    )

    def simultaneous_flow_constraint_rule(mod, g, tmp):
        """
        Total flow on lines in each group cannot exceed limit
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Simultaneous_Flow_MW[g, tmp] \
            <= mod.simultaneous_flow_limit_mw[g, mod.period[tmp]]

    m.Simultaneous_Flow_Constraint = Constraint(
        m.SIMULTANEOUS_FLOW_LIMIT_GROUP_TIMEPOINTS,
        rule=simultaneous_flow_constraint_rule
    )


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
    data_portal.load(filename=os.path.join(
        scenario_directory, "inputs", "transmission_simultaneous_flows.tab"),
                     select=("simultaneous_flow_group", "period",
                             "simultaneous_flow_limit_mw"),
                     index=m.SIMULTANEOUS_FLOW_LIMIT_GROUP_PERIODS,
                     param=m.simultaneous_flow_limit_mw
                     )

    data_portal.load(filename=os.path.join(
        scenario_directory, "inputs",
        "transmission_simultaneous_flow_group_lines.tab"),
                     select=("simultaneous_flow_group", "transmission_line",
                             "simultaneous_flow_direction"),
                     index=m.SIMULTANEOUS_FLOW_GROUP_LINES,
                     param=m.simultaneous_flow_direction
                     )


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export transmission operations
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "transmission_simultaneous_flows.csv"), "wb") as \
            tx_op_results_file:
        writer = csv.writer(tx_op_results_file)
        writer.writerow(["simultaneous_flow_group", "timepoint", "period",
                         "horizon", "horizon_weight",
                         "simultaneous_flow_mw"])
        for (g, tmp) in m.SIMULTANEOUS_FLOW_LIMIT_GROUP_TIMEPOINTS:
            writer.writerow([
                g,
                tmp,
                m.period[tmp],
                m.horizon[tmp],
                m.horizon_weight[m.horizon[tmp]],
                value(m.Simultaneous_Flow_MW[g, tmp])
            ])


def save_duals(m):
    m.constraint_indices["Simultaneous_Flow_Constraint"] = \
        ["simultaneous_flow_group", "timepoint", "dual"]


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """
    # Simultaneous flow
    with open(os.path.join(inputs_directory,
                           "transmission_simultaneous_flow_group_lines.tab"),
              "w") as \
            sim_flow_group_lines_file:
        writer = csv.writer(sim_flow_group_lines_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["simultaneous_flow_group", "transmission_line",
             "simultaneous_flow_direction"]
        )

        group_lines = c.execute(
            """SELECT transmission_simultaneous_flow_group, transmission_line,
            simultaneous_flow_direction
            FROM transmission_simultaneous_flow_group_lines
            WHERE load_zone_scenario_id = {}
            AND transmission_line_scenario_id = {}
            AND transmission_simultaneous_flow_group_lines_scenario_id = {};
            """.format(
                subscenarios.LOAD_ZONE_SCENARIO_ID,
                subscenarios.TRANSMISSION_LINE_SCENARIO_ID,
                subscenarios.
                    TRANSMISSION_SIMULTANEOUS_FLOW_GROUP_LINES_SCENARIO_ID
            )
        )
        for row in group_lines:
            writer.writerow(row)

    # transmission_simultaneous_flows.tab
    with open(os.path.join(inputs_directory,
                           "transmission_simultaneous_flows.tab"), "w") as \
            sim_flows_file:
        writer = csv.writer(sim_flows_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["simultaneous_flow_group", "period", "simultaneous_flow_limit_mw"]
        )

        flow_limits = c.execute(
            """SELECT transmission_simultaneous_flow_group, period, max_flow_mw
            FROM transmission_simultaneous_flow_limits
            WHERE load_zone_scenario_id = {}
            AND transmission_line_scenario_id = {}
            AND transmission_simultaneous_flow_group_lines_scenario_id = {}
            AND period_scenario_id = {}
            AND transmission_simultaneous_flow_limit_scenario_id = {};
            """.format(
                subscenarios.LOAD_ZONE_SCENARIO_ID,
                subscenarios.TRANSMISSION_LINE_SCENARIO_ID,
                subscenarios.
                    TRANSMISSION_SIMULTANEOUS_FLOW_GROUP_LINES_SCENARIO_ID,
                subscenarios.PERIOD_SCENARIO_ID,
                subscenarios.TRANSMISSION_SIMULTANEOUS_FLOW_LIMIT_SCENARIO_ID
            )
        )
        for row in flow_limits:
            writer.writerow(row)
