#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
The **gridpath.temporal.investment.periods** module describes the temporal
unit over which investment and retirement variables are defined. The period
setup determines what infrastructure is available in each timepoint.
"""

import csv
import os.path

from pyomo.environ import Set, Param, NonNegativeReals, NonNegativeIntegers


def add_model_components(m, d):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the dynamic inputs class object; not used here

    The module adds the *PERIODS* set to the model formulation.

    Periods must be non-negative integers and the set is ordered.

    We will designate the *PERIODS* set with :math:`P` and the timepoints
    index will be :math:`p`.

    Each period is associated with a *discount_factor* parameter and a
    *number_years_represented* parameter.

    The *discount_factor* parameter determines the relative objective
    function weight of investment and operational decisions made in each
    period (i.e. future costs can be weighted less).

    The *number_years_represented* parameter accounts for the number of
    years that the periods is meant to represent. Investment cost inputs in
    GridPath are annualized, so they are multiplied by this parameter in the
    objective function.

    This module organizes timepoints into periods. Each timepoint is
    assigned a *period* parameter where :math:`period_t\in H`, i.e. each
    timepoint occurs within a specific period.

    We also derive the following set and parameters:

    We use :math:`period_t` to create the indexed set
    *TIMEPOINTS_IN_PERIOD* (:math:`\{T_p\}_{p\in P}`; :math:`T_p\subset T`)
    that allows us to determine the subsets of timepoints :math:`T_p` that
    occur in each period :math:`p`.

    Finally, we determine which period is the first period
    (:math:`first\_period\in P`), which periods are in the set
    NOT_FIRST_PERIODS, i.e. the period(s) (if any) that is/are not the first
    (:math:`N\_F\_P\subset P`), and which is the previous period for each
    period (:math:`previous\_period_{n\_f\_p}\in P`).

    """
    m.PERIODS = Set(within=NonNegativeIntegers, ordered=True)
    m.discount_factor = Param(m.PERIODS, within=NonNegativeReals)

    # TODO: think this through and figure out appropriate documentation
    #  wording; can we have periods that are smaller than an year,
    #  considering how costs are defined ($/kW-yr)?
    m.number_years_represented = Param(m.PERIODS, within=NonNegativeReals)

    m.period = Param(m.TIMEPOINTS, within=m.PERIODS)

    m.TIMEPOINTS_IN_PERIOD = \
        Set(m.PERIODS,
            initialize=lambda mod, p:
            set(tmp for tmp in mod.TIMEPOINTS if mod.period[tmp] == p))

    # Figure out which one is the first period; the PERIODS set is ordered
    # so we can just use the list index
    m.first_period = Param(within=m.PERIODS,
                           initialize=lambda mod: list(mod.PERIODS)[0])
    m.NOT_FIRST_PERIODS = Set(within=m.PERIODS,
                              initialize=lambda mod: list(mod.PERIODS)[1:])
    # Figure out the previous period for each period other than the first
    # period, which doesn't have a previous period
    m.previous_period = Param(m.NOT_FIRST_PERIODS,
                              initialize=lambda mod, p:
                              list(mod.PERIODS)[list(mod.PERIODS).index(p)-1]
                              )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs", "periods.tab"),
                     select=("PERIODS", "discount_factor",
                             "number_years_represented"),
                     index=m.PERIODS,
                     param=(m.discount_factor, m.number_years_represented)
                     )

    data_portal.load(filename=os.path.join(scenario_directory, subproblem, stage,
                                           "inputs", "timepoints.tab"),
                     select=("TIMEPOINTS","period"),
                     index=m.TIMEPOINTS,
                     param=m.period
                     )


def get_inputs_from_database(subscenarios, subproblem, stage, c):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    periods = c.execute(
        """SELECT period, discount_factor, number_years_represented
           FROM inputs_temporal_periods
           WHERE temporal_scenario_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID
        )
    ).fetchall()

    return periods


def validate_inputs(subscenarios, subproblem, stage, c):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """
    pass
    # Validation to be added
    # periods = get_inputs_from_database(
    #     subscenarios, subproblem, stage, c)


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, c):
    """
    Get inputs from database and write out the model input
    periods.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param c: database cursor
    :return:
    """

    periods = get_inputs_from_database(
        subscenarios, subproblem, stage, c)

    with open(os.path.join(inputs_directory, "periods.tab"), "w") as \
            periods_tab_file:
        writer = csv.writer(periods_tab_file, delimiter="\t")

        # Write header
        writer.writerow(
            ["PERIODS", "discount_factor", "number_years_represented"])

        for row in periods:
            writer.writerow(row)
