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
Simplest PRM contribution where each PRM project contributes a fraction of 
its installed capacity.
"""
from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Param, PercentFraction, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.validations import write_validation_to_database, \
    validate_values, validate_missing_inputs


def add_model_components(m, d, subproblem_stage_directory):
    """

    :param m:
    :param d:
    :return:
    """
    # The fraction of ELCC-eligible capacity that counts for the PRM via the
    # simple PRM method (whether or not project also contributes through the
    # ELCC surface)
    m.elcc_simple_fraction = Param(m.PRM_PROJECTS, within=PercentFraction)

    def elcc_simple_rule(mod, g, p):
        """
        
        :param g: 
        :param p: 
        :return: 
        """
        return mod.ELCC_Eligible_Capacity_MW[g, p] \
            * mod.elcc_simple_fraction[g]

    m.PRM_Simple_Contribution_MW = Expression(
        m.PRM_PRJ_OPR_PRDS, rule=elcc_simple_rule
    )


def load_model_data(
    m, d, data_portal, scenario_directory, subproblem, stage,
    subproblem_stage_directory
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
    data_portal.load(filename=os.path.join(
                        subproblem_stage_directory, "inputs",
                        "projects.tab"),
                     select=("project", "elcc_simple_fraction"),
                     param=(m.elcc_simple_fraction,)
                     )


def export_results(scenario_directory, subproblem, stage, m, d, subproblem_stage_directory):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(subproblem_stage_directory, "results",
                           "prm_project_elcc_simple_contribution.csv"),
              "w", newline="") as \
            results_file:
        writer = csv.writer(results_file)
        writer.writerow(["project", "period", "prm_zone", "technology",
                         "load_zone",
                         "capacity_mw",
                         "elcc_eligible_capacity_mw",
                         "elcc_simple_fraction",
                         "elcc_mw"])
        for (prj, period) in m.PRM_PRJ_OPR_PRDS:
            writer.writerow([
                prj,
                period,
                m.prm_zone[prj],
                m.technology[prj],
                m.load_zone[prj],
                value(m.Capacity_MW[prj, period]),
                value(m.ELCC_Eligible_Capacity_MW[prj, period]),
                value(m.elcc_simple_fraction[prj]),
                value(m.PRM_Simple_Contribution_MW[prj, period])
            ])


def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()
    project_fractions = c.execute(
        """SELECT project, elcc_simple_fraction
        FROM 
        (SELECT project
        FROM inputs_project_prm_zones
        WHERE project_prm_zone_scenario_id = {}) as proj_tbl
        LEFT OUTER JOIN 
        (SELECT project, elcc_simple_fraction
        FROM inputs_project_elcc_chars
        WHERE project_elcc_chars_scenario_id = {}) as frac_tbl
        USING (project);""".format(
            subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
        )
    )

    return project_fractions


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    project_fractions = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    df = cursor_to_df(project_fractions)

    # Make sure fraction is specified
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_elcc_chars",
        severity="High",
        errors=validate_values(df, ["elcc_simple_fraction"], min=0, max=1)
    )

    # Make sure fraction is specified
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_elcc_chars",
        severity="High",
        errors=validate_missing_inputs(df, "elcc_simple_fraction")
    )


def write_model_inputs(scenario_directory, scenario_id, subscenarios, subproblem, stage, conn, subproblem_stage_directory):
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
    project_fractions = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    # Make a dict for easy access
    prj_frac_dict = dict()
    for (prj, fraction) in project_fractions:
        prj_frac_dict[str(prj)] = "." if fraction is None else str(fraction)

    with open(os.path.join(subproblem_stage_directory, "inputs", "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t", lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("elcc_simple_fraction")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_frac_dict.keys()):
                row.append(prj_frac_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(subproblem_stage_directory, "inputs", "projects.tab"), "w", newline="") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)


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
    if not quiet:
        print("project simple elcc")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_elcc_simple",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "prm_project_elcc_simple_contribution.csv"), "r") \
            as elcc_file:
        reader = csv.reader(elcc_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            prm_zone = row[2]
            technology = row[3]
            load_zone = row[4]
            capacity = row[5]
            elcc_eligible_capacity = row[6]
            prm_fraction = row[7]
            elcc = row[8]
            
            results.append(
                (scenario_id, project, period, subproblem, stage,
                        prm_zone, technology, load_zone,
                        capacity, elcc_eligible_capacity, prm_fraction, elcc)
            )

    insert_temp_sql = """
        INSERT INTO temp_results_project_elcc_simple{}
        (scenario_id, project, period, subproblem_id, stage_id,
        prm_zone, technology, load_zone,
        capacity_mw, elcc_eligible_capacity_mw,
        elcc_simple_contribution_fraction, elcc_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_elcc_simple
        (scenario_id, project, period, subproblem_id, stage_id,
        prm_zone, technology, load_zone, 
        capacity_mw, elcc_eligible_capacity_mw,
        elcc_simple_contribution_fraction, elcc_mw)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        prm_zone, technology, load_zone, 
        capacity_mw, elcc_eligible_capacity_mw,
        elcc_simple_contribution_fraction, elcc_mw
        FROM temp_results_project_elcc_simple{}
        ORDER BY scenario_id, project, period, subproblem_id, stage_id;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
