# Copyright 2016-2020 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This capacity type describes new generation projects that can be built by the
optimization at a pre-specified size and cost. The model can decide to build
the project at the specified size in some or all investment *periods*, or not
at all. Once built, the capacity remains available for the duration of the
project's pre-specified lifetime.

The cost input to the model is an annualized cost per unit capacity. If the
optimization makes the decision to build new capacity, the total annualized
cost is incurred in each period of the study (and multiplied by the number
of years the period represents) for the duration of the project's lifetime.
Annual fixed O&M costs are also incurred by binary new-build generation.
"""

from __future__ import print_function

from builtins import str
import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, NonNegativeReals, Binary, \
    Constraint, value

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets
from gridpath.auxiliary.validations import write_validation_to_database, \
    validate_values, get_expected_dtypes, get_projects, validate_dtypes, \
    validate_idxs
from gridpath.project.capacity.capacity_types.common_methods import \
    operational_periods_by_project_vintage, project_operational_periods, \
    project_vintages_operational_in_period, update_capacity_results_table


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_NEW_BIN`                                                   |
    |                                                                         |
    | Two-dimensional set of project-vintage combinations to describe all     |
    | possible project-vintage combinations for projects with a cumulative    |
    | minimum build capacity specified.                                       |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_NEW_BIN_VNTS`                                              |
    |                                                                         |
    | A two-dimensional set of project-vintage combinations to describe the   |
    | periods in time when project capacity can be built in the optimization. |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_new_bin_lifetime_yrs_by_vintage`                           |
    | | *Defined over*: :code:`GEN_NEW_BIN_VNTS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's lifetime, i.e. how long project capacity of a particular  |
    | vintage remains operational.                                            |
    +-------------------------------------------------------------------------+
    | | :code:`gen_new_bin_annualized_real_cost_per_mw_yr`                    |
    | | *Defined over*: :code:`GEN_NEW_BIN_VNTS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's cost to build new capacity in annualized real dollars per |
    | MW.                                                                     |
    +-------------------------------------------------------------------------+
    | | :code:`gen_new_bin_build_size_mw`                                     |
    | | *Defined over*: :code:`GEN_NEW_BIN`                                   |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's specified build size in MW. The model can only build the  |
    | project in this pre-specified size.                                     |
    +-------------------------------------------------------------------------+

    .. note:: The cost input to the model is a levelized cost per unit
        capacity. This annualized cost is incurred in each period of the study
        (and multiplied by the number of years the period represents) for
        the duration of the project's lifetime. It is up to the user to
        ensure that the :code:`gen_new_bin_lifetime_yrs_by_vintage` and
        :code:`gen_new_bin_annualized_real_cost_per_mw_yr` parameters are
        consistent.

    +-------------------------------------------------------------------------+
    | Derived Sets                                                            |
    +=========================================================================+
    | | :code:`OPR_PRDS_BY_GEN_NEW_BIN_VINTAGE`                               |
    | | *Defined over*: :code:`GEN_NEW_BIN_VNTS`                              |
    |                                                                         |
    | Indexed set that describes the operational periods for each possible    |
    | project-vintage combination, based on the                               |
    | :code:`gen_new_bin_lifetime_yrs_by_vintage`. For instance, capacity of  |
    | the 2020 vintage with lifetime of 30 years will be assumed operational  |
    | starting Jan 1, 2020 and through Dec 31, 2049, but will *not* be        |
    | operational in 2050.                                                    |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_NEW_BIN_OPR_PRDS`                                          |
    |                                                                         |
    | Two-dimensional set that includes the periods when project capacity of  |
    | any vintage *could* be operational if built. This set is added to the   |
    | list of sets to join to get the final :code:`PRJ_OPR_PRDS` set defined  |
    | in **gridpath.project.capacity.capacity**.                              |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_NEW_BIN_VNTS_OPR_IN_PERIOD`                                |
    | | *Defined over*: :code:`PERIODS`                                       |
    |                                                                         |
    | Indexed set that describes the project-vintages that could be           |
    | operational in each period based on the                                 |
    | :code:`gen_new_bin_lifetime_yrs_by_vintage`.                            |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`GenNewBin_Build`                                               |
    | | *Defined over*: :code:`GEN_NEW_BIN_VNTS`                              |
    | | *Within*: :code:`Binary`                                              |
    |                                                                         |
    | Binary build decision for each project-vintage combination (1=build).   |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`GenNewBin_Only_Build_Once_Constraint`                          |
    | | *Defined over*: :code:`GEN_NEW_BIN_OPR_PRDS`                          |
    |                                                                         |
    | Once a project is built, it cannot be built again in another vintage    |
    | until its lifetime is expired.                                          |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.GEN_NEW_BIN = Set(
        within=m.PROJECTS
    )

    m.GEN_NEW_BIN_VNTS = Set(
        dimen=2, within=m.PROJECTS*m.PERIODS
    )

    # Required Params
    ###########################################################################

    m.gen_new_bin_lifetime_yrs_by_vintage = Param(
        m.GEN_NEW_BIN_VNTS,
        within=NonNegativeReals
    )

    m.gen_new_bin_annualized_real_cost_per_mw_yr = Param(
        m.GEN_NEW_BIN_VNTS,
        within=NonNegativeReals
    )

    m.gen_new_bin_build_size_mw = Param(
        m.GEN_NEW_BIN,
        within=NonNegativeReals
    )

    # Derived Sets
    ###########################################################################

    m.OPR_PRDS_BY_GEN_NEW_BIN_VINTAGE = Set(
        m.GEN_NEW_BIN_VNTS,
        initialize=operational_periods_by_generator_vintage
    )

    m.GEN_NEW_BIN_OPR_PRDS = Set(
        dimen=2,
        initialize=gen_new_bin_operational_periods
    )

    m.GEN_NEW_BIN_VNTS_OPR_IN_PERIOD = Set(
        m.PERIODS, dimen=2,
        initialize=gen_new_bin_vintages_operational_in_period
    )

    # Variables
    ###########################################################################

    m.GenNewBin_Build = Var(
        m.GEN_NEW_BIN_VNTS,
        within=Binary
    )

    # Constraints
    ###########################################################################

    m.GenNewBin_Only_Build_Once_Constraint = Constraint(
        m.GEN_NEW_BIN_OPR_PRDS,
        rule=only_build_once_rule
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "GEN_NEW_BIN_OPR_PRDS",
    )


# Set Rules
###############################################################################

def operational_periods_by_generator_vintage(mod, prj, v):
    return operational_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"), vintage=v,
        lifetime=mod.gen_new_bin_lifetime_yrs_by_vintage[prj, v]
    )


def gen_new_bin_operational_periods(mod):
    return project_operational_periods(
        project_vintages_set=mod.GEN_NEW_BIN_VNTS,
        operational_periods_by_project_vintage_set=
        mod.OPR_PRDS_BY_GEN_NEW_BIN_VINTAGE
    )


def gen_new_bin_vintages_operational_in_period(mod, p):
    return project_vintages_operational_in_period(
        project_vintage_set=mod.GEN_NEW_BIN_VNTS,
        operational_periods_by_project_vintage_set=
        mod.OPR_PRDS_BY_GEN_NEW_BIN_VINTAGE,
        period=p
    )


# Constraint Formulation Rules
###############################################################################

def only_build_once_rule(mod, g, p):
    """
    **Constraint Name**: GenNewBin_Only_Build_Once_Constraint
    **Enforced Over**: GEN_NEW_BIN_OPR_PRDS

    Once a project is built, it cannot be built again in another vintage
    until its lifetime is expired. We sum all binary build decisions of
    vintages operational in the current period and limit this to be less
    than or equal than 1.

    Note: this constraint could be generalized into a min and max build
    constraint if we want to allow multiple units to be built.
    """

    return sum(
        mod.GenNewBin_Build[g, v] for (gen, v)
        in mod.GEN_NEW_BIN_VNTS_OPR_IN_PERIOD[p]
        if gen == g
    ) <= 1


# Capacity Type Methods
###############################################################################

def capacity_rule(mod, g, p):
    """
    The capacity of a new generator project in a given operational period
    is equal to the sum of all binary build decisions of vintages
    operational in that period multiplied with the build capacity size.

    Note: only one vintage can have a non-zero GenNewBin_Build variable in each
    period due to the *only_build_once_rule*.
    """

    return sum(
        mod.GenNewBin_Build[g, v]
        * mod.gen_new_bin_build_size_mw[g]
        for (gen, v) in mod.GEN_NEW_BIN_VNTS_OPR_IN_PERIOD[p]
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
    The capacity cost for new-build generators in a given period is the
    capacity-build of a particular vintage times the annualized cost for
    that vintage summed over all vintages operational in the period.
    """
    return sum(
        mod.GenNewBin_Build[g, v]
        * mod.gen_new_bin_build_size_mw[g]
        * mod.gen_new_bin_annualized_real_cost_per_mw_yr[g, v]
        for (gen, v) in mod.GEN_NEW_BIN_VNTS_OPR_IN_PERIOD[p]
        if gen == g
    )


def new_capacity_rule(mod, g, p):
    """
    New capacity built at project g in period p.
    Returns 0 if we can't build capacity at this project in period p.
    """
    return mod.GenNewBin_Build[g, p] * mod.gen_new_bin_build_size_mw[g] \
        if (g, p) in mod.GEN_NEW_BIN_VNTS else 0


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

    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                              "new_binary_build_generator_vintage_costs.tab"),
        index=m.GEN_NEW_BIN_VNTS,
        select=("project", "vintage", "lifetime_yrs",
                "annualized_real_cost_per_mw_yr"),
        param=(m.gen_new_bin_lifetime_yrs_by_vintage,
               m.gen_new_bin_annualized_real_cost_per_mw_yr)
    )

    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                              "new_binary_build_generator_size.tab"),
        index=m.GEN_NEW_BIN,
        select=("project", "binary_build_size_mw"),
        param=(m.gen_new_bin_build_size_mw)
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
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "capacity_gen_new_bin.csv"),
              "w", newline="") as f:

        writer = csv.writer(f)
        writer.writerow(["project", "vintage", "technology", "load_zone",
                         "new_build_binary", "new_build_mw"])
        for (prj, v) in m.GEN_NEW_BIN_VNTS:
            writer.writerow([
                prj,
                v,
                m.technology[prj],
                m.load_zone[prj],
                value(m.GenNewBin_Build[prj, v]),
                value(m.GenNewBin_Build[prj, v] * m.gen_new_bin_build_size_mw[prj])
            ])


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
        os.path.join(scenario_directory, str(subproblem), str(stage),
                     "results", "capacity_gen_new_bin.csv")
    )

    capacity_results_agg_df = capacity_results_df.groupby(
        by=["load_zone", "technology", "vintage"],
        as_index=True
    ).sum()

    # Get all technologies with the new binary build capacity
    new_build_df = pd.DataFrame(
        capacity_results_agg_df[
            capacity_results_agg_df["new_build_mw"] > 0
        ]["new_build_mw"]
    )

    # Get the power units from the units.csv file
    units_df = pd.read_csv(os.path.join(scenario_directory, "units.csv"),
                           index_col="metric")
    power_unit = units_df.loc["power", "unit"]

    # Rename column header
    new_build_df.columns = ["New Binary Build Capacity ({})".format(
        power_unit)]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> New Binary Build Generation Capacity <--\n")
        if new_build_df.empty:
            outfile.write("No new generation was built.\n")
        else:
            new_build_df.to_string(outfile, float_format="{:,.2f}".format)
            outfile.write("\n")


# Database
###############################################################################

def get_module_specific_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c1 = conn.cursor()
    new_gen_costs = c1.execute(
        """SELECT project, vintage, lifetime_yrs,
        annualized_real_cost_per_mw_yr
        FROM inputs_project_portfolios
        
        CROSS JOIN
        (SELECT period AS vintage
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_vintages
        
        INNER JOIN
        (SELECT project, vintage, lifetime_yrs,
        annualized_real_cost_per_mw_yr
        FROM inputs_project_new_cost
        WHERE project_new_cost_scenario_id = {}) as cost
        USING (project, vintage)
        
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 'gen_new_bin';""".format(
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
        AND capacity_type = 'gen_new_bin';""".format(
            subscenarios.PROJECT_NEW_BINARY_BUILD_SIZE_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    return new_gen_costs, new_gen_build_size


def write_module_specific_model_inputs(
        scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    new_binary_build_generator_vintage_costs.tab file and the
    new_binary_build_generator_size.tab file
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    new_gen_costs, new_gen_build_size = get_module_specific_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "new_binary_build_generator_vintage_costs.tab"),
              "w", newline="") as new_gen_costs_tab_file:
        writer = csv.writer(new_gen_costs_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["project", "vintage", "lifetime_yrs",
             "annualized_real_cost_per_mw_yr"]
        )

        for row in new_gen_costs:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "new_binary_build_generator_size.tab"),
              "w", newline="") as new_build_size_tab_file:
        writer = csv.writer(new_build_size_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["project", "binary_build_size_mw"]
        )

        for row in new_gen_build_size:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


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
        print("project new binary build generator")

    update_capacity_results_table(
        db=db, c=c, results_directory=results_directory,
        scenario_id=scenario_id, subproblem=subproblem, stage=stage,
        results_file="capacity_gen_new_bin.csv"
    )


# Validation
###############################################################################

def validate_module_specific_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Get the binary build generator inputs
    new_gen_costs, new_build_size = get_module_specific_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    projects = get_projects(conn, scenario_id, subscenarios, "capacity_type", "gen_new_bin")

    # Convert input data into pandas DataFrame
    cost_df = cursor_to_df(new_gen_costs)
    bld_size_df = cursor_to_df(new_build_size)

    # get the project lists
    cost_projects = cost_df["project"].unique()
    bld_size_projects = bld_size_df["project"]

    # Get expected dtypes
    expected_dtypes = get_expected_dtypes(
        conn=conn,
        tables=["inputs_project_new_cost",
                "inputs_project_new_binary_build_size"]
    )

    # Check dtypes - cost_df
    dtype_errors, error_columns = validate_dtypes(cost_df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_new_cost",
        severity="High",
        errors=dtype_errors
    )

    # Check valid numeric columns are non-negative - cost_df
    numeric_columns = [c for c in cost_df.columns
                       if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_new_cost",
        severity="High",
        errors=validate_values(cost_df, valid_numeric_columns, min=0)
    )

    # Check dtypes - bld_size_df
    dtype_errors, error_columns = validate_dtypes(bld_size_df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_new_binary_build_size",
        severity="High",
        errors=dtype_errors
    )

    # Check valid numeric columns are non-negative - bld_size_df
    numeric_columns = [c for c in bld_size_df.columns
                       if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_new_binary_build_size",
        severity="High",
        errors=validate_values(bld_size_df, valid_numeric_columns, min=0)
    )

    # Check that all binary new build projects are available in >=1 vintage
    msg = "Expected cost data for at least one vintage."
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_new_cost",
        severity="Mid",
        errors=validate_idxs(actual_idxs=cost_projects,
                             req_idxs=projects,
                             idx_label="project",
                             msg=msg)
    )

    # Check that all binary new build projects have build size specified
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_new_binary_build_size",
        severity="High",
        errors=validate_idxs(actual_idxs=bld_size_projects,
                             req_idxs=projects,
                             idx_label="project")
    )

