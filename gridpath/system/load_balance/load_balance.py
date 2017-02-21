#!/usr/bin/env python

import csv
import os.path
from pyomo.environ import Param, Var, Constraint, NonNegativeReals

from gridpath.auxiliary.dynamic_components import \
    load_balance_consumption_components, load_balance_production_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Static load
    m.static_load_mw = Param(m.LOAD_ZONES, m.TIMEPOINTS,
                             within=NonNegativeReals)
    getattr(d, load_balance_consumption_components).append("static_load_mw")

    # Penalty variables
    m.Overgeneration_MW = Var(m.LOAD_ZONES, m.TIMEPOINTS,
                              within=NonNegativeReals)
    m.Unserved_Energy_MW = Var(m.LOAD_ZONES, m.TIMEPOINTS,
                               within=NonNegativeReals)

    getattr(d, load_balance_production_components).append("Unserved_Energy_MW")
    getattr(d, load_balance_consumption_components).append("Overgeneration_MW")

    def meet_load_rule(mod, z, tmp):
        """
        The sum across all energy generation components added by other modules
        for each zone and timepoint must equal the sum across all energy
        consumption components added by other modules for each zone and
        timepoint
        :param mod:
        :param z:
        :param tmp:
        :return:
        """
        return sum(getattr(mod, component)[z, tmp]
                   for component in getattr(d,
                                            load_balance_production_components)
                   ) \
            == \
            sum(getattr(mod, component)[z, tmp]
                for component in getattr(d,
                                         load_balance_consumption_components)
                )

    m.Meet_Load_Constraint = Constraint(m.LOAD_ZONES, m.TIMEPOINTS,
                                        rule=meet_load_rule)


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
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs", "load_mw.tab"),
                     param=m.static_load_mw
                     )


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
                           "load_balance.csv"), "wb") as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["zone", "timepoint",
                         "overgeneration_mw",
                         "unserved_energy_mw"]
                        )
        for z in getattr(m, "LOAD_ZONES"):
            for tmp in getattr(m, "TIMEPOINTS"):
                writer.writerow([
                    z,
                    tmp,
                    m.Overgeneration_MW[z, tmp].value,
                    m.Unserved_Energy_MW[z, tmp].value]
                )


def save_duals(m):
    m.constraint_indices["Meet_Load_Constraint"] = \
        ["zone", "timepoint", "dual"]
