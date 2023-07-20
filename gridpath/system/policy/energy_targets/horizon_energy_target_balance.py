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
Simplest implementation with a MWh target by horizon.
"""


import csv
import os.path
import pandas as pd

from pyomo.environ import Var, Constraint, NonNegativeReals, Expression, value

from gridpath.common_functions import create_results_df
from gridpath.system.policy.energy_targets import ENERGY_TARGET_ZONE_HRZ_DF


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.Horizon_Energy_Target_Shortage_MWh = Var(
        m.ENERGY_TARGET_ZONE_BLN_TYPE_HRZS_WITH_ENERGY_TARGET, within=NonNegativeReals
    )

    def violation_expression_rule(mod, z, bt, h):
        return (
            mod.Horizon_Energy_Target_Shortage_MWh[z, bt, h]
            * mod.energy_target_allow_violation[z]
        )

    m.Horizon_Energy_Target_Shortage_MWh_Expression = Expression(
        m.ENERGY_TARGET_ZONE_BLN_TYPE_HRZS_WITH_ENERGY_TARGET,
        rule=violation_expression_rule,
    )

    def energy_target_rule(mod, z, bt, h):
        """
        Total delivered energy-target-eligible energy must exceed target
        :param mod:
        :param z:
        :param bt:
        :param h:
        :return:
        """
        return (
            mod.Total_Delivered_Horizon_Energy_Target_Energy_MWh[z, bt, h]
            + mod.Horizon_Energy_Target_Shortage_MWh_Expression[z, bt, h]
            >= mod.Horizon_Energy_Target[z, bt, h]
        )

    m.Horizon_Energy_Target_Constraint = Constraint(
        m.ENERGY_TARGET_ZONE_BLN_TYPE_HRZS_WITH_ENERGY_TARGET, rule=energy_target_rule
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
            bt,
            h,
            value(m.Horizon_Energy_Target[z, bt, h]),
            value(m.Total_Delivered_Horizon_Energy_Target_Energy_MWh[z, bt, h])
            + value(m.Total_Curtailed_Horizon_Energy_Target_Energy_MWh[z, bt, h]),
            1
            if float(m.horizon_energy_target_mwh[z, bt, h]) == 0
            else value(m.Total_Delivered_Horizon_Energy_Target_Energy_MWh[z, bt, h])
            / float(m.horizon_energy_target_mwh[z, bt, h]),
            0
            if (
                value(m.Total_Delivered_Horizon_Energy_Target_Energy_MWh[z, bt, h])
                + value(m.Total_Curtailed_Horizon_Energy_Target_Energy_MWh[z, bt, h])
            )
            == 0
            else value(m.Total_Curtailed_Horizon_Energy_Target_Energy_MWh[z, bt, h])
            / (
                value(m.Total_Delivered_Horizon_Energy_Target_Energy_MWh[z, bt, h])
                + value(m.Total_Curtailed_Horizon_Energy_Target_Energy_MWh[z, bt, h])
            ),
            value(m.Horizon_Energy_Target_Shortage_MWh_Expression[z, bt, h]),
            m.dual[getattr(m, "Horizon_Energy_Target_Constraint")[z, bt, h]]
            if (z, bt, h)
            in [idx for idx in getattr(m, "Horizon_Energy_Target_Constraint")]
            else None,
            (
                m.dual[getattr(m, "Horizon_Energy_Target_Constraint")[z, bt, h]]
                / m.hrz_objective_coefficient[bt, h]
                if (z, bt, h)
                in [idx for idx in getattr(m, "Horizon_Energy_Target_Constraint")]
                else None
            ),
        ]
        for (z, bt, h) in m.ENERGY_TARGET_ZONE_BLN_TYPE_HRZS_WITH_ENERGY_TARGET
    ]
    results_df = create_results_df(
        index_columns=["energy_target_zone", "balancing_type", "horizon"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, ENERGY_TARGET_ZONE_HRZ_DF)[c] = None
    getattr(d, ENERGY_TARGET_ZONE_HRZ_DF).update(results_df)


def save_duals(scenario_directory, subproblem, stage, instance, dynamic_components):
    instance.constraint_indices["Horizon_Energy_Target_Constraint"] = [
        "energy_target_zone",
        "balancing_type",
        "horizon",
        "dual",
    ]


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
        outfile.write("\n### HORIZON ENERGY TARGET RESULTS ###\n")

    # All these files are small, so won't be setting indices

    # Get the main energy-target results file
    results_df = pd.read_csv(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "system_horizon_energy_target.csv",
        )
    )

    results_df.set_index(
        ["energy_target_zone", "balancing_type", "horizon"],
        inplace=True,
        verify_integrity=True,
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
        results_df.percent_curtailed[indx] = pct

    # Drop unnecessary columns before exporting
    results_df.drop("total_energy_target_energy_mwh", axis=1, inplace=True)
    results_df.drop("fraction_of_energy_target_met", axis=1, inplace=True)
    results_df.drop("fraction_of_energy_target_energy_curtailed", axis=1, inplace=True)
    results_df.drop("energy_target_shortage_mwh", axis=1, inplace=True)

    # Rearrange the columns
    cols = results_df.columns.tolist()
    results_df = results_df[cols]
    results_df.sort_index(inplace=True)
    with open(summary_results_file, "a") as outfile:
        results_df.to_string(outfile, float_format="{:,.2f}".format)
        outfile.write("\n")
