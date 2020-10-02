#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module keeps track of fuel burn for each project. Fuel burn consists of
both operational fuel burn for power production, and startup fuel burn (if
applicable).
"""

import csv
import os.path
from pyomo.environ import Set, Var, Expression, Constraint, \
    NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.auxiliary import get_required_subtype_modules_from_projects_file, \
    load_operational_type_modules
import gridpath.project.operations.operational_types as op_type


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`FUEL_PRJ_OPR_TMPS`                                             |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | The two-dimensional set of projects for which a fuel is specified and   |
    | their operational timepoints.                                           |
    +-------------------------------------------------------------------------+
    | | :code:`HR_CURVE_PRJS_OPR_TMPS_SGMS`                                   |
    |                                                                         |
    | The three-dimensional set of projects for which a heat rate curve is    |
    | specified along with the heat rate curve segments and the project       |
    | operational timepoints.                                                 |
    +-------------------------------------------------------------------------+
    | | :code:`HR_CURVE_PRJS_OPR_TMPS`                                        |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | The two-dimensional set of projects for which a heat rate curve is      |
    | specified along with their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`STARTUP_FUEL_PRJ_OPR_TMPS`                                     |
    | | *Within*: :code:`FUEL_PRJ_OPR_TMPS`                                   |
    |                                                                         |
    | The two-dimensional set of projects for which startup fuel burn is      |
    | specified and their operational timepoints.                             |
    +-------------------------------------------------------------------------+

    |                                                                         |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`HR_Curve_Prj_Fuel_Burn`                                        |
    | | *Defined over*: :code:`HR_CURVE_PRJS_OPR_TMPS`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Fuel burn in each operational timepoint of projects with a heat rate    |
    | curve.                                                                  |
    +-------------------------------------------------------------------------+

    |                                                                         |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`HR_Curve_Prj_Fuel_Burn_Constraint`                             |
    | | *Defined over*: :code:`HR_CURVE_PRJS_OPR_TMPS_SGMS`                   |
    |                                                                         |
    | Determines fuel burn from the project in each timepoint based on its    |
    | heat rate curve.                                                        |
    +-------------------------------------------------------------------------+

    |                                                                         |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Operations_Fuel_Burn_MMBtu`                                    |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | This expression describes each project's operational fuel consumption   |
    | (in MMBtu) in all operational timepoints. We obtain it by calling the   |
    | *fuel_burn_rule* method in the relevant *operational_type*. This does   |
    | not include fuel burn for startups, which has a separate expression.    |
    +-------------------------------------------------------------------------+
    | | :code:`Startup_Fuel_Burn_MMBtu`                                       |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | This expression describes each project's startup fuel consumption       |
    | (in MMBtu) in all operational timepoints. We obtain it by calling the   |
    | *startup_fuel_burn_rule* method in the relevant *operational_type*.     |
    | Only operational types with commitment variables can have startup fuel  |
    | burn (for others it will always return zero).                           |
    +-------------------------------------------------------------------------+
    | | :code:`Total_Fuel_Burn_MMBtu`                                         |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | Total fuel burn is the sum of operational fuel burn for power           |
    | production and startup fuel burn.                                       |
    +-------------------------------------------------------------------------+

    """

    # Dynamic Inputs
    ###########################################################################

    required_operational_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, which_type="operational_type"
    )

    imported_operational_modules = load_operational_type_modules(
        required_operational_modules
    )

    # Sets
    ###########################################################################

    m.FUEL_PRJ_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        rule=lambda mod: [(p, tmp) for (p, tmp) in mod.PRJ_OPR_TMPS
                          if p in mod.FUEL_PRJS]
    )

    m.HR_CURVE_PRJS_OPR_TMPS_SGMS = Set(
        dimen=3,
        rule=lambda mod:
        set((g, tmp, s) for (g, tmp) in mod.PRJ_OPR_TMPS
            for _g, p, s in mod.HR_CURVE_PRJS_PRDS_SGMS
            if g == _g and mod.period[tmp] == p)
    )

    m.HR_CURVE_PRJS_OPR_TMPS = Set(
        dimen=2,
        within=m.FUEL_PRJ_OPR_TMPS,
        rule=lambda mod:
        set((g, tmp)
            for (g, tmp, s) in mod.HR_CURVE_PRJS_OPR_TMPS_SGMS)
    )

    m.STARTUP_FUEL_PRJ_OPR_TMPS = Set(
        dimen=2,
        within=m.FUEL_PRJ_OPR_TMPS,
        rule=lambda mod: [(p, tmp) for (p, tmp) in mod.FUEL_PRJ_OPR_TMPS
                          if p in mod.STARTUP_FUEL_PRJS]
    )

    # Variables
    ###########################################################################

    m.HR_Curve_Prj_Fuel_Burn = Var(
        m.HR_CURVE_PRJS_OPR_TMPS,
        within=NonNegativeReals
    )

    # Constraints
    ###########################################################################

    def fuel_burn_by_ll_constraint_rule(mod, prj, tmp, s):
        """
        **Constraint Name**: HR_Curve_Prj_Fuel_Burn_Constraint
        **Enforced Over**: HR_CURVE_PRJS_OPR_TMPS_SGMS

        Fuel burn is set by piecewise linear representation of input/output
        curve.

        Note: we assume that when projects are de-rated for availability, the
        input/output curve is de-rated by the same amount. The implicit
        assumption is that when a generator is de-rated, some of its units
        are out rather than it being forced to run below minimum stable level
        at very inefficient operating points.
        """
        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type],
                   "fuel_burn_by_ll_rule"):
            fuel_burn_by_ll = imported_operational_modules[gen_op_type]. \
                fuel_burn_by_ll_rule(mod, prj, tmp, s)
        else:
            fuel_burn_by_ll = \
                op_type.fuel_burn_by_ll_rule(mod, prj, tmp, s)

        return mod.HR_Curve_Prj_Fuel_Burn[prj, tmp] >= fuel_burn_by_ll

    m.HR_Curve_Prj_Fuel_Burn_Constraint = Constraint(
        m.HR_CURVE_PRJS_OPR_TMPS_SGMS,
        rule=fuel_burn_by_ll_constraint_rule
    )

    # Expressions
    ###########################################################################

    def fuel_burn_rule(mod, prj, tmp):
        """
        Emissions from each project based on operational type
        (and whether a project burns fuel)
        """
        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type],
                   "fuel_burn_rule"):
            fuel_burn_simple = imported_operational_modules[gen_op_type]. \
                fuel_burn_rule(mod, prj, tmp)
        else:
            fuel_burn_simple = op_type.fuel_burn_rule(mod, prj, tmp)

        return fuel_burn_simple \
            + (mod.HR_Curve_Prj_Fuel_Burn[prj, tmp] if prj in mod.HR_CURVE_PRJS
               else 0)

    m.Operations_Fuel_Burn_MMBtu = Expression(
        m.FUEL_PRJ_OPR_TMPS,
        rule=fuel_burn_rule
    )

    def startup_fuel_burn_rule(mod, prj, tmp):
        """
        Startup fuel burn is defined for some operational types while
        they are zero for others. Get the appropriate expression for each
        generator based on its operational type.
        """
        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type],
                   "startup_fuel_burn_rule"):
            return imported_operational_modules[gen_op_type]. \
                startup_fuel_burn_rule(mod, prj, tmp)
        else:
            return op_type.startup_fuel_burn_rule(mod, prj, tmp)

    m.Startup_Fuel_Burn_MMBtu = Expression(
        m.STARTUP_FUEL_PRJ_OPR_TMPS,
        rule=startup_fuel_burn_rule
    )

    def total_fuel_burn_rule(mod, g, tmp):
        """
        *Expression Name*: :code:`Total_Fuel_Burn_MMBtu`
        *Defined Over*: :code:`PRJ_OPR_TMPS`

        Total fuel burn is the sum of operational fuel burn (power production)
        and startup fuel burn.
        """
        return mod.Operations_Fuel_Burn_MMBtu[g, tmp] \
            + (mod.Startup_Fuel_Burn_MMBtu[g, tmp]
               if g in mod.STARTUP_FUEL_PRJS
               else 0)

    m.Total_Fuel_Burn_MMBtu = Expression(
        m.FUEL_PRJ_OPR_TMPS,
        rule=total_fuel_burn_rule
    )

# Input-Output
###############################################################################

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
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
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
                value(m.Startup_Fuel_Burn_MMBtu[p, tmp])
                if p in m.STARTUP_FUEL_PRJS else None,
                value(m.Total_Fuel_Burn_MMBtu[p, tmp])
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
    with open(os.path.join(results_directory, "fuel_burn.csv"),
              "r") as fuel_burn_file:
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
            opr_fuel_burn_tons = row[9]
            startup_fuel_burn_tons = row[10]
            total_fuel_burn = row[11]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                    horizon, timepoint, timepoint_weight,
                    number_of_hours_in_timepoint,
                    load_zone, technology, fuel, opr_fuel_burn_tons,
                    startup_fuel_burn_tons, total_fuel_burn)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_fuel_burn{}
         (scenario_id, project, period, subproblem_id, stage_id, 
         horizon, timepoint, timepoint_weight,
         number_of_hours_in_timepoint,
         load_zone, technology, fuel, operations_fuel_burn_mmbtu, 
         startup_fuel_burn_mmbtu, total_fuel_burn_mmbtu)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_fuel_burn
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, fuel, operations_fuel_burn_mmbtu, 
         startup_fuel_burn_mmbtu, total_fuel_burn_mmbtu)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, number_of_hours_in_timepoint,
        load_zone, technology, fuel, operations_fuel_burn_mmbtu, 
         startup_fuel_burn_mmbtu, total_fuel_burn_mmbtu
        FROM temp_results_project_fuel_burn{}
         ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
         """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)
