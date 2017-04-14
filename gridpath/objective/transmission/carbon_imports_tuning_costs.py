#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Tuning costs to prevent undesirable behavior if there are non-binding
constraints, problem is degenerate, etc.
Import_Carbon_Emissions_Tons must be non-negative and greater than the flow
on the line times the emissions intensity. In the case, this constraint is
non-binding -- and without a tuning cost, the optimization is allowed to
set Import_Carbon_Emissions higher than the product of flow and emissions
rate. Adding a tuning cost prevents that behavior as it pushes the emissions
variable down to be equal
"""

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

    m.import_carbon_tuning_cost = Param(default=0)

    def total_import_carbon_tuning_cost_rule(mod):
        """
        Hurdle costs for all transmission lines across all timepoints
        :param mod:
        :return:
        """
        return sum(
            mod.Import_Carbon_Emissions_Tons[tx, tmp]
            * mod.import_carbon_tuning_cost
            * mod.number_of_hours_in_timepoint[tmp]
            * mod.horizon_weight[mod.horizon[tmp]]
            * mod.number_years_represented[mod.period[tmp]]
            * mod.discount_factor[mod.period[tmp]]
            for (tx, tmp)
            in mod.CARBONACEOUS_TRANSMISSION_OPERATIONAL_TIMEPOINTS
        )

    m.Total_Import_Carbon_Tuning_Cost = Expression(
        rule=total_import_carbon_tuning_cost_rule
    )
    getattr(d, total_cost_components).append(
        "Total_Import_Carbon_Tuning_Cost"
    )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """
    Get tuning param value from file if file exists
    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    tuning_param_file = os.path.join(
        scenario_directory, horizon, stage, "inputs", "tuning_params.tab"
    )

    if os.path.exists(tuning_param_file):
        data_portal.load(filename=tuning_param_file,
                         select=("import_carbon_tuning_cost",),
                         param=m.import_carbon_tuning_cost
                         )
    else:
        pass


def get_inputs_from_database(subscenarios, c, inputs_directory):
    """

    :param subscenarios
    :param c:
    :param inputs_directory:
    :return:
    """

    import_carbon_tuning_cost = c.execute(
        """SELECT import_carbon_tuning_cost
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
            header = reader.next()
            header.append("import_carbon_tuning_cost")
            new_rows.append(header)

            # Append tuning param value
            param_value = reader.next()
            param_value.append(import_carbon_tuning_cost)
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
            writer.writerows(["import_carbon_tuning_cost"])
            writer.writerows([import_carbon_tuning_cost])
