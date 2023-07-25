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


from .reserve_balance import (
    generic_add_model_components,
    generic_export_results,
    generic_save_duals,
    generic_import_results_to_database,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m=m,
        d=d,
        reserve_zone_set="REGULATION_DOWN_ZONES",
        reserve_violation_variable="Regulation_Down_Violation_MW",
        reserve_violation_expression="Regulation_Down_Violation_MW_Expression",
        reserve_violation_allowed_param="regulation_down_allow_violation",
        reserve_requirement_expression="Reg_Down_Requirement",
        total_reserve_provision_expression="Total_Regulation_Down_Provision_MW",
        meet_reserve_constraint="Meet_Regulation_Down_Constraint",
    )


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    generic_export_results(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        m=m,
        d=d,
        reserve_type="regulation_down",
        reserve_zone_set="REGULATION_DOWN_ZONES",
        reserve_violation_expression="Regulation_Down_Violation_MW_Expression",
    )


def save_duals(scenario_directory, subproblem, stage, instance, dynamic_components):
    """

    :param m:
    :return:
    """
    generic_save_duals(instance, "Meet_Regulation_Down_Constraint")


def import_results_into_database(
    scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    generic_import_results_to_database(
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
        c=c,
        db=db,
        results_directory=results_directory,
        reserve_type="regulation_down",
        quiet=quiet,
    )
