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
Describe operational constraints on generation, storage, and DR projects.

This module contains the defaults for the operational type module methods (
the standard methods used by the operational type modules to interact with
the rest of the model).
If an operational type module method is not specified in an operational type
module, these defaults are used.
"""

import csv
import os.path

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import get_required_subtype_modules_from_projects_file
from gridpath.project.operations.common_functions import load_operational_type_modules
from gridpath.auxiliary.db_interface import setup_results_import


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed operational modules
    required_operational_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        which_type="operational_type",
    )

    imported_operational_modules = load_operational_type_modules(
        required_operational_modules
    )

    # Add any components specific to the operational modules
    for op_m in required_operational_modules:
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "add_model_components"):
            imp_op_m.add_model_components(m, d, scenario_directory, subproblem, stage)


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
    # Import needed operational modules
    required_operational_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        which_type="operational_type",
    )

    imported_operational_modules = load_operational_type_modules(
        required_operational_modules
    )

    # Add any components specific to the operational modules
    for op_m in required_operational_modules:
        if hasattr(imported_operational_modules[op_m], "load_model_data"):
            imported_operational_modules[op_m].load_model_data(
                m, d, data_portal, scenario_directory, subproblem, stage
            )
        else:
            pass


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param subproblem:
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
    required_operational_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        which_type="operational_type",
    )

    imported_operational_modules = load_operational_type_modules(
        required_operational_modules
    )

    # Add any components specific to the operational modules
    for op_m in required_operational_modules:
        if hasattr(imported_operational_modules[op_m], "export_results"):
            imported_operational_modules[op_m].export_results(
                m,
                d,
                scenario_directory,
                subproblem,
                stage,
            )
        else:
            pass


# TODO: move this into SubScenarios class?
def get_required_opchar_modules(scenario_id, c):
    """
    Get the required operational type submodules based on the database inputs
    for the specified scenario_id. Required modules are the unique set of
    generator operational types in the scenario's portfolio. Get the list based
    on the project_operational_chars_scenario_id of the scenario_id.

    This list will be used to know for which operational type submodules we
    should validate inputs, get inputs from database, or save results to
    database.

    Note: once we have determined the dynamic components, this information
    will also be stored in the DynamicComponents class object.

    :param scenario_id: user-specified scenario ID
    :param c: database cursor
    :return: List of the required operational type submodules
    """

    project_portfolio_scenario_id = c.execute(
        """SELECT project_portfolio_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(
            scenario_id
        )
    ).fetchone()[0]

    project_opchars_scenario_id = c.execute(
        """SELECT project_operational_chars_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(
            scenario_id
        )
    ).fetchone()[0]

    required_opchar_modules = [
        p[0]
        for p in c.execute(
            """SELECT DISTINCT operational_type 
            FROM 
            (SELECT project FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}) as prj_tbl
            INNER JOIN 
            (SELECT project, operational_type
            FROM inputs_project_operational_chars
            WHERE project_operational_chars_scenario_id = {}) as op_type_tbl
            USING (project);""".format(
                project_portfolio_scenario_id, project_opchars_scenario_id
            )
        ).fetchall()
    ]

    return required_opchar_modules


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Load in the required operational modules
    c = conn.cursor()

    required_opchar_modules = get_required_opchar_modules(scenario_id, c)
    imported_operational_modules = load_operational_type_modules(
        required_opchar_modules
    )

    # Validate module-specific inputs
    for op_m in required_opchar_modules:
        if hasattr(imported_operational_modules[op_m], "validate_inputs"):
            imported_operational_modules[op_m].validate_inputs(
                scenario_id, subscenarios, subproblem, stage, conn
            )
        else:
            pass


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input .tab files
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Load in the required operational modules
    c = conn.cursor()

    required_opchar_modules = get_required_opchar_modules(scenario_id, c)
    imported_operational_modules = load_operational_type_modules(
        required_opchar_modules
    )

    # Write module-specific inputs
    for op_m in required_opchar_modules:
        if hasattr(imported_operational_modules[op_m], "write_model_inputs"):
            imported_operational_modules[op_m].write_model_inputs(
                scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
            )
        else:
            pass


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
        print("project dispatch all")
    # dispatch_all.csv
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_project_dispatch",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "dispatch_all.csv"), "r"
    ) as dispatch_file:
        reader = csv.reader(dispatch_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            operational_type = row[4]
            balancing_type = row[5]
            timepoint_weight = row[6]
            number_of_hours_in_timepoint = row[7]
            load_zone = row[8]
            technology = row[9]
            power_mw = row[10]

            results.append(
                (
                    scenario_id,
                    project,
                    period,
                    subproblem,
                    stage,
                    timepoint,
                    operational_type,
                    balancing_type,
                    horizon,
                    timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone,
                    technology,
                    power_mw,
                )
            )
    insert_temp_sql = """
        INSERT INTO temp_results_project_dispatch{}
        (scenario_id, project, period, subproblem_id, stage_id, timepoint,
        operational_type, balancing_type,
        horizon, timepoint_weight,
        number_of_hours_in_timepoint,
        load_zone, technology, power_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_dispatch
        (scenario_id, project, period, subproblem_id, stage_id, timepoint,
        operational_type, balancing_type,
        horizon, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, timepoint,
        operational_type, balancing_type,
        horizon, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw
        FROM temp_results_project_dispatch{}
        ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)

    # Load in the required operational modules
    required_opchar_modules = get_required_opchar_modules(scenario_id, c)
    imported_operational_modules = load_operational_type_modules(
        required_opchar_modules
    )

    # Import module-specific results
    for op_m in required_opchar_modules:
        if hasattr(
            imported_operational_modules[op_m], "import_model_results_to_database"
        ):
            imported_operational_modules[op_m].import_model_results_to_database(
                scenario_id, subproblem, stage, c, db, results_directory, quiet
            )
        else:
            pass


def process_results(db, c, scenario_id, subscenarios, quiet):
    """

    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """

    # Load in the required operational modules

    required_opchar_modules = get_required_opchar_modules(scenario_id, c)
    imported_operational_modules = load_operational_type_modules(
        required_opchar_modules
    )

    # Process module-specific results
    for op_m in required_opchar_modules:
        if hasattr(imported_operational_modules[op_m], "process_model_results"):
            imported_operational_modules[op_m].process_model_results(
                db, c, scenario_id, subscenarios, quiet
            )
        else:
            pass


# Operational Type Module Method Defaults
###############################################################################


def power_provision_rule(mod, prj, tmp):
    """
    If no power_provision_rule is specified in an operational type module, the
    default power provision for load-balance purposes is 0.
    """
    return 0


def online_capacity_rule(mod, g, tmp):
    """
    The default online capacity is the available capacity.
    """
    return mod.Capacity_MW[g, mod.period[tmp]] * mod.Availability_Derate[g, tmp]


def variable_om_cost_rule(mod, prj, tmp):
    """
    By default the variable cost is the power provision (for load balancing
    purposes) times the variable cost. Projects of operational type that
    produce power not used for load balancing (e.g. curtailed power or
    auxiliary power) should not use this default rule.
    """
    return mod.Power_Provision_MW[prj, tmp] * mod.variable_om_cost_per_mwh[prj]


def variable_om_cost_by_ll_rule(mod, prj, tmp, s):
    """
    By default the VOM curve cost needs to be greater than or equal to 0.
    """
    return 0


def fuel_burn_rule(mod, prj, tmp):
    """
    If no fuel_burn_rule is specified in an operational type module, the
    default fuel burn is 0.
    """
    return 0


def fuel_burn_by_ll_rule(mod, prj, tmp, s):
    """
    If no fuel_burn_by_ll_rule is specified in an operational type module, the
    default fuel burn needs to be greater than or equal to 0.
    """
    return 0


def startup_cost_simple_rule(mod, prj, tmp):
    """
    If no startup_cost_simple_rule is specified in an operational type module,
    the default startup cost is 0.
    """
    return 0


def startup_cost_by_st_rule(mod, prj, tmp):
    """
    If no startup_cost_rule is specified in an operational type module, the
    default startup fuel cost is 0.
    """
    return 0


def shutdown_cost_rule(mod, prj, tmp):
    """
    If no shutdown_cost_rule is specified in an operational type module, the
    default shutdown fuel cost is 0.
    """
    return 0


def startup_fuel_burn_rule(mod, prj, tmp):
    """
    If no startup_fuel_burn_rule is specified in an operational type module, the
    default startup fuel burn is 0.
    """
    return 0


def rec_provision_rule(mod, prj, tmp):
    """
    If no rec_provision_rule is specified in an operational type module,
    the default REC provisions is the power provision for load-balancing
    purposes.
    """
    return mod.Power_Provision_MW[prj, tmp]


def scheduled_curtailment_rule(mod, prj, tmp):
    """
    If no scheduled_curtailment_rule is specified in an operational type
    module, the default scheduled curtailment is 0.
    """
    return 0


def subhourly_curtailment_rule(mod, prj, tmp):
    """
    If no subhourly_curtailment_rule is specified in an operational type
    module, the default subhourly curtailment is 0.
    """
    return 0


def subhourly_energy_delivered_rule(mod, prj, tmp):
    """
    If no subhourly_energy_delivered_rule is specified in an operational type
    module, the default subhourly energy delivered is 0.
    """
    return 0


def operational_violation_cost_rule(mod, prj, tmp):
    """
    If no operational_violation_cost_rule is specified, the default
    operational violation cost is 0.
    """
    return 0


def curtailment_cost_rule(mod, prj, tmp):
    """
    If no curtailment_cost_rule is specified, the default curtailment cost
    is 0.
    """
    return 0


def fuel_contribution_rule(mod, prj, tmp):
    """ """
    return 0
