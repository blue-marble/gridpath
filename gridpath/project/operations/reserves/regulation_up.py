# Copyright 2016-2023 Blue Marble Analytics LLC.
# Copyright 2026 Sylvan Energy Analytics LLC
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
Add project-level components for upward regulation reserves
"""

from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.auxiliary.dynamic_components import headroom_variables
from gridpath.project.operations.reserves.reserve_provision import (
    generic_record_dynamic_components,
    generic_add_model_components,
    generic_load_model_data,
    generic_export_results,
    generic_import_results_into_database,
    generic_get_inputs_from_database,
    generic_validate_project_bas,
    generic_write_model_inputs,
    project_bas_input_file_name,
)

# Reserve-module variables
MODULE_NAME = "regulation_up"
# Dynamic components
HEADROOM_OR_FOOTROOM_DICT_NAME = headroom_variables
# Inputs
PROJECT_BAS_INPUT_FILE_NAME = project_bas_input_file_name(MODULE_NAME)
RESERVE_PROVISION_DERATE_COLUMN_NAME_IN_INPUT_FILE = "regulation_up_derate"
RESERVE_BALANCING_AREAS_INPUT_FILE_NAME = "regulation_up_balancing_areas.tab"
# Model components
RESERVE_PROVISION_VARIABLE_NAME = "Provide_Regulation_Up_MW"
RESERVE_PROVISION_BY_BA_VARIABLE_NAME = "Provide_Regulation_Up_by_BA_MW"
RESERVE_PROVISION_DERATE_PARAM_NAME = "regulation_up_derate"
RESERVE_MAX_FRACTION_PARAM_NAME = "regulation_up_max_fraction_of_provision"
RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME = "regulation_up_reserve_to_energy_adjustment"
RESERVE_PROJECTS_SET_NAME = "REGULATION_UP_PROJECTS"
RESERVE_PRJ_BAS_SET_NAME = "REGULATION_UP_PRJ_BAS"
RESERVE_BAS_BY_PRJ_SET_NAME = "REGULATION_UP_BAS_BY_PRJ"
RESERVE_PRJS_BY_BA_SET_NAME = "REGULATION_UP_PRJS_BY_BA"
RESERVE_MULTI_BA_PRJS_SET_NAME = "REGULATION_UP_MULTI_BA_PRJS"
RESERVE_MULTI_BA_PRJ_BA_OPR_TMPS_SET_NAME = "REGULATION_UP_MULTI_BA_PRJ_BA_OPR_TMPS"
RESERVE_BALANCING_AREAS_SET_NAME = "REGULATION_UP_ZONES"
RESERVE_PRJ_OPR_TMPS_SET_NAME = "REGULATION_UP_PRJ_OPR_TMPS"
RESERVE_BA_ALLOCATION_CONSTRAINT_NAME = "Regulation_Up_BA_Allocation_Constraint"
RESERVE_MAX_FRACTION_CONSTRAINT_NAME = "Regulation_Up_Max_Fraction_to_BA_Constraint"


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
        project_bas_input_file=PROJECT_BAS_INPUT_FILE_NAME,
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME,
        reserve_provision_derate_param_name=RESERVE_PROVISION_DERATE_PARAM_NAME,
        reserve_to_energy_adjustment_param_name=RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME,
        reserve_bas_by_project_set_name=RESERVE_BAS_BY_PRJ_SET_NAME,
        reserve_provision_by_ba_variable_name=RESERVE_PROVISION_BY_BA_VARIABLE_NAME,
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
        reserve_prj_bas_set=RESERVE_PRJ_BAS_SET_NAME,
        reserve_bas_by_prj_set=RESERVE_BAS_BY_PRJ_SET_NAME,
        reserve_prjs_by_ba_set=RESERVE_PRJS_BY_BA_SET_NAME,
        reserve_multi_ba_prjs_set=RESERVE_MULTI_BA_PRJS_SET_NAME,
        reserve_multi_ba_prj_ba_opr_tmps_set=RESERVE_MULTI_BA_PRJ_BA_OPR_TMPS_SET_NAME,
        reserve_max_fraction_param=RESERVE_MAX_FRACTION_PARAM_NAME,
        reserve_provision_derate_param=RESERVE_PROVISION_DERATE_PARAM_NAME,
        reserve_balancing_areas_set=RESERVE_BALANCING_AREAS_SET_NAME,
        reserve_project_operational_timepoints_set=RESERVE_PRJ_OPR_TMPS_SET_NAME,
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME,
        reserve_provision_by_ba_variable_name=RESERVE_PROVISION_BY_BA_VARIABLE_NAME,
        reserve_ba_allocation_constraint=RESERVE_BA_ALLOCATION_CONSTRAINT_NAME,
        reserve_max_fraction_constraint=RESERVE_MAX_FRACTION_CONSTRAINT_NAME,
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
        project_bas_input_file=PROJECT_BAS_INPUT_FILE_NAME,
        derate_column_name=RESERVE_PROVISION_DERATE_COLUMN_NAME_IN_INPUT_FILE,
        reserve_prj_bas_set=RESERVE_PRJ_BAS_SET_NAME,
        reserve_max_fraction_param=RESERVE_MAX_FRACTION_PARAM_NAME,
        reserve_provision_derate_param=RESERVE_PROVISION_DERATE_PARAM_NAME,
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
    Export project-level results for upward regulation reserves
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
        reserve_bas_by_prj_set=RESERVE_BAS_BY_PRJ_SET_NAME,
        reserve_multi_ba_prj_ba_opr_tmps_set=RESERVE_MULTI_BA_PRJ_BA_OPR_TMPS_SET_NAME,
        reserve_provision_by_ba_variable_name=RESERVE_PROVISION_BY_BA_VARIABLE_NAME,
        reserve_max_fraction_param=RESERVE_MAX_FRACTION_PARAM_NAME,
        reserve_max_fraction_constraint=RESERVE_MAX_FRACTION_CONSTRAINT_NAME,
    )


def import_results_into_database(
    scenario_id,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    c,
    db,
    results_directory,
    quiet,
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    generic_import_results_into_database(
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        c=c,
        db=db,
        results_directory=results_directory,
        quiet=quiet,
        module_name=MODULE_NAME,
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

    # Get project BAs
    project_bas, prj_derates = generic_get_inputs_from_database(
        scenario_id=scenario_id,
        subscenarios=subscenarios,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        conn=conn,
        reserve_type=MODULE_NAME,
        project_ba_subscenario_id=subscenarios.PROJECT_REGULATION_UP_BA_SCENARIO_ID,
        ba_subscenario_id=subscenarios.REGULATION_UP_BA_SCENARIO_ID,
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
        reserve_type=MODULE_NAME,
        project_ba_subscenario_id=subscenarios.PROJECT_REGULATION_UP_BA_SCENARIO_ID,
        ba_subscenario_id=subscenarios.REGULATION_UP_BA_SCENARIO_ID,
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
    Get inputs from database and write out the model input files: the
    project-BA map to its own file and the derate column into projects.tab.
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

    generic_write_model_inputs(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        reserve_type=MODULE_NAME,
        project_bas=project_bas,
        prj_derates=prj_derates,
        derate_column_name=RESERVE_PROVISION_DERATE_COLUMN_NAME_IN_INPUT_FILE,
    )
