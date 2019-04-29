#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **existing_gen_binary_economic_retirement** module describes the capacity
of generators that are available to the optimization without having to incur an
investment cost, but whose fixed O&M can be avoided if they are retired.
As opposed to linear retirement, these type of generators have binary
retirement decisions (either completely retired or not).
"""

from __future__ import print_function

from builtins import next
from builtins import zip
from builtins import str
import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, Constraint, Expression, \
    NonNegativeReals, Binary, value

from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    This function adds to the model a two-dimensional set of project-period
    combinations to describe the project capacity will be available to the
    optimization in a given period: the
    *EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS* set. This set
    is then added to the list of sets to join to get the final
    *PROJECT_OPERATIONAL_PERIODS* set defined in
    **gridpath.project.capacity.capacity**. We will also use *EBR_P* to
    designate this set (index :math:`ebr, ebp` where :math:`ebr\in R` and
    :math:`ebp\in P`).

    For each :math:`ebr, ebp`, we define two parameters:
    *existing_bin_econ_ret_capacity_mw* (the specified capacity of project
    *ebr* in period *ebp* if no capacity is retired) and
    *existing_bin_econ_ret_fixed_cost_per_mw_yr* (the per-MW cost to keep
    capacity at project *ebr* operational in period *ebp*.

    The variable *Retire_Binary* is also defined over the *EBR_P* set. This
    decision variable is binary, i.e. the model decides to either retire all
    specified capacity or none at all in each operational period. The project's
    capacity in each period is then constrained as follows:

    :math:`Existing\_Binary\_Econ\_Ret\_Capacity\_MW_{ebr,ebp} =
    existing\_bin\_econ\_ret\_capacity\_mw_{ebr, ebp} *
    (1 - Binary\_Retire_{ebr, ebp}`

    The binary decision variable is then constrained to be less than or equal
    to the binary variable in the previous period in order to prevent capacity
    from coming back online after it has been retired for
    :math:`ebp\in N\_F\_P`.

    :math:`Binary\_Retire_{ebr,
    ebp}\geq Binary\_Retire_{ebr,
    previous\_period_{ebp}}`.


    """
    m.EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS = \
        Set(dimen=2)

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS",
    )

    # Make set of operational periods by generator
    m.EXISTING_BINARY_ECON_RETRMNT_GENERATORS = Set(
        initialize=
        lambda mod: set(
            g for (g, p)
            in mod.EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
        )
    )
    m.OPRTNL_PERIODS_BY_EX_BIN_ECON_RETRMNT_GENERATORS = \
        Set(
            m.EXISTING_BINARY_ECON_RETRMNT_GENERATORS,
            initialize=
            lambda mod, prj: set(
                period for (project, period)
                in mod.EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
                if project == prj
            )
        )
    m.ex_gen_bin_econ_ret_gen_first_period = \
        Param(
            m.EXISTING_BINARY_ECON_RETRMNT_GENERATORS,
            initialize=
            lambda mod, g: min(
                p for p
                in mod.OPRTNL_PERIODS_BY_EX_BIN_ECON_RETRMNT_GENERATORS[g]
            )
        )

    # Capacity and fixed cost
    m.existing_bin_econ_ret_capacity_mw = \
        Param(m.EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
              within=NonNegativeReals)
    m.existing_bin_econ_ret_fixed_cost_per_mw_yr = \
        Param(m.EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
              within=NonNegativeReals)


    # Binary retirement variable
    m.Retire_Binary = Var(
        m.EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
        within=Binary)


    # TODO: we need to check that the user hasn't specified increasing
    #  capacity to begin with
    def retire_forever_rule(mod, g, p):
        """
        Once the binary retirement decision is made, the decision will last
        through all following periods, i.e. the binary variable cannot be
        smaller than what it was in the previous period
        :param g:
        :param p:
        :return:
        """
        # Skip if we're in the first period
        if p == value(mod.first_period):
            return Constraint.Skip
        # Skip if this is the generator's first period
        if p == mod.ex_gen_bin_econ_ret_gen_first_period[g]:
            return Constraint.Skip
        else:
            return mod.Retire_Binary[g, p] \
                   >= \
                   mod.Retire_Binary[g, mod.previous_period[p]]

    m.Binary_Retirement_Retire_Forever_Constraint = Constraint(
        m.EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
        rule=retire_forever_rule
    )


def capacity_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the capacity of project *g* in period *p*

    The capacity of projects of the *existing_gen_binary_economic_retirement*
    capacity type is a pre-specified number for each of the project's
    operational periods multiplied with 1 minus the binary retirement variable.
    The expression returned is
    :math:`existing\_bin\_econ\_ret\_capacity\_mw_{ebr, ebp} *
    (1 - Binary\_Retire_{ebr, ebp}`.
    See the *add_module_specific_components* method for constraints.
    """
    return mod.existing_bin_econ_ret_capacity_mw[g, p] \
           * (1 - mod.Retire_Binary[g, p])


def capacity_cost_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the total annualized fixed cost of
        *existing_gen_binary_economic_retirement* project *g* in period *p*

    The capacity cost of projects of the
    *existing_gen_binary_economic_retirement* capacity type is its net
    capacity (pre-specified capacity or zero if retired) times the per-mw
    fixed cost for each of the project's operational periods. This method
    returns :math:`existing\_bin\_econ\_ret\_fixed\_cost\_per\_mw\_yr_{ebr,
    ebp} * existing\_bin\_econ\_ret\_capacity\_mw_{ebr, ebp} *
    (1 - Binary\_Retire_{ebr, ebp}`.
    and it will be called for :math:`(ebr, ebp)\in EBR_P`.
    """
    return mod.existing_bin_econ_ret_fixed_cost_per_mw_yr[g, p] \
        * mod.existing_bin_econ_ret_capacity_mw[g, p] \
        * (1 - mod.Retire_Binary[g, p])


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

    def determine_existing_gen_binary_econ_ret_projects():
        """
        Find the existing_gen_binary_economic_retirement capacity type projects
        :return:
        """

        ex_gen_bin_econ_ret_projects = list()

        dynamic_components = \
            pd.read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project",
                                   "capacity_type"]
            )
        for row in zip(dynamic_components["project"],
                       dynamic_components["capacity_type"]):
            if row[1] == "existing_gen_binary_economic_retirement":
                ex_gen_bin_econ_ret_projects.append(row[0])
            else:
                pass

        return ex_gen_bin_econ_ret_projects

    def determine_period_params():
        """

        :return:
        """
        generators_list = determine_existing_gen_binary_econ_ret_projects()
        generator_period_list = list()
        existing_bin_econ_ret_capacity_mw_dict = dict()
        existing_bin_econ_ret_fixed_cost_per_mw_yr_dict = dict()
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
                existing_bin_econ_ret_capacity_mw_dict[(row[0], row[1])] = \
                    float(row[2])
                existing_bin_econ_ret_fixed_cost_per_mw_yr_dict[(row[0],
                                                                 row[1])] = \
                    float(row[3])
            else:
                pass

        return generator_period_list, \
               existing_bin_econ_ret_capacity_mw_dict, \
               existing_bin_econ_ret_fixed_cost_per_mw_yr_dict

    data_portal.data()[
        "EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS"
    ] = {
        None: determine_period_params()[0]
    }

    data_portal.data()["existing_bin_econ_ret_capacity_mw"] = \
        determine_period_params()[1]

    data_portal.data()["existing_bin_econ_ret_fixed_cost_per_mw_yr"] = \
        determine_period_params()[2]


def export_module_specific_results(scenario_directory, horizon, stage, m, d):
    """
    Export existing gen binary economic retirement results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "capacity_existing_gen_binary_economic_retirement"
                           ".csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "technology", "load_zone",
                         "retire_mw"])
        for (prj, p) in \
                m.EXISTING_BIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS:
            writer.writerow([
                prj,
                p,
                m.technology[prj],
                m.load_zone[prj],
                value(m.Retire_Binary[prj, p] *
                      m.existing_bin_econ_ret_capacity_mw[prj, p])
            ])


def summarize_module_specific_results(
        problem_directory, horizon, stage, summary_results_file
):
    """
    Summarize existing gen binary economic retirement capacity results.
    :param problem_directory:
    :param horizon:
    :param stage:
    :param summary_results_file:
    :return:
    """

    # Get the results CSV as dataframe
    capacity_results_df = \
        pd.read_csv(os.path.join(
            problem_directory, horizon, stage, "results",
            "capacity_existing_gen_binary_economic_retirement.csv"
        ))

    capacity_results_agg_df = \
        capacity_results_df.groupby(
            by=["load_zone", "technology", 'period'],
            as_index=True
        ).sum()

    # Set the formatting of float to be readable
    pd.options.display.float_format = "{:,.0f}".format

    # Get all technologies with the new build capacity
    bin_retirement_df = pd.DataFrame(
        capacity_results_agg_df[
            capacity_results_agg_df["retire_mw"] > 0
            ]["retire_mw"]
    )

    bin_retirement_df.columns = ["Retired Capacity (MW)"]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> Retired Capacity <--\n")
        if bin_retirement_df.empty:
            outfile.write("No retirements.\n")
        else:
            bin_retirement_df.to_string(outfile)
            outfile.write("\n")


# TODO: untested functionality
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

    # Select generators of 'existing_gen_binary_economic_retirement' capacity
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
        AND capacity_type = 
        'existing_gen_binary_economic_retirement';""".format(
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

# TODO: untested functionality
def import_module_specific_results_into_database(
        scenario_id, c, db, results_directory
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # New build capacity results
    print("project binary economic retirements")
    c.execute(
        """DELETE FROM results_project_capacity_binary_economic_retirement 
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS 
        temp_results_project_capacity_binary_economic_retirement"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE 
        temp_results_project_capacity_binary_economic_retirement"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        project VARCHAR(64),
        period INTEGER,
        technology VARCHAR(32),
        load_zone VARCHAR(32),
        retired_mw FLOAT,
        PRIMARY KEY (scenario_id, project, period)
        );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(
            results_directory,
            "capacity_existing_gen_binary_economic_retirement.csv"), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            technology = row[2]
            load_zone = row[3]
            retired_mw = row[4]

            c.execute(
                """INSERT INTO 
                temp_results_project_capacity_binary_economic_retirement"""
                + str(scenario_id) + """
                (scenario_id, project, period, technology, load_zone,
                retired_mw)
                VALUES ({}, '{}', {}, '{}', '{}', {});""".format(
                    scenario_id, project, period, technology, load_zone,
                    retired_mw
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_capacity_binary_economic_retirement
        (scenario_id, project, period, technology, load_zone, retired_mw)
        SELECT
        scenario_id, project, period, technology, load_zone, retired_mw
        FROM temp_results_project_capacity_binary_economic_retirement"""
        + str(scenario_id)
        + """
        ORDER BY scenario_id, project, period;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE 
        temp_results_project_capacity_binary_economic_retirement"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
