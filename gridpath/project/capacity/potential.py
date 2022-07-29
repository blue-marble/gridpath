# Copyright 2016-2022 Blue Marble Analytics LLC.
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
Constraints on the minimum and maximum capacity build by vintage and the minimum and
maximum cumulative capacity by period.
"""

import csv
import os.path
from pyomo.environ import Param, Constraint, NonNegativeReals, Expression

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    validate_row_monotonicity,
    validate_column_monotonicity,
)
from gridpath.auxiliary.auxiliary import get_required_subtype_modules_from_projects_file
from gridpath.project.capacity.common_functions import (
    load_project_capacity_type_modules,
)
import gridpath.project.capacity.capacity_types as cap_type_init


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`min_new_build_power`                                           |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The minimum amount of power capacity for a project to be built in a     |
    | certain period.                                                         |
    +-------------------------------------------------------------------------+
    | | :code:`max_new_build_power`                                           |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`Infinity`                                           |
    |                                                                         |
    | The maximum amount of power capacity for a project to be built in a     |
    | certain period.                                                         |
    +-------------------------------------------------------------------------+
    | | :code:`min_capacity_power`                                            |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The minimum amount of power capacity for a project in a certain period. |
    +-------------------------------------------------------------------------+
    | | :code:`max_capacity_power`                                            |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`Infinity`                                           |
    |                                                                         |
    | The maximum amount of power capacity for a project in a certain period. |
    +-------------------------------------------------------------------------+
    | | :code:`min_new_build_energy`                                          |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The minimum amount of energy capacity for a project to be built in a    |
    | certain period.                                                         |
    +-------------------------------------------------------------------------+
    | | :code:`max_new_build_energy`                                          |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`Infinity`                                           |
    |                                                                         |
    | The maximum amount of energy capacity for a project to be built in a    |
    | certain period.                                                         |
    +-------------------------------------------------------------------------+
    | | :code:`min_capacity_energy`                                           |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The minimum amount of energy capacity for a project in a certain period.|
    +-------------------------------------------------------------------------+
    | | :code:`max_capacity_energy`                                           |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`Infinity`                                           |
    |                                                                         |
    | The maximum amount of energy capacity for a project in a certain period.|
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`Min_Build_Power_Constraint`                                    |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    |                                                                         |
    | Ensures that certain amount of power capacity must be built in a        |
    | particular period, based on :code:`min_new_build_power`.                |
    +-------------------------------------------------------------------------+
    | | :code:`Max_Build_Power_Constraint`                                    |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    |                                                                         |
    | Limits the amount of power capacity that can be built in a particular   |
    | period based on :code:`max_new_build_power`.                            |
    +-------------------------------------------------------------------------+
    | | :code:`Min_Power_Constraint`                                          |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    |                                                                         |
    | Ensures that certain amount of power capacity must exist in a certain   |
    | period, based on :code:`min_capacity_power`.                            |
    +-------------------------------------------------------------------------+
    | | :code:`Max_Power_Constraint`                                          |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    |                                                                         |
    | Limits the amount of power capacity that can exist in a certain period, |
    | based on :code:`max_capacity_power`.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`Min_Build_Energy_Constraint`                                   |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    |                                                                         |
    | Ensures that certain amount of energy capacity must be built in a       |
    | particular period, based on :code:`min_new_build_energy`.               |
    +-------------------------------------------------------------------------+
    | | :code:`Max_Build_Energy_Constraint`                                   |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    |                                                                         |
    | Limits the amount of energy capacity that can be built in a particular  |
    | period based on :code:`max_new_build_energy`.                           |
    +-------------------------------------------------------------------------+
    | | :code:`Min_Energy_Constraint`                                         |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    |                                                                         |
    | Ensures that certain amount of energy capacity must exist in a certain  |
    | period, based on :code:`min_capacity_energy`.                           |
    +-------------------------------------------------------------------------+
    | | :code:`Max_Energy_Constraint`                                         |
    | | *Defined over*: :code:`PROJECTS`, :code:`PERIODS`                     |
    |                                                                         |
    | Limits the amount of energy capacity that can exist in a certain        |
    | period, based on :code:`max_capacity_energy`.                           |
    +-------------------------------------------------------------------------+


    """
    # Import needed capacity type modules
    required_capacity_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        which_type="capacity_type",
    )

    imported_capacity_modules = load_project_capacity_type_modules(
        required_capacity_modules
    )

    def new_capacity_rule(mod, prj, prd):
        cap_type = mod.capacity_type[prj]
        # The capacity type modules check if this period is a "vintage" for
        # this project and return 0 if not
        if hasattr(imported_capacity_modules[cap_type], "new_capacity_rule"):
            return imported_capacity_modules[cap_type].new_capacity_rule(mod, prj, prd)
        else:
            return cap_type_init.new_capacity_rule(mod, prj, prd)

    def new_energy_capacity_rule(mod, prj, prd):
        cap_type = mod.capacity_type[prj]
        # The capacity type modules check if this period is a "vintage" for
        # this project and return 0 if not
        if hasattr(imported_capacity_modules[cap_type], "new_energy_capacity_rule"):
            return imported_capacity_modules[cap_type].new_energy_capacity_rule(
                mod, prj, prd
            )
        else:
            return cap_type_init.new_energy_capacity_rule(mod, prj, prd)

    # Optional Params
    ###########################################################################

    m.min_new_build_power = Param(
        m.PROJECTS, m.PERIODS, within=NonNegativeReals, default=0
    )

    m.max_new_build_power = Param(
        m.PROJECTS,
        m.PERIODS,
        within=NonNegativeReals,
        default=float("inf"),
    )

    m.min_capacity_power = Param(
        m.PROJECTS,
        m.PERIODS,
        within=NonNegativeReals,
        default=0,
    )

    m.max_capacity_power = Param(
        m.PROJECTS,
        m.PERIODS,
        within=NonNegativeReals,
        default=float("inf"),
    )

    m.min_new_build_energy = Param(
        m.PROJECTS, m.PERIODS, within=NonNegativeReals, default=0
    )

    m.max_new_build_energy = Param(
        m.PROJECTS,
        m.PERIODS,
        within=NonNegativeReals,
        default=float("inf"),
    )

    m.min_capacity_energy = Param(
        m.PROJECTS,
        m.PERIODS,
        within=NonNegativeReals,
        default=0,
    )

    m.max_capacity_energy = Param(
        m.PROJECTS,
        m.PERIODS,
        within=NonNegativeReals,
        default=float("inf"),
    )

    # Constraints
    ###########################################################################

    # Power capacity
    def min_build_capacity_rule(mod, prj, prd):
        """
        **Constraint Name**: Min_Build_Power_Constraint
        **Enforced Over**: m.PROJECTS, m.PERIODS

        Must build a certain amount of capacity in period.
        """
        if mod.min_new_build_power[prj, prd] == 0:
            return Constraint.Skip
        else:
            return new_capacity_rule(mod, prj, prd) >= mod.min_new_build_power[prj, prd]

    m.Min_Build_Power_Constraint = Constraint(
        m.PROJECTS, m.PERIODS, rule=min_build_capacity_rule
    )

    def max_build_capacity_rule(mod, prj, prd):
        """
        **Constraint Name**: Max_Build_Power_Constraint
        **Enforced Over**: m.PROJECTS, m.PERIODS

        Can't build more than certain amount of capacity in period.
        """
        if mod.max_new_build_power[prj, prd] == float("inf"):
            return Constraint.Skip
        return new_capacity_rule(mod, prj, prd) <= mod.max_new_build_power[prj, prd]

    m.Max_Build_Power_Constraint = Constraint(
        m.PROJECTS, m.PERIODS, rule=max_build_capacity_rule
    )

    def min_capacity_rule(mod, prj, prd):
        """
        **Constraint Name**: Min_Power_Constraint
        **Enforced Over**: m.PROJECTS, m.PERIOD

        Must have a certain amount of capacity in period.
        """
        if mod.min_capacity_power[prj, prd] == 0:
            return Constraint.Skip
        else:
            return mod.Capacity_MW[prj, prd] >= mod.min_capacity_power[prj, prd]

    m.Min_Power_Constraint = Constraint(m.PROJECTS, m.PERIODS, rule=min_capacity_rule)

    def max_capacity_rule(mod, prj, prd):
        """
        **Constraint Name**: Max_Power_Constraint
        **Enforced Over**: m.PROJECTS, m.PERIOD

        Can't have more than certain amount of capacity in period.
        """
        if mod.max_capacity_power[prj, prd] == float("inf"):
            return Constraint.Skip
        return mod.Capacity_MW[prj, prd] <= mod.max_capacity_power[prj, prd]

    m.Max_Power_Constraint = Constraint(m.PROJECTS, m.PERIODS, rule=max_capacity_rule)

    # Energy capacity (for storage)
    def min_build_energy_rule(mod, prj, prd):
        """
        **Constraint Name**: Min_Build_Energy_Constraint
        **Enforced Over**: m.PROJECTS, m.PERIODS

        Must build a certain amount of energy capacity in period.
        """
        if mod.min_new_build_energy[prj, prd] == 0:
            return Constraint.Skip
        else:
            return (
                new_energy_capacity_rule(mod, prj, prd)
                >= mod.min_new_build_energy[prj, prd]
            )

    m.Min_Build_Energy_Constraint = Constraint(
        m.PROJECTS, m.PERIODS, rule=min_build_energy_rule
    )

    def max_build_energy_rule(mod, prj, prd):
        """
        **Constraint Name**: Max_Build_Energy_Constraint
        **Enforced Over**: m.PROJECTS, m.PERIODS

        Can't build more than certain amount of energy capacity in period.
        """
        if mod.max_new_build_energy[prj, prd] == float("inf"):
            return Constraint.Skip
        return (
            new_energy_capacity_rule(mod, prj, prd)
            <= mod.max_new_build_energy[prj, prd]
        )

    m.Max_Build_Energy_Constraint = Constraint(
        m.PROJECTS, m.PERIODS, rule=max_build_energy_rule
    )

    def min_energy_rule(mod, prj, prd):
        """
        **Constraint Name**: Min_Energy_Constraint
        **Enforced Over**: m.PROJECTS, m.PERIOD

        Must have a certain amount of energy capacity in period.
        """
        if mod.min_capacity_energy[prj, prd] == 0:
            return Constraint.Skip
        else:
            return (
                mod.Energy_Capacity_MWh[prj, prd] >= mod.min_capacity_energy[prj, prd]
            )

    m.Min_Energy_Constraint = Constraint(m.PROJECTS, m.PERIODS, rule=min_energy_rule)

    def max_energy_rule(mod, prj, prd):
        """
        **Constraint Name**: Max_Energy_Constraint
        **Enforced Over**: m.PROJECTS, m.PERIOD

        Can't have more than certain amount of energy capacity in period.
        """
        if mod.max_capacity_energy[prj, prd] == float("inf"):
            return Constraint.Skip
        return mod.Energy_Capacity_MWh[prj, prd] <= mod.max_capacity_energy[prj, prd]

    m.Max_Energy_Constraint = Constraint(m.PROJECTS, m.PERIODS, rule=max_energy_rule)


# Input-Output
###############################################################################


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    potentials_file = os.path.join(
        scenario_directory,
        str(subproblem),
        str(stage),
        "inputs",
        "new_build_potentials.tab",
    )
    if os.path.exists(potentials_file):
        data_portal.load(
            filename=potentials_file,
            param=(
                m.min_new_build_power,
                m.max_new_build_power,
                m.min_capacity_power,
                m.max_capacity_power,
                m.min_new_build_energy,
                m.max_new_build_energy,
                m.min_capacity_energy,
                m.max_capacity_energy,
            ),
        )


# Database
###############################################################################


def get_model_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()

    potentials = c.execute(
        """SELECT project, period, min_new_build_power, max_new_build_power,
            min_capacity_power, max_capacity_power,
            min_new_build_energy, max_new_build_energy,
            min_capacity_energy, max_capacity_energy
            FROM inputs_project_portfolios
            CROSS JOIN
            (SELECT period
            FROM inputs_temporal_periods
            WHERE temporal_scenario_id = {temporal}) as relevant_vintages
            INNER JOIN (
            SELECT project, period, min_new_build_power, max_new_build_power,
            min_capacity_power, max_capacity_power,
            min_new_build_energy, max_new_build_energy,
            min_capacity_energy, max_capacity_energy
            FROM inputs_project_new_potential
            WHERE project_new_potential_scenario_id = {potential}) as potential
            USING (project, period)
            WHERE project_portfolio_scenario_id = {portfolio}
            """.format(
            temporal=subscenarios.TEMPORAL_SCENARIO_ID,
            potential=subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID,
            portfolio=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        )
    )

    return potentials


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    new_build_generator_vintage_costs.tab file
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    potentials = [
        row
        for row in get_model_inputs_from_database(
            scenario_id, subscenarios, subproblem, stage, conn
        ).fetchall()
    ]

    if not potentials:
        pass
    else:
        with open(
            os.path.join(
                scenario_directory,
                str(subproblem),
                str(stage),
                "inputs",
                "new_build_potentials.tab",
            ),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                [
                    "project",
                    "period",
                    "min_new_build_power",
                    "max_new_build_power",
                    "min_capacity_power",
                    "max_capacity_power",
                    "min_new_build_energy",
                    "max_new_build_energy",
                    "min_capacity_energy",
                    "max_capacity_energy",
                ]
            )

            for row in potentials:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)


# Validation
###############################################################################


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    potentials = get_model_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    # Convert input data into pandas DataFrame
    potentials_df = cursor_to_df(potentials)
    df_cols = potentials_df.columns

    cols = [
        "min_new_build_power",
        "max_new_build_power",
        "min_capacity_power",
        "max_capacity_power",
    ]
    # Check that maximum new build doesn't decrease
    if cols[1] in df_cols:
        write_validation_to_database(
            conn=conn,
            scenario_id=scenario_id,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table="inputs_project_new_potential",
            severity="Mid",
            errors=validate_row_monotonicity(
                df=potentials_df, col=cols[1], rank_col="period"
            ),
        )

    # check that min build <= max build
    if set(cols).issubset(set(df_cols)):
        write_validation_to_database(
            conn=conn,
            scenario_id=scenario_id,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table="inputs_project_new_potential",
            severity="High",
            errors=validate_column_monotonicity(
                df=potentials_df, cols=cols, idx_col=["project", "period"]
            ),
        )

    cols = ["min_capacity_energy", "max_capacity_energy"]
    # Check that maximum new build doesn't decrease - MWh
    if cols[1] in df_cols:
        write_validation_to_database(
            conn=conn,
            scenario_id=scenario_id,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table="inputs_project_new_potential",
            severity="Mid",
            errors=validate_row_monotonicity(
                df=potentials_df, col=cols[1], rank_col="period"
            ),
        )

    # check that min build <= max build - MWh
    if set(cols).issubset(set(df_cols)):
        write_validation_to_database(
            conn=conn,
            scenario_id=scenario_id,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table="inputs_project_new_potential",
            severity="High",
            errors=validate_column_monotonicity(
                df=potentials_df, cols=cols, idx_col=["project", "period"]
            ),
        )
