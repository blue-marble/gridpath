#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This capacity type describes generator projects with the same
characteristics as *gen_spec*, but whose fixed O&M cost can be avoided by
'retiring' them.

The optimization can make the decision to retire generation in each study
*period*. Once retired, the generator may not become operational again.
Retirement decisions for this capacity type are 'linearized,' i.e. the
optimization may retire generators partially (e.g. retire only 200 MW of
a 500-MW generator). If retired, the annual fixed O&M cost of these projects
is avoided in the objective function.

"""

from __future__ import print_function

from builtins import next
from builtins import zip
import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, Constraint, Expression, \
    NonNegativeReals, value

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
    | | :code:`GEN_RET_LIN`                                                   |
    |                                                                         |
    | The list of projects of the :code:`gen_ret_lin` capacity type.          |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_RET_LIN_OPR_PRDS`                                          |
    |                                                                         |
    | Two-dimensional set of project-period combinations that helps describe  |
    | the project capacity available in a given period. This set is added to  |
    | the list of sets to join to get the final :code:`PRJ_OPR_PRDS` set      |
    | defined in **gridpath.project.capacity.capacity**.                      |
    +-------------------------------------------------------------------------+
    | | :code:`OPR_PRDS_BY_GEN_RET_LIN`                                       |
    |                                                                         |
    | Indexed set that describes the operational periods for each             |
    | :code:`gen_ret_lin` project.                                            |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_ret_lin_capacity_mw`                                       |
    | | *Defined over*: :code:`GEN_RET_LIN_OPR_PRDS`                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's specified capacity (in MW) in each operational period if  |
    | no capacity is retired.                                                 |
    +-------------------------------------------------------------------------+
    | | :code:`gen_ret_lin_fixed_cost_per_mw_yr`                              |
    | | *Defined over*: :code:`GEN_RET_LIN_OPR_PRDS`                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's fixed cost (in $ per MW-yr.) in each operational period.  |
    | This cost can be avoided by retiring the generation project.            |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`GenRetLin_Retire_MW`                                           |
    | | *Defined over*: :code:`GEN_RET_LIN_OPR_PRDS`                          |
    |                                                                         |
    | The amount of capacity (in MW) to be retired for each project in each   |
    | operational period. Has to be larger than zero and smaller than         |
    | :code:`gen_ret_lin_capacity_mw`.                                        |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`GenRetLin_Retire_Forever_Constraint`                           |
    | | *Defined over*: :code:`GEN_RET_LIN_OPR_PRDS`                          |
    |                                                                         |
    | Total capacity after retirement must be less than or equal what is was  |
    | in the previous period. This ensures retirement decisions cannot be     |
    | undone.                                                                 |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.GEN_RET_LIN_OPR_PRDS = Set(dimen=2)

    m.GEN_RET_LIN = Set(
        initialize=lambda mod: set(g for (g, p) in mod.GEN_RET_LIN_OPR_PRDS)
    )

    m.OPR_PRDS_BY_GEN_RET_LIN = Set(
        m.GEN_RET_LIN,
        initialize=lambda mod, prj:
            set(period for (project, period)
                in mod.GEN_RET_LIN_OPR_PRDS
                if project == prj)
    )

    # Required Params
    ###########################################################################

    m.gen_ret_lin_capacity_mw = Param(
        m.GEN_RET_LIN_OPR_PRDS,
        within=NonNegativeReals
    )

    m.gen_ret_lin_fixed_cost_per_mw_yr = Param(
        m.GEN_RET_LIN_OPR_PRDS,
        within=NonNegativeReals
    )

    # Derived Params
    ###########################################################################

    m.gen_ret_lin_first_period = Param(
        m.GEN_RET_LIN,
        initialize=lambda mod, g:
        min(p for p in mod.OPR_PRDS_BY_GEN_RET_LIN[g])
    )

    # Variables
    ###########################################################################

    # Retire capacity variable
    m.GenRetLin_Retire_MW = Var(
        m.GEN_RET_LIN_OPR_PRDS,
        bounds=retire_capacity_bounds
    )

    # Expressions
    ###########################################################################

    m.GenRetLin_Capacity_MW = Expression(
        m.GEN_RET_LIN_OPR_PRDS,
        rule=gen_ret_lin_capacity_rule
    )

    # Constraints
    ###########################################################################

    m.GenRetLin_Retire_Forever_Constraint = Constraint(
        m.GEN_RET_LIN_OPR_PRDS,
        rule=retire_forever_rule
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "GEN_RET_LIN_OPR_PRDS",
    )


# Variable Bound Rules
###############################################################################

def retire_capacity_bounds(mod, g, p):
    """
    Shouldn't be able to retire more than available capacity
    """
    return 0, mod.gen_ret_lin_capacity_mw[g, p]


# Expression Rules
###############################################################################

def gen_ret_lin_capacity_rule(mod, g, p):
    """
    **Expressions Name**: GenRetLin_Capacity_MW
    **Enforced Over**: GEN_RET_LIN_OPR_PRDS

    Existing capacity minus retirements.
    """
    return mod.gen_ret_lin_capacity_mw[g, p] \
        - mod.GenRetLin_Retire_MW[g, p]


# Constraint Formulation Rules
###############################################################################

# TODO: we need to check that the user hasn't specified increasing
#  capacity to begin with
def retire_forever_rule(mod, g, p):
    """
    **Constraint Name**: GenRetLin_Retire_Forever_Constraint
    **Enforced Over**: GEN_RET_LIN_OPR_PRDS

    Once retired, capacity cannot be brought back (i.e. in the current
    period, total capacity (after retirement) must be less than or equal
    what it was in the last period.
    """
    # Skip if we're in the first period
    if p == value(mod.first_period):
        return Constraint.Skip
    # Skip if this is the generator's first period
    if p == mod.gen_ret_lin_first_period[g]:
        return Constraint.Skip
    else:
        return mod.GenRetLin_Capacity_MW[g, p] \
            <= mod.GenRetLin_Capacity_MW[
                g, mod.prev_period[p]]


# Capacity Type Methods
###############################################################################

def capacity_rule(mod, g, p):
    """
    The capacity of projects of the *gen_ret_lin* capacity type is a
    pre-specified number for each of the project's operational periods minus
    any capacity that was retired.
    """
    return mod.GenRetLin_Capacity_MW[g, p]


def capacity_cost_rule(mod, g, p):
    """
    The capacity cost of projects of the *gen_ret_lin* capacity type is its net
    capacity (pre-specified capacity minus retired capacity) times the per-mw
    fixed cost for each of the project's operational periods.
    """
    return mod.GenRetLin_Capacity_MW[g, p] \
        * mod.gen_ret_lin_fixed_cost_per_mw_yr[g, p]


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

    def determine_gen_ret_lin_projects():
        gen_ret_lin_projects = list()

        df = pd.read_csv(
            os.path.join(scenario_directory, subproblem, stage, "inputs",
                         "projects.tab"),
            sep="\t",
            usecols=["project", "capacity_type"]
        )
        for row in zip(df["project"],
                       df["capacity_type"]):
            if row[1] == "gen_ret_lin":
                gen_ret_lin_projects.append(row[0])
            else:
                pass

        return gen_ret_lin_projects

    def determine_period_params():
        generators_list = determine_gen_ret_lin_projects()
        generator_period_list = list()
        gen_ret_lin_capacity_mw_dict = dict()
        gen_ret_lin_fixed_cost_per_mw_yr_dict = dict()
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
                gen_ret_lin_capacity_mw_dict[(row[0], row[1])] = float(row[2])
                gen_ret_lin_fixed_cost_per_mw_yr_dict[(row[0], row[1])] = \
                    float(row[3])
            else:
                pass

        return generator_period_list, \
            gen_ret_lin_capacity_mw_dict, \
            gen_ret_lin_fixed_cost_per_mw_yr_dict

    data_portal.data()["GEN_RET_LIN_OPR_PRDS"] = \
        {None: determine_period_params()[0]}

    data_portal.data()["gen_ret_lin_capacity_mw"] = \
        determine_period_params()[1]

    data_portal.data()["gen_ret_lin_fixed_cost_per_mw_yr"] = \
        determine_period_params()[2]


def export_module_specific_results(
        scenario_directory, subproblem, stage, m, d
):
    """
    Export gen_ret_lin retirement results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "capacity_gen_ret_lin"
                           ".csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "technology", "load_zone",
                         "retired_mw"])
        for (prj, p) in m.GEN_RET_LIN_OPR_PRDS:
            writer.writerow([
                prj,
                p,
                m.technology[prj],
                m.load_zone[prj],
                value(m.GenRetLin_Retire_MW[prj, p])
            ])


def summarize_module_specific_results(
    scenario_directory, subproblem, stage, summary_results_file
):
    """
    Summarize existing gen linear economic retirement capacity results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param summary_results_file:
    :return:
    """

    # Get the results CSV as dataframe
    capacity_results_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "results",
                     "capacity_gen_ret_lin.csv")
    )

    capacity_results_agg_df = capacity_results_df.groupby(
        by=["load_zone", "technology",'period'],
        as_index=True
    ).sum()

    # Set the formatting of float to be readable
    pd.options.display.float_format = "{:,.0f}".format

    # Get all technologies with the new build capacity
    lin_retirement_df = pd.DataFrame(
        capacity_results_agg_df[
            capacity_results_agg_df["retired_mw"] > 0
        ]["retired_mw"]
    )

    lin_retirement_df.columns = ["Retired Capacity (MW)"]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> Retired Capacity <--\n")
        if lin_retirement_df.empty:
            outfile.write("No retirements.\n")
        else:
            lin_retirement_df.to_string(outfile)
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
    # Select generators of 'gen_ret_lin' capacity type only
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
        annual_fixed_cost_per_kw_year * 1000 AS annual_fixed_cost_per_mw_year
        FROM inputs_project_specified_fixed_cost
        WHERE project_specified_fixed_cost_scenario_id = {}) as fixed_om
        USING (project, period)
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 
        'gen_ret_lin';""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_SPECIFIED_FIXED_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )
    return ep_capacities


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    specified_generation_period_params.tab file
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
        print("project linear economic retirements")

    update_capacity_results_table(
        db=db, c=c, results_directory=results_directory,
        scenario_id=scenario_id, subproblem=subproblem, stage=stage,
        results_file="capacity_gen_ret_lin.csv"
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

    # do validation
    # make sure existing capacity is a postive number
    # make sure annual fixed costs are positive
