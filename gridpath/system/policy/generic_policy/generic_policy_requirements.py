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
Requirements for each policy and policy zone
"""

import csv
import os.path

from pyomo.environ import Set, Param, NonNegativeReals, Expression, value, Any

from gridpath.auxiliary.db_interface import directories_to_db_values
from gridpath.common_functions import create_results_df

from gridpath.system.policy.generic_policy import POLICY_ZONE_PRD_DF


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

    m.POLICIES = Set(
        within=Any,
        initialize=lambda mod: sorted(list(set([p for (p, z) in mod.POLICIES_ZONES]))),
    )

    m.POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ = Set(
        dimen=4, within=m.POLICIES_ZONES * m.BLN_TYPE_HRZS
    )

    # Target specified as a scalar
    m.policy_requirement = Param(
        m.POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ, within=NonNegativeReals, default=0
    )

    # Target specified as function of load
    m.policy_requirement_f_load_coeff = Param(
        m.POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ,
        within=NonNegativeReals,
        default=0,
    )

    # Load zones included in the function of load policy requirement
    m.POLICIES_ZONE_LOAD_ZONES = Set(dimen=3, within=m.POLICIES_ZONES * m.LOAD_ZONES)

    def policy_requirement_rule(mod, policy_name, policy_zone, bt, h):
        """
        The policy target consists of two additive components: an energy term
        and a 'percent of load x load' term, where a mapping between the policy
        zone and the load zones whose load to consider must be specified.
        Either the energy target or the percent target can be omitted (they
        default to 0). If a mapping is not specified, the
        'percent of load x load' is 0.
        """
        # If we have a map of policy zones to load zones, apply the percentage
        # target; if no map provided, the fraction_target is 0
        if mod.POLICIES_ZONE_LOAD_ZONES:
            total_bt_horizon_load_modifier_adjusted_load = sum(
                mod.LZ_Modified_Load_in_Tmp[lz, tmp]
                * mod.hrs_in_tmp[tmp]
                * mod.tmp_weight[tmp]
                for (
                    _policy_name,
                    _policy_requirement_zone,
                    lz,
                ) in mod.POLICIES_ZONE_LOAD_ZONES
                if (_policy_name, _policy_requirement_zone)
                == (policy_name, policy_zone)
                for tmp in mod.TMPS
                if tmp in mod.TMPS_BY_BLN_TYPE_HRZ[bt, h]
            )
            fraction_target = (
                mod.policy_requirement_f_load_coeff[policy_name, policy_zone, bt, h]
                * total_bt_horizon_load_modifier_adjusted_load
            )
        else:
            fraction_target = 0

        return mod.policy_requirement[policy_name, policy_zone, bt, h] + fraction_target

    m.Policy_Zone_Horizon_Requirement = Expression(
        m.POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ,
        rule=policy_requirement_rule,
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
    :param subproblem:
    :param stage:
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
            "policy_requirements.tab",
        ),
        index=m.POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ,
        param=(m.policy_requirement, m.policy_requirement_f_load_coeff),
    )

    # If we have a policy zone to load zone map input file, load it; otherwise,
    # initialize HORIZON_ENERGY_TARGET_ZONE_LOAD_ZONES as an empty list
    map_filename = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "policy_zone_load_zone_map.tab",
    )
    if os.path.exists(map_filename):
        data_portal.load(filename=map_filename, set=m.POLICIES_ZONE_LOAD_ZONES)
    else:
        data_portal.data()["POLICIES_ZONE_LOAD_ZONES"] = {None: []}


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
    policy_requirements = c.execute(
        """SELECT policy_name, policy_zone, balancing_type_horizon, horizon, 
        policy_requirement, policy_requirement_f_load_coeff
        FROM inputs_system_policy_requirements
        JOIN
        (SELECT balancing_type_horizon, horizon
        FROM inputs_temporal_horizons
        WHERE temporal_scenario_id = {}) as relevant_horizons
        USING (balancing_type_horizon, horizon)
        JOIN
        (SELECT policy_zone
        FROM inputs_geography_policy_zones
        WHERE policy_zone_scenario_id = {}) as relevant_zones
        using (policy_zone)
        WHERE policy_requirement_scenario_id = {}
        AND subproblem_id = {}
        AND stage_id = {};
        """.format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.POLICY_ZONE_SCENARIO_ID,
            subscenarios.POLICY_REQUIREMENT_SCENARIO_ID,
            subproblem,
            stage,
        )
    )

    # Get any policy zone to load zone mapping for the percent target
    c2 = conn.cursor()
    lz_mapping = c2.execute(
        """SELECT policy_name, policy_zone, load_zone
        FROM inputs_system_policy_requirements_load_zone_map
        JOIN
        (SELECT policy_name, policy_zone
        FROM inputs_geography_policy_zones
        WHERE policy_zone_scenario_id = {}) as relevant_zones
        USING (policy_name, policy_zone)
        WHERE policy_requirement_scenario_id = {}
        """.format(
            subscenarios.POLICY_ZONE_SCENARIO_ID,
            subscenarios.POLICY_REQUIREMENT_SCENARIO_ID,
        )
    )

    return policy_requirements, lz_mapping


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
    # policy_requirements = get_inputs_from_database(
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
    policy_requirements.tab file.
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

    policy_requirements, lz_mapping = get_inputs_from_database(
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
            "policy_requirements.tab",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "policy_name",
                "policy_zone",
                "balancing_type",
                "horizon",
                "policy_requirement",
                "policy_requirement_f_load_coeff",
            ]
        )

        for row in policy_requirements:
            # It's OK if targets are not specified; they default to 0
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    # Write the policy-zone to load zone map file for the policy percent
    # target if there are any mappings only
    policy_zone_lz_map_list = [row for row in lz_mapping]
    if policy_zone_lz_map_list:
        with open(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "policy_zone_load_zone_map.tab",
            ),
            "w",
            newline="",
        ) as policy_zone_lz_map_tab_file:
            writer = csv.writer(
                policy_zone_lz_map_tab_file, delimiter="\t", lineterminator="\n"
            )

            # Write header
            writer.writerow(["policy_name", "policy_zone", "load_zone"])
            for row in policy_zone_lz_map_list:
                writer.writerow(row)


def export_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
    d,
):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    results_columns = [
        "policy_requirement",
        "policy_requirement_f_load_coeff",
    ]
    data = [
        [
            p,
            z,
            bt,
            h,
            m.policy_requirement[p, z, bt, h],
            m.policy_requirement_f_load_coeff[p, z, bt, h],
        ]
        for (p, z, bt, h) in m.POLICIES_ZONE_BLN_TYPE_HRZS_WITH_REQ
    ]
    results_df = create_results_df(
        index_columns=[
            "policy_name",
            "policy_zone",
            "balancing_type_horizon",
            "horizon",
        ],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, POLICY_ZONE_PRD_DF)[c] = None
    getattr(d, POLICY_ZONE_PRD_DF).update(results_df)
