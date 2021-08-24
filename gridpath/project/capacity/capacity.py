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
This is a project-level module that adds to the formulation components that
describe the capacity of projects that are available to the optimization for
each period. For example, the capacity can be a fixed number or an
expression with variables depending on the project's *capacity_type*. The
project capacity can then be used to constrain operations, contribute to
reliability constraints, etc.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import \
    get_required_subtype_modules_from_projects_file, join_sets
from gridpath.project.capacity.common_functions import \
    load_project_capacity_type_modules
from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets
from gridpath.auxiliary.db_interface import setup_results_import
import gridpath.project.capacity.capacity_types as cap_type_init


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    First, we iterate over all required *capacity_types* modules (this is the
    set of distinct project capacity types in the list of projects specified
    by the user) and add the components specific to the respective
    *capacity_type* module. We do this by calling the
    *add_model_components* method of the capacity_type module if
    the method exists.

    Then, the following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`PRJ_OPR_PRDS`                                                  |
    | | *Within*: :code:`PROJECTS x PERIODS`                                  |
    |                                                                         |
    | Two-dimensional set that defines all project-period combinations when   |
    | a project can be operational (i.e. either has specified capacity or     |
    | can be build). This set is created by joining sets added by the         |
    | capacity_type modules (which is done before loading this module),       |
    | as how operational periods are determined differs by capacity type.     |
    +-------------------------------------------------------------------------+
    | | :code:`OPR_PRDS_BY_PRJ`                                               |
    | | *Defined over*: :code:`PROJECTS`                                      |
    |                                                                         |
    | Indexed set that describes the possible operational periods for each    |
    | project.                                                                |
    +-------------------------------------------------------------------------+
    | | :code:`PRJ_OPR_TMPS`                                                  |
    |                                                                         |
    | Two-dimensional set that defines all project-timepoint combinations     |
    | when a project can be operational.                                      |
    +-------------------------------------------------------------------------+
    | | :code:`OPR_PRJS_IN_TMP`                                               |
    | | *Defined over*: :code:`TMPS`                                          |
    |                                                                         |
    | Indexed set that describes all projects that could be operational in    |
    | each timepoint.                                                         |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Capacity_MW`                                                   |
    | | *Defined over*: :code:`PRJ_OPR_PRDS`                                  |
    |                                                                         |
    | Defines the project capacity in each period (in which the project can   |
    | exist) in the model. The exact formulation of the expression depends on |
    | the project's capacity_type. For each project, we call its              |
    | capacity_type module's capacity_rule method in order to formulate the   |
    | expression. E.g. a project of the gen_spec capacity_type will have a    |
    | have a pre-specified capacity whereas a project of the gen_new_lin      |
    | capacity_type will have a model variable (or sum of variables) as its   |
    | Capacity_MW.                                                            |
    +-------------------------------------------------------------------------+
    | | :code:`Energy_Capacity_MWh`                                           |
    | | *Defined over*: :code:`PRJ_OPR_PRDS`                                  |
    |                                                                         |
    | Defines the project's energy capacity in each period (in which the      |
    | project can exist). The exact formulation of the expression depends on  |
    | the project's capacity_type. For each project, we call its              |
    | capacity_type module's energy_capacity_rule method in order to          |
    | formulate the expression.                                               |
    +-------------------------------------------------------------------------+

    """

    # Dynamic Inputs
    ###########################################################################

    required_capacity_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, which_type="capacity_type"
    )

    # Import needed capacity type modules
    imported_capacity_modules = load_project_capacity_type_modules(
        required_capacity_modules
    )

    # Add any components specific to the capacity type modules
    for op_m in required_capacity_modules:
        imp_op_m = imported_capacity_modules[op_m]
        if hasattr(imp_op_m, "add_model_components"):
            imp_op_m.add_model_components(
                m, d, scenario_directory, subproblem, stage
            )

    # Sets
    ###########################################################################

    m.PRJ_OPR_PRDS = Set(
        dimen=2,
        within=m.PROJECTS * m.PERIODS,
        initialize=lambda mod:
        join_sets(mod, getattr(d, capacity_type_operational_period_sets),),
    )  # assumes capacity types model components are already added!

    m.OPR_PRDS_BY_PRJ = Set(
        m.PROJECTS,
        initialize=lambda mod, project:
        operational_periods_by_project(
            prj=project,
            project_operational_periods=mod.PRJ_OPR_PRDS
        )
    )

    m.PRJ_OPR_TMPS = Set(
        dimen=2,
        initialize=lambda mod: [
            (g, tmp) for g in mod.PROJECTS
            for p in mod.OPR_PRDS_BY_PRJ[g]
            for tmp in mod.TMPS_IN_PRD[p]
        ]
    )

    m.OPR_PRJS_IN_TMP = Set(
        m.TMPS,
        initialize=op_gens_by_tmp
    )

    # Expressions
    ###########################################################################

    def capacity_rule(mod, prj, prd):
        cap_type = mod.capacity_type[prj]
        if hasattr(imported_capacity_modules[cap_type],
                   "capacity_rule"):
            return imported_capacity_modules[cap_type]. \
                capacity_rule(mod, prj, prd)
        else:
            return cap_type_init.capacity_rule(mod, prj, prd)

    m.Capacity_MW = Expression(
        m.PRJ_OPR_PRDS,
        rule=capacity_rule
    )

    def hyb_gen_capacity_rule(mod, prj, prd):
        cap_type = mod.capacity_type[prj]
        if hasattr(imported_capacity_modules[cap_type],
                   "hyb_gen_capacity_rule"):
            return imported_capacity_modules[cap_type]. \
                hyb_gen_capacity_rule(mod, prj, prd)
        else:
            return cap_type_init.hyb_gen_capacity_rule(mod, prj, prd)

    m.Hyb_Gen_Capacity_MW = Expression(
        m.PRJ_OPR_PRDS,
        rule=hyb_gen_capacity_rule
    )

    def hyb_stor_capacity_rule(mod, prj, prd):
        cap_type = mod.capacity_type[prj]
        if hasattr(imported_capacity_modules[cap_type],
                   "hyb_stor_capacity_rule"):
            return imported_capacity_modules[cap_type]. \
                hyb_stor_capacity_rule(mod, prj, prd)
        else:
            return cap_type_init.hyb_stor_capacity_rule(mod, prj, prd)

    m.Hyb_Stor_Capacity_MW = Expression(
        m.PRJ_OPR_PRDS,
        rule=hyb_stor_capacity_rule
    )

    def energy_capacity_rule(mod, prj, prd):
        cap_type = mod.capacity_type[prj]
        if hasattr(imported_capacity_modules[cap_type],
                   "energy_capacity_rule"):
            return imported_capacity_modules[cap_type]. \
                energy_capacity_rule(mod, prj, prd)
        else:
            return cap_type_init.energy_capacity_rule(mod, prj, prd)

    m.Energy_Capacity_MWh = Expression(
        m.PRJ_OPR_PRDS,
        rule=energy_capacity_rule
    )

# Set Rules
###############################################################################

# TODO: the creation of the OPR_PRJS_IN_TMPS is by far
#  the most time-consuming step in instantiating the problem; is there
#  any way to speed it up? It is perhaps inefficient to iterate over all
#  (g, t) for every timepoint, but how do we get around having to do that?
#  Also, this is a more general problem with all the indexed sets,
#  but the larger timepoints-based sets are more of a problem
def op_gens_by_tmp(mod, tmp):
    """
    Figure out which generators are operational in each timepoins.
    """
    gens = list(
        g for (g, t) in mod.PRJ_OPR_TMPS if t == tmp
    )
    return gens


def operational_periods_by_project(prj, project_operational_periods):
    """
    """
    return list(
        set(period for (project, period) in project_operational_periods
            if project == prj)
    )


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    required_capacity_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, which_type="capacity_type"
    )

    # Import needed capacity type modules
    imported_capacity_modules = load_project_capacity_type_modules(
        required_capacity_modules
    )
    for op_m in required_capacity_modules:
        if hasattr(imported_capacity_modules[op_m],
                   "load_model_data"):
            imported_capacity_modules[op_m].load_model_data(
                m, d, data_portal, scenario_directory, subproblem, stage)
        else:
            pass


# TODO: move this to gridpath.project.capacity.__init__?
def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export capacity results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    # Total capacity for all projects
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "capacity_all.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period",
                         "capacity_type", "technology", "load_zone",
                         "capacity_mw", "hyb_gen_capacity_mw",
                         "hyb_stor_capacity_mw", "capacity_mwh"])
        for (prj, p) in m.PRJ_OPR_PRDS:
            writer.writerow([
                prj,
                p,
                m.capacity_type[prj],
                m.technology[prj],
                m.load_zone[prj],
                value(m.Capacity_MW[prj, p]),
                value(m.Hyb_Gen_Capacity_MW[prj, p]),
                value(m.Hyb_Stor_Capacity_MW[prj, p]),
                value(m.Energy_Capacity_MWh[prj, p])
            ])

    # Module-specific capacity results
    required_capacity_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, which_type="capacity_type"
    )

    # Import needed capacity type modules
    imported_capacity_modules = load_project_capacity_type_modules(
        required_capacity_modules
    )
    for op_m in required_capacity_modules:
        if hasattr(imported_capacity_modules[op_m],
                   "export_results"):
            imported_capacity_modules[
                op_m].export_results(
                scenario_directory, subproblem, stage, m, d
            )
        else:
            pass


def summarize_results(scenario_directory, subproblem, stage):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:

    Summarize capacity results
    """

    summary_results_file = os.path.join(
        scenario_directory, subproblem, stage, "results", "summary_results.txt"
    )
    # Check if the 'technology' exists in  projects.tab; if it doesn't, we
    # don't have a category to aggregate by, so we'll skip summarizing results

    # Open in 'append' mode, so that results already written by other
    # modules are not overridden
    with open(summary_results_file, "a") as outfile:
        outfile.write(
            "\n### CAPACITY RESULTS ###\n"
        )

    # Get the results CSV as dataframe
    capacity_results_df = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                     "capacity_all.csv")
    )

    required_capacity_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, which_type="capacity_type"
    )

    # Import needed capacity type modules
    imported_capacity_modules = load_project_capacity_type_modules(
        required_capacity_modules
    )
    for op_m in required_capacity_modules:
        if hasattr(imported_capacity_modules[op_m],
                   "summarize_results"):
            imported_capacity_modules[
                op_m].summarize_results(
                scenario_directory, subproblem, stage, summary_results_file
            )
        else:
            pass


# Database
###############################################################################

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
            hyb_gen_capacity_mw = None if row[6] == "" else row[6]
            hyb_stor_capacity_mw = None if row[7] == "" else row[7]
            energy_capacity_mwh = None if row[8] == "" else row[8]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 capacity_type, technology, load_zone,
                 capacity_mw, hyb_gen_capacity_mw, hyb_stor_capacity_mw,
                 energy_capacity_mwh)
            )

    insert_temp_sql = """
        INSERT INTO temp_results_project_capacity{}
        (scenario_id, project, period, subproblem_id, stage_id, capacity_type,
        technology, load_zone, capacity_mw, hyb_gen_capacity_mw, 
        hyb_stor_capacity_mw, energy_capacity_mwh)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_capacity
        (scenario_id, project, period, subproblem_id, stage_id, capacity_type,
        technology, load_zone, capacity_mw, hyb_gen_capacity_mw, 
        hyb_stor_capacity_mw, energy_capacity_mwh)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, capacity_type,
        technology, load_zone, capacity_mw, hyb_gen_capacity_mw, 
        hyb_stor_capacity_mw, energy_capacity_mwh
        FROM temp_results_project_capacity{}
        ORDER BY scenario_id, project, period, subproblem_id, 
        stage_id;""".format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)

