#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Subtracting a small amount from the objective function when the Dynamic_ELCC
expression is higher to make sure that it is set to the maximum available in
case the PRM constraint is non-binding.
"""


from builtins import next
import csv
import os.path
from pyomo.environ import Param, Expression

from gridpath.auxiliary.dynamic_components import total_cost_components


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    m.dynamic_elcc_tuning_cost_per_mw = Param(default=0)

    def total_elcc_tuning_cost_rule(mod):
        """
        Set dynamic elcc to max available by subtracting a small amount from 
        the objective function when Dynamic_ELCC is higher
        :param mod:
        :return:
        """
        if mod.dynamic_elcc_tuning_cost_per_mw == 0:
            return 0
        else:
            return - sum(
                mod.Dynamic_ELCC_MW[z, p]
                * mod.dynamic_elcc_tuning_cost_per_mw
                * mod.number_years_represented[p]
                * mod.discount_factor[p]
                for (z, p)
                in mod.PRM_ZONE_PERIODS_WITH_REQUIREMENT
            )

    m.Total_Dynamic_ELCC_Tuning_Cost = Expression(
        rule=total_elcc_tuning_cost_rule
    )
    getattr(d, total_cost_components).append("Total_Dynamic_ELCC_Tuning_Cost")
    
    
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
                         select=("dynamic_elcc_tuning_cost_per_mw",),
                         param=m.dynamic_elcc_tuning_cost_per_mw
                         )
    else:
        pass


def get_inputs_from_database(subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    dynamic_elcc_tuning_cost = c.execute(
        """SELECT dynamic_elcc_tuning_cost_per_mw
        FROM inputs_tuning
        WHERE tuning_scenario_id = {}""".format(
            subscenarios.TUNING_SCENARIO_ID
        )
    ).fetchone()[0]
    # TODO: remove fetch out of this function?
    return dynamic_elcc_tuning_cost


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
    # dynamic_elcc_tuning_cost = get_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)


def write_model_inputs(inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input
    tuning_params.tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    dynamic_elcc_tuning_cost = get_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    # If tuning params file exists, add column to file, else create file and
    #  writer header and tuning param value
    if os.path.isfile(os.path.join(inputs_directory, "tuning_params.tab")):
        with open(os.path.join(inputs_directory, "tuning_params.tab"), "r"
                  ) as tuning_params_file_in:
            reader = csv.reader(tuning_params_file_in, delimiter="\t")

            new_rows = list()

            # Append column header
            header = next(reader)
            header.append("dynamic_elcc_tuning_cost_per_mw")
            new_rows.append(header)

            # Append tuning param value
            param_value = next(reader)
            param_value.append(dynamic_elcc_tuning_cost)
            new_rows.append(param_value)

        with open(os.path.join(inputs_directory, "tuning_params.tab"),
                  "w", newline="") as \
                tuning_params_file_out:
            writer = csv.writer(tuning_params_file_out, delimiter="\t")
            writer.writerows(new_rows)

    else:
        with open(os.path.join(inputs_directory, "tuning_params.tab"),
                  "w", newline="") as \
                tuning_params_file_out:
            writer = csv.writer(tuning_params_file_out, delimiter="\t")
            writer.writerows(["dynamic_elcc_tuning_cost_per_mw"])
            writer.writerows([dynamic_elcc_tuning_cost])
