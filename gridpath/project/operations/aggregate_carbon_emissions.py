#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Aggregate carbon emissions from the project-timepoint level to
the carbon cap zone - period level.
"""

import csv
import os.path
from pyomo.environ import Param, Set, Expression, value

from gridpath.auxiliary.dynamic_components import \
    required_operational_modules, carbon_cap_balance_emission_components
from gridpath.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # First figure out which projects we need to track for the carbon cap
    m.CARBONACEOUS_PROJECTS = Set(within=m.PROJECTS)
    m.carbon_cap_zone = Param(m.CARBONACEOUS_PROJECTS,
                              within=m.CARBON_CAP_ZONES)

    m.CARBONACEOUS_PROJECTS_BY_CARBON_CAP_ZONE = \
        Set(m.CARBON_CAP_ZONES, within=m.CARBONACEOUS_PROJECTS,
            initialize=lambda mod, co2_z:
            [p for p in mod.CARBONACEOUS_PROJECTS
             if mod.carbon_cap_zone[p] == co2_z])

    # Get operational carbon cap projects - timepoints combinations
    m.CARBONACEOUS_PROJECT_OPERATIONAL_TIMEPOINTS = Set(
        within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod: [(p, tmp) for (p, tmp) in
                          mod.PROJECT_OPERATIONAL_TIMEPOINTS
                          if p in mod.CARBONACEOUS_PROJECTS]
    )
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # Get emissions for each carbon cap project
    def carbon_emissions_rule(mod, g, tmp):
        """
        Emissions from each project based on operational type 
        (and whether a project burns fuel)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            fuel_burn_rule(mod, g, tmp, "Project {} has no fuel, so should "
                                        "not be labeled carbonaceous: "
                                        "replace its carbon_cap_zone with "
                                        "'.' in projects.tab.".format(g)) \
            * mod.co2_intensity_tons_per_mmbtu[mod.fuel[g]]

    m.Carbon_Emissions_Tons = Expression(
        m.CARBONACEOUS_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=carbon_emissions_rule
    )
    
    def total_carbon_emissions_rule(mod, z, p):
        """
        Calculate total emissions from all carbonaceous generators in carbon 
        cap zone
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(mod.Carbon_Emissions_Tons[g, tmp]
                   * mod.number_of_hours_in_timepoint[tmp]
                   * mod.horizon_weight[mod.horizon[tmp]]
                   for (g, tmp) in
                   mod.CARBONACEOUS_PROJECT_OPERATIONAL_TIMEPOINTS
                   if g in mod.CARBONACEOUS_PROJECTS_BY_CARBON_CAP_ZONE[z]
                   and tmp in mod.TIMEPOINTS_IN_PERIOD[p]
                   )

    m.Total_Carbon_Emissions_Tons = Expression(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
        rule=total_carbon_emissions_rule
    )

    # Add to emission imports to carbon balance
    getattr(d, carbon_cap_balance_emission_components).append(
        "Total_Carbon_Emissions_Tons"
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
                                           "inputs", "projects.tab"),
                     select=("project", "carbon_cap_zone"),
                     param=(m.carbon_cap_zone,)
                     )

    data_portal.data()['CARBONACEOUS_PROJECTS'] = {
        None: data_portal.data()['carbon_cap_zone'].keys()
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
                           "carbon_emissions_by_project.csv"), "wb") as \
            carbon_emissions_results_file:
        writer = csv.writer(carbon_emissions_results_file)
        writer.writerow(["project", "timepoint", "period",
                         "horizon", "horizon_weight",
                         "carbon_emissions_tons"])
        for (p, tmp) in m.CARBONACEOUS_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                tmp,
                m.period[tmp],
                m.horizon[tmp],
                m.horizon_weight[m.horizon[tmp]],
                value(m.Carbon_Emissions_Tons[p, tmp])
            ])
