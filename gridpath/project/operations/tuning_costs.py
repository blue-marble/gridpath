#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operational tuning costs that prevent erratic dispatch in case of degeneracy.
Tuning costs can be applied to hydro up and down ramps (gen_hydro
and gen_hydro_must_take operational types) and to storage up-ramps (
stor operational type) in order to force smoother dispatch.
"""

from builtins import next
import csv
import os.path
from pyomo.environ import Param, Var, Expression, Constraint, \
    NonNegativeReals

from gridpath.auxiliary.dynamic_components import required_operational_modules
from gridpath.auxiliary.auxiliary import load_operational_type_modules
from gridpath.project.common_functions import \
    check_if_boundary_type_and_first_timepoint


def add_model_components(m, di, dc):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Input Params                                                            |
    +=========================================================================+
    | | :code:`ramp_tuning_cost_per_mw`                                       |
    | | *Default*: :code:`0`                                                  |
    |                                                                         |
    | The tuning cost for ramping in $ per MW of ramp. The cost is the same   |
    | for upward and downward ramping.                                        |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`Ramp_Up_Tuning_Cost`                                           |
    | | *Defined over*: :code:`PRJ_OPR_TMPS`                                  |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | This variable represents the total upward ramping tuning cost for each  |
    | project in each operational timepoint.                                  |
    +-------------------------------------------------------------------------+
    | | :code:`Ramp_Up_Tuning_Cost`                                           |
    | | *Defined over*: :code:`PRJ_OPR_TMPS`                                  |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | This variable represents the total downwward ramping tuning cost for    |
    | each project in each operational timepoint.                             |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Ramp_Expression`                                               |
    | | *Defined over*: :code:`PRJ_OPR_TMPS`                                  |
    |                                                                         |
    | This expression pulls the ramping expression from the appropriate       |
    | operational type module. It represents the difference in power output   |
    | (in MW) between 2 timepoints; i.e. a positive number means upward ramp  |
    | and a negative number means downward ramp. For simplicity, we only look |
    | at the difference in power setpoints, i.e. ignore the effect of         |
    | providing any reserves.                                                 |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`Ramp_Up_Tuning_Cost_Constraint`                                |
    | | *Defined over*: :code:`PRJ_OPR_TMPS`                                  |
    |                                                                         |
    | Sets the upward ramping tuning cost to be equal to the ramp expression  |
    | times the tuning cost (for the appropriate operational types only).     |
    +-------------------------------------------------------------------------+
    | | :code:`Ramp_Down_Tuning_Cost_Constraint`                              |
    | | *Defined over*: :code:`PRJ_OPR_TMPS`                                  |
    |                                                                         |
    | Sets the downward ramping tuning cost to be equal to the ramp           |
    | expression times the tuning cost (for the appropriate operational types |
    | only).                                                                  |
    +-------------------------------------------------------------------------+

    """

    # Dynamic Components
    ###########################################################################

    imported_operational_modules = load_operational_type_modules(
        getattr(d, required_operational_modules)
    )

    # Input Params
    ###########################################################################

    m.ramp_tuning_cost_per_mw = Param(default=0)

    # Expressions
    ###########################################################################

    def ramp_rule(mod, g, tmp):
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            power_delta_rule(mod, g, tmp)

    m.Ramp_Expression = Expression(
        m.PRJ_OPR_TMPS,
        rule=ramp_rule
    )

    # Variables
    ###########################################################################

    m.Ramp_Up_Tuning_Cost = Var(
        m.PRJ_OPR_TMPS,
        within=NonNegativeReals
    )

    m.Ramp_Down_Tuning_Cost = Var(
        m.PRJ_OPR_TMPS,
        within=NonNegativeReals
    )

    # Constraints
    ###########################################################################

    m.Ramp_Up_Tuning_Cost_Constraint = Constraint(
        m.PRJ_OPR_TMPS,
        rule=ramp_up_rule
    )

    m.Ramp_Down_Tuning_Cost_Constraint = Constraint(
        m.PRJ_OPR_TMPS,
        rule=ramp_down_rule
    )


# Constraint Rules
###############################################################################

def ramp_up_rule(mod, g, tmp):
    """
    **Constraint Name**: Ramp_Up_Tuning_Cost_Constraint
    **Enforced Over**: PRJ_OPR_TMPS
    """
    gen_op_type = mod.operational_type[g]
    tuning_cost = mod.ramp_tuning_cost_per_mw \
        if gen_op_type in ["gen_hydro", "gen_hydro_must_take", "stor"] \
        else 0
    if check_if_boundary_type_and_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g],
        boundary_type="linear"
    ):
        return Constraint.Skip
    elif tuning_cost == 0:
        return Constraint.Skip
    else:
        return mod.Ramp_Up_Tuning_Cost[g, tmp] \
               >= mod.Ramp_Expression[g, tmp] \
               * tuning_cost


def ramp_down_rule(mod, g, tmp):
    """
    **Constraint Name**: Ramp_Down_Tuning_Cost_Constraint
    **Enforced Over**: PRJ_OPR_TMPS
    """
    gen_op_type = mod.operational_type[g]
    # TODO: is storage missing on purpose?
    tuning_cost = mod.ramp_tuning_cost_per_mw \
        if gen_op_type in ["gen_hydro", "gen_hydro_must_take"] \
        else 0
    if check_if_boundary_type_and_first_timepoint(
        mod=mod, tmp=tmp, balancing_type=mod.balancing_type_project[g],
        boundary_type="linear"
    ):
        return Constraint.Skip
    elif tuning_cost == 0:
        return Constraint.Skip
    else:
        return mod.Ramp_Down_Tuning_Cost[g, tmp] \
            >= mod.Ramp_Expression[g, tmp] \
            * - tuning_cost


# Input-Output
###############################################################################

def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """
    Get tuning param value from file if file exists
    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    tuning_param_file = os.path.join(
        scenario_directory, subproblem, stage, "inputs", "tuning_params.tab"
    )

    if os.path.exists(tuning_param_file):
        data_portal.load(
            filename=tuning_param_file,
            select=("ramp_tuning_cost_per_mw",),
            param=m.ramp_tuning_cost_per_mw
        )
    else:
        pass


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
    subproblem = 1 if subproblem == "" else subproblem
    stage = 1 if stage == "" else stage
    c = conn.cursor()
    ramp_tuning_cost = c.execute(
        """SELECT ramp_tuning_cost_per_mw
        FROM inputs_tuning
        WHERE tuning_scenario_id = {}""".format(
            subscenarios.TUNING_SCENARIO_ID
        )
    ).fetchone()[0]
    # TODO: move fetchone out of this functions for consistency (always return
    #   SQL cursor?
    return ramp_tuning_cost


def write_model_inputs(scenario_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    tuning_params.tab file (to be precise, amend it).
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    ramp_tuning_cost = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # If tuning params file exists, add column to file, else create file and
    #  writer header and tuning param value
    if os.path.isfile(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "tuning_params.tab")):
        with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "tuning_params.tab"),
                  "r") as projects_file_in:
            reader = csv.reader(projects_file_in, delimiter="\t",
                                lineterminator="\n")

            new_rows = list()

            # Append column header
            header = next(reader)
            header.append("ramp_tuning_cost_per_mw")
            new_rows.append(header)

            # Append tuning param value
            param_value = next(reader)
            param_value.append(ramp_tuning_cost)
            new_rows.append(param_value)

        with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "tuning_params.tab"),
                  "w", newline="") as tuning_params_file_out:
            writer = csv.writer(tuning_params_file_out, delimiter="\t",
                                lineterminator="\n")
            writer.writerows(new_rows)

    else:
        with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs", "tuning_params.tab"),
                  "w", newline="") as tuning_params_file_out:
            writer = csv.writer(tuning_params_file_out, delimiter="\t",
                                lineterminator="\n")
            writer.writerow(["ramp_tuning_cost_per_mw"])
            writer.writerow([ramp_tuning_cost])


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

    # ramp_tuning_cost = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

    # do stuff here to validate inputs
