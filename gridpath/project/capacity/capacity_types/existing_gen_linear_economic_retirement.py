#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **existing_gen_linear_economic_retirement** module describes the capacity
of generators that are available to the optimization without having to incur an
investment cost, but whose fixed O&M can be avoided if they are retired.
"""

from __future__ import print_function

from builtins import next
from builtins import zip
from builtins import str
import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, Constraint, Expression, \
    NonNegativeReals, value

from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    This function adds to the model a two-dimensional set of project-period
    combinations to describe the project capacity will be available to the
    optimization in a given period: the
    *EXISTING_LIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS* set. This set
    is then added to the list of sets to join to get the final
    *PROJECT_OPERATIONAL_PERIODS* set defined in
    **gridpath.project.capacity.capacity**. We will also use *ELR_P* to
    designate this set (index :math:`elr, elp` where :math:`elr\in R` and
    :math:`elp\in P`).

    For each :math:`elr, elp`, we define two parameters:
    *existing_lin_econ_ret_capacity_mw* (the specified capacity of project
    *elr* in period *elp* if no capacity is retired) and
    *existing_lin_econ_ret_fixed_cost_per_mw_yr* (the per-MW cost to keep
    capacity at project *elr* operational in period *elp*.

    The variable *Retire_MW* is also defined over the *ELR_P* set. This is
    the amount of capacity that the model can retire in each operational
    period. The project's capacity in each period is then constrained as
    follows:

    :math:`Existing\_Linear\_Econ\_Ret\_Capacity\_MW_{elr,
    elp}\leq existing\_lin\_econ\_ret\_capacity\_mw_{elr, elp} -
    Retire\_MW_{elr, elp}`

    The capacity expression is then constrained to be less than or equal to
    the capacity in the previous period in order to prevent capacity from
    coming back online after it has been retired for :math:`elp\in N\_F\_P`.

    :math:`Existing\_Linear\_Econ\_Ret\_Capacity\_MW_{elr,
    elp}\leq Existing\_Linear\_Econ\_Ret\_Capacity\_MW_{elr,
    previuos\_period_{elp}}`.


    """
    m.EXISTING_LIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS = \
        Set(dimen=2)

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "EXISTING_LIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS",
    )

    # Make set of operational periods by generator
    m.EXISTING_LINEAR_ECON_RETRMNT_GENERATORS = Set(
        initialize=
        lambda mod: set(
            g for (g, p)
            in mod.EXISTING_LIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
        )
    )
    m.OPRTNL_PERIODS_BY_EX_LIN_ECON_RETRMNT_GENERATORS = \
        Set(
            m.EXISTING_LINEAR_ECON_RETRMNT_GENERATORS,
            initialize=
            lambda mod, prj: set(
                period for (project, period)
                in mod.EXISTING_LIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS
                if project == prj
            )
        )
    m.ex_gen_lin_econ_ret_gen_first_period = \
        Param(
            m.EXISTING_LINEAR_ECON_RETRMNT_GENERATORS,
            initialize=
            lambda mod, g: min(
                p for p
                in mod.OPRTNL_PERIODS_BY_EX_LIN_ECON_RETRMNT_GENERATORS[g]
            )
        )

    # Capacity and fixed cost
    m.existing_lin_econ_ret_capacity_mw = \
        Param(m.EXISTING_LIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
              within=NonNegativeReals)
    m.existing_lin_econ_ret_fixed_cost_per_mw_yr = \
        Param(m.EXISTING_LIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
              within=NonNegativeReals)

    def retire_capacity_bounds(mod, g, p):
        """
        Shouldn't be able to retire more than available capacity
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return 0, mod.existing_lin_econ_ret_capacity_mw[g, p]

    # Retire capacity variable
    m.Retire_MW = Var(
        m.EXISTING_LIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
        bounds=retire_capacity_bounds
    )

    # Existing capacity minus retirements
    def existing_existing_econ_ret_capacity_rule(mod, g, p):
        """

        :param mod:
        :param g:
        :param p:
        :return:
        """
        return mod.existing_lin_econ_ret_capacity_mw[g, p] \
            - mod.Retire_MW[g, p]
    m.Existing_Linear_Econ_Ret_Capacity_MW = \
        Expression(
            m.EXISTING_LIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
            rule=existing_existing_econ_ret_capacity_rule
        )

    # TODO: we need to check that the user hasn't specified increasing
    #  capacity to begin with
    def retire_forever_rule(mod, g, p):
        """
        Once retired, capacity cannot be brought back (i.e. in the current 
        period, total capacity (after retirement) must be less than or equal 
        what it was in the last period
        :param mod: 
        :param g: 
        :param p: 
        :return: 
        """
        # Skip if we're in the first period
        if p == value(mod.first_period):
            return Constraint.Skip
        # Skip if this is the generator's first period
        if p == mod.ex_gen_lin_econ_ret_gen_first_period[g]:
            return Constraint.Skip
        else:
            return mod.Existing_Linear_Econ_Ret_Capacity_MW[g, p] \
                <= \
                mod.Existing_Linear_Econ_Ret_Capacity_MW[
                    g, mod.previous_period[p]
                ]

    m.Retire_Forever_Constraint = Constraint(
        m.EXISTING_LIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS,
        rule=retire_forever_rule
    )
        

def capacity_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the capacity of project *g* in period *p*

    The capacity of projects of the *existing_gen_no_econoimc_retirement*
    capacity type is a pre-specified number for each of the project's
    operational periods minus any capacity that was retired. The expression
    returned is :math:`Existing\_Linear\_Econ\_Ret\_Capacity\_MW_{elr,
    elp}`. See the *add_module_specific_components* method for constraints.
    """
    return mod.Existing_Linear_Econ_Ret_Capacity_MW[g, p]


def capacity_cost_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the total annualized fixed cost of
        *existing_gen_linear_economic_retirement* project *g* in period *p*

    The capacity cost of projects of the
    *existing_gen_linear_econoimc_retirement* capacity type is its net
    capacity (pre-specified capacity minus retired capacity) times the per-mw
    fixed cost for each of the project's operational periods. This method
    returns :math:`Existing\_Linear\_Econ\_Ret\_Capacity\_MW_{g,
    p} \\times existing\_lin\_econ\_ret\_fixed\_cost\_per\_mw\_yr_{g,
    p}` and it will be called for :math:`(g, p)\in ELR_P`.
    """
    return mod.Existing_Linear_Econ_Ret_Capacity_MW[g, p] \
        * mod.existing_lin_econ_ret_fixed_cost_per_mw_yr[g, p]


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
    def determine_existing_gen_linear_econ_ret_projects():
        """
        Find the existing_gen_linear_economic_retirement capacity type projects
        :return:
        """

        ex_gen_lin_econ_ret_projects = list()

        dynamic_components = \
            pd.read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project",
                                   "capacity_type"]
            )
        for row in zip(dynamic_components["project"],
                       dynamic_components["capacity_type"]):
            if row[1] == "existing_gen_linear_economic_retirement":
                ex_gen_lin_econ_ret_projects.append(row[0])
            else:
                pass

        return ex_gen_lin_econ_ret_projects

    def determine_period_params():
        """

        :return:
        """
        generators_list = determine_existing_gen_linear_econ_ret_projects()
        generator_period_list = list()
        existing_lin_econ_ret_capacity_mw_dict = dict()
        existing_lin_econ_ret_fixed_cost_per_mw_yr_dict = dict()
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
                existing_lin_econ_ret_capacity_mw_dict[(row[0], row[1])] = \
                    float(row[2])
                existing_lin_econ_ret_fixed_cost_per_mw_yr_dict[(row[0],
                                                                 row[1])] = \
                    float(row[3])
            else:
                pass

        return generator_period_list, \
            existing_lin_econ_ret_capacity_mw_dict, \
            existing_lin_econ_ret_fixed_cost_per_mw_yr_dict

    data_portal.data()[
        "EXISTING_LIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS"
    ] = {
        None: determine_period_params()[0]
    }

    data_portal.data()["existing_lin_econ_ret_capacity_mw"] = \
        determine_period_params()[1]

    data_portal.data()["existing_lin_econ_ret_fixed_cost_per_mw_yr"] = \
        determine_period_params()[2]


def export_module_specific_results(scenario_directory, horizon, stage, m, d):
    """
    Export existing gen linear economic retirement results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "capacity_existing_gen_linear_economic_retirement"
                           ".csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "technology", "load_zone",
                         "retire_mw"])
        for (prj, p) in \
                m.EXISTING_LIN_ECON_RETRMNT_GENERATORS_OPERATIONAL_PERIODS:
            writer.writerow([
                prj,
                p,
                m.technology[prj],
                m.load_zone[prj],
                value(m.Retire_MW[prj, p])
            ])


def summarize_module_specific_results(
    problem_directory, horizon, stage, summary_results_file
):
    """
    Summarize existing gen linear economic retirement capacity results.
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
            "capacity_existing_gen_linear_economic_retirement.csv"
        ))

    capacity_results_agg_df = \
        capacity_results_df.groupby(
            by=["load_zone", "technology",'period'],
            as_index=True
        ).sum()

    # Set the formatting of float to be readable
    pd.options.display.float_format = "{:,.0f}".format

    # Get all technologies with the new build capacity
    lin_retirement_df = pd.DataFrame(
        capacity_results_agg_df[
            capacity_results_agg_df["retire_mw"] > 0
        ]["retire_mw"]
    )

    lin_retirement_df.columns = ["Retired Capacity (MW)"]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> Retired Capacity <--\n")
        if lin_retirement_df.empty:
            outfile.write("No retirements.\n")
        else:
            lin_retirement_df.to_string(outfile)
            outfile.write("\n")


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

    # Select generators of 'existing_gen_linear_economic_retirement' capacity
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
        'existing_gen_linear_economic_retirement';""".format(
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
    print("project linear economic retirements")
    c.execute(
        """DELETE FROM results_project_capacity_linear_economic_retirement 
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS 
        temp_results_project_capacity_linear_economic_retirement"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE 
        temp_results_project_capacity_linear_economic_retirement"""
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
            "capacity_existing_gen_linear_economic_retirement.csv"), "r") as \
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
                temp_results_project_capacity_linear_economic_retirement"""
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
        """INSERT INTO results_project_capacity_linear_economic_retirement
        (scenario_id, project, period, technology, load_zone, retired_mw)
        SELECT
        scenario_id, project, period, technology, load_zone, retired_mw
        FROM temp_results_project_capacity_linear_economic_retirement"""
        + str(scenario_id)
        + """
        ORDER BY scenario_id, project, period;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE 
        temp_results_project_capacity_linear_economic_retirement"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
