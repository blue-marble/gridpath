#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Keep track of fuel burn
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

    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # Get emissions for each carbon cap project
    def fuel_burn_rule(mod, g, tmp):
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
                                        "'.' in projects.tab.".format(g))

    m.Fuel_Burn_MMBtu = Expression(
        m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=fuel_burn_rule
    )


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export fuel burn results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
              "fuel_burn.csv"), "wb") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "horizon", "timepoint", "horizon_weight",
             "number_of_hours_in_timepoint", "fuel", "fuel_burn_mmbtu"]
        )
        for (p, tmp) in m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp],
                tmp,
                m.horizon_weight[m.horizon[tmp]],
                m.number_of_hours_in_timepoint[tmp],
                m.fuel[p],
                value(m.Fuel_Burn_MMBtu[p, tmp])
            ])
