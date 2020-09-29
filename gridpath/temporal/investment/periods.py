#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Each *timepoint* in a GridPath model also belongs to a *period* (e.g. a year),
which describes when decisions to build or retire infrastructure are made. A
*period* must be specified in both capacity-expansion and production-cost
models. In a production-cost simulation context, we can use the period to
exogenously change the amount of available capacity, but the *period*
temporal unit is mostly used in the capacity-expansion approach, as it
defines when capacity decisions are made and new infrastructure becomes
available (or is retired). That information in turn feeds into the horizon-
and timepoint-level operational constraints, i.e. once a generator is build,
the optimization is allowed to operate it in subsequent periods (usually for
the duration of the generators's lifetime).
The *period* duration is assumed to be 1 year (which can be broken up into
multiple subproblems in production-cost mode). However, a period can
represent multiple years, e.g. when modeling investment decisions in 5-year
increments. A discount factor can also be applied to weight costs
differently depending on when (in which period) they are incurred.
In the future, we might support investment periods that are shorter than 1
year, e.g. monthly investment decisions.

"""

import csv
import os.path

from pyomo.environ import Set, Param, PositiveIntegers, NonNegativeReals

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.validations import write_validation_to_database, \
    get_expected_dtypes, validate_dtypes, validate_values, validate_columns

def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`PERIODS`                                                       |
    | | *Within*: :code:`PositiveIntegers`                                    |
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
    | | :code:`hours_in_full_period`                                          |
    | | *Defined over*: :code:`PERIODS`                                       |
    | | *Within*: :code:`[8760, 8766, 8784]`                                  |
    |                                                                         |
    | The number of hours in a period. This should be 1 year                  |
    | (8760-8784 hours) even if the period represents more than 1 year!       |
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
    | | :code:`hours_in_subproblem_period`                                    |
    | | *Defined over*: :code:`PERIODS`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The number of hours in each period for the current subproblem, taking   |
    | into account the timepoints in each period-subproblem, the number of    |
    | hours in each timepoint, and their associated timepoint weights.        |
    | In capacity expansion mode with one subproblem, this should simply be   |
    | equal to :code:`hours_in_full_period`. In production simulation mode    |
    | with multiple subproblems within 1 period, this number is compared to   |
    | :code: hours_in_full_period` and used to adjust the reported            |
    | "per-period" costs. For instance, when running daily subproblems the    |
    | fixed cost in each day should be only 1/365 of the annualized fixed     |
    | cost.                                                                   |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.PERIODS = Set(
        within=PositiveIntegers,
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

    m.hours_in_full_period = Param(
        m.PERIODS,
        within=[8760, 8766, 8784]
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

    m.hours_in_subproblem_period = Param(
        m.PERIODS,
        within=NonNegativeReals,
        initialize=lambda mod, p:
        sum(mod.hrs_in_tmp[tmp] * mod.tmp_weight[tmp]
            for tmp in mod.TMPS_IN_PRD[p])
    )


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    """
    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage),
                              "inputs", "periods.tab"),
        select=("period", "discount_factor", "number_years_represented",
                "hours_in_full_period"),
        index=m.PERIODS,
        param=(m.discount_factor, m.number_years_represented,
               m.hours_in_full_period)
    )

    data_portal.load(
        filename=os.path.join(scenario_directory, str(subproblem), str(stage),
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
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()
    periods = c.execute(
        """SELECT period, discount_factor, number_years_represented, 
           hours_in_full_period
           FROM inputs_temporal_periods
           WHERE temporal_scenario_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID
        )
    )

    return periods


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    periods.tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    periods = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "periods.tab"),
              "w", newline="") as periods_tab_file:
        writer = csv.writer(periods_tab_file, delimiter="\t",
                            lineterminator="\n")

        # Write header
        writer.writerow(
            ["period", "discount_factor", "number_years_represented",
             "hours_in_full_period"])

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

    # TODO: check that hours in full period is within x and y
    #  ("within" check or "validate" check in param definition returns obscure
    #  error message that isn't helpful).

    periods = get_inputs_from_database(
        subscenarios, subproblem, stage, conn
    )

    df = cursor_to_df(periods)

    # Get expected dtypes
    expected_dtypes = get_expected_dtypes(
        conn=conn,
        tables=["inputs_temporal_periods"]
    )

    # Check dtypes
    dtype_errors, error_columns = validate_dtypes(df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_temporal_periods",
        severity="High",
        errors=dtype_errors
    )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in df.columns
                       if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_temporal_periods",
        severity="Mid",
        errors=validate_values(df, valid_numeric_columns, "period", min=0)
    )

    # Check values of hours_in_full_period
    write_validation_to_database(
        conn=conn,
        scenario_id=subscenarios.SCENARIO_ID,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_temporal_periods",
        severity="Mid",
        errors=validate_columns(
            df=df,
            columns="hours_in_full_period",
            valids=[8760, 8766, 8784]
        )
    )



