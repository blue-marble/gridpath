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
This capacity type describes the power (i.e. charging and discharging
capacity) and energy capacity (i.e. duration) of storage projects that are
available to the optimization without having to incur an investment cost.
For example, it can be applied to existing storage projects or to
storage projects that will be built in the future and whose capital costs we
want to ignore (in the objective function).

It is not required to specify a capacity for all periods, i.e. a project can
be operational in some periods but not in others with no restriction on the
order and combination of periods. The user may specify a fixed O&M cost for
specified-storage projects, but this cost will be a fixed number in the
objective function and will therefore not affect any of the optimization
decisions.

"""

import csv
import os.path
from pyomo.environ import Set, Param, NonNegativeReals

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets, \
    storage_only_capacity_type_operational_period_sets
from gridpath.auxiliary.validations import get_projects, get_expected_dtypes, \
    write_validation_to_database, validate_dtypes, validate_values, \
    validate_idxs, validate_missing_inputs


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`STOR_SPEC_OPR_PRDS`                                            |
    |                                                                         |
    | Two-dimensional set of project-period combinations that helps describe  |
    | the project capacity available in a given period. This set is added to  |
    | the list of sets to join to get the final :code:`PRJ_OPR_PRDS` set      |
    | defined in **gridpath.project.capacity.capacity**.                      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`stor_spec_power_capacity_mw`                                   |
    | | *Defined over*: :code:`STOR_SPEC_OPR_PRDS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The storage project's specified power capacity (in MW) in each          |
    | operational period.                                                     |
    +-------------------------------------------------------------------------+
    | | :code:`stor_spec_energy_capacity_mwh`                                 |
    | | *Defined over*: :code:`STOR_SPEC_OPR_PRDS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The storage project's specified energy capacity (in MWh) in each        |
    | operational period.                                                     |
    +-------------------------------------------------------------------------+
    | | :code:`stor_spec_fixed_cost_per_mw_yr`                                |
    | | *Defined over*: :code:`STOR_SPEC_OPR_PRDS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The storage project's fixed cost for the power components (in $ per     |
    | MW-yr.) in each operational period. This cost will be added to the      |
    | objective function but will not affect optimization decisions.          |
    +-------------------------------------------------------------------------+
    | | :code:`stor_spec_fixed_cost_per_mwh_yr`                               |
    | | *Defined over*: :code:`STOR_SPEC_OPR_PRDS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The storage project's fixed cost for the energy components (in $ per    |
    | MWh-yr.) in each operational period. This cost will be added to the     |
    | objective function but will not affect optimization decisions.          |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.STOR_SPEC_OPR_PRDS = Set(dimen=2)

    # Required Params
    ###########################################################################

    m.stor_spec_power_capacity_mw = Param(
        m.STOR_SPEC_OPR_PRDS,
        within=NonNegativeReals
    )

    m.stor_spec_energy_capacity_mwh = Param(
        m.STOR_SPEC_OPR_PRDS,
        within=NonNegativeReals
    )

    m.stor_spec_fixed_cost_per_mw_yr = Param(
        m.STOR_SPEC_OPR_PRDS,
        within=NonNegativeReals
    )

    m.stor_spec_fixed_cost_per_mwh_yr = Param(
        m.STOR_SPEC_OPR_PRDS,
        within=NonNegativeReals
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "STOR_SPEC_OPR_PRDS",
    )

    # Add to list of sets we'll join to get the final
    # STOR_OPR_PRDS set
    getattr(d, storage_only_capacity_type_operational_period_sets).append(
        "STOR_SPEC_OPR_PRDS",
    )


# Capacity Type Methods
###############################################################################

def capacity_rule(mod, g, p):
    """
    The power capacity of projects of the *stor_spec* capacity type is a
    pre-specified number for each of the project's operational periods.
    """
    return mod.stor_spec_power_capacity_mw[g, p]


def energy_capacity_rule(mod, g, p):
    """
    The energy capacity of projects of the *stor_spec* capacity type is a
    pre-specified number for each of the project's operational periods.
    """
    return mod.stor_spec_energy_capacity_mwh[g, p]


def capacity_cost_rule(mod, g, p):
    """
    The capacity cost of projects of the *stor_spec* capacity type is a
    pre-specified number equal to the power capacity times the per-mw fixed
    cost plus the energy capacity times the per-mwh fixed cost for each of
    the project's operational periods.
    """
    return mod.stor_spec_power_capacity_mw[g, p] \
        * mod.stor_spec_fixed_cost_per_mw_yr[g, p] \
        + mod.stor_spec_energy_capacity_mwh[g, p] \
        * mod.stor_spec_fixed_cost_per_mwh_yr[g, p]


def new_capacity_rule(mod, g, p):
    """
    New capacity built at project g in period p.
    """
    return 0


# Input-Output
###############################################################################

def load_model_data(
    m, d, data_portal, scenario_directory, subproblem, stage
):
    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                              "storage_specified_capacities.tab"),
        index=m.STOR_SPEC_OPR_PRDS,
        select=("project", "period",
                "storage_specified_power_capacity_mw",
                "storage_specified_energy_capacity_mwh",
                "storage_specified_fixed_cost_per_mw_yr",
                "storage_specified_fixed_cost_per_mwh_yr"),
        param=(m.stor_spec_power_capacity_mw,
               m.stor_spec_energy_capacity_mwh,
               m.stor_spec_fixed_cost_per_mw_yr,
               m.stor_spec_fixed_cost_per_mwh_yr)
    )


# Database
###############################################################################

def get_model_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    stor_capacities = c.execute(
        """SELECT project, period, specified_capacity_mw,
        specified_capacity_mwh,
        annual_fixed_cost_per_mw_year, annual_fixed_cost_per_mwh_year
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        INNER JOIN
        (SELECT project, period, specified_capacity_mw,
        specified_capacity_mwh
        FROM inputs_project_specified_capacity
        WHERE project_specified_capacity_scenario_id = {}) as capacity
        USING (project, period)
        INNER JOIN
        (SELECT project, period,
        annual_fixed_cost_per_mw_year,
        annual_fixed_cost_per_mwh_year
        FROM inputs_project_specified_fixed_cost
        WHERE project_specified_fixed_cost_scenario_id = {}) as fixed_om
        USING (project, period)
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 
        'stor_spec';""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_SPECIFIED_FIXED_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )
    return stor_capacities


def write_model_model_inputs(
        scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    storage_specified_capacities.tab file
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    stor_capacities = get_model_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "storage_specified_capacities.tab"),
              "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["project", "period",
             "storage_specified_power_capacity_mw",
             "storage_specified_energy_capacity_mwh",
             "storage_specified_fixed_cost_per_mw_yr",
             "storage_specified_fixed_cost_per_mwh_yr"]
        )

        for row in stor_capacities:
            writer.writerow(row)


# Validation
###############################################################################

def validate_model_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    stor_spec_params = get_model_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    projects = get_projects(conn, scenario_id, subscenarios, "capacity_type", "stor_spec")

    # Convert input data into pandas DataFrame and extract data
    df = cursor_to_df(stor_spec_params)
    spec_projects = df["project"].unique()

    # Get expected dtypes
    expected_dtypes = get_expected_dtypes(
        conn=conn,
        tables=["inputs_project_specified_capacity",
                "inputs_project_specified_fixed_cost"]
    )

    # Check dtypes
    dtype_errors, error_columns = validate_dtypes(df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_specified_capacity, "
                 "inputs_project_specified_fixed_cost",
        severity="High",
        errors=dtype_errors
    )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in df.columns
                       if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_specified_capacity, "
                 "inputs_project_specified_fixed_cost",
        severity="High",
        errors=validate_values(df, valid_numeric_columns, min=0)
    )

    # Ensure project capacity & fixed cost is specified in at least 1 period
    msg = "Expected specified capacity & fixed costs for at least one period."
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_specified_capacity, "
                 "inputs_project_specified_fixed_cost",
        severity="High",
        errors=validate_idxs(actual_idxs=spec_projects,
                             req_idxs=projects,
                             idx_label="project",
                             msg=msg)
    )

    # Check for missing values (vs. missing row entries above)
    cols = ["specified_capacity_mw",
            "annual_fixed_cost_per_mw_year",
            "annual_fixed_cost_per_mwh_year"]
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_specified_capacity, "
                 "inputs_project_specified_fixed_cost",
        severity="High",
        errors=validate_missing_inputs(df, cols)
    )

