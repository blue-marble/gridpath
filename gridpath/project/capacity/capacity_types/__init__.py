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
    load_gen_storage_capacity_type_modules, setup_results_import


# TODO: we should shorten the names of the capacity-type modules, e.g. to
#   gen_specified, gen_specified_lin_ret, gen_new, stor_specified, stor_new,
#   shift_load_supply_curve
# TODO: We should decide on naming conventions for sets, variables, etc. in
#  the capacity type modules


def get_required_capacity_type_modules(scenario_id, c):
    """
    Get the required capacity type submodules based on the database inputs
    for the specified scenario_id. Required modules are the unique set of
    generator capacity types in the scenario's portfolio. Get the list based
    on the project_operational_chars_scenario_id of the scenario_id.

    This list will be used to know for which capacity type submodules we
    should validate inputs, get inputs from database , or save results to
    database.

    Note: once we have determined the dynamic components, this information
    will also be stored in the DynamicComponents class object.

    :param scenario_id: user-specified scenario ID
    :param c: database cursor
    :return: List of the required capacity type submodules
    """

    project_portfolio_scenario_id = c.execute(
        """SELECT project_portfolio_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    required_capacity_type_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT capacity_type 
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}""".format(
                project_portfolio_scenario_id
            )
        ).fetchall()
    ]

    return required_capacity_type_modules


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Load in the required capacity type modules
    c = conn.cursor()
    scenario_id = subscenarios.SCENARIO_ID
    required_capacity_type_modules = get_required_capacity_type_modules(
        scenario_id, c)
    imported_capacity_type_modules = load_gen_storage_capacity_type_modules(
        required_capacity_type_modules)

    # Validate module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "validate_module_specific_inputs"):
            imported_capacity_type_modules[op_m]. \
                validate_module_specific_inputs(
                    subscenarios, subproblem, stage, conn)
        else:
            pass


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input .tab files
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    # Load in the required capacity type modules
    scenario_id = subscenarios.SCENARIO_ID
    required_capacity_type_modules = get_required_capacity_type_modules(
        scenario_id, c)
    imported_capacity_type_modules = load_gen_storage_capacity_type_modules(
        required_capacity_type_modules)

    # Get module-specific inputs
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "write_module_specific_model_inputs"):
            imported_capacity_type_modules[op_m].\
                write_module_specific_model_inputs(
                    inputs_directory, subscenarios, subproblem, stage, conn)
        else:
            pass


# TODO: move this to gridpath.project.capacity.__init__?
def import_results_into_database(scenario_id, subproblem, stage,
                                 c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # First import the capacity_all results; the capacity type modules will
    # then update the database tables rather than insert (all projects
    # should have been inserted here)
    # Delete prior results and create temporary import table for ordering
    # Capacity results
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
            energy_capacity_mwh = 'NULL' if row[6] == "" else row[6]

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
    required_capacity_type_modules = get_required_capacity_type_modules(
        scenario_id, c)
    imported_capacity_type_modules = load_gen_storage_capacity_type_modules(
        required_capacity_type_modules)

    # Import module-specific results
    for op_m in required_capacity_type_modules:
        if hasattr(imported_capacity_type_modules[op_m],
                   "import_module_specific_results_into_database"):
            imported_capacity_type_modules[op_m]. \
                import_module_specific_results_into_database(
                scenario_id, subproblem, stage, c, db, results_directory
            )
        else:
            pass
