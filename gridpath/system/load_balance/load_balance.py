#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Param, Var, Constraint, NonNegativeReals

from gridpath.auxiliary.dynamic_components import \
    load_balance_consumption_components, load_balance_production_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.overgeneration_penalty_per_mw = \
        Param(m.LOAD_ZONES, within=NonNegativeReals)
    m.unserved_energy_penalty_per_mw = \
        Param(m.LOAD_ZONES, within=NonNegativeReals)

    # Penalty variables
    m.Overgeneration_MW = Var(m.LOAD_ZONES, m.TIMEPOINTS,
                              within=NonNegativeReals)
    m.Unserved_Energy_MW = Var(m.LOAD_ZONES, m.TIMEPOINTS,
                               within=NonNegativeReals)

    getattr(d, load_balance_production_components).append("Unserved_Energy_MW")
    getattr(d, load_balance_consumption_components).append("Overgeneration_MW")

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
                   for component in getattr(d,
                                            load_balance_production_components)
                   ) \
            == \
            sum(getattr(mod, component)[z, tmp]
                for component in getattr(d,
                                         load_balance_consumption_components)
                )

    m.Meet_Load_Constraint = Constraint(m.LOAD_ZONES, m.TIMEPOINTS,
                                        rule=meet_load_rule)


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
                                           "inputs", "load_zones.tab"),
                     param=(m.overgeneration_penalty_per_mw,
                            m.unserved_energy_penalty_per_mw)
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
                           "load_balance.csv"), "w") as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["zone", "period", "horizon", "timepoint",  "horizon",
                         "discount_factor", "number_years_represented",
                         "horizon_weight", "number_of_hours_in_timepiont",
                         "overgeneration_mw",
                         "unserved_energy_mw"]
                        )
        for z in getattr(m, "LOAD_ZONES"):
            for tmp in getattr(m, "TIMEPOINTS"):
                writer.writerow([
                    z,
                    m.period[tmp],
                    m.horizon[tmp],
                    tmp,
                    m.discount_factor[m.period[tmp]],
                    m.number_years_represented[m.period[tmp]],
                    m.horizon_weight[m.horizon[tmp]],
                    m.number_of_hours_in_timepoint[tmp],
                    m.Overgeneration_MW[z, tmp].value,
                    m.Unserved_Energy_MW[z, tmp].value]
                )


def save_duals(m):
    m.constraint_indices["Meet_Load_Constraint"] = \
        ["zone", "timepoint", "dual"]


def import_results_into_database(
        scenario_id, c, db, results_directory
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    print("system load balance")
    
    c.execute(
        """DELETE FROM results_system_load_balance
        WHERE scenario_id = {};""".format(scenario_id)
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS 
        temp_results_system_load_balance"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_system_load_balance"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        load_zone VARCHAR(32),
        period INTEGER,
        horizon INTEGER,
        timepoint INTEGER,
        discount_factor FLOAT,
        number_years_represented FLOAT,
        horizon_weight FLOAT,
        number_of_hours_in_timepoint FLOAT,
        overgeneration_mw FLOAT,
        unserved_energy_mw FLOAT,
        PRIMARY KEY (scenario_id, load_zone, timepoint)
            );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory, "load_balance.csv"),
              "r") as load_balance_file:
        reader = csv.reader(load_balance_file)

        next(reader)  # skip header
        for row in reader:
            ba = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            discount_factor = row[4]
            number_years = row[5]
            horizon_weight = row[6]
            number_of_hours_in_timepoint = row[7]
            overgen = row[8]
            unserved_energy = row[9]
            c.execute(
                """INSERT INTO 
                temp_results_system_load_balance"""
                + str(scenario_id) + """
                (scenario_id, load_zone, period, horizon, 
                timepoint, discount_factor, number_years_represented,
                horizon_weight, number_of_hours_in_timepoint,
                overgeneration_mw, unserved_energy_mw)
                VALUES ({}, '{}', {}, {}, {}, {}, {}, {}, {}, {}, 
                {});""".format(
                    scenario_id, ba, period, horizon, timepoint,
                    discount_factor, number_years,
                    horizon_weight, number_of_hours_in_timepoint,
                    overgen, unserved_energy
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_system_load_balance
        (scenario_id, load_zone, period, horizon, timepoint,
        discount_factor, number_years_represented,
        horizon_weight, number_of_hours_in_timepoint,
        overgeneration_mw, unserved_energy_mw)
        SELECT
        scenario_id, load_zone, period, horizon, timepoint,
        discount_factor, number_years_represented,
        horizon_weight, number_of_hours_in_timepoint,
        overgeneration_mw, unserved_energy_mw
        FROM temp_results_system_load_balance"""
        + str(scenario_id) + """
        ORDER BY scenario_id, load_zone, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_system_load_balance"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()

    # Update duals
    with open(os.path.join(results_directory, "Meet_Load_Constraint.csv"),
              "r") as load_balance_duals_file:
        reader = csv.reader(load_balance_duals_file)

        next(reader)  # skip header

        for row in reader:
            c.execute(
                """UPDATE results_system_load_balance
                SET dual = {}
                WHERE load_zone = '{}'
                AND timepoint = {}
                AND scenario_id = {};""".format(
                    row[2], row[0], row[1], scenario_id
                )
            )
    db.commit()

    # Calculate marginal cost per MW
    c.execute(
        """UPDATE results_system_load_balance
        SET marginal_price_per_mw = 
        dual / (discount_factor * number_years_represented * horizon_weight 
        * number_of_hours_in_timepoint)
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()
