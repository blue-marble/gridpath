#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate delivered RPS-eligible power from the project-timepoint level to
the RPS zone - period level.
"""
import csv
import os.path
from pyomo.environ import Param, Set, Expression, value

from gridpath.auxiliary.dynamic_components import required_operational_modules
from gridpath.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # First figure out which projects are RPS-eligible
    m.RPS_PROJECTS = Set(within=m.PROJECTS)
    m.rps_zone = Param(m.RPS_PROJECTS, within=m.RPS_ZONES)

    def determine_rps_generators_by_rps_zone(mod, rps_z):
        return [p for p in mod.RPS_PROJECTS if mod.rps_zone[p] == rps_z]

    m.RPS_PROJECTS_BY_RPS_ZONE = \
        Set(m.RPS_ZONES, within=m.RPS_PROJECTS,
            initialize=determine_rps_generators_by_rps_zone)

    # Get operational RPS projects - timepoints combinations
    m.RPS_PROJECT_OPERATIONAL_TIMEPOINTS = Set(
        within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod: [(p, tmp) for (p, tmp) in
                          mod.PROJECT_OPERATIONAL_TIMEPOINTS
                          if p in mod.RPS_PROJECTS]
    )
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    def scheduled_recs_rule(mod, g, tmp):
        """
        This how many RECs are scheduled to be delivered at the timepoint
        (hourly) schedule
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            rec_provision_rule(mod, g, tmp)

    m.Scheduled_RPS_Energy_MW = Expression(
        m.RPS_PROJECT_OPERATIONAL_TIMEPOINTS, 
        rule=scheduled_recs_rule
    )

    # Keep track of curtailment
    def scheduled_curtailment_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the scheduled
        curtailment component
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            scheduled_curtailment_rule(mod, g, tmp)

    m.Scheduled_Curtailment_MW = Expression(
        m.RPS_PROJECT_OPERATIONAL_TIMEPOINTS, rule=scheduled_curtailment_rule
    )

    def subhourly_curtailment_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the subhourly
        curtailment component
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            subhourly_curtailment_rule(mod, g, tmp)

    m.Subhourly_Curtailment_MW = Expression(
        m.RPS_PROJECT_OPERATIONAL_TIMEPOINTS, rule=subhourly_curtailment_rule
    )

    def subhourly_recs_delivered_rule(mod, g, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the subhourly
        curtailment component
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            subhourly_energy_delivered_rule(mod, g, tmp)

    m.Subhourly_RPS_Energy_Delivered_MW = Expression(
        m.RPS_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=subhourly_recs_delivered_rule
    )

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
                * mod.number_of_hours_in_timepoint[tmp]
                * mod.horizon_weight[mod.horizon[tmp]]
                for (g, tmp) in mod.RPS_PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.RPS_PROJECTS_BY_RPS_ZONE[z]
                and tmp in mod.TIMEPOINTS_IN_PERIOD[p]
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
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   for (g, tmp) in mod.RPS_PROJECT_OPERATIONAL_TIMEPOINTS
                   if g in mod.RPS_PROJECTS_BY_RPS_ZONE[z]
                   and tmp in mod.TIMEPOINTS_IN_PERIOD[p]
                   )
    # TODO: is this only needed for export and, if so, should it be created on
    # export?
    m.Total_Curtailed_RPS_Energy_MWh = \
        Expression(m.RPS_ZONE_PERIODS_WITH_RPS,
                   rule=total_curtailed_rps_energy_rule)


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
                                           "inputs", "projects.tab"),
                     select=("project", "rps_zone"),
                     param=(m.rps_zone,)
                     )

    data_portal.data()['RPS_PROJECTS'] = {
        None: data_portal.data()['rps_zone'].keys()
    }


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "rps_by_project.csv"), "wb") as rps_results_file:
        writer = csv.writer(rps_results_file)
        writer.writerow(["project", "timepoint", "period",
                         "horizon", "horizon_weight",
                         "scheduled_rps_energy_mw",
                         "scheduled_curtailment_mw",
                         "subhourly_rps_energy_delivered_mw",
                         "subhourly_curtailment_mw"])
        for (p, tmp) in m.RPS_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                tmp,
                m.period[tmp],
                m.horizon[tmp],
                m.horizon_weight[m.horizon[tmp]],
                value(m.Scheduled_RPS_Energy_MW[p, tmp]),
                value(m.Scheduled_Curtailment_MW[p, tmp]),
                value(m.Subhourly_RPS_Energy_Delivered_MW[p, tmp]),
                value(m.Subhourly_Curtailment_MW[p, tmp])
            ])
