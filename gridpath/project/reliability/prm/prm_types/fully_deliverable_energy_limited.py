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
Storage projects with additional constraints on deliverability based on their 
duration
"""


import csv
import os.path
from pyomo.environ import Param, Var, Set, Constraint, PositiveReals, NonNegativeReals

from gridpath.auxiliary.auxiliary import (
    cursor_to_df,
    subset_init_by_param_value,
    subset_init_by_set_membership,
)
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    validate_values,
    validate_missing_inputs,
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
    FDDL: Fully Deliverable Duration Limited
    :param m:
    :param d:
    :return:
    """

    m.FDDL_PRM_PROJECTS = Set(
        within=m.PRM_PROJECTS,
        initialize=lambda mod: subset_init_by_param_value(
            mod=mod,
            set_name="PRM_PROJECTS",
            param_name="prm_type",
            param_value="fully_deliverable_energy_limited",
        ),
    )

    # Will limit this to storage project operational periods in addition to
    # PRM project operational periods
    m.FDDL_PRM_PRJ_OPR_PRDS = Set(
        dimen=2,
        within=m.PRM_PRJ_OPR_PRDS & m.PRJ_OPR_PRDS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod,
            superset="PRM_PRJ_OPR_PRDS",
            index=0,
            membership_set=mod.FDDL_PRM_PROJECTS,
        ),
    )

    m.min_duration_for_full_capacity_credit = Param(
        m.FDDL_PRM_PROJECTS, within=PositiveReals
    )

    m.FDDL_Project_Capacity_Credit_Eligible_Capacity_MW = Var(
        m.FDDL_PRM_PRJ_OPR_PRDS, within=NonNegativeReals
    )

    def eligible_capacity_is_less_than_total_capacity_rule(mod, g, p):
        """
        The ELCC capacity can't exceed the total project capacity
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return (
            mod.FDDL_Project_Capacity_Credit_Eligible_Capacity_MW[g, p]
            <= mod.Capacity_MW[g, p]
        )

    m.Max_FDDL_Project_Capacity_Credit_Constraint = Constraint(
        m.FDDL_PRM_PRJ_OPR_PRDS, rule=eligible_capacity_is_less_than_total_capacity_rule
    )

    def eligible_capacity_duration_derate_rule(mod, g, p):
        """
        The ELCC capacity can't exceed the total project capacity
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return (
            mod.FDDL_Project_Capacity_Credit_Eligible_Capacity_MW[g, p]
            <= mod.Energy_Capacity_MWh[g, p]
            / mod.min_duration_for_full_capacity_credit[g]
        )

    m.FDDL_Project_Capacity_Credit_Duration_Derate_Constraint = Constraint(
        m.FDDL_PRM_PRJ_OPR_PRDS, rule=eligible_capacity_duration_derate_rule
    )


def elcc_eligible_capacity_rule(mod, g, p):
    """

    :param mod:
    :param g:
    :param p:
    :return:
    """
    return mod.FDDL_Project_Capacity_Credit_Eligible_Capacity_MW[g, p]


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
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
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
        select=("project", "minimum_duration_for_full_capacity_credit_hours"),
        param=m.min_duration_for_full_capacity_credit,
    )


def get_model_inputs_from_database(
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
    project_zone_dur = c.execute(
        """SELECT project, prm_zone, 
        min_duration_for_full_capacity_credit_hours
        FROM 
        (SELECT project, prm_zone
        FROM inputs_project_prm_zones
        WHERE project_prm_zone_scenario_id = {}) as prj_tbl
        LEFT OUTER JOIN 
        (SELECT project, min_duration_for_full_capacity_credit_hours 
        FROM inputs_project_elcc_chars
        WHERE project_elcc_chars_scenario_id = {}) as min_dur_tbl
        USING (project);""".format(
            subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID,
        )
    )

    return project_zone_dur


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

    project_zone_dur = get_model_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )

    df = cursor_to_df(project_zone_dur)
    cols = ["min_duration_for_full_capacity_credit_hours"]

    # Make sure param sign is as expected
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_elcc_chars",
        severity="High",
        errors=validate_values(df, cols, min=0, strict_min=True),
    )

    # Make sure param is specified
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_elcc_chars",
        severity="High",
        errors=validate_missing_inputs(df, cols),
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

    project_zone_dur = get_model_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )

    # Make a dict for easy access
    # Only assign a min duration to projects that contribute to a PRM zone in
    # case we have projects with missing zones here
    prj_zone_dur_dict = dict()
    for prj, zone, min_dur in project_zone_dur:
        prj_zone_dur_dict[str(prj)] = "." if zone is None else min_dur

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
        header.append("minimum_duration_for_full_capacity_credit_hours")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            if row[0] in list(prj_zone_dur_dict.keys()):
                (
                    row.append(".")
                    if prj_zone_dur_dict[row[0]] is None
                    else row.append(prj_zone_dur_dict[row[0]])
                )
                new_rows.append(row)
            # If project not specified
            else:
                row.append(".")
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
