# Copyright 2016-2023 Blue Marble Analytics LLC.
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
Relative capacity of project pairs.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Constraint, NonNegativeReals, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import get_required_subtype_modules_from_projects_file
from gridpath.project.capacity.common_functions import (
    load_project_capacity_type_modules,
)
from gridpath.auxiliary.db_interface import setup_results_import
import gridpath.project.capacity.capacity_types as cap_type_init


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS`                        |
    |                                                                         |
    | A 3-dimensional set of project-project-period combinations for which    |
    | there may be a relative capacity requirement.                           |
    +-------------------------------------------------------------------------+

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`min_relative_capacity_limit_new`                               |
    | | *Defined over*: :code:`RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS`        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The minimum amount of (new) capacity for project 1 must be >= this      |
    | parameter times the (new) capacity of project 2 in this period.         |
    +-------------------------------------------------------------------------+
    | | :code:`max_relative_capacity_limit_new`                               |
    | | *Defined over*: :code:`RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS`        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`inf`                                                |
    |                                                                         |
    | The maximum amount of (new) capacity for project 1 must be <= this      |
    | parameter times the (new) capacity of project 2 in this period.         |
    +-------------------------------------------------------------------------+
    | | :code:`min_relative_capacity_limit_total`                             |
    | | *Defined over*: :code:`RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS`        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The minimum amount of (total) capacity for project 1 must be >= this    |
    | parameter times the (total) capacity of project 2 in this period.       |
    +-------------------------------------------------------------------------+
    | | :code:`max_relative_capacity_limit_total`                             |
    | | *Defined over*: :code:`RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS`        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`inf`                                                |
    |                                                                         |
    | The maximum amount of (total) capacity for project 1 must be <= this    |
    | parameter times the (total) capacity of project 2 in this period.       |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`Min_Relative_New_Capacity_Limit_in_Period_Constraint`          |
    | | *Defined over*: :code:`RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS`        |
    |                                                                         |
    | Provides a lower limit on the amount of new capacity for a based on the |
    | new capacity of another project.                                        |
    +-------------------------------------------------------------------------+
    | | :code:`Max_Relative_New_Capacity_Limit_in_Period_Constraint`          |
    | | *Defined over*: :code:`RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS`        |
    |                                                                         |
    | Provides an upper limit on the amount of new capacity for a based on    |
    | the (new) capacity of another project.                                  |
    +-------------------------------------------------------------------------+
    | | :code:`Min_Relative_Total_Capacity_Limit_in_Period_Constraint`        |
    | | *Defined over*: :code:`RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS`        |
    |                                                                         |
    | Provides a lower limit on the amount of total capacity for a based on   |
    | the total capacity of another project.                                  |
    +-------------------------------------------------------------------------+
    | | :code:`Max_Relative_New_Capacity_Limit_in_Period_Constraint`          |
    | | *Defined over*: :code:`RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS`        |
    |                                                                         |
    | Provides a upper limit on the amount of total capacity for a based on   |
    | the total capacity of another project.                                  |
    +-------------------------------------------------------------------------+
    """

    # Sets
    m.RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS = Set(dimen=3)

    # Params
    m.min_relative_capacity_limit_new = Param(
        m.RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS, within=NonNegativeReals, default=0
    )
    m.max_relative_capacity_limit_new = Param(
        m.RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS,
        within=NonNegativeReals,
        default=float("inf"),
    )

    m.min_relative_capacity_limit_total = Param(
        m.RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS, within=NonNegativeReals, default=0
    )
    m.max_relative_capacity_limit_total = Param(
        m.RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS,
        within=NonNegativeReals,
        default=float("inf"),
    )

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

    # Get the new and total capacity in the group for the respective
    # expressions
    def project_new_capacity(mod, prj, prd):
        cap_type = mod.capacity_type[prj]
        # The capacity type modules check if this period is a "vintage" for
        # this project and return 0 if not
        if hasattr(imported_capacity_modules[cap_type], "new_capacity_rule"):
            return imported_capacity_modules[cap_type].new_capacity_rule(mod, prj, prd)
        else:
            return cap_type_init.new_capacity_rule(mod, prj, prd)

    def project_total_capacity(mod, prj, prd):
        cap_type = mod.capacity_type[prj]
        # Return the capacity type's capacity rule if the project is
        # operational in this timepoint; otherwise, return 0
        if prd not in mod.OPR_PRDS_BY_PRJ[prj]:
            return 0
        else:
            if hasattr(imported_capacity_modules[cap_type], "capacity_rule"):
                return imported_capacity_modules[cap_type].capacity_rule(mod, prj, prd)
            else:
                return cap_type_init.capacity_rule(mod, prj, prd)

    # Constraints
    # Limit the min and max amount of new and total capacity based on another
    # project in a given period
    def new_capacity_min_rule(mod, prj, prj_for_limit, prd):
        if mod.min_relative_capacity_limit_new[prj, prj_for_limit, prd] == 0:
            return Constraint.Feasible
        else:
            return project_new_capacity(
                mod, prj, prd
            ) >= mod.min_relative_capacity_limit_new[
                prj, prj_for_limit, prd
            ] * project_new_capacity(
                mod, prj_for_limit, prd
            )

    m.Min_Relative_New_Capacity_Limit_in_Period_Constraint = Constraint(
        m.RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS, rule=new_capacity_min_rule
    )

    def new_capacity_max_rule(mod, prj, prj_for_limit, prd):
        if mod.max_relative_capacity_limit_new[prj, prj_for_limit, prd] == float("inf"):
            return Constraint.Feasible
        else:
            return project_new_capacity(
                mod, prj, prd
            ) <= mod.max_relative_capacity_limit_new[
                prj, prj_for_limit, prd
            ] * project_new_capacity(
                mod, prj_for_limit, prd
            )

    m.Max_Relative_New_Capacity_Limit_in_Period_Constraint = Constraint(
        m.RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS, rule=new_capacity_max_rule
    )

    # Limit the min and max amount of total capacity in a period based on
    # another project
    def total_capacity_min_rule(mod, prj, prj_for_limit, prd):
        if mod.min_relative_capacity_limit_total[prj, prj_for_limit, prd] == 0:
            return Constraint.Feasible
        else:
            return project_total_capacity(
                mod, prj, prd
            ) >= mod.min_relative_capacity_limit_total[
                prj, prj_for_limit, prd
            ] * project_total_capacity(
                mod, prj_for_limit, prd
            )

    m.Min_Relative_Total_Capacity_Limit_in_Period_Constraint = Constraint(
        m.RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS, rule=total_capacity_min_rule
    )

    def total_capacity_max_rule(mod, prj, prj_for_limit, prd):
        if mod.max_relative_capacity_limit_total[prj, prj_for_limit, prd] == float(
            "inf"
        ):
            return Constraint.Feasible
        else:
            return project_total_capacity(
                mod, prj, prd
            ) <= mod.max_relative_capacity_limit_total[
                prj, prj_for_limit, prd
            ] * project_total_capacity(
                mod, prj_for_limit, prd
            )

    m.Max_Relative_Total_Capacity_Limit_in_Period_Constraint = Constraint(
        m.RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS, rule=total_capacity_max_rule
    )


# Input-Output
###############################################################################


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """ """
    # Only load data if the input files were written; otehrwise, we won't
    # initialize the components in this module

    req_file = os.path.join(
        scenario_directory,
        subproblem,
        stage,
        "inputs",
        "project_relative_capacity_requirements.tab",
    )
    if os.path.exists(req_file):
        data_portal.load(
            filename=req_file,
            index=m.RELATIVE_CAPACITY_PROJECT_PAIR_PERIODS,
            param=(
                m.min_relative_capacity_limit_new,
                m.max_relative_capacity_limit_new,
                m.min_relative_capacity_limit_total,
                m.max_relative_capacity_limit_total,
            ),
        )


# Database
###############################################################################


def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()
    rel_cap = c.execute(
        f"""
        SELECT project, project_for_limits, period,
        min_relative_capacity_limit_new, max_relative_capacity_limit_new,
        min_relative_capacity_limit_total, max_relative_capacity_limit_total
        FROM inputs_project_relative_capacity_requirements
        WHERE project_relative_capacity_requirement_scenario_id = 
        {subscenarios.PROJECT_RELATIVE_CAPACITY_REQUIREMENT_SCENARIO_ID}
        """
    )

    return rel_cap


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """ """
    rel_cap = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    # Write the input files only if a subscenario is specified
    if subscenarios.PROJECT_RELATIVE_CAPACITY_REQUIREMENT_SCENARIO_ID != "NULL":
        with open(
            os.path.join(
                scenario_directory,
                str(subproblem),
                str(stage),
                "inputs",
                "project_relative_capacity_requirements.tab",
            ),
            "w",
            newline="",
        ) as req_file:
            writer = csv.writer(req_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                [
                    "project",
                    "project_for_limits",
                    "period",
                    "min_relative_capacity_limit_new",
                    "max_relative_capacity_limit_new",
                    "min_relative_capacity_limit_total",
                    "max_relative_capacity_limit_total",
                ]
            )

            for row in rel_cap:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)
