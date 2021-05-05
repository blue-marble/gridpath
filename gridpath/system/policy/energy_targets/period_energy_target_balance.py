# Copyright 2016-2021 Blue Marble Analytics LLC.
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

from __future__ import division
from __future__ import print_function

from builtins import next
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

    m.Period_Energy_Target_Shortage_MWh = Var(
        m.ENERGY_TARGET_ZONE_PERIODS_WITH_ENERGY_TARGET, within=NonNegativeReals
    )

    def violation_expression_rule(mod, z, p):
        return mod.Period_Energy_Target_Shortage_MWh[z, p] * mod.energy_target_allow_violation[z]

    m.Period_Energy_Target_Shortage_MWh_Expression = Expression(
        m.ENERGY_TARGET_ZONE_PERIODS_WITH_ENERGY_TARGET, rule=violation_expression_rule
    )

    def energy_target_rule(mod, z, p):
        """
        Total delivered energy-target-eligible energy must exceed target
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return mod.Total_Delivered_Period_Energy_Target_Energy_MWh[z, p] \
            + mod.Period_Energy_Target_Shortage_MWh_Expression[z, p] \
            >= mod.Period_Energy_Target[z, p]

    m.Period_Energy_Target_Constraint = Constraint(m.ENERGY_TARGET_ZONE_PERIODS_WITH_ENERGY_TARGET,
                                         rule=energy_target_rule)


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "period_energy_target.csv"), "w", newline="") as \
            energy_target_results_file:
        writer = csv.writer(energy_target_results_file)
        writer.writerow(["energy_target_zone", "period",
                         "discount_factor", "number_years_represented",
                         "energy_target_mwh",
                         "delivered_energy_target_energy_mwh",
                         "curtailed_energy_target_energy_mwh",
                         "total_energy_target_energy_mwh",
                         "fraction_of_energy_target_met",
                         "fraction_of_energy_target_energy_curtailed",
                         "energy_target_shortage_mwh"])
        for (z, p) in m.ENERGY_TARGET_ZONE_PERIODS_WITH_ENERGY_TARGET:
            writer.writerow([
                z,
                p,
                m.discount_factor[p],
                m.number_years_represented[p],
                value(m.Period_Energy_Target[z, p]),
                value(m.Total_Delivered_Period_Energy_Target_Energy_MWh[z, p]),
                value(m.Total_Curtailed_Period_Energy_Target_Energy_MWh[z, p]),
                value(m.Total_Delivered_Period_Energy_Target_Energy_MWh[z, p]) +
                value(m.Total_Curtailed_Period_Energy_Target_Energy_MWh[z, p]),
                1 if float(m.period_energy_target_mwh[z, p]) == 0
                else value(
                    m.Total_Delivered_Period_Energy_Target_Energy_MWh[z, p]) /
                float(m.period_energy_target_mwh[z, p]),
                0 if (value(m.Total_Delivered_Period_Energy_Target_Energy_MWh[z, p])
                      + value(m.Total_Curtailed_Period_Energy_Target_Energy_MWh[z, p])) == 0
                else value(m.Total_Curtailed_Period_Energy_Target_Energy_MWh[z, p]) /
                (value(m.Total_Delivered_Period_Energy_Target_Energy_MWh[z, p])
                 + value(m.Total_Curtailed_Period_Energy_Target_Energy_MWh[z, p])),
                value(m.Period_Energy_Target_Shortage_MWh_Expression[z, p])
            ])


def save_duals(m):
    m.constraint_indices["Period_Energy_Target_Constraint"] = \
        ["energy_target_zone", "period", "dual"]


def summarize_results(scenario_directory, subproblem, stage):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:

    Summarize energy-target policy results
    """

    summary_results_file = os.path.join(
        scenario_directory, subproblem, stage, "results", "summary_results.txt"
    )

    # Open in 'append' mode, so that results already written by other
    # modules are not overridden
    with open(summary_results_file, "a") as outfile:
        outfile.write(
            "\n### PERIOD ENERGY TARGET RESULTS ###\n"
        )

    # All these files are small, so won't be setting indices

    # Get the main energy-target results file
    energy_target_df = \
        pd.read_csv(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                                 "period_energy_target.csv")
                    )

    # Get the energy-target dual results
    energy_target_duals_df = \
        pd.read_csv(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                                 "Period_Energy_Target_Constraint.csv")
                    )

    # # Get the input metadata for periods
    # periods_df = \
    #     pd.read_csv(os.path.join(scenario_directory, "inputs", "periods.tab"),
    #                 sep="\t")

    # Join the above
    results_df = pd.DataFrame(
        pd.merge(
            left=energy_target_df,
            right=energy_target_duals_df,
            how="left",
            left_on=["energy_target_zone", "period"],
            right_on=["energy_target_zone", "period"]
        )
    )

    results_df.set_index(["energy_target_zone", "period"], inplace=True,
                         verify_integrity=True)

    # Calculate:
    # 1) the percent of energy-target energy that was curtailed
    # 2) the marginal energy-target cost per MWh based on the energy-target constraint duals --
    # to convert back to 'real' dollars, we need to divide by the discount
    # factor and the number of years a period represents
    results_df["percent_curtailed"] = pd.Series(
        index=results_df.index, dtype="float64"
    )
    results_df["energy_target_marginal_cost_per_mwh"] = pd.Series(
        index=results_df.index, dtype="float64"
    )

    pd.options.mode.chained_assignment = None  # default='warn'
    for indx, row in results_df.iterrows():
        if (results_df.delivered_energy_target_energy_mwh[indx] +
                results_df.curtailed_energy_target_energy_mwh[indx]) == 0:
            pct = 0
        else:
            pct = results_df.curtailed_energy_target_energy_mwh[indx] \
                / (results_df.delivered_energy_target_energy_mwh[indx] +
                   results_df.curtailed_energy_target_energy_mwh[indx]) * 100
        results_df.percent_curtailed[indx] = pct

        results_df.energy_target_marginal_cost_per_mwh[indx] = \
            results_df.dual[indx] \
            / (results_df.discount_factor[indx] *
               results_df.number_years_represented[indx])

    # Drop unnecessary columns before exporting
    results_df.drop("discount_factor", axis=1, inplace=True)
    results_df.drop("number_years_represented", axis=1, inplace=True)
    results_df.drop("total_energy_target_energy_mwh", axis=1, inplace=True)
    results_df.drop("fraction_of_energy_target_met", axis=1, inplace=True)
    results_df.drop("fraction_of_energy_target_energy_curtailed", axis=1, inplace=True)
    results_df.drop("energy_target_shortage_mwh", axis=1, inplace=True)

    # Rearrange the columns
    cols = results_df.columns.tolist()
    cols = cols[0:3] + [cols[4]] + [cols[3]] + [cols[5]]
    results_df = results_df[cols]
    results_df.sort_index(inplace=True)
    with open(summary_results_file, "a") as outfile:
        results_df.to_string(outfile, float_format="{:,.2f}".format)
        outfile.write("\n")


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
        conn=db, cursor=c,
        table="results_system_period_energy_target",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )
    
    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "period_energy_target.csv"), "r") as \
            energy_target_file:
        reader = csv.reader(energy_target_file)

        next(reader)  # skip header
        for row in reader:
            energy_target_zone = row[0]
            period = row[1]
            discount_factor = row[2]
            number_years = row[3]
            energy_target = row[4]
            energy_target_provision = row[5]
            curtailment = row[6]
            total = row[7]
            fraction_met = row[8]
            fraction_curtailed = row[9]
            shortage = row[10]

            results.append(
                (scenario_id, energy_target_zone, period, subproblem, stage,
                 discount_factor, number_years, energy_target,
                 energy_target_provision, curtailment, total,
                 fraction_met, fraction_curtailed, shortage)
            )
            
    insert_temp_sql = """
        INSERT INTO temp_results_system_period_energy_target{}
         (scenario_id, energy_target_zone, period, subproblem_id, stage_id,
         discount_factor, number_years_represented, energy_target_mwh, 
         delivered_energy_target_energy_mwh, curtailed_energy_target_energy_mwh,
         total_energy_target_energy_mwh,
         fraction_of_energy_target_met, fraction_of_energy_target_energy_curtailed,
         energy_target_shortage_mwh)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_system_period_energy_target
        (scenario_id, energy_target_zone, period, subproblem_id, stage_id,
        discount_factor, number_years_represented, energy_target_mwh, 
        delivered_energy_target_energy_mwh, curtailed_energy_target_energy_mwh,
        total_energy_target_energy_mwh,
        fraction_of_energy_target_met, fraction_of_energy_target_energy_curtailed, 
        energy_target_shortage_mwh)
        SELECT scenario_id, energy_target_zone, period, subproblem_id, stage_id,
        discount_factor, number_years_represented, energy_target_mwh, 
        delivered_energy_target_energy_mwh, curtailed_energy_target_energy_mwh,
        total_energy_target_energy_mwh,
        fraction_of_energy_target_met, fraction_of_energy_target_energy_curtailed,
        energy_target_shortage_mwh
        FROM temp_results_system_period_energy_target{}
        ORDER BY scenario_id, energy_target_zone, period, subproblem_id, stage_id;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)

    # Update duals
    duals_results = []
    with open(os.path.join(results_directory, "Period_Energy_Target_Constraint.csv"),
              "r") as energy_target_duals_file:
        reader = csv.reader(energy_target_duals_file)

        next(reader)  # skip header

        for row in reader:
            duals_results.append(
                (row[2], row[0], row[1], scenario_id, subproblem, stage)
            )

    duals_sql = """
        UPDATE results_system_period_energy_target
        SET dual = ?
        WHERE energy_target_zone = ?
        AND period = ?
        AND scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=duals_sql, data=duals_results)

    # Calculate marginal energy-target cost per MWh
    mc_sql = """
        UPDATE results_system_period_energy_target
        SET energy_target_marginal_cost_per_mwh = 
        dual / (discount_factor * number_years_represented)
        WHERE scenario_id = ?
        AND subproblem_id = ?
        and stage_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=mc_sql,
                          data=(scenario_id, subproblem, stage),
                          many=False)



