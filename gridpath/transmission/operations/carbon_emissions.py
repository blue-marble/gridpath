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
Get carbon emissions on each 'carbonaceous' transmission line.

Carbon emissions are based on power sent on the transmission line.
"""


import csv
import os.path
from pyomo.environ import (
    Param,
    Set,
    Var,
    Constraint,
    Expression,
    NonNegativeReals,
    value,
)

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import subset_init_by_set_membership
from gridpath.auxiliary.db_interface import (
    setup_results_import,
    directories_to_db_values,
)
from gridpath.auxiliary.dynamic_components import carbon_cap_balance_emission_components
from gridpath.common_functions import create_results_df
from gridpath.transmission import TX_TIMEPOINT_DF


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
    | | :code:`CRB_TX_LINES`                                                  |
    |                                                                         |
    | The set of carbonaceous transmission lines, i.e. transmission lines     |
    | whose imports or exports should be accounted for in the carbon cap      |
    | calculations.                                                           |
    +-------------------------------------------------------------------------+
    | | :code:`CRB_TX_OPR_TMPS`                                               |
    |                                                                         |
    | Two-dimensional set of carbonaceous transmission lines and their        |
    | operational timepoints.                                                 |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`tx_carbon_cap_zone`                                            |
    | | *Defined over*: :code:`CRB_TX_LINES`                                  |
    | | *Within*: :code:`CARBON_CAP_ZONES`                                    |
    |                                                                         |
    | The transmission line's carbon cap zone. The imports or exports for     |
    | that transmission line will count towards that zone's carbon cap.       |
    +-------------------------------------------------------------------------+
    | | :code:`carbon_cap_zone_import_direction`                              |
    | | *Defined over*: :code:`CRB_TX_LINES`                                  |
    | | *Within*: :code:`["positive", "negative"]`                            |
    |                                                                         |
    | The transmission line's import direction: "positive" ("negative")       |
    | indicates positive (negative) line flows are flows into the carbon cap  |
    | zone while negative (positive) line flows are flows out of the carbon   |
    | zone.                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`tx_co2_intensity_tons_per_mwh`                                 |
    | | *Defined over*: :code:`CRB_TX_LINES`                                  |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The transmission line's CO2-intensity in metric tonnes per MWh. This    |
    | param indicates how much emissions are added towards the carbon cap for |
    | every MWh transmitted into the carbon cap zone.                         |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Derived Sets                                                            |
    +=========================================================================+
    | | :code:`CRB_TX_LINES_BY_CARBON_CAP_ZONE`                               |
    | | *Defined over*: :code:`CARBON_CAP_ZONES`                              |
    | | *Within*: :code:`CRB_TX_LINES`                                        |
    |                                                                         |
    | Indexed set that describes the carbonaceous transmission lines          |
    | associated with each carbon cap zone.                                   |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`Import_Carbon_Emissions_Tons`                                  |
    | | *Defined over*: :code:`CRB_TX_OPR_TMPS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Describes the amount of imported carbon emissions for each              |
    | carbonaceous transmission in each operational timepoint.                |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`Carbon_Emissions_Imports_Constraint`                           |
    | | *Enforced over*: :code:`CRB_TX_OPR_TMPS`                              |
    |                                                                         |
    | Constrains the amount of imported carbon emissions for each             |
    | carbonaceous transmission in each operational timepoint, based on the   |
    | :code:`tx_co2_intensity_tons_per_mwh` param and the transmitted power.  |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.CRB_TX_LINES = Set(within=m.TX_LINES)

    m.CRB_TX_OPR_TMPS = Set(
        within=m.TX_OPR_TMPS,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod, superset="TX_OPR_TMPS", index=0, membership_set=mod.CRB_TX_LINES
        ),
    )

    # Required Input Params
    ###########################################################################

    m.tx_carbon_cap_zone = Param(m.CRB_TX_LINES, within=m.CARBON_CAP_ZONES)

    m.carbon_cap_zone_import_direction = Param(
        m.CRB_TX_LINES, within=["positive", "negative"]
    )

    m.tx_co2_intensity_tons_per_mwh = Param(m.CRB_TX_LINES, within=NonNegativeReals)

    # Derived Sets
    ###########################################################################

    m.CRB_TX_LINES_BY_CARBON_CAP_ZONE = Set(
        m.CARBON_CAP_ZONES,
        within=m.CRB_TX_LINES,
        initialize=lambda mod, co2_z: [
            tx for tx in mod.CRB_TX_LINES if mod.tx_carbon_cap_zone[tx] == co2_z
        ],
    )

    # Variables
    ###########################################################################

    m.Import_Carbon_Emissions_Tons = Var(m.CRB_TX_OPR_TMPS, within=NonNegativeReals)

    # Constraints
    ###########################################################################

    m.Carbon_Emissions_Imports_Constraint = Constraint(
        m.CRB_TX_OPR_TMPS, rule=carbon_emissions_imports_rule
    )


# Expression Rules
###############################################################################


def calculate_carbon_emissions_imports(mod, tx_line, timepoint):
    """
    **Expression Name**: N/A
    **Defined Over**: CRB_TX_OPR_TMPS

    In case of degeneracy where the *Import_Carbon_Emissions_Tons* variable
    can take a value larger than the actual import emissions (when the
    carbon cap is non-binding), we can post-process to figure out what the
    actual imported emissions are (e.g. instead of applying a tuning cost).
    """
    if (
        mod.carbon_cap_zone_import_direction[tx_line] == "positive"
        and value(mod.Transmit_Power_MW[tx_line, timepoint]) > 0
    ):
        return (
            value(mod.Transmit_Power_MW[tx_line, timepoint])
            * mod.tx_co2_intensity_tons_per_mwh[tx_line]
        )
    elif (
        mod.carbon_cap_zone_import_direction[tx_line] == "negative"
        and -value(mod.Transmit_Power_MW[tx_line, timepoint]) > 0
    ):
        return (
            -value(mod.Transmit_Power_MW[tx_line, timepoint])
            * mod.tx_co2_intensity_tons_per_mwh[tx_line]
        )
    else:
        return 0


# Constraint Formulation Rules
###############################################################################


def carbon_emissions_imports_rule(mod, tx, tmp):
    """
    **Constraint Name**: Carbon_Emissions_Imports_Constraint
    **Defined Over**: CRB_TX_OPR_TMPS

    Constrain the *Import_Carbon_Emissions_Tons* variable to be at least as
    large as the calculated imported carbon emissions for each transmission
    line, based on its CO2-intensity.
    """
    if mod.carbon_cap_zone_import_direction[tx] == "positive":
        return (
            mod.Import_Carbon_Emissions_Tons[tx, tmp]
            >= mod.Transmit_Power_MW[tx, tmp] * mod.tx_co2_intensity_tons_per_mwh[tx]
        )
    elif mod.carbon_cap_zone_import_direction[tx] == "negative":
        return (
            mod.Import_Carbon_Emissions_Tons[tx, tmp]
            >= -mod.Transmit_Power_MW[tx, tmp] * mod.tx_co2_intensity_tons_per_mwh[tx]
        )
    else:
        raise ValueError(
            "The parameter carbon_cap_zone_import_direction "
            "have a value of either 'positive' or "
            "'negative,' not {}.".format(mod.carbon_cap_zone_import_direction[tx])
        )


# Inputs-Outputs
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
            "transmission_lines.tab",
        ),
        select=(
            "transmission_line",
            "carbon_cap_zone",
            "carbon_cap_zone_import_direction",
            "tx_co2_intensity_tons_per_mwh",
        ),
        param=(
            m.tx_carbon_cap_zone,
            m.carbon_cap_zone_import_direction,
            m.tx_co2_intensity_tons_per_mwh,
        ),
    )

    data_portal.data()["CRB_TX_LINES"] = {
        None: list(data_portal.data()["tx_carbon_cap_zone"].keys())
    }


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
        "carbon_emission_imports_tons",
        "carbon_emission_imports_tons_degen",
    ]
    data = [
        [
            tx,
            tmp,
            value(m.Import_Carbon_Emissions_Tons[tx, tmp]),
            calculate_carbon_emissions_imports(m, tx, tmp),
        ]
        for (tx, tmp) in m.CRB_TX_OPR_TMPS
    ]
    results_df = create_results_df(
        index_columns=["transmission_line", "timepoint"],
        results_columns=results_columns,
        data=data,
    )

    for c in results_columns:
        getattr(d, TX_TIMEPOINT_DF)[c] = None
    getattr(d, TX_TIMEPOINT_DF).update(results_df)


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
    transmission_zones = c.execute(
        """SELECT transmission_line, carbon_cap_zone, import_direction,
        tx_co2_intensity_tons_per_mwh
        FROM inputs_transmission_carbon_cap_zones
            WHERE transmission_carbon_cap_zone_scenario_id = {}""".format(
            subscenarios.TRANSMISSION_CARBON_CAP_ZONE_SCENARIO_ID
        )
    )

    return transmission_zones


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
    transmission_lines.tab file.
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

    transmission_zones = get_inputs_from_database(
        scenario_id,
        subscenarios,
        db_weather_iteration,
        db_hydro_iteration,
        db_availability_iteration,
        db_subproblem,
        db_stage,
        conn,
    )

    # Make a dict for easy access
    prj_zone_dict = dict()
    for prj, zone, direction, intensity in transmission_zones:
        prj_zone_dict[str(prj)] = (
            (".", ".", ".") if zone is None else (str(zone), str(direction), intensity)
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
            "transmission_lines.tab",
        ),
        "r",
    ) as tx_file_in:
        reader = csv.reader(tx_file_in, delimiter="\t", lineterminator="\n")

        new_rows = list()

        # Append column header
        header = next(reader)
        header.append("carbon_cap_zone")
        header.append("carbon_cap_zone_import_direction")
        header.append("tx_co2_intensity_tons_per_mwh")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if zone specified or not
            if row[0] in list(prj_zone_dict.keys()):
                row.append(prj_zone_dict[row[0]][0])
                row.append(prj_zone_dict[row[0]][1])
                row.append(prj_zone_dict[row[0]][2])
                new_rows.append(row)
            # If project not specified, specify no zone
            else:
                row.append(".")
                row.append(".")
                row.append(".")
                new_rows.append(row)

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "transmission_lines.tab",
        ),
        "w",
        newline="",
    ) as tx_file_out:
        writer = csv.writer(tx_file_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)


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
    pass
    # Validation to be added
    # transmission_zones = get_inputs_from_database(
    #     scenario_id, subscenarios, subproblem, stage, conn)
