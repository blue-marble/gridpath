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
Add project-level components for spinning reserves that also
depend on operational type
"""


import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Constraint, NonNegativeReals

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.auxiliary import get_required_subtype_modules
from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.auxiliary.validations import write_validation_to_database, validate_values
from gridpath.project.operations.reserves.op_type_dependent.reserve_limits_by_op_type import (
    generic_add_model_components,
    generic_load_model_data,
)
from gridpath.project.operations.common_functions import load_operational_type_modules
import gridpath.project.operations.operational_types as op_type


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

    :param m:
    :param d:
    :return:
    """

    # Ramp rate reserve limit (response time reserve limit)
    # Some reserve products may require that generators respond within a
    # certain amount of time, e.g. 1 minute, 10 minutes, etc.
    # The maximum amount of reserves that a generator can provide is
    # therefore limited by its ramp rate, e.g. if it can ramp up 60 MW an hour,
    # then it will only be able to provide 10 MW of upward reserve for a
    # reserve product with a 10-minute response requirement \
    # Here, this derate param is specified as a fraction of generator capacity
    # Defaults to 1 if not specified
    m.inertia_reserves_inertia_constant = Param(
        m.INERTIA_RESERVES_PROJECTS, within=NonNegativeReals, default=0
    )

    # Import needed operational modules
    required_operational_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        which_type="operational_type",
    )

    imported_operational_modules = load_operational_type_modules(
        required_operational_modules
    )

    def reserve_provision_inertia_limit_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        online_capacity_for_inertia = (
            imported_operational_modules[gen_op_type].capacity_providing_inertia_rule(
                mod, g, tmp
            )
            if hasattr(
                imported_operational_modules[gen_op_type],
                "capacity_providing_inertia_rule",
            )
            else op_type.capacity_providing_inertia_rule(mod, g, tmp)
        )

        return (
            mod.Provide_Inertia_Reserves_MWs[g, tmp]
            <= mod.inertia_reserves_inertia_constant[g] * online_capacity_for_inertia
        )

    m.Inertia_Reserve_Inertia_Limit_Constraint = Constraint(
        m.INERTIA_RESERVES_PRJ_OPR_TMPS, rule=reserve_provision_inertia_limit_rule
    )


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
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    columns_to_import = ("project",)
    params_to_import = ()
    projects_file_header = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        sep="\t",
        header=None,
        nrows=1,
    ).values[0]

    # Import reserve provision ramp rate limit parameter only if
    # column is present
    # Otherwise, the ramp rate limit param goes to its default of 1
    if "inertia_constant_sec" in projects_file_header:
        columns_to_import += ("inertia_constant_sec",)
        params_to_import += (m.inertia_reserves_inertia_constant,)

    # Load the needed data
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        select=columns_to_import,
        param=params_to_import,
    )


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

    c = conn.cursor()
    # Get inertia reserve inertia constant value
    prj_iner_const = c.execute(
        """SELECT project, inertia_constant_sec
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {};""".format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID
        )
    )

    return prj_iner_const


def validate_inputs(
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
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    prj_iner_const = get_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )
    df = cursor_to_df(prj_iner_const)

    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_operational_chars",
        severity="Mid",
        errors=validate_values(df, ["inertia_constant_sec"], min=0, max=100),
    )


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
    """
    Get inputs from database and write out the model input
    projects.tab file (to be precise, amend it).
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    prj_iner_const = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    # Make a dict for easy access
    prj_iner_const_dict = dict()
    for prj, iner_const in prj_iner_const:
        prj_iner_const_dict[str(prj)] = "." if iner_const is None else str(iner_const)

    # Add params to projects file
    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        "r",
    ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t", lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("inertia_constant_sec")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if ramp rate specified or not
            if row[0] in list(prj_iner_const_dict.keys()):
                row.append(prj_iner_const_dict[row[0]])
            # If project not specified, specify no ramp rate
            else:
                row.append(".")

            # Add resulting row to new_rows list
            new_rows.append(row)

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        "w",
        newline="",
    ) as projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)
