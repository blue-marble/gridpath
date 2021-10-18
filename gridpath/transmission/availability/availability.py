# Copyright 2016-2021 Blue Marble Analytics LLC.
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
import os.path

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import \
    get_required_subtype_modules_from_projects_file, load_subtype_modules
from gridpath.project.common_functions import determine_project_subset


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed availability type modules
    required_availability_modules = \
        get_required_subtype_modules_from_projects_file(
            scenario_directory=scenario_directory, subproblem=subproblem,
            stage=stage, which_type="availability_type"
        )
    imported_availability_modules = \
        load_availability_type_modules(required_availability_modules)

    # First, add any components specific to the availability type modules
    for op_m in required_availability_modules:
        imp_op_m = imported_availability_modules[op_m]
        if hasattr(imp_op_m, "add_model_components"):
            imp_op_m.add_model_components(
                m, d, scenario_directory, subproblem, stage
            )

    def availability_derate_rule(mod, tx, tmp):
        """

        :param mod:
        :param tx:
        :param tmp:
        :return:
        """
        availability_type = mod.tx_availability_type[tx]
        return imported_availability_modules[availability_type]. \
            availability_derate_rule(mod, tx, tmp)

    m.Tx_Availability_Derate = Expression(
        m.TX_OPR_TMPS, rule=availability_derate_rule
    )


# Input-Output
###############################################################################

def load_model_data(
    m, d, data_portal, scenario_directory, subproblem, stage
):
    """
    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    # Figure out which lines have this availability type
    # TODO: move determine_project_subset and rename, as we're using for tx too
    tx_subset = determine_project_subset(
        scenario_directory=scenario_directory,
        subproblem=subproblem, stage=stage, column="tx_availability_type",
        type="exogenous", prj_or_tx="transmission_line"
    )

    data_portal.data()["TX_AVL_EXOG"] = {None: tx_subset}

    # Availability derates
    # Get any derates from the tx_availability.tab file if it exists;
    # if it does not exist, all transmission lines will get 1 as a derate; if
    # it does exist but tx lines are not specified in it, they will also get 1
    # assigned as their derate
    # The test examples do not currently have a
    # transmission_availability_exogenous.tab, but use the default instead
    availability_file = os.path.join(
        scenario_directory, subproblem, stage, "inputs",
        "transmission_availability_exogenous.tab"
    )

    if os.path.exists(availability_file):
        data_portal.load(
            filename=availability_file,
            param=m.tx_avl_exog_derate
        )
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
    required_availability_modules = \
        get_required_subtype_modules_from_projects_file(
            scenario_directory=scenario_directory, subproblem=subproblem,
            stage=stage, which_type="tx_availability_type",
            prj_or_tx="transmission_line"
        )
    imported_availability_modules = \
        load_availability_type_modules(
            required_availability_modules
        )
    for op_m in required_availability_modules:
        if hasattr(imported_availability_modules[op_m],
                   "export_results"):
            imported_availability_modules[
                op_m].export_results(
                scenario_directory, subproblem, stage, m, d
            )
        else:
            pass


# Database
###############################################################################

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
                   "write_model_inputs"):
            imported_availability_type_modules[op_m]. \
                write_model_inputs(
                scenario_directory, scenario_id, subscenarios, subproblem,
                stage, conn
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

    # Load in the required availability type modules
    required_availability_type_modules = \
        get_required_availability_type_modules(scenario_id, c)
    imported_availability_modules = \
        load_availability_type_modules(required_availability_type_modules)

    # Import module-specific results
    for op_m in required_availability_type_modules:
        if hasattr(imported_availability_modules[op_m],
                   "import_results_into_database"):
            imported_availability_modules[op_m]. \
                import_results_into_database(
                scenario_id, subproblem, stage, c, db, results_directory, quiet
            )
        else:
            pass


# Auxiliary functions
###############################################################################
def get_required_availability_type_modules(scenario_id, c):
    """
    :param scenario_id: user-specified scenario ID
    :param c: database cursor
    :return: List of the required capacity type submodules

    Get the required availability type submodules based on the database inputs
    for the specified scenario_id. Required modules are the unique set of
    tx line availability types in the scenario's portfolio. Get the list
    based on the transmission_availability_scenario_id of the scenario_id.

    This list will be used to know for which availability type submodules we
    should validate inputs, get inputs from database , or save results to
    database.

    Note: once we have determined the dynamic components, this information
    will also be stored in the DynamicComponents class object.
    """

    transmission_portfolio_scenario_id = c.execute(
        """SELECT transmission_portfolio_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    transmission_availability_scenario_id = c.execute(
        """SELECT transmission_availability_scenario_id 
        FROM scenarios 
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    required_availability_type_modules = [
        p[0] for p in c.execute(
            """SELECT DISTINCT availability_type 
            FROM 
            (SELECT transmission_line FROM inputs_transmission_portfolios
            WHERE transmission_portfolio_scenario_id = {}) as prj_tbl
            INNER JOIN 
            (SELECT transmission_line, availability_type
            FROM inputs_transmission_availability
            WHERE transmission_availability_scenario_id = {}) as av_type_tbl
            USING (transmission_line)""".format(
                transmission_portfolio_scenario_id,
                transmission_availability_scenario_id
            )
        ).fetchall()
    ]

    return required_availability_type_modules


def load_availability_type_modules(required_availability_types):
    """

    :param required_availability_types:
    :return:
    """
    return load_subtype_modules(
        required_subtype_modules=required_availability_types,
        package="gridpath.transmission.availability.availability_types",
        required_attributes=["availability_derate_rule"]
    )
