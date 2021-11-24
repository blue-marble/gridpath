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
Aggregate carbon emissions from the transmission-line-timepoint level to
the carbon cap zone - period level.
"""
from __future__ import division
from __future__ import print_function

from builtins import next
import csv
import os.path
from pyomo.environ import (
    Param,
    Set,
    Var,
    Constraint,
    Expression,
    NonNegativeReals,
    value,
)

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.dynamic_components import carbon_cap_balance_emission_components
from gridpath.transmission.operations.carbon_emissions import (
    calculate_carbon_emissions_imports,
)


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    Aggregate total imports of emissions and add to carbon balance constraint
    :param m:
    :param d:
    :return:
    """

    def total_carbon_emissions_imports_rule(mod, z, p):
        """
        Calculate total emissions from all carbonaceous transmission lines
        imported into the carbon cap zone
        :param mod:
        :param z:
        :param p:
        :return:
        """
        return sum(
            mod.Import_Carbon_Emissions_Tons[tx, tmp]
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            for (tx, tmp) in mod.CRB_TX_OPR_TMPS
            if tx in mod.CRB_TX_LINES_BY_CARBON_CAP_ZONE[z]
            and tmp in mod.TMPS_IN_PRD[p]
        )

    m.Total_Carbon_Emission_Imports_Tons = Expression(
        m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP,
        rule=total_carbon_emissions_imports_rule,
    )

    record_dynamic_components(dynamic_components=d)


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    This method adds emission imports to carbon balance
    """

    getattr(dynamic_components, carbon_cap_balance_emission_components).append(
        "Total_Carbon_Emission_Imports_Tons"
    )


def total_carbon_emissions_imports_degen_expr_rule(mod, z, p):
    """
    In case of degeneracy where the Import_Carbon_Emissions_Tons variable
    can take a value larger than the actual import emissions (when the
    carbon cap is non-binding), we can upost-process to figure out what the
    actual imported emissions are (e.g. instead of applying a tuning cost)
    :param mod:
    :param z:
    :param p:
    :return:
    """
    return sum(
        calculate_carbon_emissions_imports(mod, tx, tmp)
        * mod.hrs_in_tmp[tmp]
        * mod.tmp_weight[tmp]
        for (tx, tmp) in mod.CRB_TX_OPR_TMPS
        if tx in mod.CRB_TX_LINES_BY_CARBON_CAP_ZONE[z] and tmp in mod.TMPS_IN_PRD[p]
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
            "carbon_cap_total_transmission.csv",
        ),
        "w",
        newline="",
    ) as carbon_results_file:
        writer = csv.writer(carbon_results_file)
        writer.writerow(
            [
                "carbon_cap_zone",
                "period",
                "carbon_cap_target",
                "transmission_carbon_emissions",
                "transmission_carbon_emissions_degen",
            ]
        )
        for (z, p) in m.CARBON_CAP_ZONE_PERIODS_WITH_CARBON_CAP:
            writer.writerow(
                [
                    z,
                    p,
                    float(m.carbon_cap_target[z, p]),
                    value(m.Total_Carbon_Emission_Imports_Tons[z, p]),
                    total_carbon_emissions_imports_degen_expr_rule(m, z, p),
                ]
            )


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
        print("system carbon emissions (imports)")
    # Carbon emissions from imports
    # Prior results should have already been cleared by
    # system.policy.carbon_cap.aggregate_project_carbon_emissions,
    # then project total emissions imported
    # Update results_system_carbon_emissions with NULL just in case (instead of
    # clearing prior results)
    # TODO: why not just clear the results?
    nullify_sql = """
        UPDATE results_system_carbon_emissions
        SET import_emissions = NULL
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
        os.path.join(results_directory, "carbon_cap_total_transmission.csv"), "r"
    ) as emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            carbon_cap_zone = row[0]
            period = row[1]
            tx_carbon_emissions = row[3]
            tx_carbon_emissions_degen = row[4]

            results.append(
                (
                    tx_carbon_emissions,
                    tx_carbon_emissions_degen,
                    scenario_id,
                    carbon_cap_zone,
                    period,
                    subproblem,
                    stage,
                )
            )

    imports_sql = """
        UPDATE results_system_carbon_emissions
        SET import_emissions = ?,
        import_emissions_degen = ?
        WHERE scenario_id = ?
        AND carbon_cap_zone = ?
        AND period = ?
        AND subproblem_id = ?
        AND stage_id = ?"""

    spin_on_database_lock(conn=db, cursor=c, sql=imports_sql, data=results)

    # Update the total emissions in case of degeneracy
    total_degen_sql = """
        UPDATE results_system_carbon_emissions
           SET total_emissions_degen = 
           in_zone_project_emissions + import_emissions_degen
           WHERE scenario_id = ?
           AND subproblem_id = ?
           AND stage_id = ?;
           """
    spin_on_database_lock(
        conn=db,
        cursor=c,
        sql=total_degen_sql,
        data=(scenario_id, subproblem, stage),
        many=False,
    )
