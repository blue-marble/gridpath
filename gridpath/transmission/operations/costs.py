#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This is a Tx-line-level module that adds to the formulation components that
describe the operations-related costs of transmisison lines (e.g. hurdle
rate costs).
"""

from __future__ import print_function

from builtins import next
from builtins import str
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
        m.TRANSMISSION_LINES, m.PERIODS,
        within=NonNegativeReals, default=0
    )

    m.hurdle_rate_negative_direction_per_mwh = Param(
        m.TRANSMISSION_LINES, m.PERIODS,
        within=NonNegativeReals, default=0
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
        if mod.hurdle_rate_positive_direction_per_mwh[tx, mod.period[tmp]] \
                == 0:
            return Constraint.Skip
        else:
            return mod.Hurdle_Cost_Positive_Direction[tx, tmp] \
                >= mod.Transmit_Power_MW[tx, tmp] * \
                mod.hurdle_rate_positive_direction_per_mwh[tx, mod.period[tmp]]
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
        if mod.hurdle_rate_negative_direction_per_mwh[tx, mod.period[tmp]] \
                == 0:
            return Constraint.Skip
        else:
            return mod.Hurdle_Cost_Negative_Direction[tx, tmp] \
                >= -mod.Transmit_Power_MW[tx, tmp] * \
                mod.hurdle_rate_negative_direction_per_mwh[tx, mod.period[tmp]]
    m.Hurdle_Cost_Negative_Direction_Constraint = Constraint(
        m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
        rule=hurdle_cost_negative_direction_rule
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    data_portal.load(filename=
                     os.path.join(scenario_directory, subproblem, stage, "inputs",
                                  "transmission_hurdle_rates.tab"),
                     select=("transmission_line", "period",
                             "hurdle_rate_positive_direction_per_mwh",
                             "hurdle_rate_negative_direction_per_mwh"),
                     param=(m.hurdle_rate_positive_direction_per_mwh,
                            m.hurdle_rate_negative_direction_per_mwh)
                     )


def get_inputs_from_database(subscenarios, subproblem, stage, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    # transmission_hurdle_rates.tab
    with open(os.path.join(inputs_directory,
                           "transmission_hurdle_rates.tab"),
              "w") as \
            sim_flows_file:
        writer = csv.writer(sim_flows_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["transmission_line", "period",
             "hurdle_rate_positive_direction_per_mwh",
             "hurdle_rate_negative_direction_per_mwh"]
        )

        hurdle_rates = c.execute(
            """SELECT transmission_line, period, 
            hurdle_rate_positive_direction_per_mwh,
            hurdle_rate_negative_direction_per_mwh
            FROM inputs_transmission_hurdle_rates
            INNER JOIN
            (SELECT period
             FROM inputs_temporal_periods
             WHERE temporal_scenario_id = {}) as relevant_periods
             USING (period)
             WHERE transmission_hurdle_rate_scenario_id = {};
            """.format(
                subscenarios.TEMPORAL_SCENARIO_ID,
                subscenarios.TRANSMISSION_HURDLE_RATE_SCENARIO_ID
            )
        )
        for row in hurdle_rates:
            writer.writerow(row)


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export transmission operational cost results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
              "costs_transmission_hurdle.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["tx_line", "period", "horizon", "timepoint", "horizon_weight",
             "number_of_hours_in_timepoint", "load_zone_from", "load_zone_to",
             "hurdle_cost_positive_direction",
             "hurdle_cost_negative_direction"]
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


def import_results_into_database(scenario_id, subproblem, stage, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # Hurdle costs
    print("transmission hurdle costs")
    c.execute(
        """DELETE FROM results_transmission_hurdle_costs
        WHERE scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};
        """.format(scenario_id, subproblem, stage)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_transmission_hurdle_costs"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_transmission_hurdle_costs""" 
        + str(scenario_id) + """(
        scenario_id INTEGER,
        transmission_line VARCHAR(64),
        period INTEGER,
        subproblem_id INTEGER,
        stage_id INTEGER,
        horizon INTEGER,
        timepoint INTEGER,
        horizon_weight FLOAT,
        number_of_hours_in_timepoint FLOAT,
        load_zone_from VARCHAR(32),
        load_zone_to VARCHAR(32),
        hurdle_cost_positive_direction FLOAT,
        hurdle_cost_negative_direction FLOAT,
        PRIMARY KEY (scenario_id, transmission_line, subproblem_id, stage_id, timepoint)
            );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "costs_transmission_hurdle.csv"),
              "r") as tx_op_file:
        reader = csv.reader(tx_op_file)

        next(reader)  # skip header
        for row in reader:
            tx_line = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            lz_from = row[6]
            lz_to = row[7]
            hurdle_cost_positve_direction = row[8]
            hurdle_cost_negative_direction = row[9]
            c.execute(
                """INSERT INTO temp_results_transmission_hurdle_costs"""
                + str(scenario_id) + """
                (scenario_id, transmission_line, period, subproblem_id, stage_id,
                horizon, timepoint, horizon_weight,
                number_of_hours_in_timepoint,
                load_zone_from, load_zone_to, 
                hurdle_cost_positive_direction, hurdle_cost_negative_direction)
                VALUES ({}, '{}', {}, {}, {}, {}, {}, {}, {}, 
                '{}', '{}', {}, {});""".format(
                    scenario_id, tx_line, period, subproblem, stage,
                    horizon, timepoint, horizon_weight,
                    number_of_hours_in_timepoint,
                    lz_from, lz_to,
                    hurdle_cost_positve_direction,
                    hurdle_cost_negative_direction
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_transmission_hurdle_costs
        (scenario_id, transmission_line, period, subproblem_id, stage_id, 
        horizon, timepoint, horizon_weight, number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, hurdle_cost_positive_direction,
        hurdle_cost_negative_direction)
        SELECT
        scenario_id, transmission_line, period, subproblem_id, stage_id,
        horizon, timepoint, horizon_weight, number_of_hours_in_timepoint,
        load_zone_from, load_zone_to, hurdle_cost_positive_direction,
        hurdle_cost_negative_direction
        FROM temp_results_transmission_hurdle_costs"""
        + str(scenario_id) +
        """
         ORDER BY scenario_id, transmission_line, subproblem_id, stage_id, 
        timepoint;
        """
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_transmission_hurdle_costs"""
        + str(scenario_id) + """;"""
    )
    db.commit()
