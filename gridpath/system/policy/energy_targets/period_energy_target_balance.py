# Copyright 2016-2023 Blue Marble Analytics LLC.
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

from gridpath.common_functions import (
    create_results_df,
    duals_wrapper,
    none_dual_type_error_wrapper,
)
from gridpath.system.policy.energy_targets import ENERGY_TARGET_ZONE_PRD_DF


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param m:
    :param d:
    :return:
    """

    m.Period_Energy_Target_Shortage_MWh = Var(
        m.ENERGY_TARGET_ZONE_PERIODS_WITH_ENERGY_TARGET, within=NonNegativeReals
    )

    def violation_expression_rule(mod, z, p):
        if mod.energy_target_allow_violation[z]:
            return mod.Period_Energy_Target_Shortage_MWh[z, p]
        else:
            return 0

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
        return (
            mod.Total_Delivered_Period_Energy_Target_Energy_MWh[z, p]
            + mod.Period_Energy_Target_Shortage_MWh_Expression[z, p]
            >= mod.Period_Energy_Target[z, p]
        )

    m.Period_Energy_Target_Constraint = Constraint(
        m.ENERGY_TARGET_ZONE_PERIODS_WITH_ENERGY_TARGET, rule=energy_target_rule
    )


def export_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
    d,
):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    results_columns = [
        "energy_target_mwh",
        "total_energy_target_energy_mwh",
        "fraction_of_energy_target_met",
        "fraction_of_energy_target_energy_curtailed",
        "energy_target_shortage_mwh",
        "dual",
        "energy_target_marginal_cost_per_mwh",
    ]
    data = [
        [
            z,
            p,
            value(m.Period_Energy_Target[z, p]),
            value(m.Total_Delivered_Period_Energy_Target_Energy_MWh[z, p])
            + value(m.Total_Curtailed_Period_Energy_Target_Energy_MWh[z, p]),
            (
                1
                if float(m.period_energy_target_mwh[z, p]) == 0
                else value(m.Total_Delivered_Period_Energy_Target_Energy_MWh[z, p])
                / float(m.period_energy_target_mwh[z, p])
            ),
            (
                0
                if (
                    value(m.Total_Delivered_Period_Energy_Target_Energy_MWh[z, p])
                    + value(m.Total_Curtailed_Period_Energy_Target_Energy_MWh[z, p])
                )
                == 0
                else value(m.Total_Curtailed_Period_Energy_Target_Energy_MWh[z, p])
                / (
                    value(m.Total_Delivered_Period_Energy_Target_Energy_MWh[z, p])
                    + value(m.Total_Curtailed_Period_Energy_Target_Energy_MWh[z, p])
                )
            ),
            value(m.Period_Energy_Target_Shortage_MWh_Expression[z, p]),
            (
                duals_wrapper(m, getattr(m, "Period_Energy_Target_Constraint")[z, p])
                if (z, p)
                in [idx for idx in getattr(m, "Period_Energy_Target_Constraint")]
                else None
            ),
            (
                none_dual_type_error_wrapper(
                    duals_wrapper(
                        m, getattr(m, "Period_Energy_Target_Constraint")[z, p]
                    ),
                    m.period_objective_coefficient[p],
                )
                if (z, p)
                in [idx for idx in getattr(m, "Period_Energy_Target_Constraint")]
                else None
            ),
        ]
        for (z, p) in m.ENERGY_TARGET_ZONE_PERIODS_WITH_ENERGY_TARGET
    ]
    results_df = create_results_df(
        index_columns=["energy_target_zone", "period"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, ENERGY_TARGET_ZONE_PRD_DF)[c] = None
    getattr(d, ENERGY_TARGET_ZONE_PRD_DF).update(results_df)


def save_duals(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    instance,
    dynamic_components,
):
    instance.constraint_indices["Period_Energy_Target_Constraint"] = [
        "energy_target_zone",
        "period",
        "dual",
    ]


def summarize_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:

    Summarize energy-target policy results
    """

    summary_results_file = os.path.join(
        scenario_directory,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "results",
        "summary_results.txt",
    )

    # Open in 'append' mode, so that results already written by other
    # modules are not overridden
    with open(summary_results_file, "a") as outfile:
        outfile.write("\n### PERIOD ENERGY TARGET RESULTS ###\n")

    # All these files are small, so won't be setting indices

    # Get the main energy-target results file
    results_df = pd.read_csv(
        os.path.join(
            scenario_directory,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "system_period_energy_target.csv",
        )
    )

    results_df.set_index(
        ["energy_target_zone", "period"], inplace=True, verify_integrity=True
    )

    # Calculate:
    # 1) the percent of energy-target energy that was curtailed
    # 2) the marginal energy-target cost per MWh based on the energy-target constraint duals --
    # to convert back to 'real' dollars, we need to divide by the discount
    # factor and the number of years a period represents
    results_df["percent_curtailed"] = pd.Series(index=results_df.index, dtype="float64")

    pd.options.mode.chained_assignment = None  # default='warn'
    for indx, row in results_df.iterrows():
        if (
            results_df.delivered_energy_target_energy_mwh[indx]
            + results_df.curtailed_energy_target_energy_mwh[indx]
        ) == 0:
            pct = 0
        else:
            pct = (
                results_df.curtailed_energy_target_energy_mwh[indx]
                / (
                    results_df.delivered_energy_target_energy_mwh[indx]
                    + results_df.curtailed_energy_target_energy_mwh[indx]
                )
                * 100
            )
        results_df.loc[indx, "percent_curtailed"] = pct

    # Drop unnecessary columns before exporting
    results_df.drop("discount_factor", axis=1, inplace=True)
    results_df.drop("number_years_represented", axis=1, inplace=True)
    results_df.drop("total_energy_target_energy_mwh", axis=1, inplace=True)
    results_df.drop("fraction_of_energy_target_met", axis=1, inplace=True)
    results_df.drop("fraction_of_energy_target_energy_curtailed", axis=1, inplace=True)
    results_df.drop("energy_target_shortage_mwh", axis=1, inplace=True)

    # Rearrange the columns
    cols = results_df.columns.tolist()
    cols = cols[0:3] + [cols[5]] + [cols[3]] + [cols[4]]
    results_df = results_df[cols]
    results_df.sort_index(inplace=True)
    with open(summary_results_file, "a") as outfile:
        results_df.to_string(outfile, float_format="{:,.2f}".format)
        outfile.write("\n")
