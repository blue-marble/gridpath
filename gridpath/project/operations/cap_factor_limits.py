# Copyright 2016-2022 Blue Marble Analytics LLC.
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
The **gridpath.project.operations.cap_factor_limits** module is a project-level
module that adds to the formulation components that limit the minimum and maximum
cap factor of a project over a horizon.
"""

import csv
import os.path
from pyomo.environ import Set, Param, Constraint, Expression, Reals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import

Infinity = float("inf")
Negative_Infinity = float("-inf")


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The tables below list the Pyomo model components defined in the
    'gen_commit_bin' module followed below by the respective components
    defined in the 'gen_commit_lin" module.

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`CAP_FACTOR_LIMIT_PRJ_BT_HRZ`                                   |
    | | *Within*: :code:`PROJECTS*BLN_TYPE_HRZS`                              |
    |                                                                         |
    +-------------------------------------------------------------------------+

    +-------------------------------------------------------------------------+
    | Params                                                                  |
    +=========================================================================+
    | | :code:`CAP_FACTOR_LIMIT_PRJ_BT_HRZ`                                   |
    | | *Within*: :code:`PROJECTS*BLN_TYPE_HRZS`                              |
    |                                                                         |
    +-------------------------------------------------------------------------+

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +-------------------------------------------------------------------------+
    | | :code:`Gen_Commit_BinLin_Select_Cycle_Constraint`                     |
    | | *Defined over*: :code:`CAP_FACTOR_LIMIT_PRJ_BT_HRZ`                   |
    |                                                                         |
    | This generator can only be synced if the "cycle select" generator is    |
    | not synced (the sum of the Sync variables of the two must be less than  |
    | or equal to 1.                                                          |
    +-------------------------------------------------------------------------+

    """

    m.CAP_FACTOR_LIMIT_PRJ_BT_HRZ = Set(dimen=3, within=m.PROJECTS * m.BLN_TYPE_HRZS)

    m.min_cap_factor = Param(
        m.CAP_FACTOR_LIMIT_PRJ_BT_HRZ, within=Reals, default=Negative_Infinity
    )  # allow negative values, e.g. for storage (net power is <0 due to losses)

    m.max_cap_factor = Param(
        m.CAP_FACTOR_LIMIT_PRJ_BT_HRZ, within=Reals, default=Infinity
    )  # allow negative values, e.g. for storage (net power is <0 due to losses)

    def actual_power_provision_in_horizon_rule(mod, prj, bt, h):
        """ """
        return sum(
            mod.Power_Provision_MW[prj, tmp] * mod.hrs_in_tmp[tmp] * mod.tmp_weight[tmp]
            for tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, h]
        )

    m.Actual_Power_Provision_in_Horizon_Expression = Expression(
        m.CAP_FACTOR_LIMIT_PRJ_BT_HRZ, rule=actual_power_provision_in_horizon_rule
    )

    def possible_power_provision_in_horizon_rule(mod, prj, bt, h):
        return sum(
            mod.Capacity_MW[prj, mod.period[tmp]]
            * mod.hrs_in_tmp[tmp]
            * mod.tmp_weight[tmp]
            for tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, h]
        )

    m.Possible_Power_Provision_in_Horizon_Expression = Expression(
        m.CAP_FACTOR_LIMIT_PRJ_BT_HRZ, rule=possible_power_provision_in_horizon_rule
    )

    def min_cap_factor_constraint_rule(mod, prj, bt, h):
        if mod.min_cap_factor[prj, bt, h] == Negative_Infinity:
            return Constraint.Skip
        else:
            return (
                mod.Actual_Power_Provision_in_Horizon_Expression[prj, bt, h]
                >= mod.min_cap_factor[prj, bt, h]
                * mod.Possible_Power_Provision_in_Horizon_Expression[prj, bt, h]
            )

    m.Min_Cap_Factor_Constraint = Constraint(
        m.CAP_FACTOR_LIMIT_PRJ_BT_HRZ,
        rule=min_cap_factor_constraint_rule,
    )

    def max_cap_factor_constraint_rule(mod, prj, bt, h):
        if mod.max_cap_factor[prj, bt, h] == Infinity:
            return Constraint.Skip
        else:
            return (
                mod.Actual_Power_Provision_in_Horizon_Expression[prj, bt, h]
                <= mod.max_cap_factor[prj, bt, h]
                * mod.Possible_Power_Provision_in_Horizon_Expression[prj, bt, h]
            )

    m.Max_Cap_Factor_Constraint = Constraint(
        m.CAP_FACTOR_LIMIT_PRJ_BT_HRZ,
        rule=max_cap_factor_constraint_rule,
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    # Load any projects for cycle selection
    input_file = os.path.join(
        scenario_directory,
        str(subproblem),
        str(stage),
        "inputs",
        "cap_factor_limits.tab",
    )

    if os.path.exists(input_file):
        data_portal.load(
            filename=input_file,
            index=m.CAP_FACTOR_LIMIT_PRJ_BT_HRZ,
            param=(
                m.min_cap_factor,
                m.max_cap_factor,
            ),
        )


def export_results(scenario_directory, subproblem, stage, m, d):
    """ """
    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "cap_factor_limits.csv",
        ),
        "w",
        newline="",
    ) as results_f:
        writer = csv.writer(results_f)
        writer.writerow(
            [
                "project",
                "balancing_type_horizon",
                "horizon",
                "min_cap_factor",
                "max_cap_factor",
                "actual_power_provision_mwh",
                "possible_power_provision_mwh",
            ]
        )
        for (prj, bt, h) in m.CAP_FACTOR_LIMIT_PRJ_BT_HRZ:
            writer.writerow(
                [
                    prj,
                    bt,
                    h,
                    None
                    if m.min_cap_factor[prj, bt, h] == Negative_Infinity
                    else m.min_cap_factor[prj, bt, h],
                    None
                    if m.max_cap_factor[prj, bt, h] == Infinity
                    else m.max_cap_factor[prj, bt, h],
                    value(m.Actual_Power_Provision_in_Horizon_Expression[prj, bt, h]),
                    value(m.Possible_Power_Provision_in_Horizon_Expression[prj, bt, h]),
                ]
            )


# Database
###############################################################################


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
    # Fuel burned by project and timepoint
    if not quiet:
        print("project cap factor limits")
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_project_cap_factor_limits",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "cap_factor_limits.csv"), "r"
    ) as results_file:
        reader = csv.reader(results_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            balancing_type_horizon = row[1]
            horizon = row[2]
            min_cap_factor = row[3]
            max_cap_factor = row[4]
            actual_power_provision = row[5]
            possible_power_provision = row[6]

            results.append(
                (
                    scenario_id,
                    subproblem,
                    stage,
                    project,
                    balancing_type_horizon,
                    horizon,
                    min_cap_factor,
                    max_cap_factor,
                    actual_power_provision,
                    possible_power_provision,
                )
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_cap_factor_limits{}
         (scenario_id, subproblem_id, stage_id, project, balancing_type_horizon, 
         horizon, min_cap_factor, max_cap_factor, actual_power_provision_mwh, 
         possible_power_provision_mwh)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_cap_factor_limits
        (scenario_id, subproblem_id, stage_id, project, balancing_type_horizon, 
         horizon, min_cap_factor, max_cap_factor, actual_power_provision_mwh, 
         possible_power_provision_mwh)
        SELECT
        scenario_id, subproblem_id, stage_id, project, balancing_type_horizon, 
         horizon, min_cap_factor, max_cap_factor, actual_power_provision_mwh, 
         possible_power_provision_mwh
        FROM temp_results_project_cap_factor_limits{}
         ORDER BY scenario_id, subproblem_id, stage_id, project, 
         balancing_type_horizon, horizon;
         """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)
