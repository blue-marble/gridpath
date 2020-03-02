#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This capacity type describes transmission lines that are available to the
optimization without having to incur an investment cost, e.g. existing
lines or lines that will be built in the future and whose capital costs
we want to ignore (in the objective function). A specified transmission line
can be available in all periods, or in some periods only, with no
restriction on the order and combination of periods. The two transmission
line directions may have different specified capacities, e.g. a line from
Zone 1 to Zone 2 with a minimum flow capacity of -1,000 MW and a maximum flow
capacity of 1,200 MW can transmit up to 1,000 MW from Zone 2 to Zone 1 and
up to 1,200 MW from Zone 1 to Zone 2.

"""

import csv
import os.path
from pyomo.environ import Set, Param, Reals


# TODO: add fixed O&M costs similar to gen_spec
def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`TX_SPEC_OPR_PRDS`                                              |
    |                                                                         |
    | Two-dimensional set of transmission line-period combinations that       |
    | helps describe the transmission capacity available in a given period.   |
    | This set is added to the list of sets to join to get the final          |
    | :code:`TX_OPR_PRDS` set defined in                                      |
    | **gridpath.transmission.capacity.capacity**.                            |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`tx_spec_min_flow_mw`                                           |
    | | *Defined over*: :code:`TX_SPEC_OPR_PRDS`                              |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | The transmission line's specified minimum flow capacity (in MW) in      |
    | each operational period. A negative number designates flow in the       |
    | opposite direction of the defined line flow direction.                  |
    +-------------------------------------------------------------------------+
    | | :code:`tx_spec_max_flow_mw`                                           |
    | | *Defined over*: :code:`TX_SPEC_OPR_PRDS`                              |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | The transmission line's specified maximum flow capacity (in MW) in      |
    | each operational period. A negative number designates flow in the       |
    | opposite direction of the defined line flow direction.                  |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.TX_SPEC_OPR_PRDS = Set(dimen=2)

    # Required Params
    ###########################################################################

    m.tx_spec_min_flow_mw = Param(
        m.TX_SPEC_OPR_PRDS,
        within=Reals
    )
    m.tx_spec_max_flow_mw = Param(
        m.TX_SPEC_OPR_PRDS,
        within=Reals
    )

    # Dynamic Components
    ###########################################################################

    m.tx_capacity_type_operational_period_sets.append(
        "TX_SPEC_OPR_PRDS"
    )


# Transmission Capacity Type Methods
###############################################################################

def min_transmission_capacity_rule(mod, tx, p):
    return mod.tx_spec_min_flow_mw[tx, p]


def max_transmission_capacity_rule(mod, tx, p):
    return mod.tx_spec_max_flow_mw[tx, p]


def tx_capacity_cost_rule(mod, g, p):
    """
    None for now.
    TODO: should there be a fixed cost for keeping transmission around
    """
    return 0


# Input-Output
###############################################################################

def load_module_specific_data(m, data_portal, scenario_directory,
                              subproblem, stage):
    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage, "inputs",
                              "specified_transmission_line_capacities.tab"),
        select=("transmission_line", "period",
                "specified_tx_min_mw", "specified_tx_max_mw"),
        index=m.TX_SPEC_OPR_PRDS,
        param=(m.tx_spec_min_flow_mw,
               m.tx_spec_max_flow_mw)
    )


# Database
###############################################################################

def get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    tx_capacities = c.execute(
        """SELECT transmission_line, period, min_mw, max_mw
        FROM inputs_transmission_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        INNER JOIN
        (SELECT transmission_line, period, min_mw, max_mw
        FROM inputs_transmission_existing_capacity
        WHERE transmission_existing_capacity_scenario_id = {} ) as capacity
        USING (transmission_line, period)
        WHERE transmission_portfolio_scenario_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.TRANSMISSION_EXISTING_CAPACITY_SCENARIO_ID,
            subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID
        )
    )

    return tx_capacities


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    specified_transmission_line_capacities.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    tx_capacities = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory,
                           "specified_transmission_line_capacities.tab"),
              "w", newline="") as existing_tx_capacity_tab_file:
        writer = csv.writer(existing_tx_capacity_tab_file,
                            delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["transmission_line", "period", "specified_tx_min_mw",
             "specified_tx_max_mw"]
        )

        for row in tx_capacities:
            writer.writerow(row)


# Validation
###############################################################################

def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
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
    # tx_capacities = get_module_specific_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

