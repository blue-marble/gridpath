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
Aggregate delivered transmission-target-eligible transmission flow from the tx_line-timepoint level to
the transmission-target zone - period level.
"""

from pyomo.environ import Expression, value

from gridpath.common_functions import create_results_df
from gridpath.system.policy.transmission_targets import TX_TARGETS_DF


def add_model_components(m, d, scenario_directory, hydro_year, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    def transmission_target_pos_dir_contribution_rule(mod, z, p):
        """
        Calculate the delivered energy in the positive direction for each transmission-target zone and period
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(
            (
                mod.Transmission_Target_Energy_MW_Pos_Dir[tx, tmp]
                if float(mod.contributes_net_flow_to_tx_target[tx]) == 0
                else mod.Transmission_Target_Net_Energy_MW_Pos_Dir[tx, tmp]
            )
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            for (tx, tmp) in mod.TRANSMISSION_TARGET_TX_OPR_TMPS
            if tx in mod.TRANSMISSION_TARGET_TX_LINES_BY_TRANSMISSION_TARGET_ZONE[z]
            and tmp in mod.TMPS_IN_PRD[p]
        )

    m.Total_Period_Transmission_Target_Energy_Pos_Dir_MWh = Expression(
        m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET,
        rule=transmission_target_pos_dir_contribution_rule,
    )

    def transmission_target_neg_dir_contribution_rule(mod, z, p):
        """
        Calculate the delivered energy in the negative direction for each transmission-target zone and period
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(
            (
                mod.Transmission_Target_Energy_MW_Neg_Dir[tx, tmp]
                if float(mod.contributes_net_flow_to_tx_target[tx]) == 0
                else mod.Transmission_Target_Net_Energy_MW_Neg_Dir[tx, tmp]
            )
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            for (tx, tmp) in mod.TRANSMISSION_TARGET_TX_OPR_TMPS
            if tx in mod.TRANSMISSION_TARGET_TX_LINES_BY_TRANSMISSION_TARGET_ZONE[z]
            and tmp in mod.TMPS_IN_PRD[p]
        )

    m.Total_Period_Transmission_Target_Energy_Neg_Dir_MWh = Expression(
        m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET,
        rule=transmission_target_neg_dir_contribution_rule,
    )


def export_results(scenario_directory, hydro_year, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    results_columns = [
        "total_transmission_target_energy_positive_direction_mwh",
        "total_transmission_target_energy_negative_direction_mwh",
    ]
    data = [
        [
            z,
            p,
            value(m.Total_Period_Transmission_Target_Energy_Pos_Dir_MWh[z, p]),
            value(m.Total_Period_Transmission_Target_Energy_Neg_Dir_MWh[z, p]),
        ]
        for (z, p) in m.TRANSMISSION_TARGET_ZONE_PERIODS_WITH_TRANSMISSION_TARGET
    ]
    results_df = create_results_df(
        index_columns=["transmission_target_zone", "period"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, TX_TARGETS_DF)[c] = None
    getattr(d, TX_TARGETS_DF).update(results_df)
