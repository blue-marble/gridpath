#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
GridPath's objective function consists of modularized components. This
modularity allows for different objective functions to be defined. Here, we
discuss the objective of minimizing total system costs.

Its most basic version includes the aggregated project capacity costs and
aggregated project operational costs, and any load-balance penalties
incurred (i.e. the aggregated unserved energy and/or overgeneration costs).

Other standard objective function components include:

    * aggregated transmission line capacity investment costs
    * aggregated transmission operational costs (hurdle rates)
    * aggregated reserve violation penalties

GridPath also can include custom objective function components that may not
be standard for all systems. Examples currently include:

    * local capacity shortage penalties
    * planning reserve margin costs
    * various tuning costs

All costs are net present value costs, with a user-specified discount factor
applied to call costs depending on the period in which they are incurred.
"""

import csv
import pandas as pd
import sqlite3
import numpy as np
import os


from pyomo.environ import Objective, minimize, value

from db.common_functions import spin_on_database_lock

from gridpath.auxiliary.dynamic_components import total_cost_components
from gridpath.auxiliary.auxiliary import setup_results_import


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    :param m: the Pyomo abstract model object we are adding components to
    :param d: the DynamicComponents class object we will get components from

    At this point, all relevant modules should have added cost components to
    *d.total_cost_components*. We sum them all up here. With the minimum set
    of functionality, the objective function will be as follows:

    :math:`minimize:` \n

    :math:`Total\_Capacity\_Costs + Total\_Variable\_OM\_Cost +
    Total\_Fuel\_Cost + Total\_Load\_Balance\_Penalty\_Costs`

    """

    # Define objective function
    def total_cost_rule(mod):

        return sum(getattr(mod, c)
                   for c in getattr(d, total_cost_components))

    m.Total_Cost = Objective(rule=total_cost_rule, sense=minimize)


# Input-Output
###############################################################################

# def export_results(scenario_directory, subproblem, stage, m, d):
#     """
#     Export objective function cost components
#     :param scenario_directory:
#     :param subproblem:
#     :param stage:
#     :param m:
#     The Pyomo abstract model
#     :param d:
#     Dynamic components
#     :return:
#     Nothing
#     """
#     print("Exporting total cost components")
#     print(d.total_cost_components)
#     with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
#               "system_costs.csv"), "w", newline="") as f:
#         writer = csv.writer(f)
#         components = getattr(d, total_cost_components)
#         writer.writerow(components)
#         writer.writerow((value(getattr(m, c)) for c in components))


# Database
###############################################################################

# def import_results_into_database(
#         scenario_id, subproblem, stage, c, db, results_directory, quiet
# ):
#     """
#
#     :param scenario_id:
#     :param c:
#     :param db:
#     :param results_directory:
#     :param quiet:
#     :return:
#     """
#     # Fuel burned by project and timepoint
#     if not quiet:
#         print("results system cost")
#     # Delete prior results and create temporary import table for ordering
#     setup_results_import(
#         conn=db, cursor=c,
#         table="results_system_costs",
#         scenario_id=scenario_id, subproblem=subproblem, stage=stage
#     )
#
#     df = pd.read_csv(os.path.join(results_directory, "system_costs.csv"))
#     df['scenario_id'] = scenario_id
#     df['subproblem_id'] = subproblem
#     df['stage_id'] = stage
#     results = df.to_records(index=False)
#
#     # Register numpy types with sqlite, so that they are properly inserted
#     # from pandas dataframes
#     # https://stackoverflow.com/questions/38753737/inserting-numpy-integer-types-into-sqlite-with-python3
#     sqlite3.register_adapter(np.int64, lambda val: int(val))
#     sqlite3.register_adapter(np.float64, lambda val: float(val))
#
#     insert_sql = """
#         INSERT INTO results_system_costs
#         ({})
#         VALUES ({});
#         """.format(", ".join(df.columns),
#                    ", ".join(["?"] * (len(df.columns))))
#     spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=results)

