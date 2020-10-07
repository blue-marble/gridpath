#!/usr/bin/env python
# Copyright 2016-2020 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The **gridpath.project.operations.costs** module is a project-level
module that adds to the formulation components that describe the
operations-related costs of projects (e.g. variable O&M costs, fuel costs,
startup and shutdown costs).

For the purpose, this module calls the respective method from the
operational type modules.
"""

import csv
import os.path
from pyomo.environ import Set, Var, Expression, Constraint, \
    NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import get_required_subtype_modules_from_projects_file
from gridpath.project.operations.common_functions import \
    load_operational_type_modules
from gridpath.auxiliary.db_interface import setup_results_import
import gridpath.project.operations.operational_types as op_type


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

     +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`VAR_OM_COST_SIMPLE_PRJ_OPR_TMPS`                               |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | The two-dimensional set of projects for which a simple variable O&M     |
    | cost is specified and their operational timepoints.                     |
    +-------------------------------------------------------------------------+
    | | :code:`VAR_OM_COST_CURVE_PRJS_OPR_TMPS_SGMS`                          |
    |                                                                         |
    | The three-dimensional set of projects for which a VOM cost curve is     |
    | specified along with the VOM curve segments and the project             |
    | operational timepoints.                                                 |
    +-------------------------------------------------------------------------+
    | | :code:`VAR_OM_COST_CURVE_PRJS_OPR_TMPS`                               |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | The two-dimensional set of projects for which a VOM cost curve is       |
    | specified along with their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`VAR_OM_COST_ALL_PRJS_OPR_TMPS`                                 |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | The two-dimensional set of projects for which either or both a simple   |
    | VOM or a VOM curve is specified along with their operational            |
    | timepoints.                                                             |
    +-------------------------------------------------------------------------+
    | | :code:`STARTUP_COST_PRJ_OPR_TMPS`                                     |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | The two-dimensional set of projects for which a startup cost is         |
    | specified along with their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`SHUTDOWN_COST_PRJ_OPR_TMPS`                                    |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | The two-dimensional set of projects for which a shutdown cost curve is  |
    | specified along with their operational timepoints.                      |
    +-------------------------------------------------------------------------+
    | | :code:`VIOL_ALL_PRJ_OPR_TMPS`                                         |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | The two-dimensional set of projects for which an operational constraint |
    | can be violated along with their operational timepoints.                |
    +-------------------------------------------------------------------------+
    | | :code:`CURTAILMENT_COST_PRJ_OPR_TMPS`                                 |
    | | *Within*: :code:`PRJ_OPR_TMPS`                                        |
    |                                                                         |
    | The two-dimensional set of projects for which an curtailment costs are  |
    | incurred along with their operational timepoints.                       |
    +-------------------------------------------------------------------------+

    |                                                                         |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`Variable_OM_Curve_Cost`                                        |
    | | *Defined over*: :code:`VAR_OM_COST_CURVE_PRJS_OPR_TMPS`               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Variable cost in each operational timepoint of projects with a VOM cost |
    | curve.                                                                  |
    +-------------------------------------------------------------------------+

    |                                                                         |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`Variable_OM_Curve_Constraint`                                  |
    | | *Defined over*: :code:`VAR_OM_COST_CURVE_PRJS_OPR_TMPS_SGMS`          |
    |                                                                         |
    | Determines variable cost from the project in each timepoint based on    |
    | its VOM curve.                                                          |
    +-------------------------------------------------------------------------+

    |                                                                         |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Variable_OM_Cost`                                              |
    | | *Defined over*: :code:`VAR_OM_COST_ALL_PRJS_OPR_TMPS`                 |
    |                                                                         |
    | This is the variable cost incurred in each operational timepoints for   |
    | projects for which either a simple VOM or a VOM curve is specified.     |
    | If both are specified, the two are additive. We obtain the simple VOM   |
    | by calling the *variable_om_cost_rule* method of a project's            |
    | *operational_type* module. We obtain the VOM curve cost by calling the  |
    | *variable_om_cost_by_ll_rule* method of a project's operational type,   |
    | using that to create the *Variable_OM_Curve_Constraint* on the          |
    | Variable_OM_Curve_Cost variable, and the using the variable in this     |
    | expression.                                                             |
    +-------------------------------------------------------------------------+
    | | :code:`Fuel_Cost`                                                     |
    | | *Defined over*: :code:`FUEL_PRJ_OPR_TMPS`                             |
    |                                                                         |
    | This expression defines the fuel cost of a project in all of its        |
    | operational timepoints. We obtain the expression by calling the         |
    | *fuel_cost_rule* method of a project's *operational_type* module.       |
    +-------------------------------------------------------------------------+
    | | :code:`Startup_Cost`                                                  |
    | | *Defined over*: :code:`STARTUP_COST_PRJ_OPR_TMPS`                     |
    |                                                                         |
    | This expression defines the startup cost of a project in all of its     |
    | operational timepoints. We obtain the expression by calling the         |
    | *startup_cost_rule* method of a project's *operational_type* module.    |
    +-------------------------------------------------------------------------+
    | | :code:`Shutdown_Cost`                                                 |
    | | *Defined over*: :code:`SHUTDOWN_COST_PRJ_OPR_TMPS`                    |
    |                                                                         |
    | This expression defines the shutdown cost of a project in all of its    |
    | operational timepoints. We obtain the expression by calling the         |
    | *shutdown_cost_rule* method of a project's *operational_type* module.   |
    +-------------------------------------------------------------------------+
    | | :code:`Operational_Violation_Cost`                                    |
    | | *Defined over*: :code:`VIOL_ALL_PRJ_OPR_TMPS`                         |
    |                                                                         |
    | This expression defines the operational constraint violation cost of a  |
    | project in all of its operational timepoints. We obtain the expression  |
    | by calling the *operational_violation_cost_rule* method of a project's  |
    | *operational_type* module.                                              |
    +-------------------------------------------------------------------------+
    | | :code:`Curtailment_Cost`                                              |
    | | *Defined over*: :code:`CURTAILMENT_COST_PRJ_OPR_TMPS`                 |
    |                                                                         |
    | This expression defines the curtailment cost of a project in all of its |
    | operational timepoints. We obtain the expression by calling the         |
    | *curtailment_cost_rule* method of a project's *operational_type* module.|
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

    m.VAR_OM_COST_SIMPLE_PRJ_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: [(p, tmp) for (p, tmp) in mod.PRJ_OPR_TMPS
                          if p in mod.VAR_OM_COST_SIMPLE_PRJS]
    )

    m.VAR_OM_COST_CURVE_PRJS_OPR_TMPS_SGMS = Set(
        dimen=3,
        initialize=lambda mod: list(
            set((g, tmp, s) for (g, tmp) in mod.PRJ_OPR_TMPS
                for _g, p, s in mod.VAR_OM_COST_CURVE_PRJS_PRDS_SGMS
                if g == _g and mod.period[tmp] == p)
        )
    )

    m.VAR_OM_COST_CURVE_PRJS_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: list(
            set((g, tmp) for (g, tmp, s)
                in mod.VAR_OM_COST_CURVE_PRJS_OPR_TMPS_SGMS)
        )
    )

    # All VOM projects
    m.VAR_OM_COST_ALL_PRJS_OPR_TMPS = Set(
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: list(
            set(mod.VAR_OM_COST_SIMPLE_PRJ_OPR_TMPS
                | mod.VAR_OM_COST_CURVE_PRJS_OPR_TMPS)
        )
    )

    m.STARTUP_COST_PRJ_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: [(p, tmp) for (p, tmp) in mod.PRJ_OPR_TMPS
                          if p in mod.STARTUP_COST_PRJS]
    )

    m.SHUTDOWN_COST_PRJ_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: [(p, tmp) for (p, tmp) in mod.PRJ_OPR_TMPS
                          if p in mod.SHUTDOWN_COST_PRJS]
    )

    m.VIOL_ALL_PRJ_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: [(p, tmp) for (p, tmp) in mod.PRJ_OPR_TMPS
                          if p in mod.VIOL_ALL_PRJS]
    )

    m.CURTAILMENT_COST_PRJ_OPR_TMPS = Set(
        dimen=2,
        within=m.PRJ_OPR_TMPS,
        initialize=lambda mod: [(p, tmp) for (p, tmp) in mod.PRJ_OPR_TMPS
                          if p in mod.CURTAILMENT_COST_PRJS]
    )

    # Variables
    ###########################################################################

    m.Variable_OM_Curve_Cost = Var(
        m.VAR_OM_COST_CURVE_PRJS_OPR_TMPS,
        within=NonNegativeReals
    )

    # Constraints
    ###########################################################################

    def variable_om_cost_curve_constraint_rule(mod, prj, tmp, s):
        """
        **Constraint Name**: GenCommitBin_Variable_OM_Constraint
        **Enforced Over**: GEN_COMMIT_BIN_VOM_PRJS_OPR_TMPS_SGMS

        Variable O&M cost by loading level is set by piecewise linear
        representation of the input/output curve (variable O&M cost vs.loading
        level).

        Note: we assume that when projects are derated for availability, the
        input/output curve is derated by the same amount. The implicit
        assumption is that when a generator is de-rated, some of its units
        are out rather than it being forced to run below minimum stable level
        at very costly operating points.
        """
        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type],
                   "variable_om_cost_by_ll_rule"):
            var_cost_by_ll = imported_operational_modules[gen_op_type]. \
                variable_om_cost_by_ll_rule(mod, prj, tmp, s)
        else:
            var_cost_by_ll = \
                op_type.variable_om_cost_by_ll_rule(mod, prj, tmp, s)

        return mod.Variable_OM_Curve_Cost[prj, tmp] \
            >= var_cost_by_ll

    m.Variable_OM_Curve_Constraint = Constraint(
        m.VAR_OM_COST_CURVE_PRJS_OPR_TMPS_SGMS,
        rule=variable_om_cost_curve_constraint_rule
    )

    # Expressions
    ###########################################################################

    def variable_om_cost_rule(mod, prj, tmp):
        """
        **Expression Name**: Variable_OM_Cost
        **Defined Over**: VAR_OM_COST_ALL_PRJS_OPR_TMPS

        This is the variable cost incurred in each operational timepoints for
        projects for which either a simple VOM or a VOM curve is specified.
        If both are specified, the two are additive.
        """

        # Simple VOM cost
        gen_op_type = mod.operational_type[prj]
        if prj in mod.VAR_OM_COST_SIMPLE_PRJS:
            if hasattr(imported_operational_modules[gen_op_type],
                       "variable_om_cost_rule"):
                var_cost_simple = imported_operational_modules[gen_op_type]. \
                    variable_om_cost_rule(mod, prj, tmp)
            else:
                var_cost_simple = op_type.variable_om_cost_rule(mod, prj, tmp)
        else:
            var_cost_simple = 0

        # VOM curve cost
        if prj in mod.VAR_OM_COST_CURVE_PRJS:
            var_cost_curve = mod.Variable_OM_Curve_Cost[prj, tmp]
        else:
            var_cost_curve = 0

        # The two are additive
        return var_cost_simple + var_cost_curve

    m.Variable_OM_Cost = Expression(
        m.VAR_OM_COST_ALL_PRJS_OPR_TMPS,
        rule=variable_om_cost_rule
    )

    def fuel_cost_rule(mod, prj, tmp):
        """
        **Expression Name**: Fuel_Cost
        **Defined Over**: FUEL_PRJS_OPR_TMPS
        """
        return mod.Total_Fuel_Burn_MMBtu[prj, tmp] * \
            mod.fuel_price_per_mmbtu[
                mod.fuel[prj],
                mod.period[tmp],
                mod.month[tmp]
            ]

    m.Fuel_Cost = Expression(
        m.FUEL_PRJ_OPR_TMPS,
        rule=fuel_cost_rule
    )

    def startup_cost_rule(mod, prj, tmp):
        """
        Startup costs are defined for some operational types while they are
        zero for others. Get the appropriate expression for each generator
        based on its operational type.
        """
        gen_op_type = mod.operational_type[prj]

        if prj in mod.STARTUP_COST_SIMPLE_PRJS:
            if hasattr(imported_operational_modules[gen_op_type],
                       "startup_cost_simple_rule"):
                startup_cost_simple = \
                    imported_operational_modules[gen_op_type]. \
                    startup_cost_simple_rule(mod, prj, tmp)
            else:
                startup_cost_simple = \
                    op_type.startup_cost_simple_rule(mod, prj, tmp)
        else:
            startup_cost_simple = 0

        if prj in mod.STARTUP_BY_ST_PRJS:
            if hasattr(imported_operational_modules[gen_op_type],
                       "startup_cost_by_st_rule"):
                startup_cost_by_st = \
                    imported_operational_modules[gen_op_type]. \
                    startup_cost_by_st_rule(mod, prj, tmp)
            else:
                startup_cost_by_st = \
                    op_type.startup_cost_by_st_rule(mod, prj, tmp)
        else:
            startup_cost_by_st = 0

        return startup_cost_simple + startup_cost_by_st

    m.Startup_Cost = Expression(
        m.STARTUP_COST_PRJ_OPR_TMPS,
        rule=startup_cost_rule
    )

    def shutdown_cost_rule(mod, prj, tmp):
        """
        Shutdown costs are defined for some operational types while they are
        zero for others. Get the appropriate expression for each generator
        based on its operational type.
        """
        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type],
                   "shutdown_cost_rule"):
            return imported_operational_modules[gen_op_type]. \
                shutdown_cost_rule(mod, prj, tmp)
        else:
            return op_type.shutdown_cost_rule(mod, prj, tmp)

    m.Shutdown_Cost = Expression(
        m.SHUTDOWN_COST_PRJ_OPR_TMPS,
        rule=shutdown_cost_rule
    )

    def operational_violation_cost_rule(mod, prj, tmp):
        """
        Get any operational constraint violation costs.
        """
        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type],
                   "operational_violation_cost_rule"):
            return imported_operational_modules[gen_op_type]. \
                operational_violation_cost_rule(mod, prj, tmp)
        else:
            return op_type.operational_violation_cost_rule(mod, prj, tmp)

    m.Operational_Violation_Cost = Expression(
        m.VIOL_ALL_PRJ_OPR_TMPS,
        rule=operational_violation_cost_rule
    )

    def curtailment_cost_rule(mod, prj, tmp):
        """
        Curtailment costs are defined for some operational types while they are
        zero for others. Get the appropriate expression for each generator
        based on its operational type.
        """
        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type],
                   "curtailment_cost_rule"):
            return imported_operational_modules[gen_op_type]. \
                curtailment_cost_rule(mod, prj, tmp)
        else:
            return op_type.curtailment_cost_rule(mod, prj, tmp)

    m.Curtailment_Cost = Expression(
        m.CURTAILMENT_COST_PRJ_OPR_TMPS,
        rule=curtailment_cost_rule
    )


# Input-Output
###############################################################################

def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export operations results. Note: fuel cost includes startup fuel as well
    if applicable, in which case this is startup fuel cost is additional to
    the startup costs reported here.
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
    with open(os.path.join(scenario_directory, str(subproblem), str(stage),
                           "results",
                           "costs_operations.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["project", "period", "horizon", "timepoint", "timepoint_weight",
             "number_of_hours_in_timepoint", "load_zone", "technology",
             "variable_om_cost", "fuel_cost", "startup_cost", "shutdown_cost",
             "operational_violation_cost", "curtailment_cost"]
        )
        for (p, tmp) in m.PRJ_OPR_TMPS:
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp, m.balancing_type_project[p]],
                tmp,
                m.tmp_weight[tmp],
                m.hrs_in_tmp[tmp],
                m.load_zone[p],
                m.technology[p],
                value(m.Variable_OM_Cost[p, tmp])
                if p in m.VAR_OM_COST_ALL_PRJS else None,
                value(m.Fuel_Cost[p, tmp]) if p in m.FUEL_PRJS else None,
                value(m.Startup_Cost[p, tmp])
                if p in m.STARTUP_COST_PRJS else None,
                value(m.Shutdown_Cost[p, tmp])
                if p in m.SHUTDOWN_COST_PRJS else None,
                value(m.Operational_Violation_Cost[p, tmp])
                if p in m.VIOL_ALL_PRJ_OPR_TMPS else None,
                value(m.Curtailment_Cost[p, tmp])
                if p in m.CURTAILMENT_COST_PRJS else None,
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
    if not quiet:
        print("project costs operations")

    # costs_operations.csv
    # Delete prior results and create temporary import table for ordering
    setup_results_import(conn=db, cursor=c,
                         table="results_project_costs_operations",
                         scenario_id=scenario_id, subproblem=subproblem,
                         stage=stage)

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory, "costs_operations.csv"),
              "r") as dispatch_file:
        reader = csv.reader(dispatch_file)

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
            variable_om_cost = row[8]
            fuel_cost = row[9]
            startup_cost = row[10]
            shutdown_cost = row[11]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 horizon, timepoint, timepoint_weight,
                 number_of_hours_in_timepoint, load_zone, technology,
                 variable_om_cost, fuel_cost, startup_cost, shutdown_cost)
            )

    insert_temp_sql = """
        INSERT INTO
        temp_results_project_costs_operations{}
        (scenario_id, project, period, subproblem_id, stage_id,
        horizon, timepoint, timepoint_weight,
        number_of_hours_in_timepoint, load_zone, technology, 
        variable_om_cost, fuel_cost, startup_cost, shutdown_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""".format(
        scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO 
        results_project_costs_operations
        (scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint, load_zone, technology, 
        variable_om_cost, fuel_cost, startup_cost, shutdown_cost)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        horizon, timepoint, timepoint_weight, 
        number_of_hours_in_timepoint, load_zone, technology, 
        variable_om_cost, fuel_cost, startup_cost, shutdown_cost
        FROM temp_results_project_costs_operations{}
        ORDER BY scenario_id, project, subproblem_id, stage_id, timepoint;
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


def process_results(db, c, scenario_id, subscenarios, quiet):
    """
    Aggregate costs by zone and period
    TODO: by technology too?
    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
        print("aggregate costs")

    # Delete old results
    del_sql = """
        DELETE FROM results_project_costs_operations_agg
        WHERE scenario_id = ?
        """
    spin_on_database_lock(conn=db, cursor=c, sql=del_sql,
                          data=(scenario_id,),
                          many=False)

    # Aggregate operational costs by period and load zone
    agg_sql = """
        INSERT INTO results_project_costs_operations_agg
        (scenario_id, subproblem_id, stage_id, period, 
        load_zone, spinup_or_lookahead, 
        variable_om_cost, fuel_cost, startup_cost, shutdown_cost)
        SELECT scenario_id, subproblem_id, stage_id, period, load_zone,
        spinup_or_lookahead,
        SUM(fuel_cost * timepoint_weight * number_of_hours_in_timepoint) 
        AS fuel_cost,
        SUM(variable_om_cost * timepoint_weight * number_of_hours_in_timepoint) 
        AS variable_om_cost,
        SUM(startup_cost * timepoint_weight) AS startup_cost,
        SUM(shutdown_cost * timepoint_weight) AS shutdown_cost
        FROM results_project_costs_operations
        WHERE scenario_id = ?
        GROUP BY subproblem_id, stage_id, period, load_zone, spinup_or_lookahead
        ORDER BY subproblem_id, stage_id, period, load_zone, spinup_or_lookahead
        ;"""
    spin_on_database_lock(conn=db, cursor=c, sql=agg_sql,
                          data=(scenario_id,),
                          many=False)
