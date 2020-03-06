#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Get carbon emissions on each 'carbonaceous' transmission line.

Carbon emissions are based on power sent on the transmission line.
"""
from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Param, Set, Var, Constraint, Expression, \
    NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import
from gridpath.auxiliary.dynamic_components import \
    carbon_cap_balance_emission_components


def add_model_components(m, d):
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

    m.CRB_TX_LINES = Set(
        within=m.TX_LINES
    )

    m.CRB_TX_OPR_TMPS = Set(
        within=m.TX_OPR_TMPS,
        rule=lambda mod: [(tx, tmp) for (tx, tmp) in mod.TX_OPR_TMPS
                          if tx in mod.CRB_TX_LINES]
    )

    # Required Input Params
    ###########################################################################

    m.tx_carbon_cap_zone = Param(
        m.CRB_TX_LINES,
        within=m.CARBON_CAP_ZONES
    )

    m.carbon_cap_zone_import_direction = Param(
        m.CRB_TX_LINES
    )

    m.tx_co2_intensity_tons_per_mwh = Param(
        m.CRB_TX_LINES,
        within=NonNegativeReals
    )

    # Derived Sets
    ###########################################################################

    m.CRB_TX_LINES_BY_CARBON_CAP_ZONE = Set(
        m.CARBON_CAP_ZONES,
        within=m.CRB_TX_LINES,
        initialize=lambda mod, co2_z:
        [tx for tx in mod.CRB_TX_LINES if mod.tx_carbon_cap_zone[tx] == co2_z]
    )

    # Variables
    ###########################################################################

    m.Import_Carbon_Emissions_Tons = Var(
        m.CRB_TX_OPR_TMPS,
        within=NonNegativeReals
    )

    # Constraints
    ###########################################################################

    m.Carbon_Emissions_Imports_Constraint = Constraint(
        m.CRB_TX_OPR_TMPS,
        rule=carbon_emissions_imports_rule
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
    if mod.carbon_cap_zone_import_direction[tx_line] == "positive" \
            and value(mod.Transmit_Power_Sent_MW[tx_line, timepoint]) > 0:
        return value(mod.Transmit_Power_Sent_MW[tx_line, timepoint]) \
               * mod.tx_co2_intensity_tons_per_mwh[tx_line]
    elif mod.carbon_cap_zone_import_direction[tx_line] == "negative" \
            and -value(mod.Transmit_Power_Sent_MW[tx_line, timepoint]) > 0:
        return -value(mod.Transmit_Power_Sent_MW[tx_line, timepoint]) \
               * mod.tx_co2_intensity_tons_per_mwh[tx_line]
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
        return mod.Import_Carbon_Emissions_Tons[tx, tmp] \
            >= mod.Transmit_Power_Sent_MW[tx, tmp] \
            * mod.tx_co2_intensity_tons_per_mwh[tx]
    elif mod.carbon_cap_zone_import_direction[tx] == "negative":
        return mod.Import_Carbon_Emissions_Tons[tx, tmp] \
            >= -mod.Transmit_Power_Sent_MW[tx, tmp] \
            * mod.tx_co2_intensity_tons_per_mwh[tx]
    else:
        raise ValueError("The parameter carbon_cap_zone_import_direction "
                         "have a value of either 'positive' or "
                         "'negative,' not {}.".format(
                          mod.carbon_cap_zone_import_direction[tx]
                            )
                         )


# Inputs-Outputs
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
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
        filename=os.path.join(scenario_directory, subproblem, stage,
                              "inputs", "transmission_lines.tab"),
        select=("TRANSMISSION_LINES", "carbon_cap_zone",
                "carbon_cap_zone_import_direction",
                "tx_co2_intensity_tons_per_mwh"),
        param=(m.tx_carbon_cap_zone,
               m.carbon_cap_zone_import_direction,
               m.tx_co2_intensity_tons_per_mwh)
    )

    data_portal.data()['CRB_TX_LINES'] = {
        None: list(data_portal.data()['tx_carbon_cap_zone'].keys())
    }


def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "carbon_emission_imports_by_tx_line.csv"),
              "w", newline="") as carbon_emission_imports__results_file:
        writer = csv.writer(carbon_emission_imports__results_file)
        writer.writerow(["tx_line", "period", "timepoint",
                         "timepoint_weight", "number_of_hours_in_timepoint",
                         "carbon_emission_imports_tons",
                         "carbon_emission_imports_tons_degen"])
        for (tx, tmp) in m.CRB_TX_OPR_TMPS:
            writer.writerow([
                tx,
                m.period[tmp],
                tmp,
                m.timepoint_weight[tmp],
                m.number_of_hours_in_timepoint[tmp],
                value(m.Import_Carbon_Emissions_Tons[tx, tmp]),
                calculate_carbon_emissions_imports(m, tx, tmp)
            ])


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
    inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    transmission_lines.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    transmission_zones = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # Make a dict for easy access
    prj_zone_dict = dict()
    for (prj, zone, direction, intensity) in transmission_zones:
        prj_zone_dict[str(prj)] = \
            (".", ".", ".") if zone is None \
            else (str(zone), str(direction), intensity)

    with open(os.path.join(inputs_directory, "transmission_lines.tab"),
              "r") as tx_file_in:
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

    with open(os.path.join(inputs_directory, "transmission_lines.tab"),
              "w", newline="") as tx_file_out:
        writer = csv.writer(tx_file_out, delimiter="\t", lineterminator="\n")
        writer.writerows(new_rows)


def import_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    # Carbon emission imports by transmission line and timepoint
    if not quiet:
        print("transmission carbon emissions")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_transmission_carbon_emissions",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "carbon_emission_imports_by_tx_line.csv"),
              "r") as emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            tx_line = row[0]
            period = row[1]
            timepoint = row[2]
            timepoint_weight = row[3]
            number_of_hours_in_timepoint = row[4]
            carbon_emission_imports_tons = row[5]
            carbon_emission_imports_tons_degen = row[6]

            results.append(
                (scenario_id, tx_line, period, subproblem, stage,
                 timepoint, timepoint_weight,
                 number_of_hours_in_timepoint,
                 carbon_emission_imports_tons,
                 carbon_emission_imports_tons_degen)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_transmission_carbon_emissions{}
         (scenario_id, tx_line, period, subproblem_id, stage_id, 
         timepoint, timepoint_weight, 
         number_of_hours_in_timepoint, 
         carbon_emission_imports_tons, 
         carbon_emission_imports_tons_degen)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_transmission_carbon_emissions
        (scenario_id, tx_line, period, subproblem_id, stage_id,
        timepoint, timepoint_weight, number_of_hours_in_timepoint, 
        carbon_emission_imports_tons, carbon_emission_imports_tons_degen)
        SELECT
        scenario_id, tx_line, period, subproblem_id, stage_id,
        timepoint, timepoint_weight, number_of_hours_in_timepoint, 
        carbon_emission_imports_tons, carbon_emission_imports_tons_degen
        FROM temp_results_transmission_carbon_emissions{}
         ORDER BY scenario_id, tx_line, subproblem_id, stage_id, timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


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
    # transmission_zones = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

