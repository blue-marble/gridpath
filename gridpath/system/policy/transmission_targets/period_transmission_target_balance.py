# Copyright 2022 (c) Crown Copyright, GC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Simplest implementation with a MWh target by period.
"""


import csv
import os.path
import pandas as pd

from pyomo.environ import Var, Constraint, NonNegativeReals, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.Period_Transmission_Target_Shortage_Pos_Dir_MWh = Var(
        m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET,
        within=NonNegativeReals,
    )

    m.Period_Transmission_Target_Shortage_Neg_Dir_MWh = Var(
        m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET,
        within=NonNegativeReals,
    )

    def violation_pos_dir_expression_rule(mod, z, p):
        return (
            mod.Period_Transmission_Target_Shortage_Pos_Dir_MWh[z, p]
            * mod.transmission_target_allow_violation[z]
        )

    m.Period_Transmission_Target_Shortage_Pos_Dir_MWh_Expression = Expression(
        m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET,
        rule=violation_pos_dir_expression_rule,
    )

    def violation_neg_dir_expression_rule(mod, z, p):
        return (
            mod.Period_Transmission_Target_Shortage_Neg_Dir_MWh[z, p]
            * mod.transmission_target_allow_violation[z]
        )

    m.Period_Transmission_Target_Shortage_Neg_Dir_MWh_Expression = Expression(
        m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET,
        rule=violation_neg_dir_expression_rule,
    )

    def transmission_target_pos_dir_rule(mod, z, p):
        """
        Total delivered transmission-target-eligible energy in positive direction must exceed target
        :param mod:
        :param z:
        :param p:
        :return:
        """
        if mod.period_transmission_target_pos_dir_mwh[z, p] == 0:
            return Constraint.Skip
        else:
            return (
                mod.Total_Period_Transmission_Target_Energy_Pos_Dir_MWh[z, p]
                + mod.Period_Transmission_Target_Shortage_Pos_Dir_MWh_Expression[z, p]
                >= mod.Period_Transmission_Target_Pos_Dir[z, p]
            )

    m.Period_Transmission_Target_Pos_Dir_Constraint = Constraint(
        m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET,
        rule=transmission_target_pos_dir_rule,
    )

    def transmission_target_neg_dir_rule(mod, z, p):
        """
        Total delivered transmission-target-eligible energy in negative direction must exceed target
        :param mod:
        :param z:
        :param p:
        :return:
        """
        if mod.period_transmission_target_neg_dir_mwh[z, p] == 0:
            return Constraint.Skip
        else:
            return (
                mod.Total_Period_Transmission_Target_Energy_Neg_Dir_MWh[z, p]
                + mod.Period_Transmission_Target_Shortage_Neg_Dir_MWh_Expression[z, p]
                >= mod.Period_Transmission_Target_Neg_Dir[z, p]
            )

    m.Period_Transmission_Target_Neg_Dir_Constraint = Constraint(
        m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET,
        rule=transmission_target_neg_dir_rule,
    )


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "period_transmission_target.csv",
        ),
        "w",
        newline="",
    ) as transmission_target_results_file:
        writer = csv.writer(transmission_target_results_file)
        writer.writerow(
            [
                "transmission_target_zone",
                "period",
                "discount_factor",
                "number_years_represented",
                "transmission_target_positive_direction_mwh",
                "total_transmission_target_energy_positive_direction_mwh",
                "fraction_of_transmission_target_positive_direction_met",
                "transmission_target_shortage_positive_direction_mwh",
                "transmission_target_negative_direction_mwh",
                "total_transmission_target_energy_negative_direction_mwh",
                "fraction_of_transmission_target_negative_direction_met",
                "transmission_target_shortage_negative_direction_mwh",
            ]
        )
        for z, p in m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET:
            writer.writerow(
                [
                    z,
                    p,
                    m.discount_factor[p],
                    m.number_years_represented[p],
                    value(m.Period_Transmission_Target_Pos_Dir[z, p]),
                    value(m.Total_Period_Transmission_Target_Energy_Pos_Dir_MWh[z, p]),
                    1
                    if float(m.period_transmission_target_pos_dir_mwh[z, p]) == 0
                    else value(
                        m.Total_Period_Transmission_Target_Energy_Pos_Dir_MWh[z, p]
                    )
                    / float(m.period_transmission_target_pos_dir_mwh[z, p]),
                    value(
                        m.Period_Transmission_Target_Shortage_Pos_Dir_MWh_Expression[
                            z, p
                        ]
                    ),
                    value(m.Period_Transmission_Target_Neg_Dir[z, p]),
                    value(m.Total_Period_Transmission_Target_Energy_Neg_Dir_MWh[z, p]),
                    1
                    if float(m.period_transmission_target_neg_dir_mwh[z, p]) == 0
                    else value(
                        m.Total_Period_Transmission_Target_Energy_Neg_Dir_MWh[z, p]
                    )
                    / float(m.period_transmission_target_neg_dir_mwh[z, p]),
                    value(
                        m.Period_Transmission_Target_Shortage_Neg_Dir_MWh_Expression[
                            z, p
                        ]
                    ),
                ]
            )


def import_results_into_database(
    scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_system_period_transmission_target",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "period_transmission_target.csv"), "r"
    ) as transmission_target_file:
        reader = csv.reader(transmission_target_file)

        next(reader)  # skip header
        for row in reader:
            transmission_target_zone = row[0]
            period = row[1]
            discount_factor = row[2]
            number_years = row[3]
            transmission_target_pos_dir = row[4]
            total_transmission_target_provision_pos_dir = row[5]
            fraction_met_pos_dir = row[6]
            shortage_pos_dir = row[7]
            transmission_target_neg_dir = row[8]
            total_transmission_target_provision_neg_dir = row[9]
            fraction_met_neg_dir = row[10]
            shortage_neg_dir = row[11]

            results.append(
                (
                    scenario_id,
                    transmission_target_zone,
                    period,
                    subproblem,
                    stage,
                    discount_factor,
                    number_years,
                    transmission_target_pos_dir,
                    total_transmission_target_provision_pos_dir,
                    fraction_met_pos_dir,
                    shortage_pos_dir,
                    transmission_target_neg_dir,
                    total_transmission_target_provision_neg_dir,
                    fraction_met_neg_dir,
                    shortage_neg_dir,
                )
            )

    insert_temp_sql = """
        INSERT INTO temp_results_system_period_transmission_target{}
         (scenario_id, transmission_target_zone, period, subproblem_id, stage_id,
         discount_factor, number_years_represented, transmission_target_positive_direction_mwh, 
         total_transmission_target_energy_positive_direction_mwh,
         fraction_of_transmission_target_positive_direction_met,
         transmission_target_shortage_positive_direction_mwh,
         transmission_target_negative_direction_mwh,
         total_transmission_target_energy_negative_direction_mwh,
         fraction_of_transmission_target_negative_direction_met,
         transmission_target_shortage_negative_direction_mwh)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_system_period_transmission_target
        (scenario_id, transmission_target_zone, period, subproblem_id, stage_id,
        discount_factor, number_years_represented, transmission_target_positive_direction_mwh, 
        total_transmission_target_energy_positive_direction_mwh,
        fraction_of_transmission_target_positive_direction_met,
        transmission_target_shortage_positive_direction_mwh,
        transmission_target_negative_direction_mwh,
        total_transmission_target_energy_negative_direction_mwh,
        fraction_of_transmission_target_negative_direction_met,
        transmission_target_shortage_negative_direction_mwh)
        SELECT scenario_id, transmission_target_zone, period, subproblem_id, stage_id,
        discount_factor, number_years_represented, transmission_target_positive_direction_mwh, 
        total_transmission_target_energy_positive_direction_mwh,
        fraction_of_transmission_target_positive_direction_met,
        transmission_target_shortage_positive_direction_mwh,
        transmission_target_negative_direction_mwh,
        total_transmission_target_energy_negative_direction_mwh,
        fraction_of_transmission_target_negative_direction_met,
        transmission_target_shortage_negative_direction_mwh
        FROM temp_results_system_period_transmission_target{}
        ORDER BY scenario_id, transmission_target_zone, period, subproblem_id, stage_id;
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)
