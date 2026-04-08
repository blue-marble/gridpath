# Copyright 2016-2024 Blue Marble Analytics LLC.
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
Water links for modeling hydro water systems. Water nodes are derived based
on the link definition.
"""

import csv
import os.path
from pyomo.environ import (
    Set,
    Param,
    NonNegativeReals,
    Any,
    Boolean,
)

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

    The module adds the *WATER_LINKS* set to the model formulation.
    WATER_NODES are determined based on the start and end points of the
    WATER_LINKS. Each water link is associated with a flow transport time
    water_link_flow_transport_time_hours, which defaults to 0.

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`WATER_LINKS`                                                   |
    |                                                                         |
    | Links on which water flows between water nodes.                         |
    +-------------------------------------------------------------------------+
    | | :code:`WATER_NODES`                                                   |
    |                                                                         |
    | Derived from end points of WATER_LINKS.                                 |
    +-------------------------------------------------------------------------+

    +-------------------------------------------------------------------------+
    | Params                                                                  |
    +=========================================================================+
    | | :code:`water_node_from`                                               |
    | | *Defined over*: :code:`WATER_LINKS`                                   |
    | | *Within*: :code:`Any`                                                 |
    |                                                                         |
    | Starting node of link (water flows from this node).                     |
    +-------------------------------------------------------------------------+
    | | :code:`water_node_to`                                                 |
    | | *Defined over*: :code:`WATER_LINKS`                                   |
    | | *Within*: :code:`Any`                                                 |
    |                                                                         |
    | Ending node of link (water to from this node).                          |
    +-------------------------------------------------------------------------+
    | | :code:`water_link_flow_transport_time_hours`                          |
    | | *Defined over*: :code:`WATER_LINKS`                                   |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | Water transport time (in hours) across the link.                        |
    +-------------------------------------------------------------------------+
    """

    m.WATER_LINKS = Set()
    m.water_node_from = Param(m.WATER_LINKS, within=Any)
    m.water_node_to = Param(m.WATER_LINKS, within=Any)
    m.water_link_flow_transport_time_hours = Param(
        m.WATER_LINKS, within=NonNegativeReals, default=0
    )

    m.WATER_NODES = Set(
        initialize=lambda mod: list(
            sorted(
                set(
                    [mod.water_node_from[wl] for wl in mod.WATER_LINKS]
                    + [mod.water_node_to[wl] for wl in mod.WATER_LINKS]
                )
            )
        )
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
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "water_network.tab",
        ),
        index=m.WATER_LINKS,
        param=(
            m.water_node_from,
            m.water_node_to,
            m.water_link_flow_transport_time_hours,
        ),
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
    water_links = c.execute(f"""SELECT water_link, water_node_from, water_node_to,
        water_link_flow_transport_time_hours
        FROM inputs_geography_water_network
        WHERE water_network_scenario_id = {subscenarios.WATER_NETWORK_SCENARIO_ID};
        """)

    return water_links


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
    # carbon_cap_zone = get_inputs_from_database(
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
    water_network.tab file.
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

    water_network = get_inputs_from_database(
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
            "water_network.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "water_link",
                "water_node_from",
                "water_node_to",
                "water_link_flow_transport_time_hours",
            ]
        )

        for row in water_network:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)
