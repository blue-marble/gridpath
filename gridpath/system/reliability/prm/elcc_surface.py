#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Total ELCC of projects on ELCC surface
"""
from __future__ import print_function

from builtins import next
from builtins import range
import csv
import os.path
from pyomo.environ import Param, Var, Set, NonNegativeReals, Constraint, \
    Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.dynamic_components import \
    prm_balance_provision_components, total_cost_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Surface can change by prm_zone and period
    # Limit surface to 1000 facets
    m.PRM_ZONE_PERIOD_ELCC_SURFACE_FACETS = Set(
        dimen=3, within=m.PRM_ZONES * m.PERIODS * list(range(1, 1001))
    )

    # The intercept for the prm_zone/period/facet combination
    m.elcc_surface_intercept = Param(
        m.PRM_ZONE_PERIOD_ELCC_SURFACE_FACETS, within=NonNegativeReals
    )

    # Endogenous dynamic ELCC surface
    m.Dynamic_ELCC_MW = Var(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT, within=NonNegativeReals
    )

    def elcc_surface_rule(mod, prm_zone, period, facet):
        """
        
        :param mod: 
        :param prm_zone: 
        :param period: 
        :param facet: 
        :return: 
        """
        return mod.Dynamic_ELCC_MW[prm_zone, period] \
            <= \
            sum(mod.ELCC_Surface_Contribution_MW[prj, period, facet]
                for prj in mod.ELCC_SURFACE_PROJECTS_BY_PRM_ZONE[prm_zone]
                # This is redundant since since ELCC_Surface_Contribution_MW
                # is 0 for non-operational periods, but keep here for
                # extra safety
                if period in mod.OPERATIONAL_PERIODS_BY_PROJECT[prj]
                ) \
            + mod.elcc_surface_intercept[prm_zone, period, facet]

    # Dynamic ELCC piecewise constraint
    m.Dynamic_ELCC_Constraint = Constraint(
        m.PRM_ZONE_PERIOD_ELCC_SURFACE_FACETS, rule=elcc_surface_rule
    )

    # Add to emission imports to carbon balance
    getattr(d, prm_balance_provision_components).append(
        "Dynamic_ELCC_MW"
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    # PRM zone-period-facet
    data_portal.load(filename=os.path.join(
        scenario_directory, subproblem, stage, "inputs",
        "prm_zone_surface_facets_and_intercept.tab"
    ),
                     index=m.PRM_ZONE_PERIOD_ELCC_SURFACE_FACETS,
                     param=m.elcc_surface_intercept,
                     select=("prm_zone", "period", "facet",
                             "elcc_surface_intercept")
                     )


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "prm_elcc_surface.csv"), "w", newline="") as \
            results_file:
        writer = csv.writer(results_file)
        writer.writerow(["prm_zone", "period", "elcc_mw"])
        for (z, p) in m.PRM_ZONE_PERIODS_WITH_REQUIREMENT:
            writer.writerow([
                z,
                p,
                value(m.Dynamic_ELCC_MW[z, p])
            ])


def save_duals(m):
    m.constraint_indices["Dynamic_ELCC_Constraint"] = \
        ["prm_zone", "period", "facet", "dual"]


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """
    c = conn.cursor()
    # The intercepts for the surface
    intercepts = c.execute(
        """SELECT prm_zone, period, facet, elcc_surface_intercept
        FROM inputs_system_prm_zone_elcc_surface
        INNER JOIN inputs_temporal_periods
        USING (period)
        WHERE prm_zone_scenario_id = {}
        AND elcc_surface_scenario_id = {}
        AND temporal_scenario_id = {}""".format(
            subscenarios.PRM_ZONE_SCENARIO_ID,
            subscenarios.ELCC_SURFACE_SCENARIO_ID,
            subscenarios.TEMPORAL_SCENARIO_ID
        )
    )

    return intercepts


def validate_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # intercepts = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

    # do stuff here to validate inputs


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    prm_zone_surface_facets_and_intercept.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """
    intercepts = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(
            inputs_directory, "prm_zone_surface_facets_and_intercept.tab"
    ), "w", newline="") as intercepts_file:
        writer = csv.writer(intercepts_file, delimiter="\t")

        # Writer header
        writer.writerow(
            ["prm_zone", "period", "facet", "elcc_surface_intercept"]
        )
        # Write data
        for row in intercepts:
            writer.writerow(row)


def import_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    print("system prm elcc surface")
    # PRM contribution from the ELCC surface
    # Prior results should have already been cleared by
    # system.prm.aggregate_project_simple_prm_contribution,
    # then elcc_simple_mw imported
    # Update results_system_prm with NULL for surface contribution just in
    # case (instead of clearing prior results)
    nullify_sql = """
        UPDATE results_system_prm
        SET elcc_surface_mw = NULL
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=nullify_sql, 
                          data=(scenario_id, subproblem, stage),
                          many=False)
    
    results = []
    with open(os.path.join(results_directory,
                           "prm_elcc_surface.csv"), "r") as \
            surface_file:
        reader = csv.reader(surface_file)

        next(reader)  # skip header
        for row in reader:
            prm_zone = row[0]
            period = row[1]
            elcc = row[2]
            
            results.append(
                (elcc, scenario_id, prm_zone, period, subproblem, stage)
            )

    update_sql = """
        UPDATE results_system_prm
        SET elcc_surface_mw = ?
        WHERE scenario_id = ?
        AND prm_zone = ?
        AND period = ?
        AND subproblem_id = ?
        AND stage_id = ?
        """
    spin_on_database_lock(conn=db, cursor=c, sql=update_sql, data=results)
