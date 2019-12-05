#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.project.capacity.capacity_types.stor_new_bin**
module describes the capacity of storage projects that can be built by the
optimization at a cost. The user provides the build capacity and energy, and
the optimization determines whether to build it or not (binary decision).
Once built, these storage projects remain available for the duration of their
pre-specified lifetime.
"""

from __future__ import print_function

from builtins import next
import csv
import os.path
import pandas as pd
import numpy as np
from pyomo.environ import Set, Param, Var, NonNegativeReals, \
    Constraint, value, Binary

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import check_column_sign_positive, \
    get_expected_dtypes, check_dtypes, write_validation_to_database, \
    setup_results_import
from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets, \
    storage_only_capacity_type_operational_period_sets
from gridpath.project.capacity.capacity_types.common_methods import \
    operational_periods_by_project_vintage, project_operational_periods, \
    project_vintages_operational_in_period


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    This function adds to the model a two-dimensional set of project-vintage
    combinations to describe the periods in time when project capacity can be
    built in the optimization: the *NEW_BINARY_BUILD_STORAGE_VINTAGES* set,
    which we will also designate with :math:`NS\_V` and index with
    :math:`ns, v` where :math:`ns\in R` and :math:`v\in P`. For each :math:`ns,
    v`, we load the *lifetime_yrs_by_new_binary_build_storage vintage* parameter,
    which is the project's lifetime, i.e. how long project capacity of a
    particular vintage remains operational. We will then use this parameter to
    determine the operational periods :math:`p` for each :math:`ns, v`. For
    each :math:`ns, v`, we also declare the per-unit cost to build new power
    and energy capacity: the *new_binary_build_storage_annualized_real_cost_per_mw_yr*
    and *new_binary_build_storage_annualized_real_cost_per_mwh_yr* parameters.

    .. note:: The cost inputs to the model are annualized costs per unit
        capacity. The annualized costs are incurred in each period of the study
        (and multiplied by the number of years the period represents) for
        the duration of the project's lifetime. It is up to the user to
        ensure that the *lifetime_yrs_by_new_binary_build_storage* input to the
        model is consistent with the exogenous cost annualization.

    Storage duration in this module is exogenous: the user specifies the build
    capacity and energy, and the model decides whether to build it or not
    (binary decision).

    The variable :math:`Build\_Binary\_Storage_{ns,v}` is defined over
    the :math:`NS\_V` set and determines whether the vintage :math:`v` is
    built at each new-build storage project :math:`ns`.

    We use the *NEW_BINARY_BUILD_STORAGE_VINTAGES* set and the
    *lifetime_yrs_by_new_binary_build_storage_vintage* parameter to determine
    the operational periods for capacity of each possible vintage: the
    *OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_STORAGE_VINTAGE* set indexed by
    :math:`ns,v`.

    .. note:: A period is currently defined as operational for project
        :math:`ng` if :math:`v <= p < lifetime\_yrs\_by\_new\_build\_vintage_{
        ng,v}`, so capacity of the 2020 vintage with lifetime of 30 years will
        be assumed operational starting Jan 1, 2020 and through Dec 31, 2049,
        but will not be operational in 2050.

    The *NEW_BINARY_BUILD_STORAGE_OPERATIONAL_PERIODS* set is a
    two-dimensional set that includes the periods when project capacity of
    any vintage *could* be operational if built.  This set
    is then added to the list of sets to join to get the final
    *PROJECT_OPERATIONAL_PERIODS* set defined in
    **gridpath.project.capacity.capacity**. We will also use *NS_P* to
    designate this set (index :math:`ns, np` where :math:`ns\in R` and
    :math:`np\in P`).

    Finally, we need to determine which project vintages could be
    operational in each period: the
    *NEW_BINARY_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD* set. Indexed by
    :math:`p`, this two-dimensional set :math:`\{NS\_OV_p\}_{p\in P}`
    (:math:`NS\_OV_p\subset NS\_V`) can help us tell how much power
    and energy capacity we have available in period :math:`p` of each
    new-build project :math:`ns` depending on the build decisions made by
    the optimization.

    Then, we are ready to define the power and energy capacity for binary
    new-build storage:

    :math:`Capacity\_MW_{ns,np} = \sum_{(ns,ov)\in
    NS\_OV_{np}}{Build\_Binary\_Storage_{ns,ov}}
    * {binary\_build\_size\_storage\_mw_{ns,ov}}`.

    :math:`Energy\_Capacity\_MWh_{ns,np} = \sum_{(ns,ov)\in
    NS\_OV_{np}}{Build\_Binary\_Storage_{ns,ov}}
    * {binary\_build\_size\_storage\_mwh_{ns}}`.

    The power/energy capacity of a new-build generator in a given operational
    period for the new-build generator is equal to the sum of all binary build
    decisions of vintages operational in that period multiplied with the
    power/energy capacity.

    """
    # Sets (to index params)
    m.NEW_BINARY_BUILD_STORAGE_PROJECTS = Set()
    m.NEW_BINARY_BUILD_STORAGE_VINTAGES = \
        Set(dimen=2, within=m.NEW_BINARY_BUILD_STORAGE_PROJECTS*m.PERIODS)

    # Params
    m.lifetime_yrs_by_new_binary_build_storage_vintage = \
        Param(m.NEW_BINARY_BUILD_STORAGE_VINTAGES, within=NonNegativeReals)
    m.new_binary_build_storage_annualized_real_cost_per_mw_yr = \
        Param(m.NEW_BINARY_BUILD_STORAGE_VINTAGES, within=NonNegativeReals)
    m.new_binary_build_storage_annualized_real_cost_per_mwh_yr = \
        Param(m.NEW_BINARY_BUILD_STORAGE_VINTAGES, within=NonNegativeReals)
    m.binary_build_size_storage_mw = \
        Param(m.NEW_BINARY_BUILD_STORAGE_PROJECTS, within=NonNegativeReals)
    m.binary_build_size_storage_mwh = \
        Param(m.NEW_BINARY_BUILD_STORAGE_PROJECTS, within=NonNegativeReals)

    # Build variable (binary)
    m.Build_Binary_Storage = \
        Var(m.NEW_BINARY_BUILD_STORAGE_VINTAGES, within=Binary)

    # Auxiliary sets
    m.OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_STORAGE_VINTAGE = \
        Set(m.NEW_BINARY_BUILD_STORAGE_VINTAGES,
            initialize=operational_periods_by_storage_vintage)

    m.NEW_BINARY_BUILD_STORAGE_OPERATIONAL_PERIODS = \
        Set(dimen=2, initialize=new_binary_build_storage_operational_periods)

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "NEW_BINARY_BUILD_STORAGE_OPERATIONAL_PERIODS",
    )
    # Add to list of sets we'll join to get the final
    # STORAGE_OPERATIONAL_PERIODS set
    getattr(d, storage_only_capacity_type_operational_period_sets).append(
        "NEW_BINARY_BUILD_STORAGE_OPERATIONAL_PERIODS",
    )

    m.NEW_BINARY_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD = \
        Set(m.PERIODS, dimen=2,
            initialize=new_binary_build_storage_vintages_operational_in_period)

    def only_build_once_rule(mod, g, p):
        """
        Once a project is built, it cannot be built again in another vintage
        until its lifetime is expired. Said differently, in each period only
        one vintage can have a non-zero binary build decision.

        Note: this constraint could be generalized into a min and max build
        constraint if we want to allow multiple units to be built.

        :param mod:
        :param g:
        :param p:
        :return:
        """
        # Sum of all binary build decisions of vintages operational in the
        # current period should be less than or equal to 1
        return sum(
            mod.Build_Binary_Storage[g, v] for (gen, v)
            in mod.NEW_BINARY_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD[p]
            if gen == g
        ) <= 1

    m.New_Binary_Build_Storage_Only_Build_Once_Constraint = Constraint(
        m.NEW_BINARY_BUILD_STORAGE_VINTAGES,
        rule=only_build_once_rule
    )


def capacity_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the power capacity of storage project *g* in period *p*

    Note: only one vintage can have a non-zero Build_Binary_Storage variable in
    each period due to the *only_build_once_rule*.
    """
    return sum(
        mod.Build_Binary_Storage[g, v]
        * mod.binary_build_size_storage_mw[g]
        for (gen, v)
        in mod.NEW_BINARY_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD[p]
        if gen == g
    )


def energy_capacity_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the energy capacity of storage project *g* in period *p*

    Note: only one vintage can have a non-zero Build_Binary_Storage variable in
    each period due to the *only_build_once_rule*.
    """
    return sum(
        mod.Build_Binary_Storage[g, v]
        * mod.binary_build_size_storage_mwh[g]
        for (gen, v)
        in mod.NEW_BINARY_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD[p]
        if gen == g
    )


def capacity_cost_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the total annualized capacity cost of *stor_new_bin*
        project *g* in period *p*

    This function retuns the total power and energy capacity cost for
    stor_new_bin  projects in each period (sum over all vintages
    operational in current period).
    """

    return sum(
        mod.Build_Binary_Storage[g, v]
        * (mod.binary_build_size_storage_mw[g]
           * mod.new_binary_build_storage_annualized_real_cost_per_mw_yr[g, v]
           +
           mod.binary_build_size_storage_mwh[g]
           * mod.new_binary_build_storage_annualized_real_cost_per_mwh_yr[g, v])
        for (gen, v)
        in mod.NEW_BINARY_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD[p]
        if gen == g
    )


def load_module_specific_data(m, data_portal,
                              scenario_directory, subproblem, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # TODO: once we align param names and column names, we will have conflict
    #   because binary storage and generator use same build size param name
    #   in the columns.
    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage, "inputs",
                              "new_binary_build_storage_vintage_costs.tab"),
        index=m.NEW_BINARY_BUILD_STORAGE_VINTAGES,
        select=("project", "vintage", "lifetime_yrs",
                "annualized_real_cost_per_mw_yr",
                "annualized_real_cost_per_mwh_yr"),
        param=(m.lifetime_yrs_by_new_binary_build_storage_vintage,
               m.new_binary_build_storage_annualized_real_cost_per_mw_yr,
               m.new_binary_build_storage_annualized_real_cost_per_mwh_yr)
    )

    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage, "inputs",
                              "new_binary_build_storage_size.tab"),
        index=m.NEW_BINARY_BUILD_STORAGE_PROJECTS,
        select=("project", "binary_build_size_mw", "binary_build_size_mwh"),
        param=(m.binary_build_size_storage_mw, m.binary_build_size_storage_mwh)
    )


def export_module_specific_results(scenario_directory, subproblem, stage, m, d):
    """
    Export new binary build storage results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "capacity_stor_new_bin.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "technology", "load_zone",
                         "new_build_binary", "new_build_mw", "new_build_mwh"])
        for (prj, p) in m.NEW_BINARY_BUILD_STORAGE_VINTAGES:
            writer.writerow([
                prj,
                p,
                m.technology[prj],
                m.load_zone[prj],
                value(m.Build_Binary_Storage[prj, p]),
                value(m.Build_Binary_Storage[prj, p] *
                      m.binary_build_size_storage_mw[prj]),
                value(m.Build_Binary_Storage[prj, p] *
                      m.binary_build_size_storage_mwh[prj])
            ])


def operational_periods_by_storage_vintage(mod, prj, v):
    return operational_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"), vintage=v,
        lifetime=mod.lifetime_yrs_by_new_binary_build_storage_vintage[prj, v])


def new_binary_build_storage_operational_periods(mod):
    return project_operational_periods(
        project_vintages_set=mod.NEW_BINARY_BUILD_STORAGE_VINTAGES,
        operational_periods_by_project_vintage_set=
        mod.OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_STORAGE_VINTAGE
    )


def new_binary_build_storage_vintages_operational_in_period(mod, p):
    return project_vintages_operational_in_period(
        project_vintage_set=mod.NEW_BINARY_BUILD_STORAGE_VINTAGES,
        operational_periods_by_project_vintage_set=
        mod.OPERATIONAL_PERIODS_BY_NEW_BINARY_BUILD_STORAGE_VINTAGE,
        period=p
    )


def summarize_module_specific_results(
    scenario_directory, subproblem, stage, summary_results_file
):
    """
    Summarize new build storage capacity results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param summary_results_file:
    :return:
    """

    # Get the results CSV as dataframe
    capacity_results_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "results", "capacity_stor_new_bin.csv")
    )

    capacity_results_agg_df = capacity_results_df.groupby(
        by=["load_zone", "technology", 'period'],
        as_index=True
    ).sum()

    # Set the formatting of float to be readable
    pd.options.display.float_format = "{:,.0f}".format
    # Get all technologies with new build storage power OR energy capacity
    new_build_df = pd.DataFrame(
        capacity_results_agg_df[
            (capacity_results_agg_df["new_build_mw"] > 0) |
            (capacity_results_agg_df["new_build_mwh"] > 0)
        ][["new_build_mw", "new_build_mwh"]]
    )
    new_build_df.columns =["New Binary Storage Power Capacity (MW)",
                           "New Binary Storage Energy Capacity (MWh)"]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> New Binary Storage Capacity <--\n")
        if new_build_df.empty:
            outfile.write("No new storage was built.\n")
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
    new_stor_costs = c1.execute(
        """
        SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr * 1000 as annualized_real_cost_per_kw_yr,
        annualized_real_cost_per_kwh_yr * 1000 as 
        annualized_real_cost_per_kwh_yr
        FROM inputs_project_portfolios
        
        CROSS JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE temporal_scenario_id = {}) as relevant_periods
        
        INNER JOIN
            (SELECT project, period, lifetime_yrs,
            annualized_real_cost_per_kw_yr, annualized_real_cost_per_kwh_yr
            FROM inputs_project_new_cost
            WHERE project_new_cost_scenario_id = {}) as cost
        USING (project, period)
        
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 'stor_new_bin'
        ;""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    c2 = conn.cursor()
    new_stor_build_size = c2.execute(
        """SELECT project, binary_build_size_mw, binary_build_size_mwh
        FROM inputs_project_portfolios

        INNER JOIN
            (SELECT project, binary_build_size_mw, binary_build_size_mwh
            FROM inputs_project_new_binary_build_size
            WHERE project_new_binary_build_size_scenario_id = {})
        USING (project)

        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 'stor_new_bin';""".format(
            subscenarios.PROJECT_NEW_BINARY_BUILD_SIZE_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    return new_stor_costs, new_stor_build_size


def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # TODO: check that there are no minimum duration inputs for this type
    #   (duration is specified by specifying the build size in mw and mwh)
    #   Maybe also check all other required / not required inputs?
    #   --> see example in must_run operational_type. Seems very verbose and
    #   hard to maintain. Is there a way to generalize this?

    c = conn.cursor()
    validation_results = []

    # Get the binary build generator inputs
    new_stor_costs, new_stor_build_size = \
        get_module_specific_inputs_from_database(
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
        AND capacity_type = 'stor_new_bin';""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    # Convert input data into pandas DataFrame
    cost_df = pd.DataFrame(
        data=new_stor_costs.fetchall(),
        columns=[s[0] for s in new_stor_costs.description]
    )

    bld_size_df = pd.DataFrame(
        data=new_stor_build_size.fetchall(),
        columns=[s[0] for s in new_stor_build_size.description]
    )

    # get the project lists
    projects = [p[0] for p in prj_periods]  # will have duplicates if >1 periods
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
             "inputs_project_new_cost",
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
             "inputs_project_new_cost",
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

    # Check that all binary new build storage projects have costs specified
    # for each period
    validation_errors = validate_costs(cost_df, prj_periods)
    for error in validation_errors:
        validation_results.append(
            (subscenarios.SCENARIO_ID,
             subproblem,
             stage,
             __name__,
             "PROJECT_NEW_COST_SCENARIO_ID",
             "inputs_project_new_cost",
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
    new_binary_build_storage_vintage_costs.tab file and the
    new_binary_build_storage_size.tab file
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    new_stor_costs, new_stor_build_size = \
        get_module_specific_inputs_from_database(
            subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory,
                           "new_binary_build_storage_vintage_costs.tab"),
              "w",
              newline="") as \
            new_storage_costs_tab_file:
        writer = csv.writer(new_storage_costs_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["project", "vintage", "lifetime_yrs",
             "annualized_real_cost_per_mw_yr",
             "annualized_real_cost_per_mwh_yr"]
        )

        for row in new_stor_costs:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    with open(os.path.join(inputs_directory,
                           "new_binary_build_storage_size.tab"), "w", newline="") as \
            new_build_size_tab_file:
        writer = csv.writer(new_build_size_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["project", "binary_build_size_mw", "binary_build_size_mwh"]
        )

        for row in new_stor_build_size:
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
    # Capacity results
    print("project new binary build storage")
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_capacity_stor_new_bin",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "capacity_stor_new_bin.csv"), "r") as \
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
            new_build_mwh = row[6]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 technology, load_zone, new_build_binary,
                 new_build_mw, new_build_mwh)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_capacity_stor_new_bin{}
        (scenario_id, project, period, subproblem_id, stage_id,
        technology, load_zone, new_build_binary, new_build_mw, new_build_mwh)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""".format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_capacity_stor_new_bin
        (scenario_id, project, period, subproblem_id, stage_id, 
        technology, load_zone, new_build_binary, new_build_mw, new_build_mwh)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        technology, load_zone, new_build_binary, new_build_mw, new_build_mwh
        FROM temp_results_project_capacity_stor_new_bin{}
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
