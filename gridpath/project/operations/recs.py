#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Get RECs for each project
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Param, Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import get_required_subtype_modules_from_projects_file, \
    load_operational_type_modules, cursor_to_df
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.validations import write_validation_to_database, \
    validate_idxs
import gridpath.project.operations.operational_types as op_type


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`RPS_PRJS`                                                      |
    | | *Within*: :code:`PROJECTS`                                            |
    |                                                                         |
    | The set of all RPS-eligible projects.                                   |
    +-------------------------------------------------------------------------+
    | | :code:`RPS_PRJ_OPR_TMPS`                                              |
    |                                                                         |
    | Two-dimensional set that defines all project-timepoint combinations     |
    | when an RPS-elgible project can be operational.                         |
    +-------------------------------------------------------------------------+
    | | :code:`RPS_PRJS_BY_RPS_ZONE`                                          |
    | | *Defined over*: :code:`RPS_ZONES`                                     |
    | | *Within*: :code:`RPS_PRJS`                                            |
    |                                                                         |
    | Indexed set that describes the RPS projects for each RPS zone.          |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Input Params                                                            |
    +=========================================================================+
    | | :code:`rps_zone`                                                      |
    | | *Defined over*: :code:`RPS_PRJS`                                      |
    | | *Within*: :code:`RPS_ZONES`                                           |
    |                                                                         |
    | This param describes the RPS zone for each RPS project.                 |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Scheduled_RPS_Energy_MW`                                       |
    | | *Defined over*: :code:`RPS_PRJ_OPR_TMPS`                              |
    |                                                                         |
    | Describes how many RECs (in MW) are scheduled for each RPS-eligible     |
    | project in each timepoint.                                              |
    +-------------------------------------------------------------------------+
    | | :code:`Scheduled_Curtailment_MW`                                      |
    | | *Defined over*: :code:`RPS_PRJ_OPR_TMPS`                              |
    |                                                                         |
    | Describes the amount of scheduled curtailment (in MW) for each          |
    | RPS-eligible project in each timepoint.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`Subhourly_RPS_Energy_MW`                                       |
    | | *Defined over*: :code:`RPS_PRJ_OPR_TMPS`                              |
    |                                                                         |
    | Describes how many RECs (in MW) are delivered subhourly for each        |
    | RPS-eligible project in each timepoint. Subhourly RPS energy delivery   |
    | can occur due to sub-hourly upward reserve dispatch (e.g. reg-up).      |
    +-------------------------------------------------------------------------+
    | | :code:`Subhourly_Curtailment_MW`                                      |
    | | *Defined over*: :code:`RPS_PRJ_OPR_TMPS`                              |
    |                                                                         |
    | Describes the amount of subhourly curtailment (in MW) for each          |
    | RPS-eligible project in each timepoint. Subhourly curtailment can       |
    | occur due to sub-hourly downward reserve dispatch (e.g. reg-down).      |
    +-------------------------------------------------------------------------+

    """

    # Dynamic Inputs
    ###########################################################################

    required_operational_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, which_type="operational_type"
    )

    imported_operational_modules = load_operational_type_modules(
        required_operational_modules
    )

    # Sets
    ###########################################################################

    m.RPS_PRJS = Set(within=m.PROJECTS)

    m.RPS_PRJ_OPR_TMPS = Set(
        within=m.PRJ_OPR_TMPS,
        rule=lambda mod: [(p, tmp) for (p, tmp) in mod.PRJ_OPR_TMPS
                          if p in mod.RPS_PRJS]
    )

    # Input Params
    ###########################################################################

    m.rps_zone = Param(
        m.RPS_PRJS,
        within=m.RPS_ZONES
    )

    # Derived Sets (requires input params)
    ###########################################################################

    m.RPS_PRJS_BY_RPS_ZONE = Set(
        m.RPS_ZONES,
        within=m.RPS_PRJS,
        initialize=determine_rps_generators_by_rps_zone
    )

    # Expressions
    ###########################################################################

    def scheduled_recs_rule(mod, prj, tmp):
        """
        This how many RECs are scheduled to be delivered at the timepoint
        (hourly) schedule.
        """
        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type],
                   "rec_provision_rule"):
            return imported_operational_modules[gen_op_type]. \
                rec_provision_rule(mod, prj, tmp)
        else:
            return op_type.rec_provision_rule(mod, prj, tmp)

    m.Scheduled_RPS_Energy_MW = Expression(
        m.RPS_PRJ_OPR_TMPS, 
        rule=scheduled_recs_rule
    )

    def scheduled_curtailment_rule(mod, prj, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the scheduled
        curtailment component.
        """
        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type],
                   "scheduled_curtailment_rule"):
            return imported_operational_modules[gen_op_type]. \
                scheduled_curtailment_rule(mod, prj, tmp)
        else:
            return op_type.scheduled_curtailment_rule(mod, prj, tmp)

    m.Scheduled_Curtailment_MW = Expression(
        m.RPS_PRJ_OPR_TMPS,
        rule=scheduled_curtailment_rule
    )

    def subhourly_recs_delivered_rule(mod, prj, tmp):
        """
        This how many RECs are scheduled to be delivered through sub-hourly
        dispatch (upward reserve dispatch).
        """
        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type],
                   "subhourly_energy_delivered_rule"):
            return imported_operational_modules[gen_op_type]. \
                subhourly_energy_delivered_rule(mod, prj, tmp)
        else:
            return op_type.subhourly_energy_delivered_rule(mod, prj, tmp)

    m.Subhourly_RPS_Energy_MW = Expression(
        m.RPS_PRJ_OPR_TMPS,
        rule=subhourly_recs_delivered_rule
    )

    def subhourly_curtailment_rule(mod, prj, tmp):
        """
        Keep track of curtailment to make it easier to calculate total
        curtailed RPS energy for example -- this is the subhourly
        curtailment component (downward reserve dispatch).
        """
        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type],
                   "subhourly_curtailment_rule"):
            return imported_operational_modules[gen_op_type]. \
                subhourly_curtailment_rule(mod, prj, tmp)
        else:
            return op_type.subhourly_curtailment_rule(mod, prj, tmp)

    m.Subhourly_Curtailment_MW = Expression(
        m.RPS_PRJ_OPR_TMPS,
        rule=subhourly_curtailment_rule
    )


# Set Rules
###############################################################################

def determine_rps_generators_by_rps_zone(mod, rps_z):
    return [p for p in mod.RPS_PRJS if mod.rps_zone[p] == rps_z]


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
        select=("project", "rps_zone"),
        param=(m.rps_zone,)
    )

    data_portal.data()['RPS_PRJS'] = {
        None: list(data_portal.data()['rps_zone'].keys())
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
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "rps_by_project.csv"),
              "w", newline="") as rps_results_file:
        writer = csv.writer(rps_results_file)
        writer.writerow(["project", "load_zone", "rps_zone",
                         "timepoint", "period", "horizon", "timepoint_weight",
                         "number_of_hours_in_timepoint", "technology",
                         "scheduled_rps_energy_mw",
                         "scheduled_curtailment_mw",
                         "subhourly_rps_energy_delivered_mw",
                         "subhourly_curtailment_mw"])
        for (p, tmp) in m.RPS_PRJ_OPR_TMPS:
            writer.writerow([
                p,
                m.load_zone[p],
                m.rps_zone[p],
                tmp,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type_project[p]],
                m.tmp_weight[tmp],
                m.hrs_in_tmp[tmp],
                m.technology[p],
                value(m.Scheduled_RPS_Energy_MW[p, tmp]),
                value(m.Scheduled_Curtailment_MW[p, tmp]),
                value(m.Subhourly_RPS_Energy_MW[p, tmp]),
                value(m.Subhourly_Curtailment_MW[p, tmp])
            ])

    # Export list of RPS projects and their zones for later use
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "rps_project_zones.csv"),
              "w", newline="") as rps_project_zones_file:
        writer = csv.writer(rps_project_zones_file)
        writer.writerow(["project", "rps_zone"])
        for p in m.RPS_PRJS:
            writer.writerow([p, m.rps_zone[p]])


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

    # Get the RPS zones for project in our portfolio and with zones in our
    # RPS zone
    project_zones = c.execute(
        """SELECT project, rps_zone
        FROM
        -- Get projects from portfolio only
        (SELECT project
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}
        ) as prj_tbl
        LEFT OUTER JOIN 
        -- Get rps zones for those projects
        (SELECT project, rps_zone
            FROM inputs_project_rps_zones
            WHERE project_rps_zone_scenario_id = {}
        ) as prj_rps_zone_tbl
        USING (project)
        -- Filter out projects whose RPS zone is not one included in our 
        -- rps_zone_scenario_id
        WHERE rps_zone in (
                SELECT rps_zone
                    FROM inputs_geography_rps_zones
                    WHERE rps_zone_scenario_id = {}
        );
        """.format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_RPS_ZONE_SCENARIO_ID,
            subscenarios.RPS_ZONE_SCENARIO_ID
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
        header.append("rps_zone")
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
        conn=db, cursor=c,
        table="results_project_rps",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory, "rps_by_project.csv"),
              "r") as rps_file:
        reader = csv.reader(rps_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            load_zone = row[1]
            rps_zone = row[2]
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
                (scenario_id, project, period, subproblem, stage,
                 horizon, timepoint, timepoint_weight, hours_in_tmp,
                 load_zone, rps_zone, technology,
                 scheduled_energy, scheduled_curtailment,
                 subhourly_energy, subhourly_curtailment)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_rps{}
         (scenario_id, project, period, subproblem_id, stage_id, 
         horizon, timepoint, timepoint_weight, 
         number_of_hours_in_timepoint, 
         load_zone, rps_zone, technology, 
         scheduled_rps_energy_mw, scheduled_curtailment_mw, 
         subhourly_rps_energy_delivered_mw, subhourly_curtailment_mw)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_rps
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, rps_zone, technology, 
        scheduled_rps_energy_mw, scheduled_curtailment_mw, 
        subhourly_rps_energy_delivered_mw, subhourly_curtailment_mw)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint, 
        load_zone, rps_zone, technology, 
        scheduled_rps_energy_mw, scheduled_curtailment_mw, 
        subhourly_rps_energy_delivered_mw, subhourly_curtailment_mw
        FROM temp_results_project_rps{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


def process_results(db, c, scenario_id, subscenarios, quiet):
    """

    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
        print("update rps zones")
    # Figure out RPS zone for each project
    project_zones = c.execute(
        """SELECT project, rps_zone
        FROM inputs_project_rps_zones
            WHERE project_rps_zone_scenario_id = {}""".format(
            subscenarios.PROJECT_RPS_ZONE_SCENARIO_ID
        )
    ).fetchall()

    # Update tables with RPS zone
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

    results = []
    for (prj, zone) in project_zones:
        results.append(
            (zone, scenario_id, prj)
        )

    for tbl in tables_to_update:
        sql = """
            UPDATE {}
            SET rps_zone = ?
            WHERE scenario_id = ?
            AND project = ?;
            """.format(tbl)
        spin_on_database_lock(conn=db, cursor=c, sql=sql, data=results)


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

    # Get the projects and RPS zones
    project_zones = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn)

    # Convert input data into pandas DataFrame
    df = cursor_to_df(project_zones)
    zones_w_project = df["rps_zone"].unique()

    # Get the required RPS zones
    # TODO: make this into a function similar to get_projects()?
    #  could eventually centralize all these db query functions in one place
    c = conn.cursor()
    zones = c.execute(
        """SELECT rps_zone FROM inputs_geography_rps_zones
        WHERE rps_zone_scenario_id = {}
        """.format(subscenarios.RPS_ZONE_SCENARIO_ID)
    )
    zones = [z[0] for z in zones]  # convert to list

    # Check that each RPS zone has at least one project assigned to it
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_rps_zones",
        severity="High",
        errors=validate_idxs(actual_idxs=zones_w_project,
                             req_idxs=zones,
                             idx_label="rps_zone",
                             msg="Each RPS zone needs at least 1 project "
                                 "assigned to it.")
    )
