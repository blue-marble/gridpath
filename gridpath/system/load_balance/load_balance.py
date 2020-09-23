#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

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

from __future__ import print_function

from builtins import next
import csv
import os.path
from pyomo.environ import Var, Constraint, Expression, NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import
from gridpath.auxiliary.dynamic_components import \
    load_balance_consumption_components, load_balance_production_components


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
    m.Overgeneration_MW = Var(m.LOAD_ZONES, m.TMPS,
                              within=NonNegativeReals)
    m.Unserved_Energy_MW = Var(m.LOAD_ZONES, m.TMPS,
                               within=NonNegativeReals)

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
        m.LOAD_ZONES, m.TMPS,
        rule=overgeneration_expression_rule
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
        m.LOAD_ZONES, m.TMPS,
        rule=unserved_energy_expression_rule
    )

    # Add the unserved energy and overgeneration components to the load balance
    record_dynamic_components(dynamic_components=dc)

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
        return sum(getattr(mod, component)[z, tmp]
                   for component in getattr(dc,
                                            load_balance_production_components)
                   ) \
            == \
            sum(getattr(mod, component)[z, tmp]
                for component in getattr(dc,
                                         load_balance_consumption_components)
                )

    m.Meet_Load_Constraint = Constraint(m.LOAD_ZONES, m.TMPS,
                                        rule=meet_load_rule)


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
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "load_balance.csv"), "w", newline="") as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["zone", "period", "timepoint",
                         "discount_factor", "number_years_represented",
                         "timepoint_weight", "number_of_hours_in_timepoint",
                         "load_mw", "overgeneration_mw", "unserved_energy_mw"]
                        )
        for z in getattr(m, "LOAD_ZONES"):
            for tmp in getattr(m, "TMPS"):
                writer.writerow([
                    z,
                    m.period[tmp],
                    tmp,
                    m.discount_factor[m.period[tmp]],
                    m.number_years_represented[m.period[tmp]],
                    m.tmp_weight[tmp],
                    m.hrs_in_tmp[tmp],
                    m.static_load_mw[z, tmp],
                    value(m.Overgeneration_MW_Expression[z, tmp]),
                    value(m.Unserved_Energy_MW_Expression[z, tmp])
                ]
                )


def save_duals(m):
    m.constraint_indices["Meet_Load_Constraint"] = \
        ["zone", "timepoint", "dual"]


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
        print("system load balance")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_system_load_balance",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory, "load_balance.csv"),
              "r") as load_balance_file:
        reader = csv.reader(load_balance_file)

        next(reader)  # skip header
        for row in reader:
            ba = row[0]
            period = row[1]
            timepoint = row[2]
            discount_factor = row[3]
            number_years = row[4]
            timepoint_weight = row[5]
            number_of_hours_in_timepoint = row[6]
            load = row[7]
            overgen = row[8]
            unserved_energy = row[9]

            results.append(
                (scenario_id, ba, period, subproblem, stage,
                    timepoint, discount_factor, number_years,
                    timepoint_weight, number_of_hours_in_timepoint,
                    load, overgen, unserved_energy)
            )
    insert_temp_sql = """
        INSERT INTO 
        temp_results_system_load_balance{}
        (scenario_id, load_zone, period, subproblem_id, stage_id,
        timepoint, discount_factor, number_years_represented,
        timepoint_weight, number_of_hours_in_timepoint,
        load_mw, overgeneration_mw, unserved_energy_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_system_load_balance
        (scenario_id, load_zone, period, subproblem_id, stage_id, 
        timepoint, discount_factor, number_years_represented,
        timepoint_weight, number_of_hours_in_timepoint,
        load_mw, overgeneration_mw, unserved_energy_mw)
        SELECT
        scenario_id, load_zone, period, subproblem_id, stage_id, 
        timepoint, discount_factor, number_years_represented,
        timepoint_weight, number_of_hours_in_timepoint,
        load_mw, overgeneration_mw, unserved_energy_mw
        FROM temp_results_system_load_balance{}
        ORDER BY scenario_id, load_zone, subproblem_id, stage_id, timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)

    # Update duals
    duals_results = []
    with open(os.path.join(results_directory, "Meet_Load_Constraint.csv"),
              "r") as load_balance_duals_file:
        reader = csv.reader(load_balance_duals_file)

        next(reader)  # skip header

        for row in reader:
            duals_results.append(
                (row[2], row[0], row[1], scenario_id, subproblem, stage)
            )
    duals_sql = """
        UPDATE results_system_load_balance
        SET dual = ?
        WHERE load_zone = ?
        AND timepoint = ?
        AND scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """
    spin_on_database_lock(conn=db, cursor=c, sql=duals_sql, data=duals_results)

    # Calculate marginal cost per MW
    mc_sql = """
        UPDATE results_system_load_balance
        SET marginal_price_per_mw = 
        dual / (discount_factor * number_years_represented * timepoint_weight 
        * number_of_hours_in_timepoint)
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """.format(scenario_id, subproblem, stage)
    spin_on_database_lock(conn=db, cursor=c, sql=mc_sql,
                          data=(scenario_id, subproblem, stage),
                          many=False)
