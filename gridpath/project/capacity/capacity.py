#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This is a project-level module that adds to the formulation components that
describe the capacity of projects that are available to the optimization for
each period. For example, the capacity can be a fixed number or an
expression with variables depending on the project's *capacity_type*. The
project capacity can then be used to constrain operations, contribute to
reliability constraints, etc.

.. note:: We will be renaming the *capacity_type* modules to a more
    intuitive convention than currently used.

"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Expression, value, BuildAction

from gridpath.auxiliary.auxiliary import \
    load_gen_storage_capacity_type_modules, join_sets
from gridpath.auxiliary.dynamic_components import required_capacity_modules, \
    capacity_type_operational_period_sets, \
    storage_only_capacity_type_operational_period_sets


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from;
        here we need the list of capacity types as well as the
        *capacity_type_operational_period_sets* list of sets after it has
        been populate by the capacity-type modules

    First, we iterate over all required *capacity_types* modules (this is the
    set of distinct project capacity types in the list of projects specified
    by the user) and add the components specific to the respective
    *capacity_type* module. We do this by calling the
    *add_module_specific_components* method of the capacity_type module if
    the method exists.

    The capacity_type modules will also add to the dynamic component class
    object's *capacity_type_operational_period_sets* attribute -- the list
    of sets we will then to get join to get the final
    *PROJECT_OPERATIONAL_PERIODS* set over which we'll define project capacity.

    The *PROJECT_OPERATIONAL_PERIODS* set is a two-dimensional set that
    defines all project-period combinations when a project can be operational
    (i.e. either has specified capacity or can be build). We designate the
    *PROJECT_OPERATIONAL_PERIODS* set with :math:`RP` and the index will be
    :math:`r,p`. This set is created by joining sets added by the
    *capacity_type* modules, as how operational periods are determined
    differs by capacity type.

    The Pyomo expression *Capacity_MW*\ :sub:`r,p`\  defines the project
    capacity in each period (in which the project can exist) in the model.
    The exact formulation of the expression depends on the project's
    *capacity_type*. For each project, we call its *capacity_type* module's
    *capacity_rule* method in order to formulate the expression. E.g. a
    project of the  *existing_gen_no_economic_retirement* capacity_type will
    have a pre-specified capacity whereas a project of the
    *new_build_generator* capacity_type will have a model variable (or sum of
    variables) as its *Capacity_MW*\ :sub:`r,p`\. This expression will then
    be used by other modules.

    Storage capacity_type modules will also add to the dynamic component class
    object's *storage_only_capacity_type_operational_period_sets* attribute
    -- the list of sets we will then to get join to get the final
    *STORAGE_OPERATIONAL_PERIODS* set over which we'll define project capacity.

    The *STORAGE_OPERATIONAL_PERIODS* set is a two-dimensional set that
    defines all project-period combinations when a storage project can exist (
    i.e. either has specified capacity or can be build). We designate the
    *STORAGE_OPERATIONAL_PERIODS* set with :math:`SP` and the index will be
    :math:`s,p`. *SP* is a subset of *RP*.

    The Pyomo expression *Energy_Capacity_MWh*\ :sub:`s,p`\  defines the
    storage project's energy capacity in each period (in which the project can
    exist) in the model. The exact formulation of the expression depends on
    the project's capacity_type. For each project, we call its capacity_type
    module's *energy_capacity_rule* method in order to formulate the
    expression.

    Finally, we derive three more sets for later usage:
    *OPERATIONAL_PERIODS_BY_PROJECT*, *PROJECT_OPERATIONAL_TIMEPOINTS*,
    and *OPERATIONAL_PROJECTS_IN_TIMEPOINT*.

    *OPERATIONAL_PERIODS_BY_PROJECT* (:math:`\{OP_r\}_{r\in R}`;
    :math:`OP_r\subset P`) is an indexed set of the operational periods
    :math:`p\in P` for each project :math:`r\in R`.

    *PROJECT_OPERATIONAL_TIMEPOINTS* (:math:`RT`) is a two-dimensional set that
    defines all project-timepoint combinations when a project can be
    operational.

    *OPERATIONAL_PROJECTS_IN_TIMEPOINT* (:math:`\{OR_{tmp}\}_{{tmp}\in T}`;
    :math:`OR_r\subset R`) is an indexed set of all the projects
    :math:`r\in R` that could be operational in each timepoint :math:`{
    tmp}\in T`.
    """
    # Import needed capacity type modules
    imported_capacity_modules = \
        load_gen_storage_capacity_type_modules(
            getattr(d, required_capacity_modules))

    # First, add any components specific to the capacity type modules
    for op_m in getattr(d, required_capacity_modules):
        imp_op_m = imported_capacity_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)

    m.PROJECT_OPERATIONAL_PERIODS = \
        Set(dimen=2,
            initialize=lambda mod: 
            join_sets(mod, getattr(d, capacity_type_operational_period_sets),),
            within=m.PROJECTS*m.PERIODS
            )

    def capacity_rule(mod, g, p):
        gen_cap_type = mod.capacity_type[g]
        return imported_capacity_modules[gen_cap_type].\
            capacity_rule(mod, g, p)

    m.Capacity_MW = Expression(m.PROJECT_OPERATIONAL_PERIODS,
                               rule=capacity_rule)

    m.STORAGE_OPERATIONAL_PERIODS = \
        Set(dimen=2,
            initialize=lambda mod: 
            join_sets(
                mod,
                getattr(d, storage_only_capacity_type_operational_period_sets)
            ),
            within=m.PROJECT_OPERATIONAL_PERIODS
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
        m.STORAGE_OPERATIONAL_PERIODS,
        rule=energy_capacity_rule)

    # Define various sets to be used in operations module
    m.OPERATIONAL_PERIODS_BY_PROJECT = \
        Set(m.PROJECTS,
            rule=lambda mod, project:
            operational_periods_by_project(
                prj=project,
                project_operational_periods=mod.PROJECT_OPERATIONAL_PERIODS
            )
            )

    m.PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod: [
                (g, tmp) for g in mod.PROJECTS
                for p in mod.OPERATIONAL_PERIODS_BY_PROJECT[g]
                for tmp in mod.TIMEPOINTS_IN_PERIOD[p]
                ]
            )

    # TODO: the creation of the OPERATIONAL_PROJECTS_IN_TIMEPOINTS is by far
    #  the most time-consuming step in instantiating the problem; is there
    #  any way to speed it up? It is perhaps inefficient to iterate over all
    #  (g, t) for every timepoint, but how do we get around having to do that?
    #  Also, this is a more general problem with all the indexed sets,
    #  but the larger timepoints-based sets are more of a problem
    def op_gens_by_tmp(mod, tmp):
        """
        Figure out which generators are operational in each timepoint
        :param mod:
        :param tmp:
        :return:
        """
        gens = list(
            g for (g, t) in mod.PROJECT_OPERATIONAL_TIMEPOINTS if t == tmp)
        return gens

    m.OPERATIONAL_PROJECTS_IN_TIMEPOINT = \
        Set(m.TIMEPOINTS, initialize=op_gens_by_tmp)


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
    imported_capacity_modules = \
        load_gen_storage_capacity_type_modules(
            getattr(d, required_capacity_modules)
        )
    for op_m in getattr(d, required_capacity_modules):
        if hasattr(imported_capacity_modules[op_m],
                   "load_module_specific_data"):
            imported_capacity_modules[op_m].load_module_specific_data(
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
    :param d:
    :return:
    """

    # Total capacity for all projects
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "capacity_all.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "technology", "load_zone",
                         "capacity_mw", "capacity_mwh"])
        for (prj, p) in m.PROJECT_OPERATIONAL_PERIODS:
            writer.writerow([
                prj,
                p,
                m.technology[prj],
                m.load_zone[prj],
                value(m.Capacity_MW[prj, p]),
                value(m.Energy_Capacity_MWh[prj, p])
                if (prj, p) in m.STORAGE_OPERATIONAL_PERIODS else None
            ])

    # Module-specific capacity results
    imported_capacity_modules = \
        load_gen_storage_capacity_type_modules(
            getattr(d, required_capacity_modules)
        )
    for op_m in getattr(d, required_capacity_modules):
        if hasattr(imported_capacity_modules[op_m],
                   "export_module_specific_results"):
            imported_capacity_modules[
                op_m].export_module_specific_results(
                scenario_directory, horizon, stage, m, d
            )
        else:
            pass


def summarize_results(d, problem_directory, horizon, stage):
    """
    Summarize capacity results
    :param d:
    :param problem_directory:
    :param horizon:
    :param stage:
    :return:
    """

    summary_results_file = os.path.join(
        problem_directory, horizon, stage, "results", "summary_results.txt"
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
    capacity_results_df = \
        pd.read_csv(os.path.join(problem_directory, horizon, stage, "results",
                                 "capacity_all.csv")
                    )

    capacity_results_agg_df = \
        capacity_results_df.groupby(by=["load_zone", "technology",
                                        'period'],
                                    as_index=True
                                    ).sum()

    imported_capacity_modules = \
        load_gen_storage_capacity_type_modules(
            getattr(d, required_capacity_modules)
        )
    for op_m in getattr(d, required_capacity_modules):
        if hasattr(imported_capacity_modules[op_m],
                   "summarize_module_specific_results"):
            imported_capacity_modules[
                op_m].summarize_module_specific_results(
                problem_directory, horizon, stage, summary_results_file
            )
        else:
            pass


def import_results_into_database(scenario_id, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # Capacity results
    print("project capacity")
    c.execute(
        """DELETE FROM results_project_capacity_all 
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_project_capacity_all"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_capacity_all"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        project VARCHAR(64),
        period INTEGER,
        technology VARCHAR(32),
        load_zone VARCHAR(32),
        capacity_mw FLOAT,
        energy_capacity_mwh FLOAT,
        PRIMARY KEY (scenario_id, project, period)
        );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory, "capacity_all.csv"), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            technology = row[2]
            load_zone = row[3]
            capacity_mw = row[4]
            energy_capacity_mwh = 'NULL' if row[5] == "" else row[5]

            c.execute(
                """INSERT INTO temp_results_project_capacity_all"""
                + str(scenario_id) + """
                (scenario_id, project, period, technology, load_zone,
                capacity_mw, energy_capacity_mwh)
                VALUES ({}, '{}', {}, '{}', '{}', {}, {});""".format(
                    scenario_id, project, period, technology, load_zone,
                    capacity_mw, energy_capacity_mwh,
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_capacity_all
        (scenario_id, project, period, technology, load_zone,
        capacity_mw, energy_capacity_mwh)
        SELECT
        scenario_id, project, period, technology, load_zone,
        capacity_mw, energy_capacity_mwh
        FROM temp_results_project_capacity_all""" + str(scenario_id) + """
        ORDER BY scenario_id, project, period;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_capacity_all""" + str(scenario_id) +
        """;"""
    )
    db.commit()


def operational_periods_by_project(prj, project_operational_periods):
    """

    :param prj:
    :param project_operational_periods:
    :return:
    """
    return set(period for (project, period) in project_operational_periods
               if project == prj
               )
