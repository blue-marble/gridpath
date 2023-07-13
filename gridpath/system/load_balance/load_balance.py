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
The load-balance constraint in GridPath consists of production components
and consumption components that are added by various GridPath modules
depending on the selected features. The sum of the production components
must equal the sum of the consumption components in each zone and timepoint.

At a minimum, for each load zone and timepoint, the user must specify a
static load requirement input as a consumption component. On the production
side, the model aggregates the power output of projects in the respective
load zone and timepoint.

.. note:: Net power output from storage and demand-side resources can be
    negative and is currently aggregated with the 'project' production
    component.

Net transmission into/out of the load zone is another possible production
component (see :ref:`transmission-section-ref`).

The user may also optionally allow unserved energy and/or overgeneration to be
incurred by adding the respective variables to the production and
consumption components respectively, and assigning a per unit cost for each
load-balance violation type.
"""


import csv
import os.path
from pyomo.environ import Var, Constraint, Expression, NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.dynamic_components import (
    load_balance_consumption_components,
    load_balance_production_components,
)
from gridpath.common_functions import create_results_df
from gridpath.system.load_balance import LOAD_ZONE_TMP_DF


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    Here we add, the overgeneration and unserved-energy per unit costs
    are declared here as well as the overgeneration and unserved-energy
    variables.

    We also get all other production and consumption components and add them
    to the lhs and rhs of the load-balance constraint respectively. With the
    minimum set of features, the load-balance constraint will be formulated
    like this:

    :math:`Power\_Production\_in\_Zone\_MW_{z, tmp} + Unserved\_Energy\_MW_{
    z, tmp} = static\_load\_requirement_{z, tmp} + Overgeneration\_MW_{z,
    tmp}`
    """

    # Penalty variables
    m.Overgeneration_MW = Var(m.LOAD_ZONES, m.TMPS, within=NonNegativeReals)
    m.Unserved_Energy_MW = Var(m.LOAD_ZONES, m.TMPS, within=NonNegativeReals)

    # Penalty expressions (will be zero if violations not allowed)
    def overgeneration_expression_rule(mod, z, tmp):
        """

        :param mod:
        :param z:
        :param tmp:
        :return:
        """
        return mod.allow_overgeneration[z] * mod.Overgeneration_MW[z, tmp]

    m.Overgeneration_MW_Expression = Expression(
        m.LOAD_ZONES, m.TMPS, rule=overgeneration_expression_rule
    )

    def unserved_energy_expression_rule(mod, z, tmp):
        """

        :param mod:
        :param z:
        :param tmp:
        :return:
        """
        return mod.allow_unserved_energy[z] * mod.Unserved_Energy_MW[z, tmp]

    m.Unserved_Energy_MW_Expression = Expression(
        m.LOAD_ZONES, m.TMPS, rule=unserved_energy_expression_rule
    )

    # Add the unserved energy and overgeneration components to the load balance
    record_dynamic_components(dynamic_components=d)

    def meet_load_rule(mod, z, tmp):
        """
        The sum across all energy generation components added by other modules
        for each zone and timepoint must equal the sum across all energy
        consumption components added by other modules for each zone and
        timepoint
        :param mod:
        :param z:
        :param tmp:
        :return:
        """
        return sum(
            getattr(mod, component)[z, tmp]
            for component in getattr(d, load_balance_production_components)
        ) == sum(
            getattr(mod, component)[z, tmp]
            for component in getattr(d, load_balance_consumption_components)
        )

    m.Meet_Load_Constraint = Constraint(m.LOAD_ZONES, m.TMPS, rule=meet_load_rule)

    def use_limit_constraint_rule(mod, lz):
        return (
            sum(
                mod.Unserved_Energy_MW_Expression[lz, tmp]
                * mod.hrs_in_tmp[tmp]
                * mod.tmp_weight[tmp]
                for tmp in mod.TMPS
            )
            <= mod.unserved_energy_limit_mwh[lz]
        )

    m.Total_USE_Limit_Constraint = Constraint(
        m.LOAD_ZONES, rule=use_limit_constraint_rule
    )

    def max_unserved_load_limit_constraint_rule(mod, lz, tmp):
        return (
            mod.Unserved_Energy_MW_Expression[lz, tmp]
            <= mod.max_unserved_load_limit_mw[lz]
        )

    m.Max_Unserved_Load_Limit_Constraint = Constraint(
        m.LOAD_ZONES, m.TMPS, rule=max_unserved_load_limit_constraint_rule
    )


def record_dynamic_components(dynamic_components):
    """
    :param dynamic_components:

    This method adds the unserved energy and overgeneration to the load balance
    dynamic components.
    """

    getattr(dynamic_components, load_balance_production_components).append(
        "Unserved_Energy_MW_Expression"
    )
    getattr(dynamic_components, load_balance_consumption_components).append(
        "Overgeneration_MW_Expression"
    )


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param stage:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    results_columns = [
        "overgeneration_mw",
        "unserved_energy_mw",
    ]
    data = [
        [
            lz,
            tmp,
            value(m.Overgeneration_MW_Expression[lz, tmp]),
            value(m.Unserved_Energy_MW_Expression[lz, tmp]),
        ]
        for lz in getattr(m, "LOAD_ZONES")
        for tmp in getattr(m, "TMPS")
    ]
    results_df = create_results_df(
        index_columns=["load_zone", "timepoint"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, LOAD_ZONE_TMP_DF)[c] = None
    getattr(d, LOAD_ZONE_TMP_DF).update(results_df)


def save_duals(scenario_directory, subproblem, stage, instance, dynamic_components):
    instance.constraint_indices["Meet_Load_Constraint"] = ["zone", "timepoint", "dual"]


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

    # TODO: deal with duals
    # Update the temporary table with the duals
    # Update duals
    duals_results = []
    with open(
        os.path.join(results_directory, "Meet_Load_Constraint.csv"), "r"
    ) as load_balance_duals_file:
        reader = csv.reader(load_balance_duals_file)

        next(reader)  # skip header

        for row in reader:
            duals_results.append(
                (row[2], row[0], row[1], scenario_id, subproblem, stage)
            )
    duals_sql = """
        UPDATE results_system_load_zone_timepoint
        SET dual = ?
        WHERE load_zone = ?
        AND timepoint = ?
        AND scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """.format(
        scenario_id=scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=duals_sql, data=duals_results)

    # Calculate marginal cost per MW
    mc_sql = """
        UPDATE results_system_load_zone_timepoint
        SET marginal_price_per_mw = 
        dual / (discount_factor * number_years_represented * timepoint_weight 
        * number_of_hours_in_timepoint)
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """.format(
        scenario_id=scenario_id
    )
    spin_on_database_lock(
        conn=db, cursor=c, sql=mc_sql, data=(scenario_id, subproblem, stage), many=False
    )
