#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import os.path
import pandas as pd
from pyomo.environ import Set, Expression

from gridpath.auxiliary.auxiliary import \
    load_gen_storage_capacity_type_modules, join_sets, \
    make_project_time_var_df, check_if_technology_column_exists
from gridpath.auxiliary.dynamic_components import required_capacity_modules, \
    capacity_type_operational_period_sets, \
    storage_only_capacity_type_operational_period_sets


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
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
            join_sets(mod, getattr(d, capacity_type_operational_period_sets))
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
            )
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

    d.module_specific_df = []

    imported_capacity_modules = \
        load_gen_storage_capacity_type_modules(
            getattr(d, required_capacity_modules)
        )
    for op_m in getattr(d, required_capacity_modules):
        if hasattr(imported_capacity_modules[op_m],
                   "export_module_specific_results"):
            imported_capacity_modules[
                op_m].export_module_specific_results(m, d)
        else:
            pass

    capacity_df = make_project_time_var_df(
        m,
        "PROJECT_OPERATIONAL_PERIODS",
        "Capacity_MW",
        ["project", "period"],
        "capacity_mw"
    )

    # Storage is not required, so only make this dataframe if
    # STORAGE_OPERATIONAL_PERIODS set is not empty
    if len(getattr(m, "STORAGE_OPERATIONAL_PERIODS")) > 0:
        energy_capacity_df = make_project_time_var_df(
            m,
            "STORAGE_OPERATIONAL_PERIODS",
            "Energy_Capacity_MWh",
            ["project", "period"],
            "energy_capacity_mwh"
        )
    else:
        energy_capacity_df = []

    # Merge and export dataframes
    dfs_to_merge = [capacity_df] + [energy_capacity_df] + d.module_specific_df

    df_for_export = reduce(lambda left, right:
                           left.join(right, how="outer"),
                           dfs_to_merge)
    df_for_export.to_csv(
        os.path.join(scenario_directory, horizon, stage, "results",
                     "capacity.csv"),
        header=True, index=True)


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

    if not check_if_technology_column_exists(problem_directory):
        with open(summary_results_file, "a") as outfile:
            outfile.write(
                "...skipping aggregating capacity results: column '"
                "technology' not found in projects.tab"
            )
    else:
        # Get the technology for each project by which we'll aggregate
        project_tech = \
            pd.read_csv(
                os.path.join(problem_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project", "load_zone",
                                   "technology"]
            )
        project_tech.set_index(["project"], inplace=True,
                               verify_integrity=True)

        # Get the results CSV as dataframe
        capacity_results = \
            pd.read_csv(os.path.join(problem_directory, "results",
                                     "capacity.csv")
                        )
        capacity_results.set_index(["project"], inplace=True)

        # Join the two dataframes (i.e. add technology column)
        capacity_results_df = \
            pd.merge(left=capacity_results, right=project_tech, how="left",
                     left_index=True, right_index=True)

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
                    capacity_results_agg_df, summary_results_file
                )
            else:
                pass


def operational_periods_by_project(prj, project_operational_periods):
    """

    :param prj:
    :param project_operational_periods:
    :return:
    """
    return set(period for (project, period) in project_operational_periods
               if project == prj
               )
