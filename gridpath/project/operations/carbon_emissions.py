#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Carbon emissions from each carbonaceous project.
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import
from gridpath.auxiliary.validations import write_validation_to_database, \
    validate_idxs


def add_model_components(m, d):
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

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Carbon_Emissions_Tons`                                         |
    | | *Defined over*: :code:`CRBN_PRJ_OPR_TMPS`                             |
    |                                                                         |
    | The project's carbon emissions in metric tonnes for each timepoint in   |
    | which the project could be operational.                                 |
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
        initialize=lambda mod, co2_z:
        [p for p in mod.CRBN_PRJS
         if mod.carbon_cap_zone[p] == co2_z]
    )

    m.CRBN_PRJ_OPR_TMPS = Set(
        within=m.PRJ_OPR_TMPS,
        rule=lambda mod:
        [(p, tmp) for (p, tmp) in mod.PRJ_OPR_TMPS
         if p in mod.CRBN_PRJS]
    )

    # Expressions
    ###########################################################################

    m.Carbon_Emissions_Tons = Expression(
        m.CRBN_PRJ_OPR_TMPS,
        rule=carbon_emissions_rule
    )


# Expression Rules
###############################################################################

def carbon_emissions_rule(mod, g, tmp):
    """
    **Expression Name**: Carbon_Emissions_Tons
    **Defined Over**: CRBN_PRJ_OPR_TMPS

    Emissions from each project based on operational type
    (and whether a project burns fuel)
    """
    return mod.Total_Fuel_Burn_MMBtu[g, tmp] \
        * mod.co2_intensity_tons_per_mmbtu[mod.fuel[g]]


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
                           "carbon_emissions_by_project.csv"),
              "w", newline="") as carbon_emissions_results_file:
        writer = csv.writer(carbon_emissions_results_file)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "timepoint_weight",
                         "number_of_hours_in_timepoint", "load_zone",
                         "carbon_emissions_tons"])
        for (p, tmp) in m.CRBN_PRJ_OPR_TMPS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type_project[p]],
                tmp,
                m.tmp_weight[tmp],
                m.hrs_in_tmp[tmp],
                m.load_zone[p],
                value(m.Carbon_Emissions_Tons[p, tmp])
            ])


# Database
###############################################################################

def get_inputs_from_database(subscenarios, subproblem, stage, conn):
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


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage,
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
        subscenarios, subproblem, stage, conn)

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
    # Carbon emission imports by project and timepoint
    if not quiet:
        print("project carbon emissions")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_carbon_emissions",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "carbon_emissions_by_project.csv"),
              "r") as emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            timepoint_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[6]
            carbon_emissions_tons = row[7]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 horizon, timepoint, timepoint_weight,
                 number_of_hours_in_timepoint,
                 load_zone, carbon_emissions_tons)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_carbon_emissions{}
         (scenario_id, project, period, subproblem_id, stage_id,
         horizon, timepoint, timepoint_weight,
         number_of_hours_in_timepoint,
         load_zone, carbon_emission_tons)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_carbon_emissions
        (scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, carbon_emission_tons)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, carbon_emission_tons
        FROM temp_results_project_carbon_emissions{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


def process_results(db, c, subscenarios, quiet):
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
            (zone, subscenarios.SCENARIO_ID, prj)
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
                              data=(subscenarios.SCENARIO_ID,),
                              many=False)


# Validation
###############################################################################

def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    project_zones = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Convert input data into pandas DataFrame
    df = pd.DataFrame(
        data=project_zones.fetchall(),
        columns=[s[0] for s in project_zones.description]
    )
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
        scenario_id=subscenarios.SCENARIO_ID,
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
