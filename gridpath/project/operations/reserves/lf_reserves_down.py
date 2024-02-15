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
Add project-level components for downward load-following reserves
"""
import csv
import os.path

from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.auxiliary.dynamic_components import footroom_variables
from gridpath.project.operations.reserves.reserve_provision import (
    generic_record_dynamic_components,
    generic_add_model_components,
    generic_load_model_data,
    generic_export_results,
    generic_get_inputs_from_database,
    generic_validate_project_bas,
)

# Reserve-module variables
MODULE_NAME = "lf_reserves_down"
# Dynamic components
HEADROOM_OR_FOOTROOM_DICT_NAME = footroom_variables
# Inputs
BA_COLUMN_NAME_IN_INPUT_FILE = "lf_reserves_down_ba"
RESERVE_PROVISION_DERATE_COLUMN_NAME_IN_INPUT_FILE = "lf_reserves_down_derate"
RESERVE_BALANCING_AREAS_INPUT_FILE_NAME = "load_following_down_balancing_areas.tab"
# Model components
RESERVE_PROVISION_VARIABLE_NAME = "Provide_LF_Reserves_Down_MW"
RESERVE_PROVISION_DERATE_PARAM_NAME = "lf_reserves_down_derate"
RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME = (
    "lf_reserves_down_reserve_to_energy_adjustment"
)
RESERVE_BALANCING_AREA_PARAM_NAME = "lf_reserves_down_zone"
RESERVE_PROJECTS_SET_NAME = "LF_RESERVES_DOWN_PROJECTS"
RESERVE_BALANCING_AREAS_SET_NAME = "LF_RESERVES_DOWN_ZONES"
RESERVE_PRJ_OPR_TMPS_SET_NAME = "LF_RESERVES_DOWN_PRJ_OPR_TMPS"


def record_dynamic_components(
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    generic_record_dynamic_components(
        d=d,
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        headroom_or_footroom_dict=HEADROOM_OR_FOOTROOM_DICT_NAME,
        ba_column_name=BA_COLUMN_NAME_IN_INPUT_FILE,
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME,
        reserve_provision_derate_param_name=RESERVE_PROVISION_DERATE_PARAM_NAME,
        reserve_to_energy_adjustment_param_name=RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME,
        reserve_balancing_area_param_name=RESERVE_BALANCING_AREA_PARAM_NAME,
    )


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

    record_dynamic_components(
        d,
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
    )

    generic_add_model_components(
        m=m,
        d=d,
        reserve_projects_set=RESERVE_PROJECTS_SET_NAME,
        reserve_balancing_area_param=RESERVE_BALANCING_AREA_PARAM_NAME,
        reserve_provision_derate_param=RESERVE_PROVISION_DERATE_PARAM_NAME,
        reserve_balancing_areas_set=RESERVE_BALANCING_AREAS_SET_NAME,
        reserve_project_operational_timepoints_set=RESERVE_PRJ_OPR_TMPS_SET_NAME,
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME,
        reserve_to_energy_adjustment_param=RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME,
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
    generic_load_model_data(
        m=m,
        d=d,
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        ba_column_name=BA_COLUMN_NAME_IN_INPUT_FILE,
        derate_column_name=RESERVE_PROVISION_DERATE_COLUMN_NAME_IN_INPUT_FILE,
        reserve_balancing_area_param=RESERVE_BALANCING_AREA_PARAM_NAME,
        reserve_provision_derate_param=RESERVE_PROVISION_DERATE_PARAM_NAME,
        reserve_projects_set=RESERVE_PROJECTS_SET_NAME,
        reserve_to_energy_adjustment_param=RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME,
        reserve_balancing_areas_input_file=RESERVE_BALANCING_AREAS_INPUT_FILE_NAME,
    )


def export_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
    d,
):
    """
    Export project-level results for downward load-following
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    generic_export_results(
        m=m,
        d=d,
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        module_name=MODULE_NAME,
        reserve_project_operational_timepoints_set=RESERVE_PRJ_OPR_TMPS_SET_NAME,
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME,
        reserve_ba_param_name=RESERVE_BALANCING_AREA_PARAM_NAME,
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
    # Get project BA
    project_bas, prj_derates = generic_get_inputs_from_database(
        scenario_id=scenario_id,
        subscenarios=subscenarios,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        conn=conn,
        reserve_type="lf_reserves_down",
        project_ba_subscenario_id=subscenarios.PROJECT_LF_RESERVES_DOWN_BA_SCENARIO_ID,
        ba_subscenario_id=subscenarios.LF_RESERVES_DOWN_BA_SCENARIO_ID,
    )

    return project_bas, prj_derates


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

    generic_validate_project_bas(
        scenario_id=scenario_id,
        subscenarios=subscenarios,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        conn=conn,
        reserve_type="lf_reserves_down",
        project_ba_subscenario_id=subscenarios.PROJECT_LF_RESERVES_DOWN_BA_SCENARIO_ID,
        ba_subscenario_id=subscenarios.LF_RESERVES_DOWN_BA_SCENARIO_ID,
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

    project_bas, prj_derates = get_inputs_from_database(
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
    prj_ba_dict = dict()
    for prj, ba in project_bas:
        prj_ba_dict[str(prj)] = "." if ba is None else str(ba)

    # Make a dict for easy access
    prj_derate_dict = dict()
    for prj, derate in prj_derates:
        prj_derate_dict[str(prj)] = "." if derate is None else str(derate)

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
        header.append("lf_reserves_down_ba")
        header.append("lf_reserves_down_derate")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_ba_dict.keys()):
                row.append(prj_ba_dict[row[0]])
            # If project not specified, specify no BA
            else:
                row.append(".")

            # If project specified, check if derate specified or not
            if row[0] in list(prj_derate_dict.keys()):
                row.append(prj_derate_dict[row[0]])
            # If project not specified, specify no derate
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
