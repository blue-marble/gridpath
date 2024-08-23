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
Zones between which capacity transfers can occur. Please note that each direction
must be defined separately, i.e., if PRM_Zone_1 can transfer capacity to PRM_Zone_2
and PRM_Zone_2 can transfer capacity to PRM_Zone_1,
the PRM_ZONES_CAPACITY_TRANSFER_ZONES set must include both (PRM_Zone_1, PRM_Zone_2)
and (PRM_Zone_2, PRM_Zone_1).

The allow_elcc_surface_transfers param defaults to 0 (only simple capacity can be
transferred by default, as transfers of capacity from the ELCC surfaces is likely to
result in inaccurate results).
"""

import csv
import os.path
from pyomo.environ import Set, Param, Boolean

from gridpath.auxiliary.db_interface import directories_to_db_values


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

    :param m:
    :param d:
    :return:
    """

    m.PRM_ZONES_CAPACITY_TRANSFER_ZONES = Set(dimen=2, within=m.PRM_ZONES * m.PRM_ZONES)

    m.allow_elcc_surface_transfers = Param(
        m.PRM_ZONES_CAPACITY_TRANSFER_ZONES, within=Boolean, default=0
    )


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

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param stage:
    :param stage:
    :return:
    """
    prm_zone_transfers_tab_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "prm_capacity_transfer_zone_links.tab",
    )
    if os.path.exists(prm_zone_transfers_tab_file):
        data_portal.load(
            filename=prm_zone_transfers_tab_file,
            index=m.PRM_ZONES_CAPACITY_TRANSFER_ZONES,
            param=m.allow_elcc_surface_transfers,
        )


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
    prm_zone_transfers = c.execute(
        """SELECT prm_zone, prm_capacity_transfer_zone, allow_elcc_surface_transfers
        FROM inputs_transmission_prm_capacity_transfers
        WHERE prm_capacity_transfer_scenario_id = {prm_transfer}
        AND prm_zone IN
        (SELECT prm_zone FROM inputs_geography_prm_zones
        WHERE prm_zone_scenario_id = {prm_zone})
        AND prm_capacity_transfer_zone IN
        (SELECT prm_zone FROM inputs_geography_prm_zones
        WHERE prm_zone_scenario_id = {prm_zone});""".format(
            prm_transfer=subscenarios.PRM_CAPACITY_TRANSFER_SCENARIO_ID,
            prm_zone=subscenarios.PRM_ZONE_SCENARIO_ID,
        )
    )

    return prm_zone_transfers


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
    pass
    # Validation to be added
    # prm_zone_transfers = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)


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
    prm_zones.tab file.
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

    prm_zone_transfers = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    prm_zone_transfers = prm_zone_transfers.fetchall()
    if prm_zone_transfers:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "prm_capacity_transfer_zone_links.tab",
            ),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                [
                    "prm_zone",
                    "prm_capacity_transfer_zones",
                    "allow_elcc_surface_transfers",
                ]
            )

            for row in prm_zone_transfers:
                replace_nulls = ["." if i is None else i for i in row]
                writer.writerow(replace_nulls)
