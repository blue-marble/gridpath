#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Carbon emissions from each carbonaceous project.
"""

from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
from pyomo.environ import Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import, \
    load_operational_type_modules
from gridpath.auxiliary.dynamic_components import \
    required_operational_modules
import gridpath.project.operations.operational_types as op_type


def add_model_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Project_Carbon_Emissions`                                      |
    | | *Defined over*: :code:`PRJ_OPR_TMPS`                                  |
    |                                                                         |
    | The project's carbon emissions for each timepoint in which the project  |
    | could be operational. Note that this is an emissions *RATE* (per hour)  |
    | and should be multiplied by the timepoint duration and timepoint        |
    | weight to get the total emissions amount during that timepoint.         |
    +-------------------------------------------------------------------------+

    """

    # Dynamic Components
    ###########################################################################

    imported_operational_modules = load_operational_type_modules(
        getattr(d, required_operational_modules)
    )

    # Expressions
    ###########################################################################

    def carbon_emissions_rule(mod, prj, tmp):
        """
        Emissions from each project based on operational type
        (and whether a project burns fuel). Multiply by the timepoint duration
        and timepoint weight to get the total emissions amount.
        """

        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type],
                   "carbon_emissions_rule"):
            return imported_operational_modules[gen_op_type]. \
                carbon_emissions_rule(mod, prj, tmp)
        else:
            return op_type.carbon_emissions_rule(mod, prj, tmp)

    m.Project_Carbon_Emissions = Expression(
        m.PRJ_OPR_TMPS,
        rule=carbon_emissions_rule
    )


# Input-Output
###############################################################################

def export_results(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "carbon_emissions_by_project.csv"),
              "w", newline="") as carbon_emissions_results_file:
        writer = csv.writer(carbon_emissions_results_file)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "timepoint_weight",
                         "number_of_hours_in_timepoint", "load_zone",
                         "carbon_emissions_tons"])
        for (p, tmp) in m.PRJ_OPR_TMPS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type_project[p]],
                tmp,
                m.tmp_weight[tmp],
                m.hrs_in_tmp[tmp],
                m.load_zone[p],
                value(m.Project_Carbon_Emissions[p, tmp])
            ])


# Database
###############################################################################

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
    # Carbon emission imports by project and timepoint
    if not quiet:
        print("project carbon emissions")

    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_carbon_emissions",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "carbon_emissions_by_project.csv"),
              "r") as emissions_file:
        reader = csv.reader(emissions_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            timepoint_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[6]
            carbon_emissions_tons = row[7]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 horizon, timepoint, timepoint_weight,
                 number_of_hours_in_timepoint,
                 load_zone, carbon_emissions_tons)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_carbon_emissions{}
         (scenario_id, project, period, subproblem_id, stage_id,
         horizon, timepoint, timepoint_weight,
         number_of_hours_in_timepoint,
         load_zone, carbon_emission_tons)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_carbon_emissions
        (scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, carbon_emission_tons)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, carbon_emission_tons
        FROM temp_results_project_carbon_emissions{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
