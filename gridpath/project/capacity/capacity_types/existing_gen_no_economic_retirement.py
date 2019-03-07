#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
gridpath.project.capacity.capacity_types.existing_gen_no_economic_retirement
----------------------------------------------------------------------------
The **existing_gen_no_economic_retirement** module describes the capacity of
generators that are available to the optimization without having to incur an
investment cost. For example, this module can be applied to existing
generators or to generators that we know will be built in the future and
whose capital costs we want to ignore.

It is not required to specify a capacity for all periods, i.e. a project can
be operational in some periods but not in others with no restriction on the
order and combination of periods.
"""


from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, NonNegativeReals

from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets


# TODO: rename 'existing' to 'specified' to better reflect functionality (
#  i.e. this module can be used to specify capacity that comes online in the
#  future but is 'given' to the optimization without having to incur
#  investment costs)
def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    This function adds to the model a two-dimensional set of project-period
    combinations to describe the project capacity will be available to the
    optimization in a given period: the
    *EXISTING_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS* set. This set
    is then added to the list of sets to join to get the final
    *PROJECT_OPERATIONAL_PERIODS* set defined in
    **gridpath.project.capacity.capacity**. We will also use *EG_P* to
    designate this set (index :math:`eg, ep` where :math:`eg\in R` and
    :math:`ep\in P`).

    We then add two parameters associated with this capacity_type,
    the project capacity and its fixed cost for each operational period:
    :math:`existing\_gen\_no\_econ\_ret\_capacity\_mw_{eg,ep}` and
    :math:`existing\_no\_econ\_ret\_fixed\_cost\_per\_mw\_yr_{eg,ep}`. The
    latter can be added to the objective function for cost-tracking
    purposes but will not affect any optimization decisions.
    """
    m.EXISTING_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS = \
        Set(dimen=2, within=m.PROJECTS*m.PERIODS)

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
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the capacity of project *g* in period *p*

    The capacity of projects of the *existing_gen_no_econoimc_retirement*
    capacity type is a pre-specified number for each of the project's
    operational periods.
    """
    return mod.existing_gen_no_econ_ret_capacity_mw[g, p]


def capacity_cost_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the total annualized fixed cost of
        *existing_gen_no_economic_retirement* project *g* in period *p*

    The capacity cost of projects of the *existing_gen_no_econoimc_retirement*
    capacity type is a pre-specified number equal to the capacity times the
    per-mw fixed cost for each of the project's operational periods.
    """
    existing_gen_no_econ_ret_total_fixed_cost = \
        mod.existing_gen_no_econ_ret_capacity_mw[g, p] \
        * mod.existing_no_econ_ret_fixed_cost_per_mw_yr[g, p]

    return existing_gen_no_econ_ret_total_fixed_cost


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

        for row in zip(dynamic_components["project"],
                       dynamic_components["period"],
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
            existing_no_econ_ret_capacity_mw_dict, \
            existing_no_econ_ret_fixed_cost_per_mw_yr_dict

    data_portal.data()[
        "EXISTING_NO_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS"
    ] = {
        None: determine_period_params()[0]
    }

    data_portal.data()["existing_gen_no_econ_ret_capacity_mw"] = \
        determine_period_params()[1]

    data_portal.data()["existing_no_econ_ret_fixed_cost_per_mw_yr"] = \
        determine_period_params()[2]


def get_module_specific_inputs_from_database(
        subscenarios, c, inputs_directory
):
    """
    existing_generation_period_params.tab
    :param subscenarios: 
    :param c: 
    :param inputs_directory: 
    :return: 
    """

    # Select generators of 'existing_gen_no_economic_retirement' capacity
    # type only
    ep_capacities = c.execute(
        """SELECT project, period, existing_capacity_mw,
        annual_fixed_cost_per_mw_year
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE timepoint_scenario_id = {}) as relevant_periods
        INNER JOIN
        (SELECT project, period, existing_capacity_mw
        FROM inputs_project_existing_capacity
        WHERE project_existing_capacity_scenario_id = {}
        AND existing_capacity_mw > 0) as capacity
        USING (project, period)
        LEFT OUTER JOIN
        (SELECT project, period, 
        annual_fixed_cost_per_kw_year * 1000 AS annual_fixed_cost_per_mw_year
        FROM inputs_project_existing_fixed_cost
        WHERE project_existing_fixed_cost_scenario_id = {}) as fixed_om
        USING (project, period)
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 'existing_gen_no_economic_retirement';""".format(
            subscenarios.TIMEPOINT_SCENARIO_ID,
            subscenarios.PROJECT_EXISTING_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_EXISTING_FIXED_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    # If existing_generation_period_params.tab file already exists, append
    # rows to it
    if os.path.isfile(os.path.join(inputs_directory,
                                   "existing_generation_period_params.tab")
                      ):
        with open(os.path.join(inputs_directory,
                               "existing_generation_period_params.tab"), "a") \
                as existing_project_capacity_tab_file:
            writer = csv.writer(existing_project_capacity_tab_file,
                                delimiter="\t")
            for row in ep_capacities:
                writer.writerow(row)
    # If existing_generation_period_params.tab file does not exist,
    # write header first, then add input data
    else:
        with open(os.path.join(inputs_directory,
                               "existing_generation_period_params.tab"), "w") \
                as existing_project_capacity_tab_file:
            writer = csv.writer(existing_project_capacity_tab_file,
                                delimiter="\t")

            # Write header
            writer.writerow(
                ["project", "period", "existing_capacity_mw",
                 "fixed_cost_per_mw_yr"]
            )

            # Write input data
            for row in ep_capacities:
                writer.writerow(row)
