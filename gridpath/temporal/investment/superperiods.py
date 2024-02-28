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
Superperiods are combinations of periods over which variable and constraints
can be defined.
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
    | | :code:`SUPERPERIOD_PERIODS`                                           |
    | | *Within*: :code:`PositiveIntegers`                                    |
    |                                                                         |
    | The list of all superperiods being modeled.                             |
    +-------------------------------------------------------------------------+
    """

    # Sets
    ###########################################################################

    m.SUPERPERIOD_PERIODS = Set(dimen=2, within=PositiveIntegers * m.PERIODS)

    m.SUPERPERIODS = Set(
        within=PositiveIntegers,
        initialize=lambda mod: sorted(
            list(set([s_p for (s_p, p) in mod.SUPERPERIOD_PERIODS])),
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
    input_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "superperiods.tab",
    )

    if os.path.exists(input_file):
        data_portal.load(
            filename=input_file,
            set=m.SUPERPERIOD_PERIODS,
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

    superperiod_periods = c.execute(
        f"""
        SELECT superperiod, period
        FROM inputs_temporal_superperiods 
        WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
        AND period in (
            SELECT period
            FROM inputs_temporal_periods
            WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
        );"""
    )

    return superperiod_periods


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

    superperiod_periods = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    ).fetchall()

    if superperiod_periods:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "superperiods.tab",
            ),
            "w",
            newline="",
        ) as periods_tab_file:
            writer = csv.writer(periods_tab_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                [
                    "superperiod",
                    "period",
                ]
            )

            for row in superperiod_periods:
                writer.writerow(row)
