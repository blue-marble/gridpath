#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Each *timepoint* in a GridPath model also belongs to a *period* (e.g. a year),
which describes when decisions to build or retire infrastructure are made. A
*period* must be specified in both capacity-expansion and production-cost
model. In a production-cost simulation context, we can use the period to
exogenously change the amount of available capacity, but the *period*
temporal unit is mostly used in the capacity-expansion approach, as it
defines when capacity decisions are made and new infrastructure becomes
available (or is retired). That information in turn feeds into the horizon-
and timepoint-level operational constraints, i.e. once a generator is build,
the optimization is allowed to operate it in subsequent periods (usually for
the duration of the generators's lifetime). The *period* duration is
flexible: e.g. capacity decisions can be made every month, every year, every
10 years, etc. A discount factor can also be applied to weight costs
differently depending on when they are incurred.
"""

import csv
import os.path

from pyomo.environ import Set, Param, NonNegativeReals, NonNegativeIntegers


def add_model_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`PERIODS`                                                       |
    | | *Within*: :code:`NonNegativeIntegers`                                 |
    |                                                                         |
    | The list of all periods being modeled. Periods must be non-negative     |
    | integers and the set is ordered.                                        |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Derived Sets                                                            |
    +=========================================================================+
    | | :code:`TMPS_IN_PRD`                                                   |
    | | *Defined over*: :code:`PERIODS`                                       |
    |                                                                         |
    | Indexed set that describes the timepoints that occur in each period.    |
    +-------------------------------------------------------------------------+
    | | :code:`NOT_FIRST_PRDS`                                                |
    | | *Within*: :code:`PERIODS`                                             |
    |                                                                         |
    | The list of periods excluding the first period. Relies on periods being |
    | ordered.                                                                |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`discount_factor`                                               |
    | | *Defined over*: :code:`PERIODS`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Determines the relative objective function weight of investment and     |
    | operational decisions made in each period (i.e. future costs can be     |
    | weighted less).                                                         |
    +-------------------------------------------------------------------------+
    | | :code:`number_years_represented`                                      |
    | | *Defined over*: :code:`PERIODS`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Accounts for the number of years that the periods is meant to           |
    | represent. Investment cost inputs in GridPath are annualized, so they   |
    | are multiplied by this parameter in the objective function.             |
    +-------------------------------------------------------------------------+
    | | :code:`period`                                                        |
    | | *Defined over*: :code:`TMPS`                                          |
    | | *Within*: :code:`PERIODS`                                             |
    |                                                                         |
    | Specifies the associated period for each timepoint.                     |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Derived Input Params                                                    |
    +=========================================================================+
    | | :code:`first_period`                                                  |
    | | *Within*: :code:`PERIODS`                                             |
    |                                                                         |
    | The first period in the model. Relies on the PERIODS set being ordered. |
    +-------------------------------------------------------------------------+
    | | :code:`prev_period`                                                   |
    | | *Defined over*: :code:`NOT_FIRST_PRDS`                                |
    | | *Within*: :code:`PERIODS`                                             |
    |                                                                         |
    | Determines the previous period for each period other than the first     |
    | period, which doesn't have a previous period.                           |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.PERIODS = Set(
        within=NonNegativeIntegers,
        ordered=True
    )

    # Required Input Params
    ###########################################################################

    m.discount_factor = Param(
        m.PERIODS,
        within=NonNegativeReals
    )

    m.number_years_represented = Param(
        m.PERIODS,
        within=NonNegativeReals
    )

    # TODO: think numbers_years_represent through and figure out appropriate
    #  documentation wording; can we have periods that are smaller than an
    #  year, considering how costs are defined ($/MW-yr)?

    m.period = Param(
        m.TMPS,
        within=m.PERIODS
    )

    # Derived Sets
    ###########################################################################

    m.TMPS_IN_PRD = Set(
        m.PERIODS,
        initialize=lambda mod, p:
        set(tmp for tmp in mod.TMPS if mod.period[tmp] == p)
    )

    m.NOT_FIRST_PRDS = Set(
        within=m.PERIODS,
        initialize=lambda mod: list(mod.PERIODS)[1:]
    )

    # Derived Input Params
    ###########################################################################

    m.first_period = Param(
        within=m.PERIODS,
        initialize=lambda mod: list(mod.PERIODS)[0]
    )

    m.prev_period = Param(
        m.NOT_FIRST_PRDS,
        within=m.PERIODS,
        initialize=lambda mod, p:
        list(mod.PERIODS)[list(mod.PERIODS).index(p)-1]
    )


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage,
                              "inputs", "periods.tab"),
        select=("period", "discount_factor", "number_years_represented"),
        index=m.PERIODS,
        param=(m.discount_factor, m.number_years_represented)
    )

    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage,
                              "inputs", "timepoints.tab"),
        select=("timepoint", "period"),
        index=m.TMPS,
        param=m.period
    )


# Database
###############################################################################

def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    periods = c.execute(
        """SELECT period, discount_factor, number_years_represented
           FROM inputs_temporal_periods
           WHERE temporal_scenario_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID
        )
    )

    return periods


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    periods.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    periods = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory, "periods.tab"),
              "w", newline="") as periods_tab_file:
        writer = csv.writer(periods_tab_file, delimiter="\t",
                            lineterminator="\n")

        # Write header
        writer.writerow(
            ["period", "discount_factor", "number_years_represented"])

        for row in periods:
            writer.writerow(row)


# Validation
###############################################################################

def validate_inputs(subscenarios, subproblem, stage, conn):
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
    # periods = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

