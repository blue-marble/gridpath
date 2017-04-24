#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Contributions to ELCC surface
"""

import csv
import os.path
from pyomo.environ import Param, Set, Var, Constraint, NonNegativeReals, \
    Binary, Expression, value


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Which projects contribute to the PRM surface
    m.contributes_to_elcc_surface = Param(m.PRM_PROJECTS, within=Binary)
    m.ELCC_SURFACE_PROJECTS = Set(
        within=m.PRM_PROJECTS,
        initialize=lambda mod: [p for p in mod.PRM_PROJECTS if
                                mod.contributes_to_elcc_surface[p]]
    )

    m.ELCC_SURFACE_PROJECTS_BY_PRM_ZONE = \
        Set(m.PRM_ZONES, within=m.ELCC_SURFACE_PROJECTS,
            initialize=lambda mod, prm_z:
            [p for p in mod.ELCC_SURFACE_PROJECTS
             if mod.prm_zone[p] == prm_z])

    # The coefficient for each project contributing to the ELCC surface
    # Surface is limited to 1000 facets
    m.PROJECT_PERIOD_ELCC_SURFACE_FACETS = Set(
        dimen=3, within=m.ELCC_SURFACE_PROJECTS * m.PERIODS * range(1, 1001)
    )

    # The project coefficient for the surface
    # This goes into the piecewise linear constraint for the aggregate ELCC
    # calculation; unless we have a very detailed surface, this coefficient
    # would actually likely only vary by technology (e.g. wind and solar for a
    # 2-dimensional surface), but we have it by project here for maximum
    # flexibility
    m.elcc_surface_coefficient = Param(
        m.PROJECT_PERIOD_ELCC_SURFACE_FACETS, within=NonNegativeReals
    )

    # TODO: how to define this for operational periods only
    # ELCC surface contribution of each project
    def elcc_surface_contribution_rule(mod, prj, p, f):
        """
        
        :param mod: 
        :param prj: 
        :param p: 
        :param f: 
        :return: 
        """
        if (prj, p) in mod.PROJECT_OPERATIONAL_PERIODS:
            return mod.elcc_surface_coefficient[prj, p, f] \
                * mod.Capacity_MW[prj, p]
        else:
            return 0

    m.ELCC_Surface_Contribution_MW = Expression(
        m.PROJECT_PERIOD_ELCC_SURFACE_FACETS,
        rule=elcc_surface_contribution_rule
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
    # Projects that contribute to the ELCC surface
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     select=("project", "contributes_to_elcc_surface"),
                     param=(m.contributes_to_elcc_surface,)
                     )

    # Project-period-facet
    data_portal.load(filename=os.path.join(
        scenario_directory, horizon, stage, "inputs",
        "project_elcc_surface_coefficients.tab"
    ),
                     index=m.PROJECT_PERIOD_ELCC_SURFACE_FACETS,
                     param=m.elcc_surface_coefficient,
                     select=("project", "period", "facet",
                             "elcc_surface_coefficient")
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
                           "prm_project_elcc_surface_contribution.csv"),
              "wb") as \
            results_file:
        writer = csv.writer(results_file)
        writer.writerow(["project", "period",
                         "capacity_mw",
                         "facet", "elcc_surface_coefficient",
                         "elcc_mw"])
        for (prj, period, facet) in m.PROJECT_PERIOD_ELCC_SURFACE_FACETS:
            writer.writerow([
                prj,
                period,
                value(m.Capacity_MW[prj, period]),
                facet,
                value(m.elcc_surface_coefficient[prj, period, facet]),
                value(m.ELCC_Surface_Contribution_MW[prj, period, facet])
            ])


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    # Which projects will contribute to the surface
    project_contr = c.execute(
        """SELECT project, contributes_to_elcc_surface
        FROM inputs_project_elcc_chars
            WHERE project_elcc_chars_scenario_id = {}""".format(
            subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID
        )
    ).fetchall()

    # Make a dict for easy access
    prj_contr_dict = dict()
    for (prj, zone) in project_contr:
        prj_contr_dict[str(prj)] = "." if zone is None else str(zone)

    with open(os.path.join(inputs_directory, "projects.tab"), "r"
              ) as projects_file_in:
        reader = csv.reader(projects_file_in, delimiter="\t")

        new_rows = list()

        # Append column header
        header = reader.next()
        header.append("contributes_to_elcc_surface")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if BA specified or not
            if row[0] in prj_contr_dict.keys():
                row.append(prj_contr_dict[row[0]])
                new_rows.append(row)
            # If project not specified, specify no BA
            else:
                row.append(".")
                new_rows.append(row)

    with open(os.path.join(inputs_directory, "projects.tab"), "w") as \
            projects_file_out:
        writer = csv.writer(projects_file_out, delimiter="\t")
        writer.writerows(new_rows)

    # The coefficients for the surface
    coefficients = c.execute(
        """SELECT project, period, facet, elcc_surface_coefficient
        FROM inputs_project_elcc_surface
        JOIN inputs_project_portfolios
        USING (project)
        WHERE prm_zone_scenario_id = {}
        AND project_prm_zone_scenario_id = {}
        AND elcc_surface_scenario_id = {}
        AND project_portfolio_scenario_id = {}""".format(
            subscenarios.PRM_ZONE_SCENARIO_ID,
            subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
            subscenarios.ELCC_SURFACE_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    ).fetchall()

    with open(os.path.join(inputs_directory,
                           "project_elcc_surface_coefficients.tab"), "w") as \
            coefficients_file:
        writer = csv.writer(coefficients_file, delimiter="\t")

        # Writer header
        writer.writerow(
            ["project", "period", "facet", "elcc_surface_coefficient"]
        )
        # Write data
        for row in coefficients:
            writer.writerow(row)
