# Copyright 2016-2020 Blue Marble Analytics LLC.
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
Aggregate delivered RPS-eligible power from the project-timepoint level to
the RPS zone - period level.
"""

from pyomo.environ import Param, Set, Expression, value


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """
    def rps_energy_provision_rule(mod, z, p):
        """
        Calculate the delivered RPS energy for each zone and period
        Scheduled power provision (available energy minus reserves minus
        scheduled curtailment) + subhourly delivered energy (from
        providing upward reserves) - subhourly curtailment (from providing
        downward reserves)
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return \
            sum((mod.Scheduled_RPS_Energy_MW[g, tmp]
                 - mod.Subhourly_Curtailment_MW[g, tmp]
                 + mod.Subhourly_RPS_Energy_MW[g,tmp])
                * mod.hrs_in_tmp[tmp]
                * mod.tmp_weight[tmp]
                for (g, tmp) in mod.RPS_PRJ_OPR_TMPS
                if g in mod.RPS_PRJS_BY_RPS_ZONE[z]
                and tmp in mod.TMPS_IN_PRD[p]
                )

    m.Total_Delivered_RPS_Energy_MWh = \
        Expression(m.RPS_ZONE_PERIODS_WITH_RPS,
                   rule=rps_energy_provision_rule)

    def total_curtailed_rps_energy_rule(mod, z, p):
        """
        Calculate how much RPS-eligible energy was curtailed in each RPS zone
        in each period
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum((mod.Scheduled_Curtailment_MW[g, tmp] +
                    mod.Subhourly_Curtailment_MW[g, tmp] -
                    mod.Subhourly_RPS_Energy_MW[g, tmp])
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   for (g, tmp) in mod.RPS_PRJ_OPR_TMPS
                   if g in mod.RPS_PRJS_BY_RPS_ZONE[z]
                   and tmp in mod.TMPS_IN_PRD[p]
                   )
    # TODO: is this only needed for export and, if so, should it be created on
    # export?
    m.Total_Curtailed_RPS_Energy_MWh = \
        Expression(m.RPS_ZONE_PERIODS_WITH_RPS,
                   rule=total_curtailed_rps_energy_rule)

