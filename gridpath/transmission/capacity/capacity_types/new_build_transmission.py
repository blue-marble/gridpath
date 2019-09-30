#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

import csv
import os.path
from pyomo.environ import Set, Param, Var, Expression, NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import


# TODO: can we have different capacities depending on the direction
def add_module_specific_components(m, d):
    """

    """
    m.NEW_BUILD_TRANSMISSION_VINTAGES = Set(dimen=2)
    m.tx_lifetime_yrs_by_new_build_vintage = \
        Param(m.NEW_BUILD_TRANSMISSION_VINTAGES, within=NonNegativeReals)
    m.tx_annualized_real_cost_per_mw_yr = \
        Param(m.NEW_BUILD_TRANSMISSION_VINTAGES, within=NonNegativeReals)

    m.Build_Transmission_MW = \
        Var(m.NEW_BUILD_TRANSMISSION_VINTAGES, within=NonNegativeReals)

    def operational_periods_by_new_build_transmission_vintage(mod, g, v):
        operational_periods = list()
        for p in mod.PERIODS:
            if v <= p < v + mod.tx_lifetime_yrs_by_new_build_vintage[g, v]:
                operational_periods.append(p)
            else:
                pass
        return operational_periods

    m.OPERATIONAL_PERIODS_BY_NEW_BUILD_TRANSMISSION_VINTAGE = \
        Set(m.NEW_BUILD_TRANSMISSION_VINTAGES,
            initialize=operational_periods_by_new_build_transmission_vintage)

    def new_build_transmission_operational_periods(mod):
        return \
            set((g, p) for (g, v) in mod.NEW_BUILD_TRANSMISSION_VINTAGES
                for p in mod.
                OPERATIONAL_PERIODS_BY_NEW_BUILD_TRANSMISSION_VINTAGE[g, v]
                )

    m.NEW_BUILD_TRANSMISSION_OPERATIONAL_PERIODS = \
        Set(dimen=2, initialize=new_build_transmission_operational_periods)

    m.tx_capacity_type_operational_period_sets.append(
        "NEW_BUILD_TRANSMISSION_OPERATIONAL_PERIODS",
    )

    def new_build_transmission_vintages_operational_in_period(mod, p):
        build_vintages_by_period = list()
        for (g, v) in mod.NEW_BUILD_TRANSMISSION_VINTAGES:
            if p in mod.\
                    OPERATIONAL_PERIODS_BY_NEW_BUILD_TRANSMISSION_VINTAGE[g, v]:
                build_vintages_by_period.append((g, v))
            else:
                pass
        return build_vintages_by_period

    m.NEW_BUILD_TRANSMISSION_VINTAGES_OPERATIONAL_IN_PERIOD = \
        Set(m.PERIODS, dimen=2,
            initialize=new_build_transmission_vintages_operational_in_period)

    def new_build_tx_capacity_rule(mod, g, p):
        """
        Sum all builds of vintages operational in the current period
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return sum(
            mod.Build_Transmission_MW[g, v] for (gen, v)
            in mod.NEW_BUILD_TRANSMISSION_VINTAGES_OPERATIONAL_IN_PERIOD[p]
            if gen == g
        )

    m.New_Build_Transmission_Capacity_MW = \
        Expression(m.NEW_BUILD_TRANSMISSION_OPERATIONAL_PERIODS,
                   rule=new_build_tx_capacity_rule)


def min_transmission_capacity_rule(mod, g, p):
    """

    :param mod:
    :param g:
    :param p:
    :return:
    """
    return -mod.New_Build_Transmission_Capacity_MW[g, p]


def max_transmission_capacity_rule(mod, g, p):
    """

    :param mod:
    :param g:
    :param p:
    :return:
    """
    return mod.New_Build_Transmission_Capacity_MW[g, p]


def tx_capacity_cost_rule(mod, g, p):
    """
    Capacity cost for new builds in each period (sum over all vintages
    operational in current period)
    :param mod:
    :return:
    """
    return sum(mod.Build_Transmission_MW[g, v]
               * mod.tx_annualized_real_cost_per_mw_yr[g, v]
               for (gen, v)
               in mod.NEW_BUILD_TRANSMISSION_VINTAGES_OPERATIONAL_IN_PERIOD[p]
               if gen == g)


def load_module_specific_data(m,
                              data_portal, scenario_directory, subproblem, stage):

    # TODO: throw an error when a line of the 'new_build_transmission' capacity
    #   type is not found in new_build_transmission_vintage_costs.tab
    data_portal.load(filename=os.path.join(
                        scenario_directory, subproblem, stage, "inputs",
                        "new_build_transmission_vintage_costs.tab"),
                     index=m.NEW_BUILD_TRANSMISSION_VINTAGES,
                     select=("transmission_line", "vintage",
                             "tx_lifetime_yrs",
                             "tx_annualized_real_cost_per_mw_yr"),
                     param=(m.tx_lifetime_yrs_by_new_build_vintage,
                            m.tx_annualized_real_cost_per_mw_yr)
                     )


# TODO: untested
def get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    # TODO: add inputs_transmission_new_cost and
    #  subscenarios_transmission_new_cost tables to testing database
    tx_cost = c.execute(
        """SELECT transmission_line, vintage, tx_lifetime_yrs, 
        tx_annualized_real_cost_per_mw_yr
        FROM inputs_transmission_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        INNER JOIN
        (SELECT transmission_line, vintage, tx_lifetime_yrs, 
        tx_annualized_real_cost_per_mw_yr
        FROM inputs_transmission_new_cost
        WHERE transmission_new_cost_scenario_id = {} ) as cost
        USING (transmission_line, vintage   )
        WHERE transmission_portfolio_scenario_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.TRANSMISSION_EXISTING_CAPACITY_SCENARIO_ID,
            subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID
        )
    )

    return tx_cost


def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass
    # Validation to be added
    # tx_cost = get_module_specific_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


# TODO: untested
def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    .tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    tx_cost = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory,
                           "new_build_transmission_vintage_costs.tab"),
              "w", newline="") as existing_tx_capacity_tab_file:
        writer = csv.writer(existing_tx_capacity_tab_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["transmission_line", "vintage",
             "tx_lifetime_yrs", "tx_annualized_real_cost_per_mw_yr"]
        )

        for row in tx_cost:
            writer.writerow(row)


# TODO: untested
def export_module_specific_results(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Export transmission capacity
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "transmission_new_capacity.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["transmission_line", "period",
                         "load_zone_from", "load_zone_to",
                         "new_build_transmission_capacity_mw"])
        for (transmission_line, p) in m.TRANSMISSION_OPERATIONAL_PERIODS:
            writer.writerow([
                transmission_line,
                p,
                m.load_zone_from[transmission_line],
                m.load_zone_to[transmission_line],
                value(m.Build_Transmission_MW[transmission_line, p])
            ])


# TODO: untested
def import_module_specific_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # New build capacity results
    print("transmission new build")
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_transmission_capacity_new_build",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "transmission_new_capacity.csv"), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)

        next(reader)  # skip header
        for row in reader:
            transmission_line = row[0]
            period = row[1]
            load_zone_from = row[2]
            load_zone_to = row[3]
            new_build_transmission_capacity_mw = row[4]
            
            results.append(
                (scenario_id, transmission_line, period, subproblem, stage,
                 load_zone_from, load_zone_to,
                 new_build_transmission_capacity_mw)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_transmission_capacity_new_build{}
        (scenario_id, transmission_line, period, subproblem_id, stage_id, 
        load_zone_from, load_zone_to, 
        new_build_transmission_capacity_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_transmission_capacity_new_build
        (scenario_id, transmission_line, period, subproblem_id, stage_id,
        load_zone_from, load_zone_to, new_build_transmission_capacity_mw)
        SELECT
        scenario_id, transmission_line, period, subproblem_id, stage_id, 
        load_zone_from, load_zone_to, new_build_transmission_capacity_mw
        FROM temp_results_transmission_capacity_new_build{}
        ORDER BY scenario_id, transmission_line, period, subproblem_id, 
        stage_id;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
