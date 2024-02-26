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

from gridpath.auxiliary.auxiliary import get_required_subtype_modules
from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.project.capacity.common_functions import (
    load_project_capacity_type_modules,
)
import gridpath.project.capacity.capacity_types as cap_type_init


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`REL_CAP_PRJ_PRD`                                               |
    |                                                                         |
    | A 2-dimensional set of project-period combinations for which there      |
    | may be a relative capacity requirement.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`PRJS_FOR_REL_CAP_LIMIT`                                        |
    | | *Defined over*: :code:`REL_CAP_PRJ_PRD`                               |
    |                                                                         |
    | List of projects who capacity counts toward the limit for each project- |
    | period with a limit.                                                    |
    +-------------------------------------------------------------------------+

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`min_relative_capacity_limit_new`                               |
    | | *Defined over*: :code:`REL_CAP_PRJ_PRD`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The minimum amount of (new) capacity for project 1 must be >= this      |
    | parameter times the (new) capacity of project 2 in this period.         |
    +-------------------------------------------------------------------------+
    | | :code:`max_relative_capacity_limit_new`                               |
    | | *Defined over*: :code:`REL_CAP_PRJ_PRD`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`inf`                                                |
    |                                                                         |
    | The maximum amount of (new) capacity for project 1 must be <= this      |
    | parameter times the (new) capacity of project 2 in this period.         |
    +-------------------------------------------------------------------------+
    | | :code:`min_relative_capacity_limit_total`                             |
    | | *Defined over*: :code:`REL_CAP_PRJ_PRD`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The minimum amount of (total) capacity for project 1 must be >= this    |
    | parameter times the (total) capacity of project 2 in this period.       |
    +-------------------------------------------------------------------------+
    | | :code:`max_relative_capacity_limit_total`                             |
    | | *Defined over*: :code:`REL_CAP_PRJ_PRD`                               |
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
    | | *Defined over*: :code:`REL_CAP_PRJ_PRD`                               |
    |                                                                         |
    | Provides a lower limit on the amount of new capacity for a based on the |
    | new capacity of another project.                                        |
    +-------------------------------------------------------------------------+
    | | :code:`Max_Relative_New_Capacity_Limit_in_Period_Constraint`          |
    | | *Defined over*: :code:`REL_CAP_PRJ_PRD`                               |
    |                                                                         |
    | Provides an upper limit on the amount of new capacity for a based on    |
    | the (new) capacity of another project.                                  |
    +-------------------------------------------------------------------------+
    | | :code:`Min_Relative_Total_Capacity_Limit_in_Period_Constraint`        |
    | | *Defined over*: :code:`REL_CAP_PRJ_PRD`                               |
    |                                                                         |
    | Provides a lower limit on the amount of total capacity for a based on   |
    | the total capacity of another project.                                  |
    +-------------------------------------------------------------------------+
    | | :code:`Max_Relative_New_Capacity_Limit_in_Period_Constraint`          |
    | | *Defined over*: :code:`REL_CAP_PRJ_PRD`                               |
    |                                                                         |
    | Provides a upper limit on the amount of total capacity for a based on   |
    | the total capacity of another project.                                  |
    +-------------------------------------------------------------------------+
    """

    # Sets
    m.REL_CAP_PRJ_PRD = Set(dimen=2)

    m.PRJS_FOR_REL_CAP_LIMIT = Set(m.REL_CAP_PRJ_PRD, within=m.PROJECTS)

    # Params
    m.min_relative_capacity_limit_new = Param(
        m.REL_CAP_PRJ_PRD, within=NonNegativeReals, default=0
    )
    m.max_relative_capacity_limit_new = Param(
        m.REL_CAP_PRJ_PRD,
        within=NonNegativeReals,
        default=float("inf"),
    )

    m.min_relative_capacity_limit_total = Param(
        m.REL_CAP_PRJ_PRD, within=NonNegativeReals, default=0
    )
    m.max_relative_capacity_limit_total = Param(
        m.REL_CAP_PRJ_PRD,
        within=NonNegativeReals,
        default=float("inf"),
    )

    # Import needed capacity type modules
    required_capacity_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
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
    def new_capacity_min_rule(mod, prj, prd):
        if mod.min_relative_capacity_limit_new[prj, prd] == 0:
            return Constraint.Feasible
        else:
            return project_new_capacity(
                mod, prj, prd
            ) >= mod.min_relative_capacity_limit_new[prj, prd] * sum(
                project_new_capacity(mod, prj_for_limit, prd)
                for prj_for_limit in mod.PRJS_FOR_REL_CAP_LIMIT[prj, prd]
            )

    m.Min_Relative_New_Capacity_Limit_in_Period_Constraint = Constraint(
        m.REL_CAP_PRJ_PRD, rule=new_capacity_min_rule
    )

    def new_capacity_max_rule(mod, prj, prd):
        if mod.max_relative_capacity_limit_new[prj, prd] == float("inf"):
            return Constraint.Feasible
        else:
            return project_new_capacity(
                mod, prj, prd
            ) <= mod.max_relative_capacity_limit_new[prj, prd] * sum(
                project_new_capacity(mod, prj_for_limit, prd)
                for prj_for_limit in mod.PRJS_FOR_REL_CAP_LIMIT[prj, prd]
            )

    m.Max_Relative_New_Capacity_Limit_in_Period_Constraint = Constraint(
        m.REL_CAP_PRJ_PRD, rule=new_capacity_max_rule
    )

    # Limit the min and max amount of total capacity in a period based on
    # another project
    def total_capacity_min_rule(mod, prj, prd):
        if mod.min_relative_capacity_limit_total[prj, prd] == 0:
            return Constraint.Feasible
        else:
            return project_total_capacity(
                mod, prj, prd
            ) >= mod.min_relative_capacity_limit_total[prj, prd] * sum(
                project_total_capacity(mod, prj_for_limit, prd)
                for prj_for_limit in mod.PRJS_FOR_REL_CAP_LIMIT[prj, prd]
            )

    m.Min_Relative_Total_Capacity_Limit_in_Period_Constraint = Constraint(
        m.REL_CAP_PRJ_PRD, rule=total_capacity_min_rule
    )

    def total_capacity_max_rule(mod, prj, prd):
        if mod.max_relative_capacity_limit_total[prj, prd] == float("inf"):
            return Constraint.Feasible
        else:
            return project_total_capacity(
                mod, prj, prd
            ) <= mod.max_relative_capacity_limit_total[prj, prd] * sum(
                project_total_capacity(mod, prj_for_limit, prd)
                for prj_for_limit in mod.PRJS_FOR_REL_CAP_LIMIT[prj, prd]
            )

    m.Max_Relative_Total_Capacity_Limit_in_Period_Constraint = Constraint(
        m.REL_CAP_PRJ_PRD, rule=total_capacity_max_rule
    )


# Input-Output
###############################################################################


def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """ """
    # Only load data if the input files were written; otehrwise, we won't
    # initialize the components in this module

    req_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "project_relative_capacity_requirements.tab",
    )

    map_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "project_relative_capacity_requirements_map.tab",
    )

    if os.path.exists(req_file):
        data_portal.load(
            filename=req_file,
            index=m.REL_CAP_PRJ_PRD,
            param=(
                m.min_relative_capacity_limit_new,
                m.max_relative_capacity_limit_new,
                m.min_relative_capacity_limit_total,
                m.max_relative_capacity_limit_total,
            ),
        )

    if os.path.exists(map_file):
        df = pd.read_csv(map_file, delimiter="\t")
        mapping = (
            df.set_index(["project", "period"])
            .groupby(["project", "period"])["project_for_limit"]
            .apply(list)
            .to_dict()
        )
        data_portal.data()["PRJS_FOR_REL_CAP_LIMIT"] = mapping


# Database
###############################################################################


def get_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c1 = conn.cursor()
    rel_cap = c1.execute(
        f"""
        SELECT project, period,
        min_relative_capacity_limit_new, max_relative_capacity_limit_new,
        min_relative_capacity_limit_total, max_relative_capacity_limit_total
        FROM inputs_project_relative_capacity_requirements
        WHERE project_relative_capacity_requirement_scenario_id = 
        {subscenarios.PROJECT_RELATIVE_CAPACITY_REQUIREMENT_SCENARIO_ID}
        """
    )

    c2 = conn.cursor()
    map = c2.execute(
        f"""
        SELECT project, period, project_for_limits
        FROM inputs_project_relative_capacity_requirements
        JOIN inputs_project_relative_capacity_requirements_map
        USING (project, prj_for_lim_map_id)
        WHERE project_relative_capacity_requirement_scenario_id = 
        {subscenarios.PROJECT_RELATIVE_CAPACITY_REQUIREMENT_SCENARIO_ID}
        """
    )

    return rel_cap, map


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """ """

    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    rel_cap, map = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    # Write the input files only if a subscenario is specified
    if subscenarios.PROJECT_RELATIVE_CAPACITY_REQUIREMENT_SCENARIO_ID != "NULL":
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
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

        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "project_relative_capacity_requirements_map.tab",
            ),
            "w",
            newline="",
        ) as map_file:
            writer = csv.writer(map_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(["project", "period", "project_for_limit"])

            for row in map:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)
