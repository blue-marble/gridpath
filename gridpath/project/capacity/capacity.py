#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Expression, value

from gridpath.auxiliary.auxiliary import \
    load_gen_storage_capacity_type_modules, join_sets, make_project_time_var_df
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
    print("capacity")
    c.execute(
        """DELETE FROM results_capacity_all WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_capacity_all"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_capacity_all""" + str(scenario_id) + """(
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

        reader.next()  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            technology = row[2]
            load_zone = row[3]
            capacity_mw = row[4]
            energy_capacity_mwh = 'NULL' if row[5] == "" else row[5]

            c.execute(
                """INSERT INTO temp_results_capacity_all"""
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
        """INSERT INTO results_capacity_all
        (scenario_id, project, period, technology, load_zone,
        capacity_mw, energy_capacity_mwh)
        SELECT
        scenario_id, project, period, technology, load_zone,
        capacity_mw, energy_capacity_mwh
        FROM temp_results_capacity_all""" + str(scenario_id) + """
        ORDER BY scenario_id, project, period;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_capacity_all""" + str(scenario_id) +
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
