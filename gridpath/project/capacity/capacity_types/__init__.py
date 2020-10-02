#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.project.capacity.capacity_types** package contains modules to
describe the various ways in which project capacity can be treated in the
optimization problem, e.g. as specified, available to be built, available to
be retired, etc.
"""
import csv
import os.path

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import \
    load_gen_storage_capacity_type_modules, setup_results_import, \
    get_required_capacity_types_from_database


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Load in the required capacity type modules
    required_capacity_type_modules = \
        get_required_capacity_types_from_database(conn, scenario_id,)
    imported_capacity_type_modules = load_gen_storage_capacity_type_modules(
        required_capacity_type_modules)

    # Validate module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "validate_module_specific_inputs"):
            imported_capacity_type_modules[op_m]. \
                validate_module_specific_inputs(
                    scenario_id, subscenarios, subproblem, stage, conn)
        else:
            pass


def write_model_inputs(scenario_directory, scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input .tab files
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    # Load in the required capacity type modules

    required_capacity_type_modules = \
        get_required_capacity_types_from_database(conn, scenario_id)
    imported_capacity_type_modules = load_gen_storage_capacity_type_modules(
        required_capacity_type_modules)

    # Get module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "write_module_specific_model_inputs"):
            imported_capacity_type_modules[op_m].\
                write_module_specific_model_inputs(
                    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn)
        else:
            pass


# TODO: move this to gridpath.project.capacity.__init__?
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
    # First import the capacity_all results; the capacity type modules will
    # then update the database tables rather than insert (all projects
    # should have been inserted here)
    # Delete prior results and create temporary import table for ordering
    # Capacity results
    if not quiet:
        print("project capacity")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(conn=db, cursor=c,
                         table="results_project_capacity",
                         scenario_id=scenario_id, subproblem=subproblem,
                         stage=stage)

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory, "capacity_all.csv"), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            capacity_type = row[2]
            technology = row[3]
            load_zone = row[4]
            capacity_mw = row[5]
            energy_capacity_mwh = None if row[6] == "" else row[6]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 capacity_type, technology, load_zone,
                 capacity_mw, energy_capacity_mwh)
            )

    insert_temp_sql = """
        INSERT INTO temp_results_project_capacity{}
        (scenario_id, project, period, subproblem_id, stage_id, capacity_type,
        technology, load_zone, capacity_mw, energy_capacity_mwh)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_capacity
        (scenario_id, project, period, subproblem_id, stage_id, capacity_type,
        technology, load_zone, capacity_mw, energy_capacity_mwh)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, capacity_type,
        technology, load_zone, capacity_mw, energy_capacity_mwh
        FROM temp_results_project_capacity{}
        ORDER BY scenario_id, project, period, subproblem_id, 
        stage_id;""".format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)

    # Load in the required capacity type modules
    required_capacity_type_modules = \
        get_required_capacity_types_from_database(db, scenario_id)
    imported_capacity_type_modules = load_gen_storage_capacity_type_modules(
        required_capacity_type_modules)

    # Import module-specific results
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "import_module_specific_results_into_database"):
            imported_capacity_type_modules[op_m]. \
                import_module_specific_results_into_database(
                scenario_id, subproblem, stage, c, db, results_directory, quiet
            )
        else:
            pass
