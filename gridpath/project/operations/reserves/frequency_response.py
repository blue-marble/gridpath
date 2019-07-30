#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Add project-level components for frequency response reserves
"""

from builtins import next
from builtins import zip
from builtins import str
from builtins import range
import csv
import os.path
import pandas as pd
from pyomo.environ import Set, value

from gridpath.project.operations.reserves.reserve_provision import \
    generic_determine_dynamic_components, generic_add_model_components, \
    generic_load_model_data

# Reserve-module variables
MODULE_NAME = "frequency_response"
# Dynamic components
HEADROOM_OR_FOOTROOM_DICT_NAME = "headroom_variables"
# Inputs
BA_COLUMN_NAME_IN_INPUT_FILE = "frequency_response_ba"
RESERVE_PROVISION_DERATE_COLUMN_NAME_IN_INPUT_FILE = \
    "frequency_response_derate"
RESERVE_BALANCING_AREAS_INPUT_FILE_NAME = \
    "load_following_down_balancing_areas.tab"
# Model components
RESERVE_PROVISION_VARIABLE_NAME = "Provide_Frequency_Response_MW"
RESERVE_PROVISION_DERATE_PARAM_NAME = "frequency_response_derate"
RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME = \
    "frequency_response_reserve_to_energy_adjustment"
RESERVE_BALANCING_AREA_PARAM_NAME = "frequency_response_ba"
RESERVE_PROJECTS_SET_NAME = "FREQUENCY_RESPONSE_PROJECTS"
RESERVE_BALANCING_AREAS_SET_NAME = "FREQUENCY_RESPONSE_BAS"
RESERVE_PROJECT_OPERATIONAL_TIMEPOINTS_SET_NAME = \
    "FREQUENCY_RESPONSE_PROJECT_OPERATIONAL_TIMEPOINTS"


def determine_dynamic_components(d, scenario_directory, subproblem, stage):
    """

    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    generic_determine_dynamic_components(
        d=d,
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        reserve_module=MODULE_NAME,
        headroom_or_footroom_dict=HEADROOM_OR_FOOTROOM_DICT_NAME,
        ba_column_name=BA_COLUMN_NAME_IN_INPUT_FILE,
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME,
        reserve_provision_derate_param_name=
        RESERVE_PROVISION_DERATE_PARAM_NAME,
        reserve_to_energy_adjustment_param_name=
        RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME,
        reserve_balancing_area_param_name=RESERVE_BALANCING_AREA_PARAM_NAME
    )


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    generic_add_model_components(
        m=m,
        d=d,
        reserve_projects_set=RESERVE_PROJECTS_SET_NAME,
        reserve_balancing_area_param=RESERVE_BALANCING_AREA_PARAM_NAME,
        reserve_provision_derate_param=RESERVE_PROVISION_DERATE_PARAM_NAME,
        reserve_balancing_areas_set=RESERVE_BALANCING_AREAS_SET_NAME,
        reserve_project_operational_timepoints_set=
        RESERVE_PROJECT_OPERATIONAL_TIMEPOINTS_SET_NAME,
        reserve_provision_variable_name=RESERVE_PROVISION_VARIABLE_NAME,
        reserve_to_energy_adjustment_param=
        RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME
    )

    # Subset of frequency response projects allowed to contribute to the
    # partial requirement
    m.FREQUENCY_RESPONSE_PARTIAL_PROJECTS = Set(
        within=m.FREQUENCY_RESPONSE_PROJECTS)

    # m.FREQUENCY_RESPONSE_PARTIAL_PROJECT_OPERATIONAL_TIMEPOINTS = \
    #     Set(dimen=2,
    #         rule=lambda mod:
    #         set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
    #             if g in m.FREQUENCY_RESPONSE_PARTIAL_PROJECTS),
    #         within=m.FREQUENCY_RESPONSE_PROJECT_OPERATIONAL_TIMEPOINTS)


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
    generic_load_model_data(
        m=m,
        d=d,
        data_portal=data_portal,
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        ba_column_name=BA_COLUMN_NAME_IN_INPUT_FILE,
        derate_column_name=
        RESERVE_PROVISION_DERATE_COLUMN_NAME_IN_INPUT_FILE,
        reserve_balancing_area_param=RESERVE_BALANCING_AREA_PARAM_NAME,
        reserve_provision_derate_param=RESERVE_PROVISION_DERATE_PARAM_NAME,
        reserve_projects_set=RESERVE_PROJECTS_SET_NAME,
        reserve_to_energy_adjustment_param=
        RESERVE_TO_ENERGY_ADJUSTMENT_PARAM_NAME,
        reserve_balancing_areas_input_file=
        RESERVE_BALANCING_AREAS_INPUT_FILE_NAME
    )

    # Load projects that can contribute to the partial frequency response
    # requirement
    project_fr_partial_list = list()
    projects = \
        pd.read_csv(
            os.path.join(scenario_directory, subproblem, stage, "inputs",
                         "projects.tab"),
            sep="\t"
        )

    for row in zip(projects["project"],
                   projects["frequency_response_ba"],
                   projects["frequency_response_partial"]):
        if row[1] is not "." and int(float(row[2])) == 1:
            project_fr_partial_list.append(row[0])
        else:
            pass

    data_portal.data()[
        "FREQUENCY_RESPONSE_PARTIAL_PROJECTS"
    ] = {
        None: project_fr_partial_list
    }


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export project-level results for downward load-following
    :param scenario_directory:
    :param stage:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    # Make a dict of whether project can contribute to partial requirement
    partial_proj = dict()
    for prj in m.FREQUENCY_RESPONSE_PROJECTS:
        if prj in m.FREQUENCY_RESPONSE_PARTIAL_PROJECTS:
            partial_proj[prj] = 1
        else:
            partial_proj[prj] = 0

    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "reserves_provision_frequency_response.csv"),
              "w") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "horizon_weight", "number_of_hours_in_timepoint",
                         "reserve_provision_mw", "partial"])
        for (p, tmp) in m.FREQUENCY_RESPONSE_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp],
                tmp,
                m.horizon_weight[m.horizon[tmp]],
                m.number_of_hours_in_timepoint[tmp],
                m.load_zone[p],
                m.frequency_response_ba[p],
                m.technology[p],
                value(m.Provide_Frequency_Response_MW[p, tmp]),
                partial_proj[p]
            ])


def get_inputs_from_database(subscenarios, subproblem, stage, c):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    # Get project BA
    project_bas = c.execute(
        """SELECT project, frequency_response_ba, contribute_to_partial
        FROM inputs_project_frequency_response_bas
            WHERE frequency_response_ba_scenario_id = {}
            AND project_frequency_response_ba_scenario_id = {}""".format(
            subscenarios.FREQUENCY_RESPONSE_BA_SCENARIO_ID,
            subscenarios.PROJECT_FREQUENCY_RESPONSE_BA_SCENARIO_ID
        )
    ).fetchall()

    # Get frequency_response footroom derate
    prj_derates = c.execute(
        """SELECT project, frequency_response_derate
        FROM inputs_project_operational_chars
        WHERE project_operational_chars_scenario_id = {};""".format(
            subscenarios.PROJECT_OPERATIONAL_CHARS_SCENARIO_ID
        )
    ).fetchall()

    return project_bas, prj_derates


def validate_inputs(subscenarios, subproblem, stage, c):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    # project_bas, prj_derates = get_inputs_from_database(
    #     subscenarios, subproblem, stage, c)

    # do stuff here to validate inputs


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, c):
    """
    Get inputs from database and write out the model input
    projects.tab file (to be precise, amend it).
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """
    project_bas, prj_derates = get_inputs_from_database(
        subscenarios, subproblem, stage, c)

    # Make a dict for easy access
    prj_ba_dict = dict()
    for (prj, ba, partial) in project_bas:
        prj_ba_dict[str(prj)] = \
            (".", ".") if ba is None \
            else (str(ba), partial)

    # Make a dict for easy access
    prj_derate_dict = dict()
    for (prj, derate) in prj_derates:
        prj_derate_dict[str(prj)] = "." if derate is None else str(derate)

    # Add params to projects file
    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("frequency_response_ba")
        header.append("frequency_response_partial")
        header.append("frequency_response_derate")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in list(prj_ba_dict.keys()):
                # Add BA and whether project contributes to partial freq resp
                row.append(prj_ba_dict[row[0]][0])
                row.append(prj_ba_dict[row[0]][1])

            # If project not specified, specify no BA and no partial freq resp
            else:
                for i in range(2):
                    row.append(".")

            # If project specified, check if derate specified or not
            if row[0] in list(prj_derate_dict.keys()):
                row.append(prj_derate_dict[row[0]])
            # If project not specified, specify no derate
            else:
                row.append(".")

            # Add resulting row to new_rows list
            new_rows.append(row)

    with open(os.path.join(inputs_directory, "projects.tab"), "w") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t")
        writer.writerows(new_rows)


def import_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory
):
    """

    :param scenario_id: 
    :param c: 
    :param db: 
    :param results_directory:
    :return: 
    """
    c.execute(
        """DELETE FROM results_project_frequency_response 
        WHERE scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};
        """.format(scenario_id, subproblem, stage)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_project_frequency_response"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_frequency_response""" + str(
            scenario_id) + """(
            scenario_id INTEGER,
            project VARCHAR(64),
            period INTEGER,
            subproblem_id INTEGER,
            stage_id INTEGER,
            horizon INTEGER,
            timepoint INTEGER,
            horizon_weight FLOAT,
            number_of_hours_in_timepoint FLOAT,
            load_zone VARCHAR(32),
            frequency_response_ba VARCHAR(32),
            technology VARCHAR(32),
            reserve_provision_mw FLOAT,
            partial INTEGER,
            PRIMARY KEY (scenario_id, project, subproblem_id, stage_id, timepoint)
                );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "reserves_provision_frequency_response.csv"), "r") \
            as reserve_provision_file:
        reader = csv.reader(reserve_provision_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            ba = row[6]
            load_zone = row[7]
            technology = row[8]
            reserve_provision = row[9]
            partial = row[10]
            c.execute(
                """INSERT INTO temp_results_project_frequency_response"""
                + str(scenario_id) + """
                    (scenario_id, project, period, subproblem_id, stage_id,
                    horizon, timepoint, horizon_weight, 
                    number_of_hours_in_timepoint, 
                    frequency_response_ba, load_zone, technology,
                    reserve_provision_mw, partial)
                    VALUES ({}, '{}', {}, {}, {}, {}, {}, {}, {}, 
                    '{}', '{}', '{}', {}, {});""".format(
                    scenario_id, project, period, subproblem, stage,
                    horizon, timepoint, horizon_weight,
                    number_of_hours_in_timepoint,
                    ba, load_zone, technology, reserve_provision, partial
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_frequency_response
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, horizon_weight, number_of_hours_in_timepoint, 
        frequency_response_ba, load_zone, technology,
        reserve_provision_mw, partial)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, horizon_weight, number_of_hours_in_timepoint,
        frequency_response_ba, load_zone, technology,
        reserve_provision_mw, partial
        FROM temp_results_project_frequency_response""" + str(scenario_id) +
        """ ORDER BY scenario_id, project, subproblem_id, stage_id, 
        timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_frequency_response"""
        + str(scenario_id) + """;"""
    )
    db.commit()
