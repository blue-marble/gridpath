#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
gridpath.project.capacity.capacity_types.new_shiftable_load_supply_curve
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This module describes a supply curve for new shiftable load capacity.

The supply curve does not have vintages, i.e. there are no cost differences for
capacity built in different periods. The cost for new capacity is specified
via a piecewise linear function of new capacity build and constraint (cost is
constrained to be greater than or equal to the function).

The new capacity build variable has units of MWh. We then calculate the
power capacity based on the 'minimum duration' specified for the project,
e.g. if the minimum duration specified is N hours, then the MW capacity will
be the new build in MWh divided by N (the MWh capacity can't be discharged
in less than N hours, as the max power constraint will bind).
"""
from __future__ import division

from builtins import zip
from builtins import range
from past.utils import old_div
import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, NonNegativeReals, \
    Reals, Expression, Constraint

from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets, \
    storage_only_capacity_type_operational_period_sets


def add_module_specific_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding the components to
    :param d: the DynamicComponents class object we are adding components to

    Describes the model formulation for a supply curve for shift DR. No
    vintages for now.
    """

    m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS = Set()
    m.shiftable_load_supply_curve_min_duration = Param(
        m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS, within=NonNegativeReals
    )

    m.new_shiftable_load_supply_curve_min_cumulative_new_build_mwh = Param(
        m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS, m.PERIODS,
        within=NonNegativeReals
    )
    m.new_shiftable_load_supply_curve_max_cumulative_new_build_mwh = Param(
        m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS, m.PERIODS,
        within=NonNegativeReals
    )

    # Limit supply curve to 1000 points
    m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_POINTS = Set(
        dimen=2,
        within=m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS*list(range(1, 1001))
    )
    m.new_shiftable_load_supply_curve_slope = Param(
        m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_POINTS,
        within=NonNegativeReals
    )
    m.new_shiftable_load_supply_curve_intercept = Param(
        m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_POINTS,
        within=Reals
    )

    # No vintages (can build in all periods with no cost differences)
    # Supply curve is in terms of energy
    m.Build_Shiftable_Load_Supply_Curve_Energy_MWh = Var(
        m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS, m.PERIODS,
        within=NonNegativeReals
    )

    # No vintages, so all periods are operational
    m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_OPERATIONAL_PERIODS = Set(
        dimen=2,
        initialize=m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS*m.PERIODS
    )

    # Add to list of sets we'll join to get the final
    # PROJECT_OPERATIONAL_PERIODS set
    getattr(d, capacity_type_operational_period_sets).append(
        "NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_OPERATIONAL_PERIODS",
    )
    # Add to list of sets we'll join to get the final
    # STORAGE_OPERATIONAL_PERIODS set
    # We'll include shiftable load with storage
    getattr(d, storage_only_capacity_type_operational_period_sets).append(
        "NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_OPERATIONAL_PERIODS",
    )

    def new_shiftable_load_supply_curve_energy_capacity_rule(mod, g, p):
        """
        Vintages = all periods
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return sum(
            mod.Build_Shiftable_Load_Supply_Curve_Energy_MWh[g, prev_p]
            for prev_p in mod.PERIODS if prev_p <= p
        )

    m.New_Shiftable_Load_Supply_Curve_Energy_Capacity_MWh = Expression(
        m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_OPERATIONAL_PERIODS,
        rule=new_shiftable_load_supply_curve_energy_capacity_rule
    )

    def new_shiftable_load_supply_curve_power_capacity_rule(mod, g, p):
        """
        Vintages = all periods

        :param mod:
        :param g:
        :param p:
        :return:
        """
        return old_div(
            mod.Build_Shiftable_Load_Supply_Curve_Energy_MWh[g, p],
            mod.shiftable_load_supply_curve_min_duration[g]
        )

    m.New_Shiftable_Load_Supply_Curve_Power_Capacity_MW = Expression(
        m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_OPERATIONAL_PERIODS,
        rule=new_shiftable_load_supply_curve_power_capacity_rule
    )

    # Cost
    m.New_Shiftable_Load_Supply_Curve_Cost = Var(
        m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_OPERATIONAL_PERIODS,
        within=NonNegativeReals
    )

    def new_shiftable_load_supply_curve_cost_rule(mod, project, point, period):
        """

        :param mod:
        :param project:
        :param point:
        :param period:
        :return:
        """
        return mod.New_Shiftable_Load_Supply_Curve_Cost[project, period] \
            >= mod.new_shiftable_load_supply_curve_slope[project, point] \
            * mod.New_Shiftable_Load_Supply_Curve_Energy_Capacity_MWh[
                      project, period] \
            + mod.new_shiftable_load_supply_curve_intercept[project, point]

    m.New_Shiftable_Load_Supply_Curve_Cost_Constraint = Constraint(
        m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_POINTS*m.PERIODS,
        rule=new_shiftable_load_supply_curve_cost_rule
    )


def capacity_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the power capacity of storage project *g* in period *p*

    The total power capacity of shiftable load operational in period :math:`p`.
    """
    return mod.New_Shiftable_Load_Supply_Curve_Power_Capacity_MW[g, p]


def energy_capacity_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the power capacity of storage project *g* in period *p*

    The total power capacity of shiftable load operational in period :math:`p`.
    """
    return mod.New_Shiftable_Load_Supply_Curve_Energy_Capacity_MWh[g, p]


def capacity_cost_rule(mod, g, p):
    """
    :param mod: the Pyomo abstract model
    :param g: the project
    :param p: the operational period
    :return: the total annualized capacity cost of
        *new_shiftable_load_supply_curve* project *g* in period *p*
    """
    return mod.New_Shiftable_Load_Supply_Curve_Cost[g, p]


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

    def determine_projects():
        """
        :return:
        """
        projects = list()
        max_fraction = dict()

        dynamic = \
            pd.read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project", "capacity_type",
                                   "minimum_duration_hours"]
            )
        for r in zip(dynamic["project"],
                     dynamic["capacity_type"],
                     dynamic["minimum_duration_hours"]):
            if r[1] == "new_shiftable_load_supply_curve":
                projects.append(r[0])
                max_fraction[r[0]] \
                    = float(r[2])
            else:
                pass

        return projects, max_fraction

    data_portal.data()["NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECTS"] = {
        None: determine_projects()[0]
    }
    data_portal.data()["shiftable_load_supply_curve_min_duration"] = \
        determine_projects()[1]

    data_portal.load(
        filename=os.path.join(
            scenario_directory, "inputs",
            "new_shiftable_load_supply_curve.tab"),
        index=m.NEW_SHIFTABLE_LOAD_SUPPLY_CURVE_PROJECT_POINTS,
        select=("project", "point", "slope", "intercept"),
        param=(m.new_shiftable_load_supply_curve_slope,
               m.new_shiftable_load_supply_curve_intercept)
    )

    data_portal.load(
        filename=os.path.join(
            scenario_directory, "inputs",
            "new_shiftable_load_supply_curve_potential.tab"),
        param=(
            m.new_shiftable_load_supply_curve_min_cumulative_new_build_mwh,
            m.new_shiftable_load_supply_curve_max_cumulative_new_build_mwh
        )
    )


def get_module_specific_inputs_from_database(
        subscenarios, c, inputs_directory
):
    """
    Get min build and max potential
    Max potential is required for this module,
    so PROJECT_NEW_POTENTIAL_SCENARIO_ID can't be NULL
    :param subscenarios:
    :param c:
    :param inputs_directory:
    :return:
    """

    if subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID is None:
        raise ValueError("Maximum potential must be specified for new "
                         "shiftable load supply curve projects.")

    min_max_builds = c.execute(
        """SELECT project, period, 
        minimum_cumulative_new_build_mwh, maximum_cumulative_new_build_mwh
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE timepoint_scenario_id = {}) as relevant_periods
        LEFT OUTER JOIN
        (SELECT project, period,
        minimum_cumulative_new_build_mw, minimum_cumulative_new_build_mwh,
        maximum_cumulative_new_build_mw, maximum_cumulative_new_build_mwh
        FROM inputs_project_new_potential
        WHERE project_new_potential_scenario_id = {}) as potential
        USING (project, period) 
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 'new_shiftable_load_supply_curve';""".format(
            subscenarios.TIMEPOINT_SCENARIO_ID,
            subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    with open(os.path.join(
            inputs_directory,
            "new_shiftable_load_supply_curve_potential.tab"
    ), "w") as potentials_tab_file:
        writer = csv.writer(potentials_tab_file, delimiter="\t")

        writer.writerow([
            "project", "period",
            "min_cumulative_new_build_mwh", "max_cumulative_new_build_mwh"
        ])

        for row in min_max_builds:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    # Supply curve
    # No supply curve periods for now, so check that we have only specified
    # a single supply curve for all periods in inputs_project_new_cost

    with open(os.path.join(
            inputs_directory,
            "new_shiftable_load_supply_curve.tab"
    ), "w") as supply_curve_tab_file:
        writer = csv.writer(supply_curve_tab_file, delimiter="\t")

        writer.writerow([
            "project", "point", "slope", "intercept"
        ])

        supply_curve_count = c.execute(
            """SELECT project, COUNT(DISTINCT(supply_curve_scenario_id))
            FROM inputs_project_portfolios
            LEFT OUTER JOIN inputs_project_new_cost
            USING (project)
            WHERE project_portfolio_scenario_id = {}
            AND project_new_cost_scenario_id = {}
            AND capacity_type = 'new_shiftable_load_supply_curve'
            GROUP BY project;""".format(
                subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
                subscenarios.PROJECT_NEW_COST_SCENARIO_ID
            )
        ).fetchall()

        for proj in supply_curve_count:
            project = proj[0]
            if proj[1] > 1:
                raise ValueError("Only a single supply curve can be specified "
                                 "for project {} because no vintages have "
                                 "been implemented for "
                                 "'new_shiftable_load_supply_curve' capacity "
                                 "type.".format(project))
            else:
                supply_curve_id = c.execute(
                    """SELECT DISTINCT supply_curve_scenario_id
                    FROM inputs_project_portfolios
                    LEFT OUTER JOIN inputs_project_new_cost
                    USING (project)
                    WHERE project_portfolio_scenario_id = {}
                    AND project_new_cost_scenario_id = {}
                    AND project = 'Shift_DR';""".format(
                        subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
                        subscenarios.PROJECT_NEW_COST_SCENARIO_ID
                    )
                ).fetchone()[0]

                supply_curve = c.execute(
                    """SELECT project, supply_curve_point, supply_curve_slope, 
                    supply_curve_intercept
                    FROM inputs_project_shiftable_load_supply_curve
                    WHERE supply_curve_scenario_id = {}""".format(
                        supply_curve_id
                    )
                ).fetchall()

                for row in supply_curve:
                    writer.writerow(row)
