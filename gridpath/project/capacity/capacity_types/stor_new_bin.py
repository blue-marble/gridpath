#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This capacity type describes new storage projects that can be built by the
optimization at a pre-specified size, duration and cost. The model can
decide to build the project at the specified size in some or all investment
*periods*, or not at all. Once built, the capacity remains available for the
duration of the project's pre-specified lifetime.

The cost input to the model is an annualized cost per unit of power capacity
(MW) and an annualized cost per unit energy capacity (MWh). Both costs are
additive. If the optimization makes the decision to build new
power/energy capacity, the total annualized cost is incurred in each period
of the study (and multiplied by the number of years the period represents)
for the duration of the project's lifetime. Annual fixed O&M costs are also
incurred by binary new-build storage.
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
    project_vintages_operational_in_period, update_capacity_results_table


def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`STOR_NEW_BIN`                                                  |
    |                                                                         |
    | The list of projects of capacity type :code:`stor_new_bin`.             |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_NEW_BIN_VNTS`                                             |
    |                                                                         |
    | A two-dimensional set of project-vintage combinations to describe the   |
    | periods in time when storage capacity/energy can be built in the        |
    | optimization.                                                           |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`stor_new_bin_lifetime_yrs`                                     |
    | | *Defined over*: :code:`STOR_NEW_BIN_VNTS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's lifetime, i.e. how long project capacity/energy of a      |
    | particular vintage remains operational.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`stor_new_bin_annualized_real_cost_per_mw_yr`                   |
    | | *Defined over*: :code:`STOR_NEW_BIN_VNTS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's cost to build new power capacity in annualized real       |
    | dollars in per MW.                                                      |
    +-------------------------------------------------------------------------+
    | | :code:`stor_new_bin_annualized_real_cost_per_mwh_yr`                  |
    | | *Defined over*: :code:`STOR_NEW_BIN_VNTS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's cost to build new energy capacity in annualized real      |
    | dollars in per MW.                                                      |
    +-------------------------------------------------------------------------+
    | | :code:`stor_new_bin_build_size_mw`                                    |
    | | *Defined over*: :code:`STOR_NEW_BIN`                                  |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's specified power capacity build size in MW. The model can  |
    | only build the project in this pre-specified size.                      |
    +-------------------------------------------------------------------------+
    | | :code:`stor_new_bin_build_size_mwh`                                   |
    | | *Defined over*: :code:`STOR_NEW_BIN`                                  |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's specified energy capacity build size in MWh. The model    |
    | can only build the project in this pre-specified size.                  |
    +-------------------------------------------------------------------------+

    .. note:: The cost input to the model is a levelized cost per unit
        capacity/energy. This annualized cost is incurred in each period of
        the study (and multiplied by the number of years the period
        represents) for the duration of the project's lifetime. It is up to
        the user to ensure that the
        :code:`stor_new_bin_lifetime_yrs`,
        :code:`stor_new_bin_annualized_real_cost_per_mw_yr`, and
        :code:`stor_new_bin_annualized_real_cost_per_mwh_yr' parameters are
        consistent.

    +-------------------------------------------------------------------------+
    | Derived Sets                                                            |
    +=========================================================================+
    | | :code:`OPR_PRDS_BY_STOR_NEW_BIN_VINTAGE`                              |
    | | *Defined over*: :code:`STOR_NEW_BIN_VNTS`                             |
    |                                                                         |
    | Indexed set that describes the operational periods for each possible    |
    | project-vintage combination, based on the                               |
    | :code:`stor_new_bin_lifetime_yrs`. For instance, capacity of 2020       |
    | vintage with lifetime of 30 years will be assumed operational starting  |
    | Jan 1, 2020 and through Dec 31, 2049, but will *not* be operational     |
    | in 2050.                                                                |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_NEW_BIN_OPR_PRDS`                                         |
    |                                                                         |
    | Two-dimensional set that includes the periods when project capacity of  |
    | any vintage *could* be operational if built. This set is added to the   |
    | list of sets to join to get the final                                   |
    | :code:`PROJECT_OPERATIONAL_PERIODS` set defined in                      |
    | **gridpath.project.capacity.capacity**.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_NEW_BIN_VNTS_OPR_IN_PRD`                                  |
    | | *Defined over*: :code:`PERIODS`                                       |
    |                                                                         |
    | Indexed set that describes the project-vintages that could be           |
    | operational in each period based on the                                 |
    | :code:`stor_new_bin_lifetime_yrs`.                                      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`StorNewBin_Build`                                              |
    | | *Defined over*: :code:`STOR_NEW_BIN_VNTS`                             |
    | | *Within*: :code:`Binary`                                              |
    |                                                                         |
    | Binary build decision for each project-vintage combination (1=build).   |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`StorNewBin_Only_Build_Once_Constraint`                         |
    | | *Defined over*: :code:`STOR_NEW_BIN_OPR_PRDS`                         |
    |                                                                         |
    | Once a project is built, it cannot be built again in another vintage    |
    | until its lifetime is expired.                                          |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.STOR_NEW_BIN = Set()

    m.STOR_NEW_BIN_VNTS = Set(
        dimen=2, within=m.STOR_NEW_BIN*m.PERIODS
    )

    # Required Params
    ###########################################################################

    m.stor_new_bin_lifetime_yrs = Param(
        m.STOR_NEW_BIN_VNTS,
        within=NonNegativeReals
    )

    m.stor_new_bin_annualized_real_cost_per_mw_yr = Param(
        m.STOR_NEW_BIN_VNTS,
        within=NonNegativeReals
    )

    m.stor_new_bin_annualized_real_cost_per_mwh_yr = Param(
        m.STOR_NEW_BIN_VNTS,
        within=NonNegativeReals
    )

    m.stor_new_bin_build_size_mw = Param(
        m.STOR_NEW_BIN,
        within=NonNegativeReals
    )

    m.stor_new_bin_build_size_mwh = Param(
        m.STOR_NEW_BIN,
        within=NonNegativeReals
    )

    # Derived Sets
    ###########################################################################

    m.OPR_PRDS_BY_STOR_NEW_BIN_VINTAGE = Set(
        m.STOR_NEW_BIN_VNTS,
        initialize=operational_periods_by_storage_vintage
    )

    m.STOR_NEW_BIN_OPR_PRDS = Set(
        dimen=2,
        initialize=stor_new_bin_operational_periods
    )

    m.STOR_NEW_BIN_VNTS_OPR_IN_PRD = Set(
        m.PERIODS, dimen=2,
        initialize=stor_new_bin_vintages_operational_in_period
    )

    # Variables
    ###########################################################################

    m.StorNewBin_Build = Var(
        m.STOR_NEW_BIN_VNTS,
        within=Binary
    )

    # Constraints
    ###########################################################################

    m.StorNewBin_Only_Build_Once_Constraint = Constraint(
        m.STOR_NEW_BIN_OPR_PRDS,
        rule=only_build_once_rule
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "STOR_NEW_BIN_OPR_PRDS",
    )
    # Add to list of sets we'll join to get the final
    # STORAGE_OPERATIONAL_PERIODS set
    getattr(d, storage_only_capacity_type_operational_period_sets).append(
        "STOR_NEW_BIN_OPR_PRDS",
    )


# Set Rules
###############################################################################

def operational_periods_by_storage_vintage(mod, prj, v):
    return operational_periods_by_project_vintage(
        periods=mod.PERIODS,
        vintage=v,
        lifetime=mod.stor_new_bin_lifetime_yrs[prj, v])


def stor_new_bin_operational_periods(mod):
    return project_operational_periods(
        project_vintages_set=mod.STOR_NEW_BIN_VNTS,
        operational_periods_by_project_vintage_set=
        mod.OPR_PRDS_BY_STOR_NEW_BIN_VINTAGE
    )


def stor_new_bin_vintages_operational_in_period(mod, p):
    return project_vintages_operational_in_period(
        project_vintage_set=mod.STOR_NEW_BIN_VNTS,
        operational_periods_by_project_vintage_set=
        mod.OPR_PRDS_BY_STOR_NEW_BIN_VINTAGE,
        period=p
    )


# Constraint Formulation Rules
###############################################################################

def only_build_once_rule(mod, g, p):
    """
    **Constraint Name**: StorNewBin_Only_Build_Once_Constraint
    **Enforced Over**: STOR_NEW_BIN_OPR_PRDS

    Once a project is built, it cannot be built again in another vintage
    until its lifetime is expired. Said differently, in each period only
    one vintage can have a non-zero binary build decision.

    Note: this constraint could be generalized into a min and max build
    constraint if we want to allow multiple units to be built.
    """
    # Sum of all binary build decisions of vintages operational in the
    # current period should be less than or equal to 1
    return sum(
        mod.StorNewBin_Build[g, v] for (gen, v)
        in mod.STOR_NEW_BIN_VNTS_OPR_IN_PRD[p]
        if gen == g
    ) <= 1


# Capacity Type Methods
###############################################################################

def capacity_rule(mod, g, p):
    """
    The power capacity of a new storage project in a given operational
    period is equal to the sum of all binary build decisions of vintages
    operational in that period multiplied with the power capacity size.

    Note: only one vintage can have a non-zero StorNewBin_Build variable in
    each period due to the *only_build_once_rule*.
    """
    return sum(
        mod.StorNewBin_Build[g, v]
        * mod.stor_new_bin_build_size_mw[g]
        for (gen, v)
        in mod.STOR_NEW_BIN_VNTS_OPR_IN_PRD[p]
        if gen == g
    )


def energy_capacity_rule(mod, g, p):
    """
    The energy capacity of a new storage project in a given operational
    period is equal to the sum of all binary build decisions of vintages
    operational in that period multiplied with the energy capacity size.

    Note: only one vintage can have a non-zero StorNewBin_Build variable in
    each period due to the *only_build_once_rule*.
    """
    return sum(
        mod.StorNewBin_Build[g, v]
        * mod.stor_new_bin_build_size_mwh[g]
        for (gen, v)
        in mod.STOR_NEW_BIN_VNTS_OPR_IN_PRD[p]
        if gen == g
    )


def capacity_cost_rule(mod, g, p):
    """
    The capacity cost for new storage projects in a given period is the
    capacity-build of a particular vintage times the annualized power cost for
    that vintage plus the energy-build of the same vintages times the
    annualized energy cost for that vintage, summed over all vintages
    operational in the period. Note that power and energy costs are additive.
    """

    return sum(
        mod.StorNewBin_Build[g, v]
        * (mod.stor_new_bin_build_size_mw[g]
           * mod.stor_new_bin_annualized_real_cost_per_mw_yr[g, v]
           + mod.stor_new_bin_build_size_mwh[g]
           * mod.stor_new_bin_annualized_real_cost_per_mwh_yr[g, v])
        for (gen, v)
        in mod.STOR_NEW_BIN_VNTS_OPR_IN_PRD[p]
        if gen == g
    )


# Input-Output
###############################################################################

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
        index=m.STOR_NEW_BIN_VNTS,
        select=("project", "vintage", "lifetime_yrs",
                "annualized_real_cost_per_mw_yr",
                "annualized_real_cost_per_mwh_yr"),
        param=(m.stor_new_bin_lifetime_yrs,
               m.stor_new_bin_annualized_real_cost_per_mw_yr,
               m.stor_new_bin_annualized_real_cost_per_mwh_yr)
    )

    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage, "inputs",
                              "new_binary_build_storage_size.tab"),
        index=m.STOR_NEW_BIN,
        select=("project", "binary_build_size_mw", "binary_build_size_mwh"),
        param=(m.stor_new_bin_build_size_mw, m.stor_new_bin_build_size_mwh)
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
        for (prj, p) in m.STOR_NEW_BIN_VNTS:
            writer.writerow([
                prj,
                p,
                m.technology[prj],
                m.load_zone[prj],
                value(m.StorNewBin_Build[prj, p]),
                value(m.StorNewBin_Build[prj, p] *
                      m.stor_new_bin_build_size_mw[prj]),
                value(m.StorNewBin_Build[prj, p] *
                      m.stor_new_bin_build_size_mwh[prj])
            ])


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
              "w", newline="") as new_storage_costs_tab_file:
        writer = csv.writer(new_storage_costs_tab_file, delimiter="\t", lineterminator="\n")

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
                           "new_binary_build_storage_size.tab"),
              "w", newline="") as new_build_size_tab_file:
        writer = csv.writer(new_build_size_tab_file, delimiter="\t", lineterminator="\n")

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

    update_capacity_results_table(
        db=db, c=c, results_directory=results_directory,
        scenario_id=scenario_id, subproblem=subproblem, stage=stage,
        results_file="capacity_stor_new_bin.csv"
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

    # TODO: check that there are no minimum duration inputs for this type
    #   (duration is specified by specifying the build size in mw and mwh)
    #   Maybe also check all other required / not required inputs?
    #   --> see example in gen_must_run operational_type. Seems very verbose and
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
