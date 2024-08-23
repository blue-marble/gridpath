# Copyright 2016-2023 Blue Marble Analytics LLC.
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
You must specify *period* duration via the *period_start_year* and
*period_end_year* parameters (the duration is calculated within GridPath
based on those values). Note that the start year is inclusive and the end year
is exclusive. Capacity can either exist or not for the entire duration of a
period. A discount factor can also be applied to weight costs differently
depending on when (in which period) they are incurred.

.. warning:: Support for investment periods that are shorter than 1 year,
    e.g. monthly investment decisions, is largely untested, so be extra careful
    if attempting to use this functionality.

"""

import csv
import os.path

from pyomo.environ import Set, Param, PositiveIntegers, NonNegativeReals

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    get_expected_dtypes,
    validate_dtypes,
    validate_values,
)


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
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
    | | :code:`hours_in_period_timepoints`                                    |
    | | *Defined over*: :code:`PERIODS`                                       |
    | | *Within*: :code:`[8760, 8766, 8784]`                                  |
    |                                                                         |
    | The number of hours in the timepoints representing a period (across     |
    | all scenario subproblems, within a stage, excluding spinup/lookahead.   |
    | Note that to ensure consistent weighting of period-level and            |
    | timepoint-level costs, this derived parameter must have a value of the  |
    | number of hours in a year. This is automatically calculated from the    |
    | temporal_scenario_id  structure if using the database and an error will |
    | be thrown if the timepoint param inputs do not summ up to one of the    |
    | allowed values. Within GridPath, this parameter is used to adjust the   |
    | capacity-related costs incurred within a subproblem if a subproblem is  |
    | shorter than the period.                                                |
    +-------------------------------------------------------------------------+
    | | :code:`period_start_year`                                             |
    | | *Defined over*: :code:`PERIODS`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The first 'year' in a period, e.g. if this is 2030, the period is       |
    | assumed to begin at 2030-01-01 00:00. Note that non-integer values      |
    | are allowed, so you could have 2030.25 for a period that starts  on     |
    | 2030-04-01, for example. Having periods shorter (or longer) than a      |
    | year is largely untested, so be extra careful if attempting to use      |
    | this functionality, as it could be buggy.                               |
    +-------------------------------------------------------------------------+
    | | :code:`period_end_year`                                               |
    | | *Defined over*: :code:`PERIODS`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The last 'year' in a period. This is exclusive following typical        |
    | Python convention, i.e. if it is 2040, the period is assumed to go      |
    | through 2039-12-01 23:59. Note that non-integer values are allowed, so  |
    | you could have 2030.50 for a period that goes through 2030-06-30, for   |
    | example. Having periods shorter (or longer) than a year is largely      |
    | untested, so be extra careful if attempting to use this functionality,  |
    | as it could be buggy.                                                   |
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
    | | :code:`number_years_represented`                                      |
    | | *Defined over*: :code:`PERIODS`                                       |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Accounts for the number of years that the periods is meant to           |
    | represent. Investment cost inputs in GridPath are annualized, so they   |
    | are multiplied by this parameter in the objective function. The         |
    | parameter is derived based on the period_start_year and period_end_year |
    | parameters.                                                             |
    +-------------------------------------------------------------------------+
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
    | equal to :code:`hours_in_period_timepoints`. In production simulation   |
    | mode with multiple subproblems within 1 period, this number is compared |
    | to :code:`hours_in_period_timepoints` and used to adjust the reported   |
    | "per-period" costs. For instance, when running daily subproblems the    |
    | fixed cost in each day should be only 1/365 of the annualized fixed     |
    | cost.                                                                   |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.PERIODS = Set(within=PositiveIntegers, ordered=True)

    # Required Input Params
    ###########################################################################

    m.discount_factor = Param(m.PERIODS, within=NonNegativeReals)

    m.hours_in_period_timepoints = Param(m.PERIODS, within=NonNegativeReals)

    m.period_start_year = Param(m.PERIODS, within=NonNegativeReals)

    m.period_end_year = Param(m.PERIODS, within=NonNegativeReals)

    m.period = Param(m.TMPS, within=m.PERIODS)

    # Derived Sets
    ###########################################################################

    m.TMPS_IN_PRD = Set(
        m.PERIODS,
        initialize=lambda mod, p: sorted(
            list(set(tmp for tmp in mod.TMPS if mod.period[tmp] == p)),
        ),
    )

    m.NOT_FIRST_PRDS = Set(
        within=m.PERIODS, initialize=lambda mod: list(mod.PERIODS)[1:]
    )

    # Derived Input Params
    ###########################################################################

    m.number_years_represented = Param(
        m.PERIODS,
        within=NonNegativeReals,
        initialize=lambda mod, p: mod.period_end_year[p] - mod.period_start_year[p],
    )

    m.first_period = Param(
        within=m.PERIODS, initialize=lambda mod: list(mod.PERIODS)[0]
    )

    m.prev_period = Param(
        m.NOT_FIRST_PRDS,
        within=m.PERIODS,
        initialize=lambda mod, p: list(mod.PERIODS)[list(mod.PERIODS).index(p) - 1],
    )

    m.hours_in_subproblem_period = Param(
        m.PERIODS,
        within=NonNegativeReals,
        initialize=lambda mod, p: sum(
            mod.hrs_in_tmp[tmp] * mod.tmp_weight[tmp] for tmp in mod.TMPS_IN_PRD[p]
        ),
    )


# Input-Output
###############################################################################


def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """ """
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "periods.tab",
        ),
        select=(
            "period",
            "discount_factor",
            "hours_in_period_timepoints",
            "period_start_year",
            "period_end_year",
        ),
        index=m.PERIODS,
        param=(
            m.discount_factor,
            m.hours_in_period_timepoints,
            m.period_start_year,
            m.period_end_year,
        ),
    )

    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "timepoints.tab",
        ),
        select=("timepoint", "period"),
        index=m.TMPS,
        param=m.period,
    )


# Database
###############################################################################


def get_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    c = conn.cursor()

    # Note that we calculate the hours_in_period_timepoints here by summing up the
    # number of hours in a period (within a stage and excluding
    # spinup/lookahead) across all subproblems in the temporal_scenario_id:
    periods = c.execute(
        """SELECT period, discount_factor, 
           period_start_year, period_end_year, hours_in_period_timepoints
           FROM
           (SELECT period, discount_factor,
           period_start_year, period_end_year
           FROM inputs_temporal_periods
           WHERE temporal_scenario_id = {}) as main_period_tbl
           JOIN
           (SELECT period, sum(number_of_hours_in_timepoint*timepoint_weight) 
           as hours_in_period_timepoints
           FROM inputs_temporal
           WHERE temporal_scenario_id = {}
           AND spinup_or_lookahead = 0
           AND stage_id = {}
           GROUP BY period) as hours_in_period_timepoints_tbl
           USING (period);""".format(
            subscenarios.TEMPORAL_SCENARIO_ID, subscenarios.TEMPORAL_SCENARIO_ID, stage
        )
    )

    return periods


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
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

    (
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
    ) = directories_to_db_values(
        weather_iteration, hydro_iteration, availability_iteration, subproblem, stage
    )

    periods = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "periods.tab",
        ),
        "w",
        newline="",
    ) as periods_tab_file:
        writer = csv.writer(periods_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "period",
                "discount_factor",
                "period_start_year",
                "period_end_year",
                "hours_in_period_timepoints",
            ]
        )

        for row in periods:
            writer.writerow(row)


# Validation
###############################################################################


def validate_inputs(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
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
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )

    df = cursor_to_df(periods)

    # Get expected dtypes
    expected_dtypes = get_expected_dtypes(conn=conn, tables=["inputs_temporal_periods"])
    # Hard-code data type for hours_in_period_timepoints
    expected_dtypes["hours_in_period_timepoints"] = "numeric"

    # Check dtypes
    dtype_errors, error_columns = validate_dtypes(df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_temporal_periods",
        severity="High",
        errors=dtype_errors,
    )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in df.columns if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_temporal_periods",
        severity="Mid",
        errors=validate_values(df, valid_numeric_columns, "period", min=0),
    )
