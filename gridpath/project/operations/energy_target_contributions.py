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
Get RECs for each project
"""

import csv
import os.path
from pyomo.environ import Param, Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import (
    get_required_subtype_modules_from_projects_file,
    cursor_to_df,
)
from gridpath.auxiliary.db_interface import (
    update_prj_zone_column,
    determine_table_subset_by_start_and_column,
)
from gridpath.project.operations.common_functions import load_operational_type_modules
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.validations import write_validation_to_database, validate_idxs
import gridpath.project.operations.operational_types as op_type_init


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`ENERGY_TARGET_PRJS`                                            |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | The set of all energy-target-eligible projects.                         |
    +-------------------------------------------------------------------------+
    | | :code:`ENERGY_TARGET_PRJ_OPR_TMPS`                                    |
    |                                                                         |
    | Two-dimensional set that defines all project-timepoint combinations     |
    | when an energy-target-elgible project can be operational.               |
    +-------------------------------------------------------------------------+
    | | :code:`ENERGY_TARGET_PRJS_BY_ENERGY_TARGET_ZONE`                      |
    | | *Defined over*: :code:`ENERGY_TARGET_ZONES`                           |
    | | *Within*: :code:`ENERGY_TARGET_PRJS`                                  |
    |                                                                         |
    | Indexed set that describes the energy-target projects for each          |
    |energy-target zone.                                                      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Input Params                                                            |
    +=========================================================================+
    | | :code:`energy_target_zone`                                            |
    | | *Defined over*: :code:`ENERGY_TARGET_PRJS`                            |
    | | *Within*: :code:`ENERGY_TARGET_ZONES`                                 |
    |                                                                         |
    | This param describes the energy-target zone for each energy-target      |
    | project.                                                                |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Scheduled_Energy_Target_Energy_MW`                             |
    | | *Defined over*: :code:`ENERGY_TARGET_PRJ_OPR_TMPS`                    |
    |                                                                         |
    | Describes how many RECs (in MW) are scheduled for each                  |
    | energy-target-eligible project in each timepoint.                       |
    +-------------------------------------------------------------------------+
    | | :code:`Scheduled_Curtailment_MW`                                      |
    | | *Defined over*: :code:`ENERGY_TARGET_PRJ_OPR_TMPS`                    |
    |                                                                         |
    | Describes the amount of scheduled curtailment (in MW) for each          |
    | energy-target-eligible project in each timepoint.                       |
    +-------------------------------------------------------------------------+
    | | :code:`Subhourly_Energy_Target_Energy_MW`                             |
    | | *Defined over*: :code:`ENERGY_TARGET_PRJ_OPR_TMPS`                    |
    |                                                                         |
    | Describes how many RECs (in MW) are delivered subhourly for each        |
    | energy-target-eligible project in each timepoint. Subhourly             |
    | energy-target energy delivery can occur due to sub-hourly upward        |
    | reserve dispatch (e.g. reg-up).                                         |
    +-------------------------------------------------------------------------+
    | | :code:`Subhourly_Curtailment_MW`                                      |
    | | *Defined over*: :code:`ENERGY_TARGET_PRJ_OPR_TMPS`                    |
    |                                                                         |
    | Describes the amount of subhourly curtailment (in MW) for each          |
    | energy-target-eligible project in each timepoint. Subhourly curtailment |
    | can occur due to sub-hourly downward reserve dispatch (e.g. reg-down).  |
    +-------------------------------------------------------------------------+

    """

    # Dynamic Inputs
    ###########################################################################

    required_operational_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        which_type="operational_type",
    )

    imported_operational_modules = load_operational_type_modules(
        required_operational_modules
    )

    # Sets
    ###########################################################################

    m.ENERGY_TARGET_PRJS = Set(within=m.PROJECTS)

    m.ENERGY_TARGET_PRJ_OPR_TMPS = Set(
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: [
            (p, tmp) for (p, tmp) in mod.PRJ_OPR_TMPS if p in mod.ENERGY_TARGET_PRJS
        ],
    )

    # Input Params
    ###########################################################################

    m.energy_target_zone = Param(m.ENERGY_TARGET_PRJS, within=m.ENERGY_TARGET_ZONES)

    # Derived Sets (requires input params)
    ###########################################################################

    m.ENERGY_TARGET_PRJS_BY_ENERGY_TARGET_ZONE = Set(
        m.ENERGY_TARGET_ZONES,
        within=m.ENERGY_TARGET_PRJS,
        initialize=determine_energy_target_generators_by_energy_target_zone,
    )

    # Expressions
    ###########################################################################

    def scheduled_recs_rule(mod, prj, tmp):
        """
        This how many RECs are scheduled to be delivered at the timepoint
        (hourly) schedule.
        """
        op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[op_type], "rec_provision_rule"):
            return imported_operational_modules[op_type].rec_provision_rule(
                mod, prj, tmp
            )
        else:
            return op_type_init.rec_provision_rule(mod, prj, tmp)

    m.Scheduled_Energy_Target_Energy_MW = Expression(
        m.ENERGY_TARGET_PRJ_OPR_TMPS, rule=scheduled_recs_rule
    )

    def scheduled_curtailment_rule(mod, prj, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed energy-target energy for example -- this is the scheduled
        curtailment component.
        """
        op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[op_type], "scheduled_curtailment_rule"):
            return imported_operational_modules[op_type].scheduled_curtailment_rule(
                mod, prj, tmp
            )
        else:
            return op_type_init.scheduled_curtailment_rule(mod, prj, tmp)

    m.Scheduled_Curtailment_MW = Expression(
        m.ENERGY_TARGET_PRJ_OPR_TMPS, rule=scheduled_curtailment_rule
    )

    def subhourly_recs_delivered_rule(mod, prj, tmp):
        """
        This how many RECs are scheduled to be delivered through sub-hourly
        dispatch (upward reserve dispatch).
        """
        op_type = mod.operational_type[prj]
        if hasattr(
            imported_operational_modules[op_type], "subhourly_energy_delivered_rule"
        ):
            return imported_operational_modules[
                op_type
            ].subhourly_energy_delivered_rule(mod, prj, tmp)
        else:
            return op_type_init.subhourly_energy_delivered_rule(mod, prj, tmp)

    m.Subhourly_Energy_Target_Energy_MW = Expression(
        m.ENERGY_TARGET_PRJ_OPR_TMPS, rule=subhourly_recs_delivered_rule
    )

    def subhourly_curtailment_rule(mod, prj, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed energy-target energy for example -- this is the subhourly
        curtailment component (downward reserve dispatch).
        """
        op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[op_type], "subhourly_curtailment_rule"):
            return imported_operational_modules[op_type].subhourly_curtailment_rule(
                mod, prj, tmp
            )
        else:
            return op_type_init.subhourly_curtailment_rule(mod, prj, tmp)

    m.Subhourly_Curtailment_MW = Expression(
        m.ENERGY_TARGET_PRJ_OPR_TMPS, rule=subhourly_curtailment_rule
    )


# Set Rules
###############################################################################


def determine_energy_target_generators_by_energy_target_zone(mod, energy_target_z):
    return [
        p
        for p in mod.ENERGY_TARGET_PRJS
        if mod.energy_target_zone[p] == energy_target_z
    ]


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
        filename=os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"
        ),
        select=("project", "energy_target_zone"),
        param=(m.energy_target_zone,),
    )

    data_portal.data()["ENERGY_TARGET_PRJS"] = {
        None: list(data_portal.data()["energy_target_zone"].keys())
    }


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    # TODO: only export for timepoints in the energy target
    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "energy_target_by_project.csv",
        ),
        "w",
        newline="",
    ) as energy_target_results_file:
        writer = csv.writer(energy_target_results_file)
        writer.writerow(
            [
                "project",
                "load_zone",
                "energy_target_zone",
                "timepoint",
                "period",
                "horizon",
                "timepoint_weight",
                "number_of_hours_in_timepoint",
                "technology",
                "scheduled_energy_target_energy_mw",
                "scheduled_curtailment_mw",
                "subhourly_energy_target_energy_delivered_mw",
                "subhourly_curtailment_mw",
            ]
        )
        for p, tmp in m.ENERGY_TARGET_PRJ_OPR_TMPS:
            writer.writerow(
                [
                    p,
                    m.load_zone[p],
                    m.energy_target_zone[p],
                    tmp,
                    m.period[tmp],
                    m.horizon[tmp, m.balancing_type_project[p]],
                    m.tmp_weight[tmp],
                    m.hrs_in_tmp[tmp],
                    m.technology[p],
                    value(m.Scheduled_Energy_Target_Energy_MW[p, tmp]),
                    value(m.Scheduled_Curtailment_MW[p, tmp]),
                    value(m.Subhourly_Energy_Target_Energy_MW[p, tmp]),
                    value(m.Subhourly_Curtailment_MW[p, tmp]),
                ]
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
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()

    # Get the energy-target zones for project in our portfolio and with zones in our
    # Energy target zone
    project_zones = c.execute(
        """SELECT project, energy_target_zone
        FROM
        -- Get projects from portfolio only
        (SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}
        ) as prj_tbl
        LEFT OUTER JOIN 
        -- Get energy_target zones for those projects
        (SELECT project, energy_target_zone
            FROM inputs_project_energy_target_zones
            WHERE project_energy_target_zone_scenario_id = {}
        ) as prj_energy_target_zone_tbl
        USING (project)
        -- Filter out projects whose RPS zone is not one included in our 
        -- energy_target_zone_scenario_id
        WHERE energy_target_zone in (
                SELECT energy_target_zone
                    FROM inputs_geography_energy_target_zones
                    WHERE energy_target_zone_scenario_id = {}
        );
        """.format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_ENERGY_TARGET_ZONE_SCENARIO_ID,
            subscenarios.ENERGY_TARGET_ZONE_SCENARIO_ID,
        )
    )

    return project_zones


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
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
    project_zones = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    # Make a dict for easy access
    prj_zone_dict = dict()
    for prj, zone in project_zones:
        prj_zone_dict[str(prj)] = "." if zone is None else str(zone)

    with open(
        os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"
        ),
        "r",
    ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t", lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("energy_target_zone")
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

    with open(
        os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"
        ),
        "w",
        newline="",
    ) as projects_file_out:
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
    # REC provision by project and timepoint
    if not quiet:
        print("project recs")
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_project_period_energy_target",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "energy_target_by_project.csv"), "r"
    ) as energy_target_file:
        reader = csv.reader(energy_target_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            load_zone = row[1]
            energy_target_zone = row[2]
            timepoint = row[3]
            period = row[4]
            horizon = row[5]
            timepoint_weight = row[6]
            hours_in_tmp = row[7]
            technology = row[8]
            scheduled_energy = row[9]
            scheduled_curtailment = row[10]
            subhourly_energy = row[11]
            subhourly_curtailment = row[12]

            results.append(
                (
                    scenario_id,
                    project,
                    period,
                    subproblem,
                    stage,
                    horizon,
                    timepoint,
                    timepoint_weight,
                    hours_in_tmp,
                    load_zone,
                    energy_target_zone,
                    technology,
                    scheduled_energy,
                    scheduled_curtailment,
                    subhourly_energy,
                    subhourly_curtailment,
                )
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_period_energy_target{}
         (scenario_id, project, period, subproblem_id, stage_id, 
         horizon, timepoint, timepoint_weight, 
         number_of_hours_in_timepoint, 
         load_zone, energy_target_zone, technology, 
         scheduled_energy_target_energy_mw, scheduled_curtailment_mw, 
         subhourly_energy_target_energy_delivered_mw, subhourly_curtailment_mw)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_period_energy_target
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, energy_target_zone, technology, 
        scheduled_energy_target_energy_mw, scheduled_curtailment_mw, 
        subhourly_energy_target_energy_delivered_mw, subhourly_curtailment_mw)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, energy_target_zone, technology, 
        scheduled_energy_target_energy_mw, scheduled_curtailment_mw, 
        subhourly_energy_target_energy_delivered_mw, subhourly_curtailment_mw
        FROM temp_results_project_period_energy_target{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
         """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)


def process_results(db, c, scenario_id, subscenarios, quiet):
    """

    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
        print("update energy_target zones")

    tables_to_update = determine_table_subset_by_start_and_column(
        conn=db, tbl_start="results_project_", cols=["energy_target_zone"]
    )

    for tbl in tables_to_update:
        update_prj_zone_column(
            conn=db,
            scenario_id=scenario_id,
            subscenarios=subscenarios,
            subscenario="project_energy_target_zone_scenario_id",
            subsc_tbl="inputs_project_energy_target_zones",
            prj_tbl=tbl,
            col="energy_target_zone",
        )


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

    # Get the projects and energy-target zones
    project_zones = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    # Convert input data into pandas DataFrame
    df = cursor_to_df(project_zones)
    zones_w_project = df["energy_target_zone"].unique()

    # Get the required RPS zones
    # TODO: make this into a function similar to get_projects()?
    #  could eventually centralize all these db query functions in one place
    c = conn.cursor()
    zones = c.execute(
        """SELECT energy_target_zone FROM inputs_geography_energy_target_zones
        WHERE energy_target_zone_scenario_id = {}
        """.format(
            subscenarios.ENERGY_TARGET_ZONE_SCENARIO_ID
        )
    )
    zones = [z[0] for z in zones]  # convert to list

    # Check that each RPS zone has at least one project assigned to it
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_energy_target_zones",
        severity="High",
        errors=validate_idxs(
            actual_idxs=zones_w_project,
            req_idxs=zones,
            idx_label="energy_target_zone",
            msg="Each energy target zone needs at least 1 " "project assigned to it.",
        ),
    )
