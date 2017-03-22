#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate carbon emissions from the transmission-line-timepoint level to
the carbon cap zone - period level.
"""

import csv
import os.path
from pyomo.environ import Param, Var, Constraint, NonNegativeReals, \
    Expression, value


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.hurdle_rate_positive_direction_per_mwh = Param(
        m.TRANSMISSION_LINES, within=NonNegativeReals, default=0
    )

    m.hurdle_rate_negative_direction_per_mwh = Param(
        m.TRANSMISSION_LINES, within=NonNegativeReals, default=0
    )

    m.Hurdle_Cost_Positive_Direction = Var(
        m.TRANSMISSION_OPERATIONAL_TIMEPOINTS, within=NonNegativeReals
    )
    m.Hurdle_Cost_Negative_Direction = Var(
        m.TRANSMISSION_OPERATIONAL_TIMEPOINTS, within=NonNegativeReals
    )

    def hurdle_cost_positive_direction_rule(mod, tx, tmp):
        """
        Hurdle_Cost_Positive_Direction must be non-negative, so will be 0
        when Transmit_Power is negative (flow in the negative direction)
        :param mod:
        :param tx:
        :param tmp:
        :return:
        """
        if mod.hurdle_rate_positive_direction_per_mwh[tx] == 0:
            return Constraint.Skip
        else:
            return mod.Hurdle_Cost_Positive_Direction[tx, tmp] \
                >= mod.Transmit_Power_MW[tx, tmp] * \
                mod.hurdle_rate_positive_direction_per_mwh[tx]
    m.Hurdle_Cost_Positive_Direction_Constraint = Constraint(
        m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
        rule=hurdle_cost_positive_direction_rule
    )

    def hurdle_cost_negative_direction_rule(mod, tx, tmp):
        """
        Hurdle_Cost_Negative_Direction must be non-negative, so will be 0
        when Transmit_Power is positive (flow in the positive direction)
        :param mod:
        :param tx:
        :param tmp:
        :return:
        """
        if mod.hurdle_rate_negative_direction_per_mwh[tx] == 0:
            return Constraint.Skip
        else:
            return mod.Hurdle_Cost_Negative_Direction[tx, tmp] \
                >= -mod.Transmit_Power_MW[tx, tmp] * \
                mod.hurdle_rate_negative_direction_per_mwh[tx]
    m.Hurdle_Cost_Negative_Direction_Constraint = Constraint(
        m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
        rule=hurdle_cost_negative_direction_rule
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
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs",
                                           "transmission_lines.tab"),
                     index=m.TRANSMISSION_LINES,
                     select=("TRANSMISSION_LINES",
                             "hurdle_rate_positive_direction_per_mwh",
                             "hurdle_rate_negative_direction_per_mwh"),
                     param=(m.hurdle_rate_positive_direction_per_mwh,
                            m.hurdle_rate_negative_direction_per_mwh)
                     )


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    hurdle_rates = c.execute(
        """SELECT transmission_line,
        hurdle_rate_positive_direction_per_mwh,
        hurdle_rate_negative_direction_per_mwh
        FROM inputs_transmission_hurdle_rates
            WHERE transmission_hurdle_rate_scenario_id = {}""".format(
            subscenarios.TRANSMISSION_HURDLE_RATE_SCENARIO_ID
        )
    ).fetchall()

    # Make a dict for easy access
    hurdle_rate_dict = dict()
    for (tx, hurdle_rate_positive, hurdle_rate_negative) in hurdle_rates:
        hurdle_rate_dict[str(tx)] = \
            (hurdle_rate_positive, hurdle_rate_negative)

    with open(os.path.join(inputs_directory, "transmission_lines.tab"), "r"
              ) as tx_file_in:
        reader = csv.reader(tx_file_in, delimiter="\t")

        new_rows = list()

        # Append column header
        header = reader.next()
        header.append("hurdle_rate_positive_direction_per_mwh")
        header.append("hurdle_rate_negative_direction_per_mwh")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If transmission line specified, assign value from dictionary
            if row[0] in hurdle_rate_dict.keys():
                row.append(hurdle_rate_dict[row[0]][0])
                row.append(hurdle_rate_dict[row[0]][1])
                new_rows.append(row)
            # If project not specified, specify 0 hurdle rates
            else:
                row.append(0)
                row.append(0)
                new_rows.append(row)

    with open(os.path.join(inputs_directory, "transmission_lines.tab"),
              "w") as tx_file_out:
        writer = csv.writer(tx_file_out, delimiter="\t")
        writer.writerows(new_rows)


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export transmission operational cost results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
              "costs_transmission_hurdle.csv"), "wb") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["tx", "period", "horizon", "timepoint", "horizon_weight",
             "number_of_hours_in_timepoint", "load_zone_from", "load_zone_to",
             "hurdle_rate_cost_positive_direction",
             "hurdle_rate_cost_negative_direction"]
        )
        for (tx, tmp) in m.TRANSMISSION_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                tx,
                m.period[tmp],
                m.horizon[tmp],
                tmp,
                m.horizon_weight[m.horizon[tmp]],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone_from[tx],
                m.load_zone_to[tx],
                value(m.Hurdle_Cost_Positive_Direction[tx, tmp]),
                value(m.Hurdle_Cost_Negative_Direction[tx, tmp])
            ])
