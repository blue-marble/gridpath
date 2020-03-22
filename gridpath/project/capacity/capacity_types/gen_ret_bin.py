#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This capacity type describes generators with the same characteristics as
*gen_ret_lin*. However, retirement decisions are binary, i.e. the generator
is either fully retired or not retired at all.

"""

from __future__ import print_function

from builtins import next
from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, Constraint, NonNegativeReals, \
    Binary, value

from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets
from gridpath.project.capacity.capacity_types.common_methods import \
    update_capacity_results_table


def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_RET_BIN`                                                   |
    |                                                                         |
    | The list of projects of the :code:`gen_ret_bin` capacity type.          |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_RET_BIN_OPR_PRDS`                                          |
    |                                                                         |
    | Two-dimensional set of project-period combinations that helps describe  |
    | the project capacity available in a given period. This set is added to  |
    | the list of sets to join to get the final                               |
    | :code:`PRJ_OPR_PRDS` set defined in                      |
    | **gridpath.project.capacity.capacity**.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`OPR_PRDS_BY_GEN_RET_BIN`                                       |
    |                                                                         |
    | Indexed set that describes the operational periods for each             |
    | :code:`gen_ret_bin` project.                                            |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_ret_bin_capacity_mw`                                       |
    | | *Defined over*: :code:`GEN_RET_BIN_OPR_PRDS`                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's specified capacity (in MW) in each operational period if  |
    | no capacity is retired.                                                 |
    +-------------------------------------------------------------------------+
    | | :code:`gen_ret_bin_fixed_cost_per_mw_yr`                              |
    | | *Defined over*: :code:`GEN_RET_BIN_OPR_PRDS`                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's fixed cost (in $ per MW-yr.) in each operational period.  |
    | This cost can be avoided by retiring the generation project.            |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`GenRetBin_Retire`                                              |
    | | *Defined over*: :code:`GEN_RET_BIN_OPR_PRDS`                          |
    |                                                                         |
    | Binary decision variable that specifies whether the project is to be    |
    | retired in a given operational period or not (1 = retire). When         |
    | retired, no capacity will be available in that period and all following |
    | periods, and any fixed costs will no longer be incurred.                |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`GenRetBin_Retire_Forever_Constraint`                           |
    | | *Defined over*: :code:`GEN_RET_BIN_OPR_PRDS`                          |
    |                                                                         |
    | The binary decision variable has to be less than or equal to the binary |
    | decision variable in the previous period. This will prevent capacity    |
    |from co ming back online after it has been retired.                      |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.GEN_RET_BIN_OPR_PRDS = Set(dimen=2)

    m.GEN_RET_BIN = Set(
        initialize=lambda mod:
            set(g for (g, p) in mod.GEN_RET_BIN_OPR_PRDS)
    )

    m.OPR_PRDS_BY_GEN_RET_BIN = Set(
        m.GEN_RET_BIN,
        initialize=lambda mod, prj:
            set(period for (project, period)
                in mod.GEN_RET_BIN_OPR_PRDS
                if project == prj)
    )

    # Required Params
    ###########################################################################

    m.gen_ret_bin_capacity_mw = Param(
        m.GEN_RET_BIN_OPR_PRDS,
        within=NonNegativeReals
    )

    m.gen_ret_bin_fixed_cost_per_mw_yr = Param(
        m.GEN_RET_BIN_OPR_PRDS,
        within=NonNegativeReals
    )

    # Derived Params
    ###########################################################################

    m.gen_ret_bin_first_period = Param(
        m.GEN_RET_BIN,
        initialize=lambda mod, g:
            min(p for p in mod.OPR_PRDS_BY_GEN_RET_BIN[g])
    )

    # Variables
    ###########################################################################

    m.GenRetBin_Retire = Var(
        m.GEN_RET_BIN_OPR_PRDS,
        within=Binary
    )

    # Constraints
    ###########################################################################

    m.GenRetBin_Retire_Forever_Constraint = Constraint(
        m.GEN_RET_BIN_OPR_PRDS,
        rule=retire_forever_rule
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "GEN_RET_BIN_OPR_PRDS",
    )


# Constraint Formulation Rules
###############################################################################

# TODO: we need to check that the user hasn't specified increasing
#  capacity to begin with
def retire_forever_rule(mod, g, p):
    """
    **Constraint Name**: GenRetBin_Retire_Forever_Constraint
    **Enforced Over**: GEN_RET_BIN_OPR_PRDS

    Once the binary retirement decision is made, the decision will last
    through all following periods, i.e. the binary variable cannot be
    smaller than what it was in the previous period.
    """
    # Skip if we're in the first period
    if p == value(mod.first_period):
        return Constraint.Skip
    # Skip if this is the generator's first period
    if p == mod.gen_ret_bin_first_period[g]:
        return Constraint.Skip
    else:
        return mod.GenRetBin_Retire[g, p] \
            >= mod.GenRetBin_Retire[g, mod.prev_period[p]]


# Capacity Type Methods
###############################################################################

def capacity_rule(mod, g, p):
    """
    The capacity of projects of the *gen_ret_bin* capacity type is a
    pre-specified number for each of the project's operational periods
    multiplied with 1 minus the binary retirement variable.
    """
    return mod.gen_ret_bin_capacity_mw[g, p] \
        * (1 - mod.GenRetBin_Retire[g, p])


def capacity_cost_rule(mod, g, p):
    """
    The capacity cost of projects of the *gen_ret_bin* capacity type is its net
    capacity (pre-specified capacity or zero if retired) times the per-mw
    fixed cost for each of the project's operational periods.
    """
    return mod.gen_ret_bin_fixed_cost_per_mw_yr[g, p] \
        * mod.gen_ret_bin_capacity_mw[g, p] \
        * (1 - mod.GenRetBin_Retire[g, p])


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

    def determine_gen_ret_bin_projects():
        gen_ret_bin_projects = list()

        df = pd.read_csv(
            os.path.join(scenario_directory, subproblem, stage, "inputs",
                         "projects.tab"),
            sep="\t",
            usecols=["project", "capacity_type"]
        )
        for row in zip(df["project"],
                       df["capacity_type"]):
            if row[1] == "gen_ret_bin":
                gen_ret_bin_projects.append(row[0])
            else:
                pass

        return gen_ret_bin_projects

    def determine_period_params():
        generators_list = determine_gen_ret_bin_projects()
        generator_period_list = list()
        gen_ret_bin_capacity_mw_dict = dict()
        gen_ret_bin_fixed_cost_per_mw_yr_dict = dict()
        df = pd.read_csv(
            os.path.join(scenario_directory, subproblem, stage, "inputs",
                         "specified_generation_period_params.tab"),
            sep="\t"
        )

        for row in zip(df["project"],
                       df["period"],
                       df["specified_capacity_mw"],
                       df["fixed_cost_per_mw_yr"]):
            if row[0] in generators_list:
                generator_period_list.append((row[0], row[1]))
                gen_ret_bin_capacity_mw_dict[(row[0], row[1])] = float(row[2])
                gen_ret_bin_fixed_cost_per_mw_yr_dict[(row[0], row[1])] = \
                    float(row[3])
            else:
                pass

        return generator_period_list, \
            gen_ret_bin_capacity_mw_dict, \
            gen_ret_bin_fixed_cost_per_mw_yr_dict

    data_portal.data()["GEN_RET_BIN_OPR_PRDS"] = \
        {None: determine_period_params()[0]}

    data_portal.data()["gen_ret_bin_capacity_mw"] = \
        determine_period_params()[1]

    data_portal.data()["gen_ret_bin_fixed_cost_per_mw_yr"] = \
        determine_period_params()[2]


def export_module_specific_results(
        scenario_directory, subproblem, stage, m, d
):
    """
    Export gen_ret_bin retirement results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "capacity_gen_ret_bin.csv"),
              "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "technology", "load_zone",
                         "retired_mw", "retired_binary"])
        for (prj, p) in m.GEN_RET_BIN_OPR_PRDS:
            writer.writerow([
                prj,
                p,
                m.technology[prj],
                m.load_zone[prj],
                value(m.GenRetBin_Retire[prj, p] *
                      m.gen_ret_bin_capacity_mw[prj, p]),
                value(m.GenRetBin_Retire[prj, p])
            ])


def summarize_module_specific_results(
        scenario_directory, subproblem, stage, summary_results_file
):
    """
    Summarize gen_ret_bin capacity results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param summary_results_file:
    :return:
    """

    # Get the results CSV as dataframe
    capacity_results_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "results",
                     "capacity_gen_ret_bin.csv")
    )

    capacity_results_agg_df = capacity_results_df.groupby(
        by=["load_zone", "technology", 'period'],
        as_index=True
    ).sum()

    # Set the formatting of float to be readable
    pd.options.display.float_format = "{:,.0f}".format

    # Get all technologies with the new build capacity
    bin_retirement_df = pd.DataFrame(
        capacity_results_agg_df[
            capacity_results_agg_df["retired_mw"] > 0
            ]["retired_mw"]
    )

    bin_retirement_df.columns = ["Retired Capacity (MW)"]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> Retired Capacity <--\n")
        if bin_retirement_df.empty:
            outfile.write("No retirements.\n")
        else:
            bin_retirement_df.to_string(outfile)
            outfile.write("\n")


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
    # Select generators of 'gen_ret_bin' capacity
    # type only
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
        WHERE project_specified_capacity_scenario_id = {}
        AND specified_capacity_mw > 0) as capacity
        USING (project, period)
        LEFT OUTER JOIN
        (SELECT project, period, 
        annual_fixed_cost_per_kw_year * 1000 AS annual_fixed_cost_per_mw_year
        FROM inputs_project_specified_fixed_cost
        WHERE project_specified_fixed_cost_scenario_id = {}) as fixed_om
        USING (project, period)
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 
        'gen_ret_bin';""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_EXISTING_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_EXISTING_FIXED_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    return ep_capacities


# TODO: untested
def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    specified_generation_period_params.tab file.
    :param inputs_directory: local directory where .tab files will be saved
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
    if os.path.isfile(os.path.join(inputs_directory,
                                   "specified_generation_period_params.tab")
                      ):
        with open(os.path.join(inputs_directory,
                               "specified_generation_period_params.tab"),
                  "a") as existing_project_capacity_tab_file:
            writer = csv.writer(existing_project_capacity_tab_file,
                                delimiter="\t", lineterminator="\n")
            for row in ep_capacities:
                writer.writerow(row)
    # If specified_generation_period_params.tab file does not exist,
    # write header first, then add input data
    else:
        with open(os.path.join(inputs_directory,
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


# TODO: untested functionality
def import_module_specific_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    # New build capacity results
    if not quiet:
        print("project binary economic retirements")

    update_capacity_results_table(
        db=db, c=c, results_directory=results_directory,
        scenario_id=scenario_id, subproblem=subproblem, stage=stage,
        results_file="capacity_gen_ret_bin.csv"
    )


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
