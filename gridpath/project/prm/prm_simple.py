#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Simplest PRM contribution where each PRM project contributes a fraction of 
its installed capacity.
"""

import csv
import os.path
from pyomo.environ import Param, PercentFraction, Expression, value


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # The fraction of installed capacity that counts for the PRM
    # Set this to 0 if project is included in an endogenous method for
    # determining ELCC
    m.elcc_simple_fraction = Param(m.PRM_PROJECTS, within=PercentFraction)

    def elcc_simple_rule(mod, g, p):
        """
        
        :param g: 
        :param p: 
        :return: 
        """
        return mod.Capacity_MW[g, p] * mod.elcc_simple_fraction[g]

    m.PRM_Simple_Contribution_MW = Expression(
        m.PRM_PROJECT_OPERATIONAL_PERIODS, rule=elcc_simple_rule
    )


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
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     select=("project", "elcc_simple_fraction"),
                     param=(m.elcc_simple_fraction,)
                     )


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "prm_project_elcc_simple_contribution.csv"),
              "wb") as \
            results_file:
        writer = csv.writer(results_file)
        writer.writerow(["project", "period",
                         "capacity_mw",
                         "elcc_simple_fraction",
                         "prm_contribution_mw"])
        for (prj, period) in m.PRM_PROJECT_OPERATIONAL_PERIODS:
            writer.writerow([
                prj,
                period,
                value(m.Capacity_MW[prj, period]),
                value(m.elcc_simple_fraction[prj]),
                value(m.PRM_Simple_Contribution_MW[prj, period])
            ])


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    project_zones = c.execute(
        """SELECT project, elcc_simple_fraction
        FROM inputs_project_elcc_chars
            WHERE project_elcc_chars_scenario_id = {}""".format(
            subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
        )
    ).fetchall()

    # Make a dict for easy access
    prj_frac_dict = dict()
    for (prj, zone) in project_zones:
        prj_frac_dict[str(prj)] = "." if zone is None else str(zone)

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t")

        new_rows = list()

        # Append column header
        header = reader.next()
        header.append("elcc_simple_fraction")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in prj_frac_dict.keys():
                row.append(prj_frac_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(inputs_directory, "projects.tab"), "w") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t")
        writer.writerows(new_rows)
