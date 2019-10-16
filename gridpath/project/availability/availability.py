#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from pyomo.environ import Expression


from gridpath.auxiliary.auxiliary import load_subtype_modules
from gridpath.auxiliary.dynamic_components import required_availability_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed availability type modules
    imported_availability_modules = \
        load_availability_type_modules(
            getattr(d, required_availability_modules))

    # First, add any components specific to the availability type modules
    for op_m in getattr(d, required_availability_modules):
        imp_op_m = imported_availability_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)

    def availability_derate_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        # TODO: make the no_availability type module, which will be the
        #  default for the availability type param (it will just return 1 as
        #  the derate)
        availability_type = mod.availability_type[g]
        return imported_availability_modules[availability_type]. \
            availability_derate_rule(mod, g, tmp)

    m.Availability_Derate = Expression(
        m.PROJECT_OPERATIONAL_TIMEPOINTS, rule=availability_derate_rule
    )


def write_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:

    Get inputs from database and write out the model input .tab files
    """
    c = conn.cursor()
    # Load in the required capacity type modules
    scenario_id = subscenarios.SCENARIO_ID
    required_availability_type_modules = \
        get_required_availability_type_modules(scenario_id, c)

    imported_availability_type_modules = load_availability_type_modules(
        required_availability_type_modules)

    # Get module-specific inputs
    for op_m in required_availability_type_modules:
        if hasattr(imported_availability_type_modules[op_m],
                   "write_module_specific_model_inputs"):
            imported_availability_type_modules[op_m].\
                write_module_specific_model_inputs(
                    inputs_directory, subscenarios, subproblem, stage, conn)
        else:
            pass


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
    imported_availability_modules = \
        load_availability_type_modules(
            getattr(d, required_availability_modules)
        )
    for op_m in getattr(d, required_availability_modules):
        if hasattr(imported_availability_modules[op_m],
                   "load_module_specific_data"):
            imported_availability_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, subproblem, stage)
        else:
            pass


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:

    Export availability results.
    """

    # Module-specific capacity results
    imported_availability_modules = \
        load_availability_type_modules(
            getattr(d, required_availability_modules)
        )
    for op_m in getattr(d, required_availability_modules):
        if hasattr(imported_availability_modules[op_m],
                   "export_module_specific_results"):
            imported_availability_modules[
                op_m].export_module_specific_results(
                scenario_directory, subproblem, stage, m, d
            )
        else:
            pass


def import_results_into_database(scenario_id, subproblem, stage,
                                 c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """

    # Load in the required capacity type modules
    required_availability_type_modules = \
        get_required_availability_type_modules(scenario_id, c)
    imported_availability_modules = \
        load_availability_type_modules(required_availability_type_modules)

    # Import module-specific results
    for op_m in required_availability_type_modules:
        if hasattr(imported_availability_modules[op_m],
                   "import_module_specific_results_into_database"):
            imported_availability_modules[op_m]. \
                import_module_specific_results_into_database(
                scenario_id, subproblem, stage, c, db, results_directory
            )
        else:
            pass


def validate_inputs(subscenarios, subproblem, stage, conn):
    """

    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """
    # Load in the required operational modules
    c = conn.cursor()
    scenario_id = subscenarios.SCENARIO_ID
    required_opchar_modules = get_required_availability_type_modules(
        scenario_id, c)
    imported_operational_modules = load_availability_type_modules(
        required_opchar_modules)

    # Validate module-specific inputs
    for op_m in required_opchar_modules:
        if hasattr(imported_operational_modules[op_m],
                   "validate_module_specific_inputs"):
            imported_operational_modules[op_m]. \
                validate_module_specific_inputs(
                subscenarios, subproblem, stage, conn)
        else:
            pass


# TODO: this seems like a better place for this function than
#  auxiliary.auxiliary, but it's inconsistent with the rest of the types
def load_availability_type_modules(required_availability_types):
    """

    :param required_availability_types:
    :return:
    """
    return load_subtype_modules(
        required_subtype_modules=required_availability_types,
        package="gridpath.project.availability.availability_types",
        required_attributes=["availability_derate_rule"]
    )


def get_required_availability_type_modules(scenario_id, c):
    """
    :param scenario_id: user-specified scenario ID
    :param c: database cursor
    :return: List of the required capacity type submodules

    Get the required availability type submodules based on the database inputs
    for the specified scenario_id. Required modules are the unique set of
    generator availability types in the scenario's portfolio. Get the list
    based on the project_availability_scenario_id of the scenario_id.

    This list will be used to know for which availability type submodules we
    should validate inputs, get inputs from database , or save results to
    database.

    Note: once we have determined the dynamic components, this information
    will also be stored in the DynamicComponents class object.
    """

    project_availability_scenario_id = c.execute(
        """SELECT project_availability_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    required_availability_type_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT availability_type 
            FROM inputs_project_availability_types
            WHERE project_availability_scenario_id = {}""".format(
                project_availability_scenario_id
            )
        ).fetchall()
    ]

    return required_availability_type_modules
