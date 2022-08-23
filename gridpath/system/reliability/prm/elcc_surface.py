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
Total ELCC of projects on ELCC surface
"""
from __future__ import print_function

from builtins import next
from builtins import range
import csv
import os.path
from pyomo.environ import (
    Param,
    Var,
    Set,
    NonNegativeReals,
    Constraint,
    Expression,
    value,
)

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.dynamic_components import (
    prm_balance_provision_components,
    cost_components,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    # Surface can change by prm_zone and period
    # Limit surface to 1000 facets
    m.ELCC_SURFACE_PRM_ZONE_PERIOD_FACETS = Set(
        dimen=4, within=m.ELCC_SURFACE_PRM_ZONE_PERIODS * list(range(1, 1001))
    )

    # The intercept for the prm_zone/period/facet combination
    m.elcc_surface_intercept = Param(
        m.ELCC_SURFACE_PRM_ZONE_PERIOD_FACETS, within=NonNegativeReals
    )

    # Endogenous dynamic ELCC surface
    m.Dynamic_ELCC_MW = Var(m.ELCC_SURFACE_PRM_ZONE_PERIODS, within=NonNegativeReals)

    def elcc_surface_rule(mod, surface, prm_zone, period, facet):
        """

        :param mod:
        :param prm_zone:
        :param period:
        :param facet:
        :return:
        """
        return (
            mod.Dynamic_ELCC_MW[surface, prm_zone, period]
            <= sum(
                mod.ELCC_Surface_Contribution_MW[s, prj, period, facet]
                for (s, prj) in mod.ELCC_SURFACE_PROJECTS_BY_PRM_ZONE[prm_zone]
                if s == surface
                # This is redundant since since ELCC_Surface_Contribution_MW
                # is 0 for non-operational periods, but keep here for
                # extra safety
                and period in mod.OPR_PRDS_BY_PRJ[prj]
            )
            + mod.elcc_surface_intercept[surface, prm_zone, period, facet]
            * mod.prm_peak_load_mw[surface, prm_zone, period]
        )

    # Dynamic ELCC piecewise constraint
    m.Dynamic_ELCC_Constraint = Constraint(
        m.ELCC_SURFACE_PRM_ZONE_PERIOD_FACETS, rule=elcc_surface_rule
    )

    def total_contribution_from_all_surfaces_init(mod, prm_zone, period):
        return sum(
            mod.Dynamic_ELCC_MW[surface, z, p]
            for (surface, z, p) in mod.ELCC_SURFACE_PRM_ZONE_PERIODS
            if z == prm_zone and p == period
        )

    m.Total_Contribution_from_ELCC_Surfaces = Expression(
        m.PRM_ZONE_PERIODS_WITH_REQUIREMENT,
        initialize=total_contribution_from_all_surfaces_init,
    )

    # Add to emission imports to carbon balance
    getattr(d, prm_balance_provision_components).append(
        "Total_Contribution_from_ELCC_Surfaces"
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
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            subproblem,
            stage,
            "inputs",
            "prm_zone_surface_facets_and_intercept.tab",
        ),
        index=m.ELCC_SURFACE_PRM_ZONE_PERIOD_FACETS,
        param=m.elcc_surface_intercept,
        select=(
            "elcc_surface_name",
            "prm_zone",
            "period",
            "facet",
            "elcc_surface_intercept",
        ),
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
    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "prm_elcc_surface.csv",
        ),
        "w",
        newline="",
    ) as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["elcc_surface_name", "prm_zone", "period", "elcc_mw"])
        for (s, z, p) in m.ELCC_SURFACE_PRM_ZONE_PERIODS:
            writer.writerow([s, z, p, value(m.Dynamic_ELCC_MW[s, z, p])])

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "prm_elcc_surface_total.csv",
        ),
        "w",
        newline="",
    ) as results_file:
        writer = csv.writer(results_file)
        writer.writerow(
            ["prm_zone", "period", "total_contribution_from_elcc_surfaces_mw"]
        )
        for (z, p) in m.PRM_ZONE_PERIODS_WITH_REQUIREMENT:
            writer.writerow(
                [z, p, value(m.Total_Contribution_from_ELCC_Surfaces[z, p])]
            )


def save_duals(m):
    m.constraint_indices["Dynamic_ELCC_Constraint"] = [
        "surface_name",
        "prm_zone",
        "period",
        "facet",
        "dual",
    ]


def get_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
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
        """SELECT elcc_surface_name, prm_zone, period, facet, elcc_surface_intercept
        FROM inputs_system_prm_zone_elcc_surface
        INNER JOIN inputs_temporal_periods
        USING (period)
        WHERE elcc_surface_scenario_id = {}
        AND temporal_scenario_id = {}""".format(
            subscenarios.ELCC_SURFACE_SCENARIO_ID, subscenarios.TEMPORAL_SCENARIO_ID
        )
    )

    return intercepts


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # intercepts = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)

    # do stuff here to validate inputs


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    prm_zone_surface_facets_and_intercept.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """
    intercepts = get_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            subproblem,
            stage,
            "inputs",
            "prm_zone_surface_facets_and_intercept.tab",
        ),
        "w",
        newline="",
    ) as intercepts_file:
        writer = csv.writer(intercepts_file, delimiter="\t", lineterminator="\n")

        # Writer header
        writer.writerow(
            [
                "elcc_surface_name",
                "prm_zone",
                "period",
                "facet",
                "elcc_surface_intercept",
            ]
        )
        # Write data
        for row in intercepts:
            writer.writerow(row)


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
    if not quiet:
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
    spin_on_database_lock(
        conn=db,
        cursor=c,
        sql=nullify_sql,
        data=(scenario_id, subproblem, stage),
        many=False,
    )

    results = []
    with open(
        os.path.join(results_directory, "prm_elcc_surface_total.csv"),
        "r",
    ) as surface_file:
        reader = csv.reader(surface_file)

        next(reader)  # skip header
        for row in reader:
            prm_zone = row[0]
            period = row[1]
            elcc = row[2]

            results.append((elcc, scenario_id, prm_zone, period, subproblem, stage))

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
