#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate delivered RPS-eligible power from the project-timepoint level to
the RPS zone - period level.
"""

from pyomo.environ import Param, Set, Expression, value


def add_model_components(m, d):
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
                 + mod.Subhourly_RPS_Energy_Delivered_MW[g,tmp])
                * mod.hrs_in_tmp[tmp]
                * mod.tmp_weight[tmp]
                for (g, tmp) in mod.RPS_PRJ_OPR_TMPS
                if g in mod.RPS_PROJECTS_BY_RPS_ZONE[z]
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
                    mod.Subhourly_RPS_Energy_Delivered_MW[g, tmp])
                   * mod.hrs_in_tmp[tmp]
                   * mod.tmp_weight[tmp]
                   for (g, tmp) in mod.RPS_PRJ_OPR_TMPS
                   if g in mod.RPS_PROJECTS_BY_RPS_ZONE[z]
                   and tmp in mod.TMPS_IN_PRD[p]
                   )
    # TODO: is this only needed for export and, if so, should it be created on
    # export?
    m.Total_Curtailed_RPS_Energy_MWh = \
        Expression(m.RPS_ZONE_PERIODS_WITH_RPS,
                   rule=total_curtailed_rps_energy_rule)

