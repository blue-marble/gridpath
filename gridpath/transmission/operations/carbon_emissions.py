#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Get carbon emissions on each 'carbonaceous' transmission line.
"""

import csv
import os.path
from pyomo.environ import Param, Set, Var, Constraint, Expression, \
    NonNegativeReals, value

from gridpath.auxiliary.dynamic_components import \
    carbon_cap_balance_emission_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # First figure out which projects we need to track for the carbon cap
    m.CARBONACEOUS_TRANSMISSION_LINES = Set(within=m.TRANSMISSION_LINES)
    m.tx_carbon_cap_zone = Param(
        m.CARBONACEOUS_TRANSMISSION_LINES,
        within=m.CARBON_CAP_ZONES
    )
    m.carbon_cap_zone_import_direction = Param(
        m.CARBONACEOUS_TRANSMISSION_LINES
    )
    m.tx_co2_intensity_tons_per_mwh = Param(
        m.CARBONACEOUS_TRANSMISSION_LINES,
        within=NonNegativeReals
    )

    m.CARBONACEOUS_TRANSMISSION_LINES_BY_CARBON_CAP_ZONE = \
        Set(m.CARBON_CAP_ZONES, within=m.CARBONACEOUS_TRANSMISSION_LINES,
            initialize=lambda mod, co2_z:
            [tx for tx in mod.CARBONACEOUS_TRANSMISSION_LINES
             if mod.tx_carbon_cap_zone[tx] == co2_z])

    # Get operational carbon cap transmission line - timepoints combinations
    m.CARBONACEOUS_TRANSMISSION_OPERATIONAL_TIMEPOINTS = Set(
        within=m.TRANSMISSION_OPERATIONAL_TIMEPOINTS,
        rule=lambda mod: [(tx, tmp) for (tx, tmp) in
                          mod.TRANSMISSION_OPERATIONAL_TIMEPOINTS
                          if tx in mod.CARBONACEOUS_TRANSMISSION_LINES]
    )

    # Variable for imported emissions
    m.Import_Carbon_Emissions_Tons = Var(
        m.CARBONACEOUS_TRANSMISSION_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals
    )

    # Get emissions brought in by each transmission line
    def carbon_emissions_imports_rule(mod, tx, tmp):
        """

        :param mod:
        :param tx:
        :param tmp:
        :return:
        """
        if mod.carbon_cap_zone_import_direction[tx] == "positive":
            return mod.Import_Carbon_Emissions_Tons[tx, tmp] \
                >= mod.Transmit_Power_MW[tx, tmp] * \
                mod.tx_co2_intensity_tons_per_mwh[tx]
        elif mod.carbon_cap_zone_import_direction[tx] == "negative":
            return mod.Import_Carbon_Emissions_Tons[tx, tmp] \
                >= -mod.Transmit_Power_MW[tx, tmp] * \
                mod.tx_co2_intensity_tons_per_mwh[tx]
        else:
            raise ValueError("The parameter carbon_cap_zone_import_direction "
                             "have a value of either 'positive' or "
                             "'negative,' not {}.".format(
                              mod.carbon_cap_zone_import_direction[tx]
                                )
                             )

    m.Imported_Carbon_Emissions_Constraint = Constraint(
        m.CARBONACEOUS_TRANSMISSION_OPERATIONAL_TIMEPOINTS,
        rule=carbon_emissions_imports_rule
    )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "transmission_lines.tab"),
                     select=("TRANSMISSION_LINES", "carbon_cap_zone",
                             "carbon_cap_zone_import_direction",
                             "tx_co2_intensity_tons_per_mwh"),
                     param=(m.tx_carbon_cap_zone,
                            m.carbon_cap_zone_import_direction,
                            m.tx_co2_intensity_tons_per_mwh)
                     )

    data_portal.data()['CARBONACEOUS_TRANSMISSION_LINES'] = {
        None: data_portal.data()['tx_carbon_cap_zone'].keys()
    }


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "carbon_emission_imports_by_tx_line.csv"), "wb") \
            as carbon_emission_imports__results_file:
        writer = csv.writer(carbon_emission_imports__results_file)
        writer.writerow(["tx_line", "timepoint", "period",
                         "horizon", "horizon_weight",
                         "carbon_emission_imports_tons"])
        for (tx, tmp) in \
                m.CARBONACEOUS_TRANSMISSION_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                tx,
                tmp,
                m.period[tmp],
                m.horizon[tmp],
                m.horizon_weight[m.horizon[tmp]],
                value(m.Import_Carbon_Emissions_Tons[tx, tmp])
            ])


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    transmission_zones = c.execute(
        """SELECT transmission_line, carbon_cap_zone, import_direction,
        tx_co2_intensity_tons_per_mwh
        FROM inputs_transmission_carbon_cap_zones
            WHERE carbon_cap_zone_scenario_id = {}
            AND transmission_carbon_cap_zone_scenario_id = {}""".format(
            subscenarios.CARBON_CAP_ZONE_SCENARIO_ID,
            subscenarios.TRANSMISSION_CARBON_CAP_ZONE_SCENARIO_ID
        )
    ).fetchall()

    # Make a dict for easy access
    prj_zone_dict = dict()
    for (prj, zone, direction, intensity) in transmission_zones:
        prj_zone_dict[str(prj)] = \
            (".", ".", ".") if zone is None \
            else (str(zone), str(direction), intensity)

    with open(os.path.join(inputs_directory, "transmission_lines.tab"), "r"
              ) as tx_file_in:
        reader = csv.reader(tx_file_in, delimiter="\t")

        new_rows = list()

        # Append column header
        header = reader.next()
        header.append("carbon_cap_zone")
        header.append("carbon_cap_zone_import_direction")
        header.append("tx_co2_intensity_tons_per_mwh")
        new_rows.append(header)

        # Append correct values
        for row in reader:
            # If project specified, check if zone specified or not
            if row[0] in prj_zone_dict.keys():
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
              "w") as tx_file_out:
        writer = csv.writer(tx_file_out, delimiter="\t")
        writer.writerows(new_rows)
