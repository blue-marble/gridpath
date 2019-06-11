#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.project.capacity.costs** module is a project-level
module that adds to the formulation components that describe the
capacity-related costs of projects (e.g. investment capital costs and fixed
O&M costs).
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Expression, value

from gridpath.auxiliary.dynamic_components import required_capacity_modules
from gridpath.auxiliary.auxiliary import load_gen_storage_capacity_type_modules


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    For each project and operational period, determine its capacity-related
    cost in the period based on its *capacity_type*. For the purpose,
    call the *capacity_cost_rule* method from the respective capacity-type
    module. The expression component added to the model is
    :math:`Capacity\_Cost\_in\_Period_{r, p}`. This expression will then be
    used by other model components. See formulation in the *capacity_type*
    modules.
    """

    # Import needed capacity type modules
    imported_capacity_modules = \
        load_gen_storage_capacity_type_modules(
            getattr(d, required_capacity_modules)
        )

    def capacity_cost_rule(mod, g, p):
        """
        Get capacity cost for each generator's respective capacity module
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return imported_capacity_modules[mod.capacity_type[g]].\
            capacity_cost_rule(mod, g, p)
    m.Capacity_Cost_in_Period = \
        Expression(m.PROJECT_OPERATIONAL_PERIODS,
                   rule=capacity_cost_rule)


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
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "costs_capacity_all_projects.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "technology", "load_zone",
             "annualized_capacity_cost"]
        )
        for (prj, p) in m.PROJECT_OPERATIONAL_PERIODS:
            writer.writerow([
                prj,
                p,
                m.technology[prj],
                m.load_zone[prj],
                value(m.Capacity_Cost_in_Period[prj, p])
            ])


def import_results_into_database(scenario_id, c, db, results_directory):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # Capacity cost results
    print("project capacity costs")
    c.execute(
        """DELETE FROM results_project_costs_capacity
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS temp_results_project_costs_capacity"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_costs_capacity"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        project VARCHAR(64),
        period INTEGER,
        technology VARCHAR(32),
        load_zone VARCHAR(32),
        annualized_capacity_cost FLOAT,
        PRIMARY KEY (scenario_id, project, period)
        );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "costs_capacity_all_projects.csv"), "r") as \
            capacity_costs_file:
        reader = csv.reader(capacity_costs_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            technology = row[2]
            load_zone = row[3]
            annualized_capacity_cost = row[4]

            c.execute(
                """INSERT INTO temp_results_project_costs_capacity"""
                + str(scenario_id) + """
                (scenario_id, project, period, technology, load_zone,
                annualized_capacity_cost)
                VALUES ({}, '{}', {}, '{}', '{}', {});""".format(
                    scenario_id, project, period, technology, load_zone,
                    annualized_capacity_cost
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_costs_capacity
        (scenario_id, project, period, technology, load_zone,
        annualized_capacity_cost)
        SELECT
        scenario_id, project, period, technology, load_zone,
        annualized_capacity_cost
        FROM temp_results_project_costs_capacity""" + str(scenario_id) + """
        ORDER BY scenario_id, project, period;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_costs_capacity""" + str(scenario_id) +
        """;"""
    )
    db.commit()
