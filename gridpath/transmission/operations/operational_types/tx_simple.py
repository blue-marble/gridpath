#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This operational type describes transmission lines whose flows are simulated
using a linear transport model, i.e. transmission flow is constrained to be
less than or equal to the line capacity. Line capacity can be defined for
both transmission flow directions.

"""

import os
import pandas as pd
from pyomo.environ import Set, Param, Var, Constraint, Reals, PercentFraction


def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`TX_SIMPLE`                                                     |
    |                                                                         |
    | The set of transmission lines of the :code:`tx_simple` operational      |
    | type.                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`TX_SIMPLE_OPR_TMPS`                                            |
    |                                                                         |
    | Two-dimensional set with transmission lines of the :code:`tx_simple`    |
    | operational type and their operational timepoints.                      |
    +-------------------------------------------------------------------------+

    +-------------------------------------------------------------------------+
    | Params                                                                  |
    +=========================================================================+
    | | :code:`tx_simple_loss_factor`                                         |
    | | *Defined over*: :code:`TX_SIMPLE`                                     |
    | | *Within*: :code:`PercentFraction`                                     |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The fraction of power that is lost when transmitted over this line.     |
    +-------------------------------------------------------------------------+


    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`TxSimple_Transmit_Power_MW`                                    |
    | | *Defined over*: :code:`TX_SIMPLE_OPR_TMPS`                            |
    | | *Within*: :code:`Reals`                                               |
    |                                                                         |
    | The transmission line's power flow in each timepoint in which the line  |
    | is operational. Negative power means the power flow goes in the         |
    | opposite direction of the line's defined direction.                     |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`TxSimple_Min_Transmit_Constraint`                              |
    | | *Defined over*: :code:`TX_SIMPLE_OPR_TMPS`                            |
    |                                                                         |
    | Transmitted power should exceed the transmission line's minimum power   |
    | flow for in every operational timepoint.                                |
    +-------------------------------------------------------------------------+
    +-------------------------------------------------------------------------+
    | | :code:`TxSimple_Max_Transmit_Constraint`                              |
    | | *Defined over*: :code:`TX_SIMPLE_OPR_TMPS`                            |
    |                                                                         |
    | Transmitted power cannot exceed the transmission line's maximum power   |
    | flow in every operational timepoint.                                    |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.TX_SIMPLE = Set(
        within=m.TX_LINES,
        rule=lambda mod: set(l for l in mod.TX_LINES if
                             mod.tx_operational_type[l] == "tx_simple")
    )

    m.TX_SIMPLE_OPR_TMPS = Set(
        dimen=2, within=m.TX_OPR_TMPS,
        rule=lambda mod:
            set((l, tmp)
                for (l, tmp) in mod.TX_OPR_TMPS
                if l in mod.TX_SIMPLE)
    )

    # Params
    ###########################################################################
    m.tx_simple_loss_factor = Param(
        m.TX_SIMPLE, within=PercentFraction, default=0
    )

    # Variables
    ###########################################################################

    m.TxSimple_Transmit_Power_MW = Var(
        m.TX_SIMPLE_OPR_TMPS,
        within=Reals
    )

    # Constraints
    ###########################################################################

    m.TxSimple_Min_Transmit_Constraint = Constraint(
        m.TX_SIMPLE_OPR_TMPS,
        rule=min_transmit_rule
    )

    m.TxSimple_Max_Transmit_Constraint = Constraint(
        m.TX_SIMPLE_OPR_TMPS,
        rule=max_transmit_rule
    )


# Constraint Formulation Rules
###############################################################################

# TODO: should these move to operations.py since all transmission op_types
#  have this constraint?
def min_transmit_rule(mod, l, tmp):
    """
    **Constraint Name**: TxSimple_Min_Transmit_Constraint
    **Enforced Over**: TX_SIMPLE_OPR_TMPS

    Transmitted power should exceed the minimum transmission flow capacity in
    each operational timepoint.
    """
    return mod.TxSimple_Transmit_Power_MW[l, tmp] \
        >= mod.Tx_Min_Capacity_MW[l, mod.period[tmp]]


def max_transmit_rule(mod, l, tmp):
    """
    **Constraint Name**: TxSimple_Max_Transmit_Constraint
    **Enforced Over**: TX_SIMPLE_OPR_TMPS

    Transmitted power cannot exceed the maximum transmission flow capacity in
    each operational timepoint.
    """
    return mod.TxSimple_Transmit_Power_MW[l, tmp] \
        <= mod.Tx_Max_Capacity_MW[l, mod.period[tmp]]


# Transmission Operational Type Methods
###############################################################################

def transmit_power_rule(mod, line, tmp):
    """
    For load-balance purposes, the power transmitted over the tx_simple line
    in each operational timepoint is the power sent derated for losses via
    the linear loss factor.
    """
    return mod.TxSimple_Transmit_Power_MW[line, tmp]\
        * (1 - mod.tx_simple_loss_factor[line])


# Input-Output
###############################################################################

def load_module_specific_data(m, data_portal, scenario_directory,
                              subproblem, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Get the simple transport model lines
    df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "inputs",
                     "transmission_lines.tab"),
        sep="\t",
        usecols=["TRANSMISSION_LINES", "tx_operational_type",
                 "tx_simple_loss_factor"]
    )
    df = df[df["tx_operational_type"] == "tx_simple"]

    # Dict of loss factor by tx_simple line
    loss_factor = dict(zip(
        df["TRANSMISSION_LINES"],
        pd.to_numeric(df["tx_simple_loss_factor"])
    ))

    # Load data
    data_portal.data()["tx_simple_loss_factor"] = loss_factor
