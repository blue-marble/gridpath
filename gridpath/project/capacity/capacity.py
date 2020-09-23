#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

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

from gridpath.auxiliary.auxiliary import get_required_subtype_modules, \
    load_gen_storage_capacity_type_modules, join_sets
from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets, \
    storage_only_capacity_type_operational_period_sets


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    First, we iterate over all required *capacity_types* modules (this is the
    set of distinct project capacity types in the list of projects specified
    by the user) and add the components specific to the respective
    *capacity_type* module. We do this by calling the
    *add_module_specific_components* method of the capacity_type module if
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
    | | :code:`STOR_OPR_PRDS`                                                 |
    | | *Within*: :code:`PRJ_OPR_PRDS`                                        |
    |                                                                         |
    | Two-dimensional set that defines all project-period combinations when a |
    | when a storage projects can be operational, i.e. either has specified   |
    | capacity or can be built).                                              |
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
    | | *Defined over*: :code:`STOR_OPR_PRDS`                                 |
    |                                                                         |
    | Defines the storage project's energy capacity in each period (in which  |
    | the project can exist). The exact formulation of the expression depends |
    | on the project's capacity_type. For each project, we call its           |
    | capacity_type module's energy_capacity_rule method in order to          |
    | formulate the expression.                                               |
    +-------------------------------------------------------------------------+

    """

    # Dynamic Components
    ###########################################################################

    required_capacity_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, which_type="capacity_type"
    )

    # Import needed capacity type modules
    imported_capacity_modules = load_gen_storage_capacity_type_modules(
        required_capacity_modules
    )

    # Add any components specific to the capacity type modules
    for op_m in required_capacity_modules:
        imp_op_m = imported_capacity_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)

    # Sets
    ###########################################################################

    m.PRJ_OPR_PRDS = Set(
        dimen=2,
        within=m.PROJECTS * m.PERIODS,
        initialize=lambda mod:
        join_sets(mod, getattr(di, capacity_type_operational_period_sets),),
    )  # assumes capacity types model components are already added!

    m.STOR_OPR_PRDS = Set(
        dimen=2,
        within=m.PRJ_OPR_PRDS,
        initialize=lambda mod:
        join_sets(mod, getattr(
            di, storage_only_capacity_type_operational_period_sets)),
    )  # assumes storage capacity type model components are already added!

    m.OPR_PRDS_BY_PRJ = Set(
        m.PROJECTS,
        rule=lambda mod, project:
        operational_periods_by_project(
            prj=project,
            project_operational_periods=mod.PRJ_OPR_PRDS
        )
    )

    m.PRJ_OPR_TMPS = Set(
        dimen=2,
        rule=lambda mod: [
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

    def capacity_rule(mod, g, p):
        gen_cap_type = mod.capacity_type[g]
        return imported_capacity_modules[gen_cap_type].capacity_rule(mod, g, p)

    m.Capacity_MW = Expression(
        m.PRJ_OPR_PRDS,
        rule=capacity_rule
    )

    def energy_capacity_rule(mod, g, p):
        cap_type = mod.capacity_type[g]
        if hasattr(imported_capacity_modules[cap_type], "energy_capacity_rule"):
            return imported_capacity_modules[cap_type]. \
                energy_capacity_rule(mod, g, p)
        else:
            raise Exception("Project " + str(g)
                            + " is of capacity type " + str(cap_type)
                            + ". This capacity type module does not have "
                            + "a function 'energy_capacity_rule,' "
                            + "but " + str(g)
                            + " is defined as storage project.")

    m.Energy_Capacity_MWh = Expression(
        m.STOR_OPR_PRDS,
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
    return set(
        period for (project, period) in project_operational_periods
        if project == prj
    )


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    imported_capacity_modules = load_gen_storage_capacity_type_modules(
        getattr(d, required_capacity_modules)
    )
    for op_m in getattr(d, required_capacity_modules):
        if hasattr(imported_capacity_modules[op_m],
                   "load_module_specific_data"):
            imported_capacity_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, subproblem, stage)
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
                         "capacity_mw", "capacity_mwh"])
        for (prj, p) in m.PRJ_OPR_PRDS:
            writer.writerow([
                prj,
                p,
                m.capacity_type[prj],
                m.technology[prj],
                m.load_zone[prj],
                value(m.Capacity_MW[prj, p]),
                value(m.Energy_Capacity_MWh[prj, p])
                if (prj, p) in m.STOR_OPR_PRDS else None
            ])

    # Module-specific capacity results
    imported_capacity_modules = load_gen_storage_capacity_type_modules(
        getattr(d, required_capacity_modules)
    )
    for op_m in getattr(d, required_capacity_modules):
        if hasattr(imported_capacity_modules[op_m],
                   "export_module_specific_results"):
            imported_capacity_modules[
                op_m].export_module_specific_results(
                scenario_directory, subproblem, stage, m, d
            )
        else:
            pass


def summarize_results(d, scenario_directory, subproblem, stage):
    """
    Summarize capacity results
    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
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

    # TODO: remove this since not used?
    capacity_results_agg_df = capacity_results_df.groupby(
        by=["load_zone", "technology", 'period'],
        as_index=True
    ).sum()

    imported_capacity_modules = load_gen_storage_capacity_type_modules(
        getattr(d, required_capacity_modules)
    )
    for op_m in getattr(d, required_capacity_modules):
        if hasattr(imported_capacity_modules[op_m],
                   "summarize_module_specific_results"):
            imported_capacity_modules[
                op_m].summarize_module_specific_results(
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
    The capacity_all.csv file is imported by
    gridpath.project.capacity.capacity_types.__init__.py
    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    pass

