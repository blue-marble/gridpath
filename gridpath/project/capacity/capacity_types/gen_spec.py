#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This capacity type describes generator projects that are available to the
optimization without having to incur an investment cost, e.g. existing
projects or projects that will be built in the future and whose capital
costs we want to ignore (in the objective function). A specified generator can
be available at a specified capacity in all periods, or in some periods only,
with no restriction on the order and combination of periods or the variation
in capacity by period.

The user may specify a fixed O&M cost for these generators, but this cost will
be a fixed number in the objective function and will therefore not affect any
of the optimization decisions.
"""


from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, NonNegativeReals

from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets


def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_SPEC_OPR_PRDS`                                             |
    |                                                                         |
    | Two-dimensional set of project-period combinations that describes the   |
    | project capacity available in a given period. This set is added to the  |
    | list of sets to join to get the final :code:`PRJ_OPR_PRDS` set defined  |
    | in **gridpath.project.capacity.capacity**.                              |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_spec_capacity_mw`                                          |
    | | *Defined over*: :code:`GEN_SPEC_OPR_PRDS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's specified capacity (in MW) in each operational period.    |
    +-------------------------------------------------------------------------+
    | | :code:`gen_spec_fixed_cost_per_mw_yr`                                 |
    | | *Defined over*: :code:`GEN_SPEC_OPR_PRDS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's fixed cost (in $ per MW-yr.) in each operational period.  |
    | This cost will be added to the objective function but will not affect   |
    | optimization decisions.                                                 |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.GEN_SPEC_OPR_PRDS = Set(
        dimen=2, within=m.PROJECTS*m.PERIODS
    )

    # Required Params
    ###########################################################################

    m.gen_spec_capacity_mw = Param(
        m.GEN_SPEC_OPR_PRDS,
        within=NonNegativeReals
    )

    m.gen_spec_fixed_cost_per_mw_yr = Param(
        m.GEN_SPEC_OPR_PRDS,
        within=NonNegativeReals
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "GEN_SPEC_OPR_PRDS",
    )


# Capacity Type Methods
###############################################################################

def capacity_rule(mod, g, p):
    """
    The capacity of projects of the *gen_spec* capacity type is a
    pre-specified number for each of the project's operational periods.
    """
    return mod.gen_spec_capacity_mw[g, p]


def capacity_cost_rule(mod, g, p):
    """
    The capacity cost of projects of the *gen_spec* capacity type is a
    pre-specified number equal to the capacity times the per-mw fixed cost
    for each of the project's operational periods.
    """
    return mod.gen_spec_capacity_mw[g, p] \
        * mod.gen_spec_fixed_cost_per_mw_yr[g, p]


# Input-Output
###############################################################################

def load_module_specific_data(
        m, data_portal, scenario_directory, subproblem, stage
):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    def determine_gen_spec_projects():
        """
        Find the gen_spec capacity type projects
        :return:
        """

        gen_spec_projects = list()

        df = pd.read_csv(
            os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                         "projects.tab"),
            sep="\t",
            usecols=["project", "capacity_type"]
        )

        for row in zip(df["project"],
                       df["capacity_type"]):
            if row[1] == "gen_spec":
                gen_spec_projects.append(row[0])
            else:
                pass

        return gen_spec_projects

    def determine_period_params():
        generators_list = determine_gen_spec_projects()
        generator_period_list = list()
        gen_spec_capacity_mw_dict = dict()
        gen_spec_fixed_cost_per_mw_yr_dict = dict()
        df = pd.read_csv(
            os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                         "specified_generation_period_params.tab"),
            sep="\t"
        )

        for row in zip(df["project"],
                       df["period"],
                       df["specified_capacity_mw"],
                       df["fixed_cost_per_mw_yr"]):
            if row[0] in generators_list:
                generator_period_list.append((row[0], row[1]))
                gen_spec_capacity_mw_dict[(row[0], row[1])] = \
                    float(row[2])
                gen_spec_fixed_cost_per_mw_yr_dict[(row[0], row[1])] = \
                    float(row[3])
            else:
                pass

        return generator_period_list, \
            gen_spec_capacity_mw_dict, \
            gen_spec_fixed_cost_per_mw_yr_dict

    data_portal.data()["GEN_SPEC_OPR_PRDS"] = \
        {None: determine_period_params()[0]}

    data_portal.data()["gen_spec_capacity_mw"] = \
        determine_period_params()[1]

    data_portal.data()["gen_spec_fixed_cost_per_mw_yr"] = \
        determine_period_params()[2]


# Database
###############################################################################

def get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    # Select generators of 'gen_spec' capacity type only
    ep_capacities = c.execute(
        """SELECT project, period, specified_capacity_mw,
        annual_fixed_cost_per_mw_year
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        INNER JOIN
        (SELECT project, period, specified_capacity_mw
        FROM inputs_project_specified_capacity
        WHERE project_specified_capacity_scenario_id = {}) as capacity
        USING (project, period)
        LEFT OUTER JOIN
        (SELECT project, period, 
        annual_fixed_cost_per_mw_year
        FROM inputs_project_specified_fixed_cost
        WHERE project_specified_fixed_cost_scenario_id = {}) as fixed_om
        USING (project, period)
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 'gen_spec';""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_SPECIFIED_FIXED_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )
    return ep_capacities


def write_module_specific_model_inputs(
        scenario_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    specified_generation_period_params.tab file
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    ep_capacities = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # If specified_generation_period_params.tab file already exists, append
    # rows to it
    if os.path.isfile(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                                   "specified_generation_period_params.tab")
                      ):
        with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                               "specified_generation_period_params.tab"),
                  "a") as existing_project_capacity_tab_file:
            writer = csv.writer(existing_project_capacity_tab_file,
                                delimiter="\t", lineterminator="\n")
            for row in ep_capacities:
                writer.writerow(row)
    # If specified_generation_period_params.tab file does not exist,
    # write header first, then add input data
    else:
        with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                               "specified_generation_period_params.tab"),
                  "w", newline="") as existing_project_capacity_tab_file:
            writer = csv.writer(existing_project_capacity_tab_file,
                                delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                ["project", "period", "specified_capacity_mw",
                 "fixed_cost_per_mw_yr"]
            )

            # Write input data
            for row in ep_capacities:
                writer.writerow(row)


# Validation
###############################################################################

def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass
    # Validation to be added
    # ep_capacities = get_module_specific_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

    # do validation
    # make sure existing capacity is a postive number
    # make sure annual fixed costs are positive
