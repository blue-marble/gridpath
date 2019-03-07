#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
gridpath.project.capacity.capacity_types.new_build_storage
----------------------------------------------------------
The **gridpath.project.capacity.capacity_types.new_build_storage**
module describes the capacity of storage projects that can be built by the
optimization at a cost. The optimization determines both the power
capacity of the storage project and its energy capacity (i.e. capacity and
duration). Once built, these storage projects remain available for the
duration of their pre-specified lifetime. Minimum and maximum power capacity
and duration constraints can be optionally implemented.
"""

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
    capacity_type_operational_period_sets, \
    storage_only_capacity_type_operational_period_sets
from gridpath.project.capacity.capacity_types.common_methods import \
    operational_periods_by_project_vintage, project_operational_periods, \
    project_vintages_operational_in_period


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    Describes the model formulation for a new-build storage option. Detailed
    description to be added.

    .. todo:: add description
    """
    m.NEW_BUILD_STORAGE_PROJECTS = Set()
    m.minimum_duration_hours = \
        Param(m.NEW_BUILD_STORAGE_PROJECTS, within=NonNegativeReals)
    m.NEW_BUILD_STORAGE_VINTAGES = \
        Set(dimen=2, within=m.NEW_BUILD_STORAGE_PROJECTS*m.PERIODS)
    m.lifetime_yrs_by_new_build_storage_vintage = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES, within=NonNegativeReals)
    m.new_build_storage_annualized_real_cost_per_mw_yr = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES, within=NonNegativeReals)
    m.new_build_storage_annualized_real_cost_per_mwh_yr = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES, within=NonNegativeReals)

    # Min and max cumulative MW and MWh are optional params that will be
    # initialized only if data are specified
    m.NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_CAPACITY_CONSTRAINT = Set(dimen=2)
    m.NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_ENERGY_CONSTRAINT = Set(dimen=2)
    m.NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_CAPACITY_CONSTRAINT = Set(dimen=2)
    m.NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_ENERGY_CONSTRAINT = Set(dimen=2)
    m.min_storage_cumulative_new_build_mw = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_CAPACITY_CONSTRAINT,
              within=NonNegativeReals)
    m.min_storage_cumulative_new_build_mwh = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_ENERGY_CONSTRAINT,
              within=NonNegativeReals)
    m.max_storage_cumulative_new_build_mw = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_CAPACITY_CONSTRAINT,
              within=NonNegativeReals)
    m.max_storage_cumulative_new_build_mwh = \
        Param(m.NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_ENERGY_CONSTRAINT,
              within=NonNegativeReals)

    m.Build_Storage_Power_MW = \
        Var(m.NEW_BUILD_STORAGE_VINTAGES,
            within=NonNegativeReals)
    m.Build_Storage_Energy_MWh = \
        Var(m.NEW_BUILD_STORAGE_VINTAGES,
            within=NonNegativeReals)

    m.OPERATIONAL_PERIODS_BY_NEW_BUILD_STORAGE_VINTAGE = \
        Set(m.NEW_BUILD_STORAGE_VINTAGES,
            initialize=operational_periods_by_storage_vintage)

    m.NEW_BUILD_STORAGE_OPERATIONAL_PERIODS = \
        Set(dimen=2, initialize=new_build_storage_operational_periods)

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "NEW_BUILD_STORAGE_OPERATIONAL_PERIODS",
    )
    # Add to list of sets we'll join to get the final
    # STORAGE_OPERATIONAL_PERIODS set
    getattr(d, storage_only_capacity_type_operational_period_sets).append(
        "NEW_BUILD_STORAGE_OPERATIONAL_PERIODS",
    )

    m.NEW_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD = \
        Set(m.PERIODS, dimen=2,
            initialize=new_build_storage_vintages_operational_in_period)

    def new_build_storage_power_capacity_rule(mod, g, p):
        """
        Sum all builds of vintages operational in the current period
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return sum(mod.Build_Storage_Power_MW[g, v] for (gen, v)
                   in mod.NEW_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                   if gen == g)

    m.New_Build_Storage_Power_Capacity_MW = \
        Expression(m.NEW_BUILD_STORAGE_OPERATIONAL_PERIODS,
                   rule=new_build_storage_power_capacity_rule)

    def new_build_storage_energy_capacity_rule(mod, g, p):
        """
        Sum all builds of vintages operational in the current period
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return sum(mod.Build_Storage_Energy_MWh[g, v] for (gen, v)
                   in mod.NEW_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD[p]
                   if gen == g)

    m.New_Build_Storage_Energy_Capacity_MWh = \
        Expression(m.NEW_BUILD_STORAGE_OPERATIONAL_PERIODS,
                   rule=new_build_storage_energy_capacity_rule)

    def minimum_duration_constraint_rule(mod, g, p):
        """
        Storage duration must be above a pre-specified requirement
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return mod.New_Build_Storage_Energy_Capacity_MWh[g, p] >= \
            mod.New_Build_Storage_Power_Capacity_MW[g, p] * \
            mod.minimum_duration_hours[g]
    m.New_Build_Storage_Minimum_Duration_Constraint = \
        Constraint(m.NEW_BUILD_STORAGE_OPERATIONAL_PERIODS,
                   rule=minimum_duration_constraint_rule)

    def min_cumulative_new_build_capacity_rule(mod, g, p):
        """
        Must build a certain amount of capacity by period p
        :param mod:
        :param g:
        :param p:
        :return:
        """
        if mod.min_storage_cumulative_new_build_mw == 0:
            return Constraint.Skip
        else:
            return mod.New_Build_Storage_Power_Capacity_MW[g, p] >= \
                mod.min_storage_cumulative_new_build_mw[g, p]
    m.Min_Storage_Cumulative_New_Capacity_Constraint = Constraint(
        m.NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_CAPACITY_CONSTRAINT,
        rule=min_cumulative_new_build_capacity_rule)

    def min_cumulative_new_build_energy_rule(mod, g, p):
        """
        Must build a certain amount of energy by period p
        :param mod:
        :param g:
        :param p:
        :return:
        """
        if mod.min_storage_cumulative_new_build_mwh == 0:
            return Constraint.Skip
        else:
            return mod.New_Build_Storage_Energy_Capacity_MWh[g, p] >= \
                mod.min_storage_cumulative_new_build_mwh[g, p]
    m.Min_Storage_Cumulative_New_Energy_Constraint = Constraint(
        m.NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_ENERGY_CONSTRAINT,
        rule=min_cumulative_new_build_energy_rule)

    def max_cumulative_new_build_capacity_rule(mod, g, p):
        """
        Can't build more than certain amount of capacity by period p
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return mod.New_Build_Storage_Power_Capacity_MW[g, p] <= \
            mod.max_storage_cumulative_new_build_mw[g, p]
    m.Max_Storage_Cumulative_New_Capacity_Constraint = Constraint(
        m.NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_CAPACITY_CONSTRAINT,
        rule=max_cumulative_new_build_capacity_rule)

    def max_cumulative_new_build_energy_rule(mod, g, p):
        """
        Can't build more than certain amount of energy by period p
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return mod.New_Build_Storage_Energy_Capacity_MWh[g, p] <= \
            mod.max_storage_cumulative_new_build_mwh[g, p]
    m.Max_Storage_Cumulative_New_Energy_Constraint = Constraint(
        m.NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_ENERGY_CONSTRAINT,
        rule=max_cumulative_new_build_energy_rule)


def capacity_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the power capacity of storage project *g* in period *p*

    The total power capacity at storage project :math:`g` that is operational
    in period :math:`p`.
    """
    return mod.New_Build_Storage_Power_Capacity_MW[g, p]


def energy_capacity_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the energy capacity of storage project *g* in period *p*

    The total energy capacity at storage project :math:`g` that is operational
    in period :math:`p`.
    """
    return mod.New_Build_Storage_Energy_Capacity_MWh[g, p]


def capacity_cost_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the total annualized capacity cost of *new_build_storage*
        project *g* in period *p*

    Power and energy capacity cost for new_build_storage projects in each
    period (sum over all vintages operational in current period).
    """
    return sum((mod.Build_Storage_Power_MW[g, v]
               * mod.new_build_storage_annualized_real_cost_per_mw_yr[g, v]
               + mod.Build_Storage_Energy_MWh[g, v]
               * mod.new_build_storage_annualized_real_cost_per_mwh_yr[g, v])
               for (gen, v)
               in mod.NEW_BUILD_STORAGE_VINTAGES_OPERATIONAL_IN_PERIOD[p]
               if gen == g)


def load_module_specific_data(m,
                              data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    def determine_minimum_duration():
        """
        :return:
        """
        new_build_storage_projects = list()
        storage_min_duration = dict()

        dynamic = \
            pd.read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project", "capacity_type",
                                   "minimum_duration_hours"]
            )
        for r in zip(dynamic["project"],
                     dynamic["capacity_type"],
                     dynamic["minimum_duration_hours"]):
            if r[1] == "new_build_storage":
                new_build_storage_projects.append(r[0])
                storage_min_duration[r[0]] \
                    = float(r[2])
            else:
                pass

        return new_build_storage_projects, storage_min_duration

    data_portal.data()["NEW_BUILD_STORAGE_PROJECTS"] = {
        None: determine_minimum_duration()[0]
    }
    data_portal.data()["minimum_duration_hours"] = \
        determine_minimum_duration()[1]

    # TODO: throw an error when a generator of the 'new_build_storage' capacity
    #   type is not found in new_build_storage_vintage_costs.tab
    data_portal.load(filename=
                     os.path.join(scenario_directory,
                                  "inputs",
                                  "new_build_storage_vintage_costs.tab"),
                     index=
                     m.NEW_BUILD_STORAGE_VINTAGES,
                     select=("project", "vintage",
                             "lifetime_yrs", "annualized_real_cost_per_mw_yr",
                             "annualized_real_cost_per_mwh_yr"),
                     param=(m.lifetime_yrs_by_new_build_storage_vintage,
                            m.new_build_storage_annualized_real_cost_per_mw_yr,
                            m.new_build_storage_annualized_real_cost_per_mwh_yr
                            )
                     )

    # Min and max power capacity and energy
    project_vintages_with_min_capacity = list()
    project_vintages_with_min_energy = list()
    project_vintages_with_max_capacity = list()
    project_vintages_with_max_energy = list()
    min_cumulative_mw = dict()
    min_cumulative_mwh = dict()
    max_cumulative_mw = dict()
    max_cumulative_mwh = dict()

    header = pd.read_csv(os.path.join(scenario_directory, "inputs",
                                      "new_build_storage_vintage_costs.tab"),
                         sep="\t", header=None, nrows=1).values[0]

    dynamic_columns = ["min_cumulative_new_build_mw",
                       "min_cumulative_new_build_mwh",
                       "max_cumulative_new_build_mw",
                       "max_cumulative_new_build_mwh"]
    used_columns = [c for c in dynamic_columns if c in header]

    dynamic_components = \
        pd.read_csv(
            os.path.join(scenario_directory, "inputs",
                         "new_build_storage_vintage_costs.tab"),
            sep="\t",
            usecols=["project", "vintage"] + used_columns
            )

    # min_storage_cumulative_new_build_mw and
    # min_storage_cumulative_new_build_mwh are optional,
    # so NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_CONSTRAINT
    # and either params won't be initialized if the param does not exist in
    # the input file
    if "min_cumulative_new_build_mw" in dynamic_components.columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["vintage"],
                       dynamic_components["min_cumulative_new_build_mw"]):
            if row[2] != ".":
                project_vintages_with_min_capacity.append((row[0], row[1]))
                min_cumulative_mw[(row[0], row[1])] = float(row[2])
            else:
                pass
    else:
        pass

    if "min_cumulative_new_build_mwh" in dynamic_components.columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["vintage"],
                       dynamic_components["min_cumulative_new_build_mwh"]):
            if row[2] != ".":
                project_vintages_with_min_energy.append((row[0], row[1]))
                min_cumulative_mwh[(row[0], row[1])] = float(row[2])
            else:
                pass
    else:
        pass

    # min_storage_cumulative_new_build_mw and
    # min_storage_cumulative_new_build_mwh are optional,
    # so NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_CONSTRAINT
    # and either params won't be initialized if the param does not exist in
    # the input file
    if "max_cumulative_new_build_mw" in dynamic_components.columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["vintage"],
                       dynamic_components["max_cumulative_new_build_mw"]):
            if row[2] != ".":
                project_vintages_with_max_capacity.append((row[0], row[1]))
                max_cumulative_mw[(row[0], row[1])] = float(row[2])
            else:
                pass
    else:
        pass

    if "max_cumulative_new_build_mwh" in dynamic_components.columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["vintage"],
                       dynamic_components["max_cumulative_new_build_mwh"]):
            if row[2] != ".":
                project_vintages_with_max_energy.append((row[0], row[1]))
                max_cumulative_mwh[(row[0], row[1])] = float(row[2])
            else:
                pass
    else:
        pass

    # Load the min and max capacity and energy data
    if not project_vintages_with_min_capacity:
        pass  # if the list is empty, don't initialize the set
    else:
        data_portal.data()[
            "NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_CAPACITY_CONSTRAINT"
        ] = {None: project_vintages_with_min_capacity}
    data_portal.data()["min_storage_cumulative_new_build_mw"] = \
        min_cumulative_mw

    if not project_vintages_with_min_energy:
        pass  # if the list is empty, don't initialize the set
    else:
        data_portal.data()[
            "NEW_BUILD_STORAGE_VINTAGES_WITH_MIN_ENERGY_CONSTRAINT"
        ] = {None: project_vintages_with_min_energy}
    data_portal.data()["min_storage_cumulative_new_build_mwh"] = \
        min_cumulative_mwh

    if not project_vintages_with_max_capacity:
        pass  # if the list is empty, don't initialize the set
    else:
        data_portal.data()[
            "NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_CAPACITY_CONSTRAINT"
        ] = {None: project_vintages_with_max_capacity}
    data_portal.data()["max_storage_cumulative_new_build_mw"] = \
        max_cumulative_mw

    if not project_vintages_with_max_energy:
        pass  # if the list is empty, don't initialize the set
    else:
        data_portal.data()[
            "NEW_BUILD_STORAGE_VINTAGES_WITH_MAX_ENERGY_CONSTRAINT"
        ] = {None: project_vintages_with_max_energy}
    data_portal.data()["max_storage_cumulative_new_build_mwh"] = \
        max_cumulative_mwh


def export_module_specific_results(scenario_directory, horizon, stage, m, d):
    """
    Export new build storage results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "capacity_new_build_storage.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "technology", "load_zone",
                         "new_build_mw", "new_build_mwh"])
        for (prj, p) in m.NEW_BUILD_STORAGE_VINTAGES:
            writer.writerow([
                prj,
                p,
                m.technology[prj],
                m.load_zone[prj],
                value(m.Build_Storage_Power_MW[prj, p]),
                value(m.Build_Storage_Energy_MWh[prj, p])
            ])


def operational_periods_by_storage_vintage(mod, prj, v):
    return operational_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"), vintage=v,
        lifetime=mod.lifetime_yrs_by_new_build_storage_vintage[prj, v])


def new_build_storage_operational_periods(mod):
    return project_operational_periods(
        project_vintages_set=mod.NEW_BUILD_STORAGE_VINTAGES,
        operational_periods_by_project_vintage_set=
        mod.OPERATIONAL_PERIODS_BY_NEW_BUILD_STORAGE_VINTAGE
    )


def new_build_storage_vintages_operational_in_period(mod, p):
    return project_vintages_operational_in_period(
        project_vintage_set=mod.NEW_BUILD_STORAGE_VINTAGES,
        operational_periods_by_project_vintage_set=
        mod.OPERATIONAL_PERIODS_BY_NEW_BUILD_STORAGE_VINTAGE,
        period=p
    )


def summarize_module_specific_results(
    problem_directory, horizon, stage, summary_results_file
):
    """
    Summarize new build storage capacity results.
    :param problem_directory:
    :param horizon:
    :param stage:
    :param summary_results_file:
    :return:
    """

    # Get the results CSV as dataframe
    capacity_results_df = \
        pd.read_csv(os.path.join(problem_directory, horizon, stage, "results",
                                 "capacity_new_build_storage.csv")
                    )

    capacity_results_agg_df = \
        capacity_results_df.groupby(by=["load_zone", "technology",
                                        'period'],
                                    as_index=True
                                    ).sum()

    # Set the formatting of float to be readable
    pd.options.display.float_format = "{:,.0f}".format
    # Get all technologies with new build storage power OR energy capacity
    new_build_df = pd.DataFrame(
        capacity_results_agg_df[
            (capacity_results_agg_df["new_build_mw"] > 0) |
            (capacity_results_agg_df["new_build_mwh"] > 0)
        ][["new_build_mw", "new_build_mwh"]]
    )
    new_build_df.columns =["New Storage Power Capacity (MW)",
                           "New Storage Energy Capacity (MWh)"]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> New Storage Capacity <--\n")
        if new_build_df.empty:
            outfile.write("No new storage was built.\n")
        else:
            new_build_df.to_string(outfile)
            outfile.write("\n")


def get_module_specific_inputs_from_database(
        subscenarios, c, inputs_directory
):
    """
    new_build_storage_vintage_costs.tab
    :param subscenarios: 
    :param c: 
    :param inputs_directory: 
    :return: 
    """

    get_potentials = \
        (" ", " ") if subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID is None \
        else (
            """, minimum_cumulative_new_build_mw, 
            minimum_cumulative_new_build_mwh,
            maximum_cumulative_new_build_mw, 
            maximum_cumulative_new_build_mwh """,
            """LEFT OUTER JOIN
            (SELECT project, period,
            minimum_cumulative_new_build_mw, minimum_cumulative_new_build_mwh,
            maximum_cumulative_new_build_mw, maximum_cumulative_new_build_mwh
            FROM inputs_project_new_potential
            WHERE project_new_potential_scenario_id = {}) as potential
            USING (project, period) """.format(
                subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID
            )
        )

    new_stor_costs = c.execute(
        """SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr * 1000,
        annualized_real_cost_per_kwh_yr * 1000"""
        + get_potentials[0] +
        """FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE timepoint_scenario_id = {}) as relevant_periods
        INNER JOIN
        (SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr, annualized_real_cost_per_kwh_yr
        FROM inputs_project_new_cost
        WHERE project_new_cost_scenario_id = {}) as cost
        USING (project, period)""".format(
            subscenarios.TIMEPOINT_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
        )
        + get_potentials[1] +
        """WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 'new_build_storage';""".format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    with open(os.path.join(inputs_directory,
                           "new_build_storage_vintage_costs.tab"), "w") as \
            new_storage_costs_tab_file:
        writer = csv.writer(new_storage_costs_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["project", "vintage", "lifetime_yrs",
             "annualized_real_cost_per_mw_yr",
             "annualized_real_cost_per_mwh_yr"] +
            ([] if subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID is None
            else [
             "min_cumulative_new_build_mw", "min_cumulative_new_build_mwh",
             "max_cumulative_new_build_mw", "max_cumulative_new_build_mwh"
            ])
        )

        for row in new_stor_costs:
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
    # Capacity results
    print("project new build storage")
    c.execute(
        """DELETE FROM results_project_capacity_new_build_storage 
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS 
        temp_results_project_capacity_new_build_storage"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_capacity_new_build_storage"""
        + str(scenario_id) + """(
        scenario_id INTEGER,
        project VARCHAR(64),
        period INTEGER,
        technology VARCHAR(32),
        load_zone VARCHAR(32),
        new_build_mw FLOAT,
        new_build_mwh FLOAT,
        PRIMARY KEY (scenario_id, project, period)
        );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(results_directory,
                           "capacity_new_build_storage.csv"), "r") as \
            capacity_file:
        reader = csv.reader(capacity_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            technology = row[2]
            load_zone = row[3]
            new_build_mw = row[4]
            new_build_mwh = row[5]

            c.execute(
                """INSERT INTO 
                temp_results_project_capacity_new_build_storage"""
                + str(scenario_id) + """
                (scenario_id, project, period, technology, load_zone,
                new_build_mw, new_build_mwh)
                VALUES ({}, '{}', {}, '{}', '{}', {}, {});""".format(
                    scenario_id, project, period, technology, load_zone,
                    new_build_mw, new_build_mwh,
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_capacity_new_build_storage
        (scenario_id, project, period, technology, load_zone,
        new_build_mw, new_build_mwh)
        SELECT
        scenario_id, project, period, technology, load_zone,
        new_build_mw, new_build_mwh
        FROM temp_results_project_capacity_new_build_storage""" + str(scenario_id) + """
        ORDER BY scenario_id, project, period;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_capacity_new_build_storage"""
        + str(scenario_id) +
        """;"""
    )
    db.commit()
