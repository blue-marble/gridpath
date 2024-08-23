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
*Timepoints* are the finest resolution over which operational decisions are
made (e.g. an hour). Generator commitment and dispatch decisions are made for
each timepoint, with some constraints applied across timepoints (e.g. ramp
constraints.) Most commonly, a timepoint is an hour, but the resolution is
flexible: a timepoint could also be a 15-minute, 5-minute, 1-minute, or 4-hour
segment. Different timepoint durations can also be mixed, e.g. some can be
5-minute segments and some can be hours.

Timepoints can also be assigned weights in order to represent other
timepoints that are not modeled explicitly (e.g. use a 24-hour period per month
to represent the whole month using the number of days in that month for the
weight of each of the 24 timepoints). Note that all costs incurred at the
timepoint level are multiplied by the period-level number_years_represented
and discount_factor parameters in the objective function. At the period 
level we use annualized capacity costs (and multiply those by the number of
years in a period), so we must also annualize operational costs incurred at
the timepoint level. In other words, we must use the timepoint weights
(along with the hours-in-timepoint parameter) to calculate the
timepoint-level cost incurred over a year. The sum of
timepoint_weight*hours_in_timepoint over all timepoints in a period must
therefore equal the number of hours in a year (8760, 8766, or 8784). This
will then get multiplied by the number of years in a period and period
discount rate to get the total operational costs.

For example, if you are representing a 10-year period with a single day at a 
24-hour timepoint resolution, the timepoint weight for each of the 24 
timepoints would need to be 365. Timepoint-level costs will be multiplied by 10
automatically to account for the length of the period. If you are 
representing a 1-year period with a single day at a 24-hour resolution, 
the timepoint weight would still be 365, and timepoint-level costs will get
multiplied by 1 automatically to account for the length of the period.
If you are representing a 0.25-year period with a single day at a 24-hour
resolution, the timepoint weight would still be 365.

To support multi-stage production simulation timepoints can also be assigned a
mapping to the previous stage (e.g. timepoints 1-12 in the 5-minute real-time
stage map to timepoint 1 in the hour-ahead stage) and a flag whether the
timepoint is part of a spinup or lookahead segment.

Timepoints that are part of a spinup or lookahead segment are included in the
optimization but are generally discarded when calculating result metrics such
as annual emissions, energy, or cost.
"""

import csv
import os.path
import pandas as pd

from pyomo.environ import (
    Param,
    Set,
    NonNegativeReals,
    NonNegativeIntegers,
    PositiveIntegers,
    NonPositiveIntegers,
    Any,
)

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import (
    determine_table_subset_by_start_and_column,
    directories_to_db_values,
)
from gridpath.auxiliary.validations import write_validation_to_database


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
    | | :code:`TMPS`                                                          |
    | | *Within*: :code:`PositiveIntegers`                                    |
    |                                                                         |
    | The list of timepoints being modeled; timepoints are ordered and must   |
    | be non-negative integers.                                               |
    +-------------------------------------------------------------------------+
    | | :code:`MONTHS`                                                        |
    | | *Within*: :code:`PositiveIntegers`                                    |
    |                                                                         |
    | The list of months (1-12).                                              |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`hrs_in_tmp`                                                    |
    | | *Defined over*: :code:`TMPS`                                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The number of hours in each timepoint (can be a fraction). For example, |
    | a 15-minute timepoint will have 0.25 hours per timepoint whereas a      |
    | 4-hour timepoint will have 4 hours per timepoint. This parameter is     |
    | used by other modules to track energy (e.g. storage state of charge)    |
    | and when evaluation ramp rates. Timepoints do not need to have the      |
    | same  :code:`hrs_in_tmp` value, i.e. one of them can represent a        |
    | 5-minute segment and another a 24-hour segment.                         |
    +-------------------------------------------------------------------------+
    | | :code:`tmp_weight`                                                    |
    | | *Defined over*: :code:`TMPS`                                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | This parameter accounts for the number of other similar 'timepoints'    |
    | that are not explicitly included in the optimization, but that the      |
    | included timepoint represents in the objective function. For example,   |
    | we could include one day from the month to represent the entire month,  |
    | in which case the timepoint_weight for each timepoint on that day will  |
    | be the number of the days in the respective month.                      |
    +-------------------------------------------------------------------------+
    | | :code:`prev_stage_tmp_map`                                            |
    | | *Defined over*: :code:`TMPS`                                          |
    | | *Within*: :code:`NonNegativeIntegers`                                 |
    |                                                                         |
    | The associated timepoint in the previous stage (if there is any) for    |
    | each timepoint. This is used to pass commitment decisions from one      |
    | stage to the next. E.g. if the real-time stage has 15-minute timepoints |
    | , and the hour-ahead stage had hourly timepoints, all 4 real-time       |
    | timepoints within an hour will point to the same hourly timepoint in    |
    | the previous hour-ahead stage to its commitment decision.               |
    +-------------------------------------------------------------------------+
    | | :code:`month`                                                         |
    | | *Defined over*: :code:`TMPS`                                          |
    | | *Within*: :code:`MONTHS`                                              |
    |                                                                         |
    | The month that each timepoint belongs to. This is used to determine     |
    | fuel costs during that timepoint, among others.                         |
    +-------------------------------------------------------------------------+

    .. TODO:: varying timepoint durations haven't been extensiveliy tested

    """

    # Sets
    ###########################################################################

    m.TMPS = Set(within=PositiveIntegers, ordered=True)

    m.MONTHS = Set(within=PositiveIntegers, initialize=list(range(1, 12 + 1)))

    # These are the timepoints from the previous subproblem for which we'll
    # have parameters to constrain the current subproblem
    m.LINKED_TMPS = Set(within=NonPositiveIntegers, ordered=True)

    # Required Params
    ###########################################################################

    m.hrs_in_tmp = Param(m.TMPS, within=NonNegativeReals)

    m.tmp_weight = Param(m.TMPS, within=NonNegativeReals)

    m.prev_stage_tmp_map = Param(m.TMPS, within=NonNegativeIntegers)

    m.month = Param(m.TMPS, within=m.MONTHS)

    m.day_of_month = Param(m.TMPS, within=NonNegativeIntegers, default=0)

    m.hour_of_day = Param(m.TMPS, within=NonNegativeIntegers, default=0)

    # Optional Params
    ###########################################################################

    m.hrs_in_linked_tmp = Param(m.LINKED_TMPS, within=NonNegativeReals)

    m.furthest_linked_tmp = Param(within=NonPositiveIntegers)


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
    """

    :param m: Pyomo AbstractModel
    :param d: class
    :param data_portal: Pyomo DataPortal
    :param scenario_directory: str
    :param subproblem: str
    :param stage: str
    :return:
    """
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
        index=m.TMPS,
        param=(
            m.tmp_weight,
            m.hrs_in_tmp,
            m.prev_stage_tmp_map,
            m.month,
            m.day_of_month,
            m.hour_of_day,
        ),
        select=(
            "timepoint",
            "timepoint_weight",
            "number_of_hours_in_timepoint",
            "previous_stage_timepoint_map",
            "month",
            "day_of_month",
            "hour_of_day",
        ),
    )

    # Load in any timepoints to link to the next subproblem and linked
    # timepoints from a previous subproblem
    # Try to load in the map CSV
    try:
        map_df = pd.read_csv(
            os.path.join(scenario_directory, "linked_subproblems_map.csv"), sep=","
        )
        # Get the linked timepoints for the current subproblem and stage
        linked_tmps_df = map_df.loc[
            (map_df["subproblem_to_link"] == int(subproblem))
            & (map_df["stage"] == (1 if stage == "" else int(stage)))
        ]
        linked_tmps = linked_tmps_df["linked_timepoint"].tolist()
        # Load in the data
        data_portal.data()["LINKED_TMPS"] = {None: linked_tmps}
        hrs_in_linked_tmp_dict = dict(
            zip(linked_tmps, linked_tmps_df["number_of_hours_in_timepoint"])
        )
        data_portal.data()["hrs_in_linked_tmp"] = hrs_in_linked_tmp_dict
        if linked_tmps:
            data_portal.data()["furthest_linked_tmp"] = {None: min(linked_tmps)}

    # If the file is not there, there were no linked subproblems and the
    # file was not written, so load in empty components
    except FileNotFoundError:
        data_portal.data()["LINKED_TMPS"] = {None: []}
        data_portal.data()["hrs_in_linked_tmp"] = {}


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
    timepoints = c.execute(
        """SELECT timepoint, period, timepoint_weight,
           number_of_hours_in_timepoint, previous_stage_timepoint_map, month, 
           day_of_month, hour_of_day
           FROM inputs_temporal
           WHERE temporal_scenario_id = {}
           AND subproblem_id = {}
           AND stage_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID, subproblem, stage
        )
    )

    return timepoints


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
    timepoints.tab file.
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

    timepoints = get_inputs_from_database(
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
            "timepoints.tab",
        ),
        "w",
        newline="",
    ) as timepoints_tab_file:
        writer = csv.writer(timepoints_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "timepoint",
                "period",
                "timepoint_weight",
                "number_of_hours_in_timepoint",
                "previous_stage_timepoint_map",
                "month",
                "day_of_month",
                "hour_of_day",
            ]
        )

        # Write timepoints
        for row in timepoints:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


def process_results(db, c, scenario_id, subscenarios, quiet):
    """

    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    # Check if there are any spinup or lookahead timepoints
    spinup_or_lookahead_sql = f"""
    SELECT spinup_or_lookahead
    FROM inputs_temporal
    WHERE spinup_or_lookahead = 1
    AND temporal_scenario_id = (
        SELECT temporal_scenario_id
        FROM scenarios
        WHERE scenario_id = {scenario_id})
    """

    spinup_or_lookahead = c.execute(spinup_or_lookahead_sql).fetchall()
    if spinup_or_lookahead:
        if not quiet:
            print("add spinup_or_lookahead flag")

        # Update tables with spinup_or_lookahead_flag
        tables_to_update = determine_table_subset_by_start_and_column(
            conn=db, tbl_start="results_", cols=["timepoint", "spinup_or_lookahead"]
        )

        for tbl in tables_to_update:
            if not quiet:
                print("... {}".format(tbl))
            sql = f"""
                UPDATE {tbl}
                SET spinup_or_lookahead = (
                SELECT spinup_or_lookahead
                FROM inputs_temporal
                WHERE temporal_scenario_id = (
                    SELECT temporal_scenario_id 
                    FROM scenarios 
                    WHERE scenario_id = {scenario_id}
                    )
                AND {tbl}.subproblem_id = 
                inputs_temporal.subproblem_id
                AND {tbl}.stage_id = inputs_temporal.stage_id
                AND {tbl}.timepoint = inputs_temporal.timepoint
                )
                WHERE scenario_id = {scenario_id};
                """.format(
                tbl, tbl, tbl, tbl
            )

            spin_on_database_lock(conn=db, cursor=c, sql=sql, data=(), many=False)


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
    # timepoints = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)
    # validate timepoint inputs

    # TODO: could gather the timepoints from the previous stage (if any) and
    #  check that the previous stage timepoint map inputs are valid

    c = conn.cursor()

    validation_data = c.execute(
        """
        SELECT period, sum(number_of_hours_in_timepoint*timepoint_weight)
           as hours_in_period_timepoints
           FROM inputs_temporal
           WHERE temporal_scenario_id = {}
           AND spinup_or_lookahead = 0
           AND stage_id = {}
           GROUP BY period;""".format(
            subscenarios.TEMPORAL_SCENARIO_ID, stage
        )
    ).fetchall()

    for row in validation_data:
        period = row[0]
        hours_in_period_timepoints = row[1]

        if hours_in_period_timepoints not in [8760, 8766, 8784]:
            msg = """
            Check timepoint parameters for period {}. Your timepoint 
            parameters currently sum up to {}. In each period,  regardless 
            of period param values, the total number of hours in timepoints 
            adjusted for timepoint weight and duration and excluding spinup 
            and lookahead timepoints should be the number of hours in a year 
            (8760, 8766, or 8784). This is to ensure consistent weighting of 
            timepoint-level and period-level costs. 
            """.format(
                str(period), str(hours_in_period_timepoints)
            )

            # Check values of hours_in_period_timepoints
            write_validation_to_database(
                conn=conn,
                scenario_id=scenario_id,
                weather_iteration=weather_iteration,
                hydro_iteration=hydro_iteration,
                availability_iteration=availability_iteration,
                subproblem_id=subproblem,
                stage_id=stage,
                gridpath_module=__name__,
                db_table="inputs_temporal",
                severity="High",
                errors=[msg],
            )
