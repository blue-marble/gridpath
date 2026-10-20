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
Add project-level components for frequency response reserves
"""

import os.path
import pandas as pd
from pyomo.environ import Set

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.auxiliary.dynamic_components import headroom_variables
from gridpath.auxiliary.validations import write_validation_to_database
from gridpath.common_functions import create_results_df, update_results_df
from gridpath.project import PROJECT_TIMEPOINT_DF
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
MODULE_NAME = "frequency_response"
# Dynamic components
HEADROOM_OR_FOOTROOM_DICT_NAME = headroom_variables
# Inputs
PROJECT_BAS_INPUT_FILE_NAME = project_bas_input_file_name(MODULE_NAME)
PARTIAL_COLUMN_NAME_IN_INPUT_FILE = "frequency_response_partial"
RESERVE_PROVISION_DERATE_COLUMN_NAME_IN_INPUT_FILE = "frequency_response_derate"
RESERVE_BALANCING_AREAS_INPUT_FILE_NAME = "frequency_response_balancing_areas.tab"
# Model components
RESERVE_PROVISION_VARIABLE_NAME = "Provide_Frequency_Response_MW"
RESERVE_PROVISION_BY_BA_VARIABLE_NAME = "Provide_Frequency_Response_by_BA_MW"
RESERVE_PROVISION_DERATE_PARAM_NAME = "frequency_response_derate"
RESERVE_MAX_FRACTION_PARAM_NAME = "frequency_response_max_fraction_of_provision"
RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME = (
    "frequency_response_reserve_to_energy_adjustment"
)
RESERVE_PROJECTS_SET_NAME = "FREQUENCY_RESPONSE_PROJECTS"
RESERVE_PRJ_BAS_SET_NAME = "FREQUENCY_RESPONSE_PRJ_BAS"
RESERVE_BAS_BY_PRJ_SET_NAME = "FREQUENCY_RESPONSE_BAS_BY_PRJ"
RESERVE_PRJS_BY_BA_SET_NAME = "FREQUENCY_RESPONSE_PRJS_BY_BA"
RESERVE_MULTI_BA_PRJS_SET_NAME = "FREQUENCY_RESPONSE_MULTI_BA_PRJS"
RESERVE_MULTI_BA_PRJ_BA_OPR_TMPS_SET_NAME = (
    "FREQUENCY_RESPONSE_MULTI_BA_PRJ_BA_OPR_TMPS"
)
RESERVE_BALANCING_AREAS_SET_NAME = "FREQUENCY_RESPONSE_BAS"
RESERVE_PRJ_OPR_TMPS_SET_NAME = "FREQUENCY_RESPONSE_PRJ_OPR_TMPS"
RESERVE_BA_ALLOCATION_CONSTRAINT_NAME = "Frequency_Response_BA_Allocation_Constraint"
RESERVE_MAX_FRACTION_CONSTRAINT_NAME = (
    "Frequency_Response_Max_Fraction_to_BA_Constraint"
)


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

    # Subset of frequency response projects allowed to contribute to the
    # partial requirement
    m.FREQUENCY_RESPONSE_PARTIAL_PROJECTS = Set(within=m.FREQUENCY_RESPONSE_PROJECTS)

    # m.FREQUENCY_RESPONSE_PARTIAL_PRJ_OPR_TMPS = \
    #     Set(dimen=2,
    #         rule=lambda mod:
    #         set((g, tmp) for (g, tmp) in mod.PRJ_OPR_TMPS
    #             if g in m.FREQUENCY_RESPONSE_PARTIAL_PROJECTS),
    #         within=m.FREQUENCY_RESPONSE_PRJ_OPR_TMPS)


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

    # Load projects that can contribute to the partial frequency response
    # requirement (the flag is only set for frequency response projects)
    project_fr_partial_list = list()
    projects = pd.read_csv(
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
    )

    for prj, partial in zip(
        projects["project"], projects[PARTIAL_COLUMN_NAME_IN_INPUT_FILE]
    ):
        if partial != "." and int(float(partial)) == 1:
            project_fr_partial_list.append(prj)

    data_portal.data()["FREQUENCY_RESPONSE_PARTIAL_PROJECTS"] = {
        None: project_fr_partial_list
    }


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
    Export project-level results for frequency response
    :param scenario_directory:
    :param stage:
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

    # Whether the project can contribute to the partial requirement
    results_df = create_results_df(
        index_columns=["project", "timepoint"],
        results_columns=["frequency_response_partial_reserve_provision"],
        data=[
            [prj, tmp, 1 if prj in m.FREQUENCY_RESPONSE_PARTIAL_PROJECTS else 0]
            for (prj, tmp) in m.FREQUENCY_RESPONSE_PRJ_OPR_TMPS
        ],
    )

    update_results_df(getattr(d, PROJECT_TIMEPOINT_DF), results_df)


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
    :return: cursor over (project, BA, max_fraction_of_provision,
        contribute_to_partial) and cursor over the project derates
    """

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
        project_ba_subscenario_id=subscenarios.PROJECT_FREQUENCY_RESPONSE_BA_SCENARIO_ID,
        ba_subscenario_id=subscenarios.FREQUENCY_RESPONSE_BA_SCENARIO_ID,
        extra_columns=("contribute_to_partial",),
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
        project_ba_subscenario_id=subscenarios.PROJECT_FREQUENCY_RESPONSE_BA_SCENARIO_ID,
        ba_subscenario_id=subscenarios.FREQUENCY_RESPONSE_BA_SCENARIO_ID,
    )

    # The partial-requirement flag is per project: a project in several BAs
    # must carry the same flag on each of its rows
    project_bas, _ = get_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )
    df = cursor_to_df(project_bas)
    n_flags = df.groupby("project")["contribute_to_partial"].nunique(dropna=False)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_frequency_response_bas",
        severity="High",
        errors=[
            "project(s) '{}': contribute_to_partial must be the same on all of "
            "the project's BA rows".format(prj)
            for prj, n in n_flags.items()
            if n > 1
        ],
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

    # The per-project partial-requirement flag rides into projects.tab (the
    # same on all of a project's BA rows; validated); the map file carries
    # (project, BA, max fraction) and is written from a cursor without the
    # flag
    project_bas_w_partial, _ = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )
    partial_by_project = {}
    for prj, ba, max_fraction, partial in project_bas_w_partial:
        if partial is not None:
            partial_by_project[str(prj)] = str(partial)

    project_bas, prj_derates = generic_get_inputs_from_database(
        scenario_id=scenario_id,
        subscenarios=subscenarios,
        weather_iteration=db_weather_iteration,
        hydro_iteration=db_hydro_iteration,
        availability_iteration=db_availability_iteration,
        subproblem=db_subproblem,
        stage=db_stage,
        conn=conn,
        reserve_type=MODULE_NAME,
        project_ba_subscenario_id=subscenarios.PROJECT_FREQUENCY_RESPONSE_BA_SCENARIO_ID,
        ba_subscenario_id=subscenarios.FREQUENCY_RESPONSE_BA_SCENARIO_ID,
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
        extra_project_columns=[(PARTIAL_COLUMN_NAME_IN_INPUT_FILE, partial_by_project)],
    )
