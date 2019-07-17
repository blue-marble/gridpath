#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operational tuning costs. Includes tuning costs on hydro ramps.
"""

from builtins import next
import csv
import os.path
from pyomo.environ import Param, Var, Expression, Constraint, \
    NonNegativeReals, value

from gridpath.auxiliary.dynamic_components import required_operational_modules
from gridpath.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """
    Sum up all operational costs and add to the objective function.
    :param m:
    :param d:
    :return:
    """

    m.ramp_tuning_cost = Param(default=0)

    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # Figure out how much each project ramped (for simplicity, only look at
    # the difference in power setpoints, i.e. ignore the effect of providing
    # any reserves)
    def ramp_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            power_delta_rule(mod, g, tmp)

    m.Ramp_Expression = Expression(
        m.PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=ramp_rule)

    # Apply costs
    m.Ramp_Up_Tuning_Cost = Var(
        m.PROJECT_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals)
    m.Ramp_Down_Tuning_Cost = Var(
        m.PROJECT_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals)

    def ramp_up_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        tuning_cost = \
            mod.ramp_tuning_cost if gen_op_type in [
                "hydro_curtailable", "hydro_noncurtailable", "storage_generic"
            ] else 0
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        elif tuning_cost == 0:
            return Constraint.Skip
        else:
            return mod.Ramp_Up_Tuning_Cost[g, tmp] \
                   >= mod.Ramp_Expression[g, tmp] \
                   * tuning_cost

    m.Ramp_Up_Tuning_Cost_Constraint = \
        Constraint(m.PROJECT_OPERATIONAL_TIMEPOINTS,
                   rule=ramp_up_rule)

    def ramp_down_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        tuning_cost = \
            mod.ramp_tuning_cost \
            if gen_op_type in ["hydro_curtailable", "hydro_noncurtailable"] \
            else 0
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        elif tuning_cost == 0:
            return Constraint.Skip
        else:
            return mod.Ramp_Down_Tuning_Cost[g, tmp] \
                   >= mod.Ramp_Expression[g, tmp] \
                   * - tuning_cost

    m.Ramp_Down_Tuning_Cost_Constraint = \
        Constraint(m.PROJECT_OPERATIONAL_TIMEPOINTS,
                   rule=ramp_down_rule)


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
        data_portal.load(filename=tuning_param_file,
                         select=("ramp_tuning_cost",),
                         param=m.ramp_tuning_cost
                         )
    else:
        pass


def get_inputs_from_database(subscenarios, subproblem, stage, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    ramp_tuning_cost = c.execute(
        """SELECT ramp_tuning_cost
        FROM inputs_tuning
        WHERE tuning_scenario_id = {}""".format(
            subscenarios.TUNING_SCENARIO_ID
        )
    ).fetchone()[0]

    # If tuning params file exists, add column to file, else create file and
    #  writer header and tuning param value
    if os.path.isfile(os.path.join(inputs_directory, "tuning_params.tab")):
        with open(os.path.join(inputs_directory, "tuning_params.tab"), "r"
                  ) as projects_file_in:
            reader = csv.reader(projects_file_in, delimiter="\t")

            new_rows = list()

            # Append column header
            header = next(reader)
            header.append("import_carbon_tuning_cost")
            new_rows.append(header)

            # Append tuning param value
            param_value = next(reader)
            param_value.append(ramp_tuning_cost)
            new_rows.append(param_value)

        with open(os.path.join(inputs_directory, "tuning_params.tab"),
                  "w") as \
                tuning_params_file_out:
            writer = csv.writer(tuning_params_file_out, delimiter="\t")
            writer.writerows(new_rows)

    else:
        with open(os.path.join(inputs_directory, "tuning_params.tab"),
                  "w") as \
                tuning_params_file_out:
            writer = csv.writer(tuning_params_file_out, delimiter="\t")
            writer.writerow(["ramp_tuning_cost"])
            writer.writerow([ramp_tuning_cost])
