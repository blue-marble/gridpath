#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Describe operational constraints on the generation infrastructure.
"""

import csv
import os.path
import pandas as pd

from gridpath.auxiliary.dynamic_components import required_operational_modules
from gridpath.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # First, add any components specific to the operational modules
    for op_m in getattr(d, required_operational_modules):
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))
    for op_m in getattr(d, required_operational_modules):
        if hasattr(imported_operational_modules[op_m],
                   "load_module_specific_data"):
            imported_operational_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, horizon, stage)
        else:
            pass


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """

    # Export module-specific results
    # Operational type modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))
    for op_m in getattr(d, required_operational_modules):
        if hasattr(imported_operational_modules[op_m],
                   "export_module_specific_results"):
            imported_operational_modules[op_m].\
                export_module_specific_results(
                m, d, scenario_directory, horizon, stage,
            )
        else:
            pass


def get_inputs_from_database(
        subscenarios, c, inputs_directory
):
    """
    
    :param subscenarios: 
    :param c: 
    :param inputs_directory: 
    :return: 
    """

    project_op_types = \
        pd.read_csv(
            os.path.join(inputs_directory, "projects.tab"),
            sep="\t", usecols=["project",
                               "operational_type"]
        )

    # Required modules are the unique set of generator operational types
    # This list will be used to know which operational modules to load
    required_operational_modules = \
            project_op_types.operational_type.unique()

    # Get module-specific inputs
    # Load in the required operational modules
    imported_operational_modules = \
        load_operational_type_modules(required_operational_modules)

    for op_m in required_operational_modules:
        if hasattr(imported_operational_modules[op_m],
                   "get_module_specific_inputs_from_database"):
            imported_operational_modules[op_m]. \
                get_module_specific_inputs_from_database(
                subscenarios, c, inputs_directory
            )
        else:
            pass


# TODO; this is here only temporarily until we decide how exactly to ensure 
# that we only call operational modules that are needed in a scenario
# Shouldn't cause problems, as at this stage, we'll always be modeling 
# variable generators, so this results file will always exist
def import_results_into_database(scenario_id, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    print("project dispatch variable")
    # dispatch_variable.csv
    c.execute(
        """DELETE FROM results_project_dispatch_variable
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_project_dispatch_variable"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_dispatch_variable"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        project VARCHAR(64),
        period INTEGER,
        horizon INTEGER,
        timepoint INTEGER,
        horizon_weight FLOAT,
        number_of_hours_in_timepoint FLOAT,
        load_zone VARCHAR(32),
        technology VARCHAR(32),
        power_mw FLOAT,
        scheduled_curtailment_mw FLOAT,
        subhourly_curtailment_mw FLOAT,
        subhourly_energy_delivered_mw FLOAT,
        total_curtailment_mw FLOAT,
        PRIMARY KEY (scenario_id, project, timepoint)
            );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "dispatch_variable.csv"), "r") as v_dispatch_file:
        reader = csv.reader(v_dispatch_file)

        reader.next()  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[7]
            technology = row[6]
            power_mw = row[8]
            scheduled_curtailment_mw = row[9]
            subhourly_curtailment_mw = row[10]
            subhourly_energy_delivered_mw = row[11]
            total_curtailment_mw = row[12]
            c.execute(
                """INSERT INTO temp_results_project_dispatch_variable"""
                + str(scenario_id) + """
                (scenario_id, project, period, horizon, timepoint,
                horizon_weight, number_of_hours_in_timepoint,
                load_zone, technology, power_mw, scheduled_curtailment_mw,
                subhourly_curtailment_mw, subhourly_energy_delivered_mw,
                total_curtailment_mw)
                VALUES ({}, '{}', {}, {}, {}, {}, {}, '{}', '{}',
                {}, {}, {}, {}, {});""".format(
                    scenario_id, project, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    load_zone, technology, power_mw, scheduled_curtailment_mw,
                    subhourly_curtailment_mw, subhourly_energy_delivered_mw,
                    total_curtailment_mw
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_dispatch_variable
        (scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw, scheduled_curtailment_mw,
        subhourly_curtailment_mw, subhourly_energy_delivered_mw,
        total_curtailment_mw)
        SELECT
        scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw, scheduled_curtailment_mw,
        subhourly_curtailment_mw, subhourly_energy_delivered_mw,
        total_curtailment_mw
        FROM temp_results_project_dispatch_variable""" + str(scenario_id) + """
        ORDER BY scenario_id, project, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_dispatch_variable""" + str(scenario_id) +
        """;"""
    )
    db.commit()


    print("project dispatch hydro curtailable")
    # dispatch_hydro_curtailable.csv
    c.execute(
        """DELETE FROM results_project_dispatch_hydro_curtailable
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS
        temp_results_project_dispatch_hydro_curtailable"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE
        temp_results_project_dispatch_hydro_curtailable"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        project VARCHAR(64),
        period INTEGER,
        horizon INTEGER,
        timepoint INTEGER,
        horizon_weight FLOAT,
        number_of_hours_in_timepoint FLOAT,
        load_zone VARCHAR(32),
        technology VARCHAR(32),
        power_mw FLOAT,
        scheduled_curtailment_mw FLOAT,
        PRIMARY KEY (scenario_id, project, timepoint)
        );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "dispatch_hydro_curtailable.csv"),
              "r") as h_dispatch_file:
        reader = csv.reader(h_dispatch_file)

        reader.next()  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[7]
            technology = row[6]
            power_mw = row[8]
            scheduled_curtailment_mw = row[9]
            c.execute(
                """INSERT INTO
                temp_results_project_dispatch_hydro_curtailable"""
                + str(scenario_id) + """
                (scenario_id, project, period, horizon, timepoint,
                horizon_weight, number_of_hours_in_timepoint,
                load_zone, technology, power_mw, scheduled_curtailment_mw)
                VALUES ({}, '{}', {}, {}, {}, {}, {}, '{}', '{}',
                {}, {});""".format(
                    scenario_id, project, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    load_zone, technology, power_mw, scheduled_curtailment_mw
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_dispatch_hydro_curtailable
        (scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw, scheduled_curtailment_mw)
        SELECT
        scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw, scheduled_curtailment_mw
        FROM temp_results_project_dispatch_hydro_curtailable"""
        + str(scenario_id) + """
        ORDER BY scenario_id, project, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE
        temp_results_project_dispatch_hydro_curtailable"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()

    print("project dispatch capacity_commit")
    # dispatch_capacity_commit.csv
    c.execute(
        """DELETE FROM results_project_dispatch_capacity_commit
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS
        temp_results_project_dispatch_capacity_commit"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_dispatch_capacity_commit"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        project VARCHAR(64),
        period INTEGER,
        horizon INTEGER,
        timepoint INTEGER,
        horizon_weight FLOAT,
        number_of_hours_in_timepoint FLOAT,
        load_zone VARCHAR(32),
        technology VARCHAR(32),
        power_mw FLOAT,
        committed_mw FLOAT,
        committed_units FLOAT,
        PRIMARY KEY (scenario_id, project, timepoint)
            );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(
            results_directory, "dispatch_capacity_commit.csv"), "r") \
            as cc_dispatch_file:
        reader = csv.reader(cc_dispatch_file)

        reader.next()  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[7]
            technology = row[6]
            power_mw = row[8]
            committed_mw = row[9]
            committed_units = row[10]
            c.execute(
                """INSERT INTO temp_results_project_dispatch_capacity_commit"""
                + str(scenario_id) + """
                (scenario_id, project, period, horizon, timepoint,
                horizon_weight, number_of_hours_in_timepoint,
                load_zone, technology, power_mw, committed_mw,
                committed_units)
                VALUES ({}, '{}', {}, {}, {}, {}, {}, '{}', '{}',
                {}, {}, {});""".format(
                    scenario_id, project, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    load_zone, technology, power_mw, committed_mw,
                    committed_units
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_dispatch_capacity_commit
        (scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw, committed_mw,
        committed_units)
        SELECT
        scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw, committed_mw, committed_units
        FROM temp_results_project_dispatch_capacity_commit""" + str(scenario_id) + """
        ORDER BY scenario_id, project, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_dispatch_capacity_commit""" + str(scenario_id) +
        """;"""
    )
    db.commit()