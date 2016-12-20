#!/usr/bin/env python

import os.path
import pandas as pd
from pyomo.environ import Set, Param, NonNegativeReals

from modules.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets


def add_module_specific_components(m, d):
    """

    """
    m.EXISTING_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS = \
        Set(dimen=2)

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "EXISTING_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS",
    )

    m.existing_gen_no_econ_ret_capacity_mw = \
        Param(m.EXISTING_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
              within=NonNegativeReals)
    m.existing_no_econ_ret_fixed_cost_per_mw_yr = \
        Param(m.EXISTING_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
              within=NonNegativeReals)


def capacity_rule(mod, g, p):
    return mod.existing_gen_no_econ_ret_capacity_mw[g, p]

def capacity_cost_rule(mod, g, p):
    """
    Capacity cost for existing capacity generators with no economic retirements
    is 0
    :param mod:
    :return:
    """
    return mod.existing_gen_no_econ_ret_capacity_mw[g, p] \
        * mod.existing_no_econ_ret_fixed_cost_per_mw_yr[g, p]


def load_module_specific_data(
        m, data_portal, scenario_directory, horizon, stage
):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    def determine_existing_gen_no_econ_ret_projects():
        """
        Find the existing_no_economic_retirement capacity type projects
        :return:
        """

        ex_gen_no_econ_ret_projects = list()

        dynamic_components = \
            pd.read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project",
                                   "capacity_type"]
                )
        for row in zip(dynamic_components["project"],
                       dynamic_components["capacity_type"]):
            if row[1] == "existing_gen_no_economic_retirement":
                ex_gen_no_econ_ret_projects.append(row[0])
            else:
                pass

        return ex_gen_no_econ_ret_projects

    def determine_period_params():
        """

        :return:
        """
        generators_list = determine_existing_gen_no_econ_ret_projects()
        generator_period_list = list()
        existing_no_econ_ret_capacity_mw_dict = dict()
        existing_no_econ_ret_fixed_cost_per_mw_yr_dict = dict()
        dynamic_components = \
            pd.read_csv(
                os.path.join(scenario_directory, "inputs",
                             "existing_generation_period_params.tab"),
                sep="\t"
                )

        for row in zip(dynamic_components["GENERATORS"],
                       dynamic_components["PERIODS"],
                       dynamic_components["existing_capacity_mw"],
                       dynamic_components["fixed_cost_per_mw_yr"]):
            if row[0] in generators_list:
                generator_period_list.append((row[0], row[1]))
                existing_no_econ_ret_capacity_mw_dict[(row[0], row[1])] = \
                    float(row[2])
                existing_no_econ_ret_fixed_cost_per_mw_yr_dict[(row[0],
                                                                 row[1])] = \
                    float(row[3])
            else:
                pass

        return generator_period_list, \
               existing_no_econ_ret_capacity_mw_dict, existing_no_econ_ret_fixed_cost_per_mw_yr_dict

    data_portal.data()["EXISTING_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS"] = {
        None: determine_period_params()[0]
    }

    data_portal.data()["existing_gen_no_econ_ret_capacity_mw"] = \
        determine_period_params()[1]

    data_portal.data()["existing_no_econ_ret_fixed_cost_per_mw_yr"] = \
        determine_period_params()[2]

