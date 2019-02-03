#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from __future__ import print_function

from builtins import next
from builtins import zip
from builtins import str
import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, Expression, NonNegativeReals, \
    Constraint, value

from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets
from gridpath.project.capacity.capacity_types.common_methods import \
    operational_periods_by_project_vintage, project_operational_periods, \
    project_vintages_operational_in_period


def add_module_specific_components(m, d):
    """

    """
    m.NEW_BUILD_GENERATOR_VINTAGES = Set(dimen=2)
    m.lifetime_yrs_by_new_build_vintage = \
        Param(m.NEW_BUILD_GENERATOR_VINTAGES, within=NonNegativeReals)
    m.annualized_real_cost_per_mw_yr = \
        Param(m.NEW_BUILD_GENERATOR_VINTAGES, within=NonNegativeReals)

    m.NEW_BUILD_GENERATOR_VINTAGES_WITH_MIN_CONSTRAINT = Set(dimen=2)
    m.NEW_BUILD_GENERATOR_VINTAGES_WITH_MAX_CONSTRAINT = Set(dimen=2)
    m.min_cumulative_new_build_mw = \
        Param(m.NEW_BUILD_GENERATOR_VINTAGES_WITH_MIN_CONSTRAINT,
              within=NonNegativeReals)
    m.max_cumulative_new_build_mw = \
        Param(m.NEW_BUILD_GENERATOR_VINTAGES_WITH_MAX_CONSTRAINT,
              within=NonNegativeReals)

    m.Build_MW = Var(m.NEW_BUILD_GENERATOR_VINTAGES, within=NonNegativeReals)

    m.OPERATIONAL_PERIODS_BY_NEW_BUILD_GENERATOR_VINTAGE = \
        Set(m.NEW_BUILD_GENERATOR_VINTAGES,
            initialize=operational_periods_by_generator_vintage)

    m.NEW_BUILD_GENERATOR_OPERATIONAL_PERIODS = \
        Set(dimen=2, initialize=new_build_option_operational_periods)

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "NEW_BUILD_GENERATOR_OPERATIONAL_PERIODS",
    )

    m.NEW_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD = \
        Set(m.PERIODS, dimen=2,
            initialize=new_build_option_vintages_operational_in_period)

    def new_build_capacity_rule(mod, g, p):
        """
        Sum all builds of vintages operational in the current period
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return sum(mod.Build_MW[g, v] for (gen, v)
                   in mod.NEW_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                   if gen == g)

    m.New_Build_Option_Capacity_MW = \
        Expression(m.NEW_BUILD_GENERATOR_OPERATIONAL_PERIODS,
                   rule=new_build_capacity_rule)

    def min_cumulative_new_build_rule(mod, g, p):
        """
        Must build a certain amount by period p
        :param mod:
        :param g:
        :param p:
        :return:
        """
        if mod.min_cumulative_new_build_mw == 0:
            return Constraint.Skip
        else:
            return mod.New_Build_Option_Capacity_MW[g, p] >= \
                mod.min_cumulative_new_build_mw[g, p]
    m.Min_Cumulative_New_Capacity_Constraint = Constraint(
        m.NEW_BUILD_GENERATOR_VINTAGES_WITH_MIN_CONSTRAINT,
        rule=min_cumulative_new_build_rule)

    def max_cumulative_new_build_rule(mod, g, p):
        """
        Can't build more than certain amount by period p
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return mod.New_Build_Option_Capacity_MW[g, p] <= \
            mod.max_cumulative_new_build_mw[g, p]
    m.Max_Cumulative_New_Capacity_Constraint = Constraint(
        m.NEW_BUILD_GENERATOR_VINTAGES_WITH_MAX_CONSTRAINT,
        rule=max_cumulative_new_build_rule)


def capacity_rule(mod, g, p):
    """

    :param mod:
    :param g:
    :param p:
    :return:
    """
    return mod.New_Build_Option_Capacity_MW[g, p]


def capacity_cost_rule(mod, g, p):
    """
    Capacity cost for new builds in each period (sum over all vintages
    operational in current period)
    :param mod: 
    :param g: 
    :param p: 
    :return: 
    """
    return sum(mod.Build_MW[g, v]
               * mod.annualized_real_cost_per_mw_yr[g, v]
               for (gen, v)
               in mod.NEW_BUILD_GENERATOR_VINTAGES_OPERATIONAL_IN_PERIOD[p]
               if gen == g)


def load_module_specific_data(
        m, data_portal, scenario_directory, horizon, stage
):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # TODO: throw an error when a generator of the 'new_build_option' capacity
    # type is not found in new_build_option_vintage_costs.tab
    data_portal.load(filename=
                     os.path.join(scenario_directory,
                                  "inputs",
                                  "new_build_generator_vintage_costs.tab"),
                     index=
                     m.NEW_BUILD_GENERATOR_VINTAGES,
                     select=("project", "vintage",
                             "lifetime_yrs", "annualized_real_cost_per_mw_yr"),
                     param=(m.lifetime_yrs_by_new_build_vintage,
                            m.annualized_real_cost_per_mw_yr)
                     )

    # Min and max cumulative capacity
    project_vintages_with_min = list()
    project_vintages_with_max = list()
    min_cumulative_mw = dict()
    max_cumulative_mw = dict()

    header = pd.read_csv(os.path.join(scenario_directory, "inputs",
                                      "new_build_generator_vintage_costs.tab"),
                         sep="\t", header=None, nrows=1).values[0]

    optional_columns = ["min_cumulative_new_build_mw",
                        "max_cumulative_new_build_mw"]
    used_columns = [c for c in optional_columns if c in header]

    dynamic_components = \
        pd.read_csv(
            os.path.join(scenario_directory, "inputs",
                         "new_build_generator_vintage_costs.tab"),
            sep="\t", usecols=["project",
                               "vintage"] + used_columns
            )

    # min_cumulative_new_build_mw is optional,
    # so NEW_BUILD_GENERATOR_VINTAGES_WITH_MIN_CONSTRAINT
    # and min_cumulative_new_build_mw simply won't be initialized if
    # min_cumulative_new_build_mw does not exist in the input file
    if "min_cumulative_new_build_mw" in dynamic_components.columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["vintage"],
                       dynamic_components["min_cumulative_new_build_mw"]):
            if row[2] != ".":
                project_vintages_with_min.append((row[0], row[1]))
                min_cumulative_mw[(row[0], row[1])] = float(row[2])
            else:
                pass
    else:
        pass

    # max_cumulative_new_build_mw is optional,
    # so NEW_BUILD_GENERATOR_VINTAGES_WITH_MAX_CONSTRAINT
    # and max_cumulative_new_build_mw simply won't be initialized if
    # max_cumulative_new_build_mw does not exist in the input file
    if "max_cumulative_new_build_mw" in dynamic_components.columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["vintage"],
                       dynamic_components["max_cumulative_new_build_mw"]):
            if row[2] != ".":
                project_vintages_with_max.append((row[0], row[1]))
                max_cumulative_mw[(row[0], row[1])] = float(row[2])
            else:
                pass
    else:
        pass

    # Load min and max cumulative capacity data
    if not project_vintages_with_min:
        pass  # if the list is empty, don't initialize the set
    else:
        data_portal.data()[
            "NEW_BUILD_GENERATOR_VINTAGES_WITH_MIN_CONSTRAINT"
        ] = {None: project_vintages_with_min}
    data_portal.data()["min_cumulative_new_build_mw"] = \
        min_cumulative_mw

    if not project_vintages_with_max:
        pass  # if the list is empty, don't initialize the set
    else:
        data_portal.data()[
            "NEW_BUILD_GENERATOR_VINTAGES_WITH_MAX_CONSTRAINT"
        ] = {None: project_vintages_with_max}
    data_portal.data()["max_cumulative_new_build_mw"] = \
        max_cumulative_mw


def export_module_specific_results(scenario_directory, horizon, stage, m, d):
    """
    Export new build generation results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "capacity_new_build_generator.csv"), "w") as f:

        writer = csv.writer(f)
        writer.writerow(["project", "period", "technology", "load_zone",
                         "new_build_mw"])
        for (prj, p) in m.NEW_BUILD_GENERATOR_VINTAGES:
            writer.writerow([
                prj,
                p,
                m.technology[prj],
                m.load_zone[prj],
                value(m.Build_MW[prj, p])
            ])


def operational_periods_by_generator_vintage(mod, prj, v):
    return operational_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"), vintage=v,
        lifetime=mod.lifetime_yrs_by_new_build_vintage[prj, v]
    )


def new_build_option_operational_periods(mod):
    return project_operational_periods(
        project_vintages_set=mod.NEW_BUILD_GENERATOR_VINTAGES,
        operational_periods_by_project_vintage_set=
        mod.OPERATIONAL_PERIODS_BY_NEW_BUILD_GENERATOR_VINTAGE
    )


def new_build_option_vintages_operational_in_period(mod, p):
    return project_vintages_operational_in_period(
        project_vintage_set=mod.NEW_BUILD_GENERATOR_VINTAGES,
        operational_periods_by_project_vintage_set=
        mod.OPERATIONAL_PERIODS_BY_NEW_BUILD_GENERATOR_VINTAGE,
        period=p
    )


def summarize_module_specific_results(
    problem_directory, horizon, stage, summary_results_file
):
    """
    Summarize new build generation capacity results.
    :param problem_directory:
    :param horizon:
    :param stage:
    :param summary_results_file:
    :return:
    """

    # Get the results CSV as dataframe
    capacity_results_df = \
        pd.read_csv(os.path.join(problem_directory, horizon, stage, "results",
                                 "capacity_new_build_generator.csv")
                    )

    capacity_results_agg_df = \
        capacity_results_df.groupby(by=["load_zone", "technology",
                                        'period'],
                                    as_index=True
                                    ).sum()

    # Set the formatting of float to be readable
    pd.options.display.float_format = "{:,.0f}".format

    # Get all technologies with the new build capacity
    new_build_df = pd.DataFrame(
        capacity_results_agg_df[
            capacity_results_agg_df["new_build_mw"] > 0
        ]["new_build_mw"]
    )

    new_build_df.columns = ["New Capacity (MW)"]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> New Generation Capacity <--\n")
        if new_build_df.empty:
            outfile.write("No new generation was built.\n")
        else:
            new_build_df.to_string(outfile)
            outfile.write("\n")


def get_module_specific_inputs_from_database(
        subscenarios, c, inputs_directory
):
    """
    new_build_generator_vintage_costs.tab
    :param subscenarios: 
    :param c: 
    :param inputs_directory: 
    :return: 
    """

    get_potentials = \
        (" ", " ") if subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID is None \
        else (
            """, minimum_cumulative_new_build_mw, 
            maximum_cumulative_new_build_mw """,
            """LEFT OUTER JOIN
            (SELECT project, period, minimum_cumulative_new_build_mw,
            maximum_cumulative_new_build_mw
            FROM inputs_project_new_potential
            WHERE project_new_potential_scenario_id = {}) as potential
            USING (project, period) """.format(
                subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID
            )
        )

    new_gen_costs = c.execute(
        """SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr * 1000"""
        + get_potentials[0] +
        """FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE timepoint_scenario_id = {}) as relevant_periods
        INNER JOIN
        (SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr
        FROM inputs_project_new_cost
        WHERE project_new_cost_scenario_id = {}) as cost
        USING (project, period)""".format(
            subscenarios.TIMEPOINT_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
        )
        + get_potentials[1] +
        """WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 'new_build_generator';""".format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    with open(os.path.join(inputs_directory,
                           "new_build_generator_vintage_costs.tab"), "w") as \
            new_gen_costs_tab_file:
        writer = csv.writer(new_gen_costs_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["project", "vintage", "lifetime_yrs",
             "annualized_real_cost_per_mw_yr"] +
            ([] if subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID is None
            else ["min_cumulative_new_build_mw",
                  "max_cumulative_new_build_mw"])
        )

        for row in new_gen_costs:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


def import_module_specific_results_into_database(
        scenario_id, c, db, results_directory
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # New build capacity results
    print("project new build generator")
    c.execute(
        """DELETE FROM results_project_capacity_new_build_generator 
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS 
        temp_results_project_capacity_new_build_generator"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_capacity_new_build_generator"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        project VARCHAR(64),
        period INTEGER,
        technology VARCHAR(32),
        load_zone VARCHAR(32),
        new_build_mw FLOAT,
        PRIMARY KEY (scenario_id, project, period)
        );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "capacity_new_build_generator.csv"), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            technology = row[2]
            load_zone = row[3]
            new_build_mw = row[4]

            c.execute(
                """INSERT INTO 
                temp_results_project_capacity_new_build_generator"""
                + str(scenario_id) + """
                (scenario_id, project, period, technology, load_zone,
                new_build_mw)
                VALUES ({}, '{}', {}, '{}', '{}', {});""".format(
                    scenario_id, project, period, technology, load_zone,
                    new_build_mw
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_capacity_new_build_generator
        (scenario_id, project, period, technology, load_zone, new_build_mw)
        SELECT
        scenario_id, project, period, technology, load_zone, new_build_mw
        FROM temp_results_project_capacity_new_build_generator"""
        + str(scenario_id)
        + """
        ORDER BY scenario_id, project, period;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_capacity_new_build_generator"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
