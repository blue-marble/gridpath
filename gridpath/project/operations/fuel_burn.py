#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Keep track of fuel burn
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Expression, value, Var, NonNegativeReals, Constraint

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import
from gridpath.auxiliary.dynamic_components import \
    required_operational_modules
from gridpath.auxiliary.auxiliary import load_operational_type_modules
from gridpath.project.common_functions import \
    check_if_linear_horizon_first_timepoint


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Import needed operational modules
    imported_operational_modules = \
        load_operational_type_modules(getattr(d, required_operational_modules))

    # Get fuel burn from operations for each project
    def fuel_burn_rule(mod, g, tmp):
        """
        Emissions from each project based on operational type
        (and whether a project burns fuel)
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type]. \
            fuel_burn_rule(mod, g, tmp, "Project {} has no fuel, so should "
                                        "not be labeled carbonaceous: "
                                        "replace its carbon_cap_zone with "
                                        "'.' in projects.tab.".format(g))

    def startup_fuel_burn_rule(mod, g, tmp):
        """
        Startup fuel burn is defined for some operational types while
        they are zero for others. Get the appropriate expression for each
        generator based on its operational type.
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type].\
            startup_fuel_burn_rule(mod, g, tmp)

    # TODO: remove lambda mod, seems redundant (see e.g. startup fuel burn)?
    m.Operations_Fuel_Burn_MMBtu = Expression(
        m.FUEL_PRJ_OPR_TMPS,
        rule=lambda mod, g, tmp: fuel_burn_rule(mod, g, tmp)
    )

    m.Startup_Fuel_Burn_MMBtu = Expression(
        m.PRJ_OPR_TMPS,
        rule=startup_fuel_burn_rule
    )

    def total_fuel_burn_rule(mod, g, tmp):
        """
        Fuel for power production + fuel for startups
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Operations_Fuel_Burn_MMBtu[g, tmp] \
            + mod.Startup_Fuel_Burn_MMBtu[g, tmp]

    m.Total_Fuel_Burn_MMBtu = Expression(
        m.FUEL_PRJ_OPR_TMPS,
        rule=total_fuel_burn_rule
    )


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export fuel burn results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    The Pyomo abstract model
    :param d:
    Dynamic components
    :return:
    Nothing
    """
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
              "fuel_burn.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "horizon", "timepoint", "timepoint_weight",
             "number_of_hours_in_timepoint", "load_zone", "technology", "fuel",
             "fuel_burn_operations_mmbtu", "fuel_burn_startup_mmbtu",
             "total_fuel_burn_mmbtu"]
        )
        for (p, tmp) in m.FUEL_PRJ_OPR_TMPS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type_project[p]],
                tmp,
                m.tmp_weight[tmp],
                m.hrs_in_tmp[tmp],
                m.load_zone[p],
                m.technology[p],
                m.fuel[p],
                value(m.Operations_Fuel_Burn_MMBtu[p, tmp]),
                value(m.Startup_Fuel_Burn_MMBtu[p, tmp]),
                value(m.Total_Fuel_Burn_MMBtu[p, tmp])
            ])


def import_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    # Fuel burned by project and timepoint
    if not quiet:
        print("project fuel burn")
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_fuel_burn",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "fuel_burn.csv"), "r") as \
            fuel_burn_file:
        reader = csv.reader(fuel_burn_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            timepoint_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[6]
            technology = row[7]
            fuel = row[8]
            fuel_burn_tons = row[9]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                    horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, fuel, fuel_burn_tons)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_fuel_burn{}
         (scenario_id, project, period, subproblem_id, stage_id, 
         horizon, timepoint, timepoint_weight,
         number_of_hours_in_timepoint,
         load_zone, technology, fuel, fuel_burn_mmbtu)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_fuel_burn
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, fuel, fuel_burn_mmbtu)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, fuel, fuel_burn_mmbtu
        FROM temp_results_project_fuel_burn{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
