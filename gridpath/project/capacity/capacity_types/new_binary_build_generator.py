#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.project.capacity.capacity_types.new_binary_build_generator**
module describes the capacity of generators that can be built by the
optimization at a cost. Once built, these generators remain available for
the duration of their pre-specified lifetime. The decision to build is binary,
i.e. either the project is built at a specfied build size capacity, or nothing
is built at all. """

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import numpy as np
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, NonNegativeReals, Binary, \
    Constraint, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets
from gridpath.auxiliary.auxiliary import check_column_sign_positive, \
    get_expected_dtypes, check_dtypes, write_validation_to_database, \
    setup_results_import

from gridpath.project.capacity.capacity_types.common_methods import \
    operational_periods_by_project_vintage, project_operational_periods, \
    project_vintages_operational_in_period


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    This function adds to the model a two-dimensional set of project-vintage
    combinations to describe the periods in time when project capacity can be
    built in the optimization: the *NEW_BINARY_BUILD_GENERATOR_VINTAGES* set,
    which we will also designate with :math:`NG\_V` and index with
    :math:`ng, v` where :math:`ng\in R` and :math:`v\in P`. For each :math:`ng,
    v`, we load the *lifetime_yrs_by_new_binary_build_vintage* parameter, which
    is the project's lifetime, i.e. how long project capacity of a particular
    vintage remains operational. We will then use this parameter to
    determine the operational periods :math:`p` for each :math:`ng, v`. For
    each :math:`ng, v`, we also declare the cost to build new capacity: the
    *new_binary_build_annualized_real_cost_per_mw_yr* parameter.

    .. note:: The cost input to the model is a levelized cost per unit
        capacity. This annualized cost is incurred in each period of the study
        (and multiplied by the number of years the period represents) for
        the duration of the project's lifetime. It is up to the user to
        ensure that the *lifetime_yrs_by_new_binary_build_vintage* and
        *new_binary_build_annualized_real_cost_per_mw_yr parameters* are
        consistent.

    The :math:`Build\_Binary_{ng,v}` variable is defined over the :math:`NG\_V`
    set and determines for each possible vintage :math:`v`at each new-build
    project :math:`ng` whether the project is built or not (this is a binary
    'on-off' decision). :math:`New\_Build\_Binary_{ng,np}` is constrained such
    that once the decision to build is made, the project cannot be built again
    in another vintage until its lifetime is expired.

    We use the *NEW_BUILD_BINARY_GENERATOR_VINTAGES* set and the
    *lifetime_yrs_by_new_binary_build_vintage* parameter to determine the
    operational periods for capacity of each possible vintage: the
    *OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_GENERATOR_VINTAGE* set indexed by
    :math:`ng,v`.

    .. note:: A period is currently defined as operational for project
        :math:`ng` if :math:`v <= p <
        lifetime\_yrs\_by\_new\_binary\_build\_vintage_{ng,v}`, so capacity of
        the 2020 vintage with lifetime of 30 years will be assumed operational
        starting Jan 1, 2020 and through Dec 31, 2049, but will not be
        operational in 2050.

    The *NEW_BINARY_BUILD_GENERATOR_OPERATIONAL_PERIODS* set is a
    two-dimensional set that includes the periods when project capacity of
    any vintage *could* be operational if built.  This set
    is then added to the list of sets to join to get the final
    *PROJECT_OPERATIONAL_PERIODS* set defined in
    **gridpath.project.capacity.capacity**. We will also use *NG_P* to
    designate this set (index :math:`ng, np` where :math:`ng\in R` and
    :math:`np\in P`).

    Finally, we need to determine which project vintages could be
    operational in each period: the
    *NEW_BINARY_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD* set. Indexed by
    :math:`p`, this two-dimensional set :math:`\{NG\_OV_p\}_{p\in P}`
    (:math:`NG\_OV_p\subset NG\_V`) can help us tell how much capacity we
    have available in period :math:`p` of each new-build project :math:`ng`
    depending on the build decisions made by the optimization.

    """

    # Indexes and param
    m.NEW_BINARY_BUILD_GENERATORS = Set(within=m.PROJECTS)
    m.NEW_BINARY_BUILD_GENERATOR_VINTAGES = \
        Set(dimen=2, within=m.PROJECTS*m.PERIODS)
    m.lifetime_yrs_by_new_binary_build_vintage = \
        Param(m.NEW_BINARY_BUILD_GENERATOR_VINTAGES, within=NonNegativeReals)
    m.new_binary_build_annualized_real_cost_per_mw_yr = \
        Param(m.NEW_BINARY_BUILD_GENERATOR_VINTAGES, within=NonNegativeReals)
    m.binary_build_size_mw = \
        Param(m.NEW_BINARY_BUILD_GENERATORS, within=NonNegativeReals)

    # Build variable
    m.Build_Binary = Var(m.NEW_BINARY_BUILD_GENERATOR_VINTAGES, within=Binary)

    # Auxiliary sets
    m.OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_GENERATOR_VINTAGE = \
        Set(m.NEW_BINARY_BUILD_GENERATOR_VINTAGES,
            initialize=operational_periods_by_generator_vintage)

    m.NEW_BINARY_BUILD_GENERATOR_OPERATIONAL_PERIODS = \
        Set(dimen=2, initialize=new_build_option_operational_periods)

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "NEW_BINARY_BUILD_GENERATOR_OPERATIONAL_PERIODS",
    )

    m.NEW_BINARY_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD = \
        Set(m.PERIODS, dimen=2,
            initialize=new_build_option_vintages_operational_in_period)

    def only_build_once_rule(mod, g, p):
        """
        Once a project is built, it cannot be built again in another vintage
        until its lifetime is expired.

        Note: this constraint could be generalized into a min and max build
        constraint if we want to allow multiple units to be built.
        """

        # Sum all binary build decisions of vintages operational in the current
        # period and limit this to be less than or equal than 1
        return sum(
            mod.Build_Binary[g, v] for (gen, v)
            in mod.NEW_BINARY_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD[p]
            if gen == g
        ) <= 1

    m.New_Binary_Build_Generator_Only_Build_Once_Constraint = Constraint(
        m.NEW_BINARY_BUILD_GENERATOR_VINTAGES,
        rule=only_build_once_rule
    )


def capacity_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the capacity of project *g* in period *p*

    Note: only one vintage can have a non-zero Build_Binary variable in each
    period due to the *only_build_once_rule*.
    """

    return sum(
        mod.Build_Binary[g, v]
        * mod.binary_build_size_mw[g]
        for (gen, v)
        in mod.NEW_BINARY_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD[p]
        if gen == g
    )


# TODO: we need to think through where to multiply the annualized costs by
#  number_years_represented[p]; currently, it's done downstream, but maybe
#  the capacity cost rule is a better place?
# TODO: it's inconsistent that the capacity available in a period is
#  calculated in an expression in add_model_components but the cost isn't;
#  that said, we don't really need to carry the extra cost expression
#  around; the capacity expression is used in the min and max cumulative
#  capacity constraints
def capacity_cost_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the total annualized capacity cost of *new_build_generator*
        project *g* in period *p*

    The capacity cost for new-build generators in a given period is the
    capacity-build of a particular vintage times the annualized cost for
    that vintage summed over all vintages operational in the period.
    """
    return sum(
        mod.Build_Binary[g, v]
        * mod.binary_build_size_mw[g]
        * mod.new_binary_build_annualized_real_cost_per_mw_yr[g, v]
        for (gen, v)
        in mod.NEW_BINARY_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD[p]
        if gen == g
    )


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

    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage, "inputs",
                              "new_binary_build_generator_vintage_costs.tab"),
        index=m.NEW_BINARY_BUILD_GENERATOR_VINTAGES,
        select=("project", "vintage", "lifetime_yrs",
                "annualized_real_cost_per_mw_yr"),
        param=(m.lifetime_yrs_by_new_binary_build_vintage,
               m.new_binary_build_annualized_real_cost_per_mw_yr)
    )

    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage, "inputs",
                              "new_binary_build_generator_size.tab"),
        index=m.NEW_BINARY_BUILD_GENERATORS,
        select=("project", "binary_build_size_mw"),
        param=(m.binary_build_size_mw)
    )


def export_module_specific_results(scenario_directory, subproblem, stage, m, d):
    """
    Export new build generation results.
    :param scenario_directory:
    :param stage:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "capacity_new_binary_build_generator.csv"),
              "w", newline="") as f:

        writer = csv.writer(f)
        writer.writerow(["project", "period", "technology", "load_zone",
                         "new_build_binary", "new_build_mw"])
        for (prj, v) in m.NEW_BINARY_BUILD_GENERATOR_VINTAGES:
            writer.writerow([
                prj,
                v,
                m.technology[prj],
                m.load_zone[prj],
                value(m.Build_Binary[prj, v]),
                value(m.Build_Binary[prj, v] * m.binary_build_size_mw[prj])
            ])


def operational_periods_by_generator_vintage(mod, prj, v):
    return operational_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"), vintage=v,
        lifetime=mod.lifetime_yrs_by_new_binary_build_vintage[prj, v]
    )


def new_build_option_operational_periods(mod):
    return project_operational_periods(
        project_vintages_set=mod.NEW_BINARY_BUILD_GENERATOR_VINTAGES,
        operational_periods_by_project_vintage_set=
        mod.OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_GENERATOR_VINTAGE
    )


def new_build_option_vintages_operational_in_period(mod, p):
    return project_vintages_operational_in_period(
        project_vintage_set=mod.NEW_BINARY_BUILD_GENERATOR_VINTAGES,
        operational_periods_by_project_vintage_set=
        mod.OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_GENERATOR_VINTAGE,
        period=p
    )


def summarize_module_specific_results(
    scenario_directory, subproblem, stage, summary_results_file
):
    """
    Summarize new binary build generation capacity results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param summary_results_file:
    :return:
    """

    # Get the results CSV as dataframe
    capacity_results_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "results", "capacity_new_binary_build_generator.csv")
    )

    capacity_results_agg_df = \
        capacity_results_df.groupby(by=["load_zone", "technology",
                                        'period'],
                                    as_index=True
                                    ).sum()

    # Set the formatting of float to be readable
    pd.options.display.float_format = "{:,.0f}".format

    # Get all technologies with the new binary build capacity
    new_build_df = pd.DataFrame(
        capacity_results_agg_df[
            capacity_results_agg_df["new_build_mw"] > 0
        ]["new_build_mw"]
    )

    new_build_df.columns = ["New Binary Build Capacity (MW)"]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> New Binary Build Generation Capacity <--\n")
        if new_build_df.empty:
            outfile.write("No new generation was built.\n")
        else:
            new_build_df.to_string(outfile)
            outfile.write("\n")


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

    # TODO: remove "as annualized_real_cost_per_kw_yr" statement
    #  once database columns and tab file columns are aligned
    c1 = conn.cursor()
    new_gen_costs = c1.execute(
        """SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr * 1000 as annualized_real_cost_per_kw_yr
        FROM inputs_project_portfolios
        
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        
        INNER JOIN
        (SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr
        FROM inputs_project_new_cost
        WHERE project_new_cost_scenario_id = {}) as cost
        USING (project, period)
        
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 'new_binary_build_generator';""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    c2 = conn.cursor()
    new_gen_build_size = c2.execute(
        """SELECT project, binary_build_size_mw
        FROM inputs_project_portfolios
        
        INNER JOIN
        (SELECT project, binary_build_size_mw
        FROM inputs_project_new_binary_build_size
        WHERE project_new_binary_build_size_scenario_id = {})
        USING (project)
        
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 'new_binary_build_generator';""".format(
            subscenarios.PROJECT_NEW_BINARY_BUILD_SIZE_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    return new_gen_costs, new_gen_build_size


def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()
    validation_results = []

    # Get the binary build generator inputs
    new_gen_costs, new_build_size = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Get the relevant projects and periods
    prj_periods = c.execute(
        """SELECT project, period
        FROM inputs_project_portfolios

        CROSS JOIN    
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods

        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 'new_binary_build_generator';""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,

        )
    )

    # Convert input data into pandas DataFrame
    cost_df = pd.DataFrame(
        data=new_gen_costs.fetchall(),
        columns=[s[0] for s in new_gen_costs.description]
    )

    bld_size_df = pd.DataFrame(
        data=new_build_size.fetchall(),
        columns=[s[0] for s in new_build_size.description]
    )

    # get the project lists
    projects = [p[0] for p in prj_periods]  # this will have duplicates if multiple periods!
    bld_size_projects = bld_size_df["project"]

    # Get expected dtypes
    expected_dtypes = get_expected_dtypes(
        conn=conn,
        tables=["inputs_project_new_cost",
                "inputs_project_new_binary_build_size"]
    )

    # Check dtypes
    dtype_errors, error_columns = check_dtypes(cost_df, expected_dtypes)
    for error in dtype_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_NEW_COST_SCENARIO_ID",
             "inputs_project_heat_rate_curves",
             "Invalid data type",
             error
             )
        )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in cost_df.columns
                       if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)

    sign_errors = check_column_sign_positive(
        df=cost_df,
        columns=valid_numeric_columns
    )
    for error in sign_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_NEW_COST_SCENARIO_ID",
             "inputs_project_new_costs",
             "Invalid numeric sign",
             error)
        )

    # Check that all binary new build projects have build size specified
    validation_errors = validate_projects(projects, bld_size_projects)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_NEW_BINARY_BUILD_SIZE_SCENARIO_ID",
             "inputs_project_new_binary_build_size",
             "Missing Project",
             error)
        )

    # Check that all binary new build projects have costs specified for each
    # period
    validation_errors = validate_costs(cost_df, prj_periods)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_NEW_COST_SCENARIO_ID",
             "inputs_project_new_costs",
             "Missing Costs",
             error)
        )

    # Write all input validation errors to database
    write_validation_to_database(validation_results, conn)


def validate_projects(list1, list2):
    """
    Check for projects in list 1 that aren't in list 2

    Note: Function will ignore duplicates in list
    :param list1:
    :param list2:
    :return: list of error messages for each missing project
    """
    results = []
    missing_projects = np.setdiff1d(list1, list2)
    for prj in missing_projects:
        results.append(
            "Missing build size inputs for project '{}'".format(prj)
        )

    return results


def validate_costs(cost_df, prj_periods):
    """
    Check that cost inputs exist for the relevant projects and periods
    :param cost_df:
    :param prj_periods: list with relevant projects and periods (tuple)
    :return: list of error messages for each missing project, period combination
    """
    results = []
    for prj, period in prj_periods:
        if not ((cost_df.project == prj) & (cost_df.period == period)).any():
            results.append(
                "Missing cost inputs for project '{}', period '{}'"
                .format(prj, str(period))
            )

    return results


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    new_binary_build_generator_vintage_costs.tab file and the
    new_binary_build_generator_size.tab file
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    new_gen_costs, new_gen_build_size = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory,
                           "new_binary_build_generator_vintage_costs.tab"), "w", newline="") as \
            new_gen_costs_tab_file:
        writer = csv.writer(new_gen_costs_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["project", "vintage", "lifetime_yrs",
             "annualized_real_cost_per_mw_yr"]
        )

        for row in new_gen_costs:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    with open(os.path.join(inputs_directory,
                           "new_binary_build_generator_size.tab"), "w", newline="") as \
            new_build_size_tab_file:
        writer = csv.writer(new_build_size_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["project", "binary_build_size_mw"]
        )

        for row in new_gen_build_size:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


def import_module_specific_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # New build capacity results
    print("project new binary build generator")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_capacity_new_binary_build_generator",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "capacity_new_binary_build_generator.csv"), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            technology = row[2]
            load_zone = row[3]
            new_build_binary = row[4]
            new_build_mw = row[5]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                    technology, load_zone, new_build_binary, new_build_mw)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_capacity_new_binary_build_generator{}
        (scenario_id, project, period, subproblem_id, stage_id, 
        technology, load_zone, new_build_binary, new_build_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""".format(scenario_id)

    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql,
                          data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_capacity_new_binary_build_generator
        (scenario_id, project, period, subproblem_id, stage_id,
        technology, load_zone, new_build_binary, new_build_mw)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        technology, load_zone, new_build_binary, new_build_mw
        FROM temp_results_project_capacity_new_binary_build_generator{}
        ORDER BY scenario_id, project, period, subproblem_id, stage_id;
        """.format(scenario_id)

    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
