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

from pyomo.environ import Expression

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import get_required_subtype_modules_from_projects_file, \
    load_subtype_modules


def add_model_components(m, d, subproblem_stage_directory):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed availability type modules
    required_availability_modules = \
        get_required_subtype_modules_from_projects_file(
            subproblem_stage_directory=subproblem_stage_directory,
            which_type="availability_type"
        )
    imported_availability_modules = \
        load_availability_type_modules(required_availability_modules)

    # First, add any components specific to the availability type modules
    for op_m in required_availability_modules:
        imp_op_m = imported_availability_modules[op_m]
        if hasattr(imp_op_m, "add_model_components"):
            imp_op_m.add_model_components(m, d, subproblem_stage_directory)

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
        m.PRJ_OPR_TMPS, rule=availability_derate_rule
    )


def write_model_inputs(
        scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:

    Get inputs from database and write out the model input .tab files
    """
    c = conn.cursor()
    # Load in the required capacity type modules

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
                    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn)
        else:
            pass


def load_model_data(
    m, d, data_portal, scenario_directory, subproblem, stage,
    subproblem_stage_directory
):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    required_availability_modules = \
        get_required_subtype_modules_from_projects_file(
            subproblem_stage_directory=subproblem_stage_directory,
            which_type="availability_type"
        )
    imported_availability_modules = \
        load_availability_type_modules(
            required_availability_modules
        )
    for op_m in required_availability_modules:
        if hasattr(imported_availability_modules[op_m],
                   "load_module_specific_data"):
            imported_availability_modules[op_m].load_module_specific_data(
                m, d, data_portal, scenario_directory, subproblem, stage,
                subproblem_stage_directory)
        else:
            pass


def export_results(scenario_directory, subproblem, stage, m, d, subproblem_stage_directory):
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
    required_availability_modules = \
        get_required_subtype_modules_from_projects_file(
        subproblem_stage_directory=subproblem_stage_directory,
            which_type="availability_type"
    )
    imported_availability_modules = \
        load_availability_type_modules(
            required_availability_modules
        )
    for op_m in required_availability_modules:
        if hasattr(imported_availability_modules[op_m],
                   "export_module_specific_results"):
            imported_availability_modules[
                op_m].export_module_specific_results(
                scenario_directory, subproblem,
                stage, m, d, subproblem_stage_directory
            )
        else:
            pass


def import_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """

    # Delete prior results for endogenous types
    del_sql = """
        DELETE FROM results_project_availability_endogenous 
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=del_sql,
                          data=(scenario_id, subproblem, stage), many=False)

    # Load in the required availability type modules
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
                scenario_id, subproblem, stage, c, db, results_directory, quiet
            )
        else:
            pass


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """

    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """
    # Load in the required operational modules
    c = conn.cursor()

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
                scenario_id, subscenarios, subproblem, stage, conn)
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

    project_portfolio_scenario_id = c.execute(
        """SELECT project_portfolio_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    project_availability_scenario_id = c.execute(
        """SELECT project_availability_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    required_availability_type_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT availability_type 
            FROM 
            (SELECT project FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}) as prj_tbl
            INNER JOIN 
            (SELECT project, availability_type
            FROM inputs_project_availability
            WHERE project_availability_scenario_id = {}) as av_type_tbl
            USING (project)""".format(
                project_portfolio_scenario_id,
                project_availability_scenario_id
            )
        ).fetchall()
    ]

    return required_availability_type_modules
