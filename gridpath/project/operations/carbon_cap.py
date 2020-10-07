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
Carbon emissions from each carbonaceous project.
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Param, Set

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import cursor_to_df, \
    subset_init_by_param_value
from gridpath.auxiliary.validations import write_validation_to_database, \
    validate_idxs


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`CRBN_PRJS`                                                     |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | Two set of carbonaceous projects we need to track for the carbon cap.   |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`carbon_cap_zone`                                               |
    | | *Defined over*: :code:`CRBN_PRJS`                                     |
    | | *Within*: :code:`CARBON_CAP_ZONES`                                    |
    |                                                                         |
    | This param describes the carbon cap zone for each carbonaceous project. |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Derived Sets                                                            |
    +=========================================================================+
    | | :code:`CRBN_PRJS_BY_CARBON_CAP_ZONE`                                  |
    | | *Defined over*: :code:`CARBON_CAP_ZONES`                              |
    | | *Within*: :code:`CRBN_PRJS`                                           |
    |                                                                         |
    | Indexed set that describes the list of carbonaceous projects for each   |
    | carbon cap zone.                                                        |
    +-------------------------------------------------------------------------+
    | | :code:`CRBN_PRJ_OPR_TMPS`                                             |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | Two-dimensional set that defines all project-timepoint combinations     |
    | when a carbonaceous project can be operational.                         |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.CRBN_PRJS = Set(
        within=m.PROJECTS
    )

    # Input Params
    ###########################################################################

    m.carbon_cap_zone = Param(
        m.CRBN_PRJS,
        within=m.CARBON_CAP_ZONES
    )

    # Derived Sets
    ###########################################################################

    m.CRBN_PRJS_BY_CARBON_CAP_ZONE = Set(
        m.CARBON_CAP_ZONES,
        within=m.CRBN_PRJS,
        initialize=lambda mod, co2_z: subset_init_by_param_value(
            mod, "CRBN_PRJS", "carbon_cap_zone", co2_z
        )
    )

    m.CRBN_PRJ_OPR_TMPS = Set(
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod:
        [(p, tmp) for (p, tmp) in mod.PRJ_OPR_TMPS
         if p in mod.CRBN_PRJS]
    )


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage),
                              "inputs", "projects.tab"),
        select=("project", "carbon_cap_zone"),
        param=(m.carbon_cap_zone,)
    )

    data_portal.data()['CRBN_PRJS'] = {
        None: list(data_portal.data()['carbon_cap_zone'].keys())
    }


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
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()
    project_zones = c.execute(
        """SELECT project, carbon_cap_zone
        FROM
        -- Get projects from portfolio only
        (SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}
        ) as prj_tbl
        LEFT OUTER JOIN 
        -- Get carbon cap zones for those projects
        (SELECT project, carbon_cap_zone
            FROM inputs_project_carbon_cap_zones
            WHERE project_carbon_cap_zone_scenario_id = {}
        ) as prj_cc_zone_tbl
        USING (project)
        -- Filter out projects whose carbon cap zone is not one included in 
        -- our carbon_cap_zone_scenario_id
        WHERE carbon_cap_zone in (
                SELECT carbon_cap_zone
                    FROM inputs_geography_carbon_cap_zones
                    WHERE carbon_cap_zone_scenario_id = {}
        );
        """.format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_CARBON_CAP_ZONE_SCENARIO_ID,
            subscenarios.CARBON_CAP_ZONE_SCENARIO_ID
        )
    )

    return project_zones


def write_model_inputs(scenario_directory, scenario_id, subscenarios, subproblem, stage,
                       conn):
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
    project_zones = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    # Make a dict for easy access
    prj_zone_dict = dict()
    for (prj, zone) in project_zones:
        prj_zone_dict[str(prj)] = "." if zone is None else str(zone)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t",
                            lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("carbon_cap_zone")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_zone_dict.keys()):
                row.append(prj_zone_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"), "w",
              newline="") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t",
                            lineterminator="\n")
        writer.writerows(new_rows)


def process_results(db, c, scenario_id, subscenarios, quiet):
    """

    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
        print("update carbon cap zones")
    # Figure out carbon_cap zone for each project
    project_zones = c.execute(
        """SELECT project, carbon_cap_zone
        FROM inputs_project_carbon_cap_zones
            WHERE project_carbon_cap_zone_scenario_id = {}""".format(
            subscenarios.PROJECT_CARBON_CAP_ZONE_SCENARIO_ID
        )
    ).fetchall()

    # Update tables with carbon cap zone
    tables_to_update = [
        "results_project_capacity",
        "results_project_dispatch",
        "results_project_fuel_burn",
        "results_project_frequency_response",
        "results_project_lf_reserves_up",
        "results_project_lf_reserves_down",
        "results_project_regulation_up",
        "results_project_regulation_down",
        "results_project_costs_capacity",
        "results_project_costs_operations",
        "results_project_carbon_emissions",
        "results_project_elcc_simple",
        "results_project_elcc_surface"
    ]

    updates = []
    for (prj, zone) in project_zones:
        updates.append(
            (zone, scenario_id, prj)
        )
    for tbl in tables_to_update:
        sql = """
            UPDATE {}
            SET carbon_cap_zone = ?
            WHERE scenario_id = ?
            AND project = ?;
            """.format(tbl)
        spin_on_database_lock(conn=db, cursor=c, sql=sql, data=updates)

    # Set carbon_cap_zone to 'no_carbon_cap' for all other projects
    # This helps for later joins (can't join on NULL values)
    for tbl in tables_to_update:
        no_cc_sql = """
            UPDATE {}
            SET carbon_cap_zone = 'no_carbon_cap'
            WHERE scenario_id = ?
            AND carbon_cap_zone IS NULL;
            """.format(tbl)
        spin_on_database_lock(conn=db, cursor=c, sql=no_cc_sql,
                              data=(scenario_id,),
                              many=False)


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

    project_zones = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    # Convert input data into pandas DataFrame
    df = cursor_to_df(project_zones)
    zones_w_project = df["carbon_cap_zone"].unique()

    # Get the required carbon cap zones
    # TODO: make this into a function similar to get_projects()?
    #  could eventually centralize all these db query functions in one place
    c = conn.cursor()
    zones = c.execute(
        """SELECT carbon_cap_zone FROM inputs_geography_carbon_cap_zones
        WHERE carbon_cap_zone_scenario_id = {}
        """.format(subscenarios.CARBON_CAP_ZONE_SCENARIO_ID)
    )
    zones = [z[0] for z in zones]  # convert to list

    # Check that each carbon cap zone has at least one project assigned to it
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_carbon_cap_zones",
        severity="High",
        errors=validate_idxs(actual_idxs=zones_w_project,
                             req_idxs=zones,
                             idx_label="carbon_cap_zone",
                             msg="Each carbon cap zone needs at least 1 "
                                 "project assigned to it.")
    )

    # TODO: need validation that projects with carbon cap zones also have fuels
