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
This capacity type describes a supply curve for new shiftable load (DR; demand
response) capacity. The supply curve does not have vintages, i.e. there are
no cost differences for capacity built in different periods. The cost for
new capacity is specified via a piecewise linear function of new capacity
build and constraint (cost is constrained to be greater than or equal to the
function).

The new capacity build variable has units of MWh. We then calculate the
power capacity based on the 'minimum duration' specified for the project,
e.g. if the minimum duration specified is N hours, then the MW capacity will
be the new build in MWh divided by N (the MWh capacity can't be discharged
in less than N hours, as the max power constraint will bind).

This type is a custom implementation for GridPath projects in the California
Integrated Resource Planning proceeding.
"""

from __future__ import division

from builtins import zip
from builtins import range
import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, NonNegativeReals, value, \
    Reals, Expression, Constraint

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets, \
    storage_only_capacity_type_operational_period_sets
from gridpath.auxiliary.validations import write_validation_to_database, \
    validate_missing_inputs, validate_idxs, get_projects


def add_model_components(m, d, subproblem_stage_directory):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`DR_NEW`                                                        |
    |                                                                         |
    | The list of :code:`dr_new` projects being modeled.                      |
    +-------------------------------------------------------------------------+
    | | :code:`DR_NEW_OPR_PRDS`                                               |
    |                                                                         |
    | Two-dimensional set of all :code:`dr_new` projects and their            |
    | operational periods.                                                    |
    +-------------------------------------------------------------------------+
    | | :code:`DR_NEW_PTS`                                                    |
    |                                                                         |
    | Two-dimensional set of all :code:`dr_new` projects and their supply     |
    | curve points.                                                           |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`dr_new_min_duration`                                           |
    | | *Defined over*: :code:`DR_NEW`                                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's duration in hours, i.e. how many hours the load can be    |
    | shifted.                                                                |
    +-------------------------------------------------------------------------+
    | | :code:`dr_new_min_cumulative_new_build_mwh`                           |
    | | *Defined over*: :code:`DR_NEW_OPR_PRDS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The minimum cumulative amount of shiftable load capacity (in MWh) that  |
    | must be built for a project by a certain period.                        |
    +-------------------------------------------------------------------------+
    | | :code:`dr_new_max_cumulative_new_build_mwh`                           |
    | | *Defined over*: :code:`DR_NEW_OPR_PRDS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The maximum cumulative amount of shiftable load capacity (in MWh) that  |
    | must be built for a project by a certain period.                        |
    +-------------------------------------------------------------------------+
    | | :code:`dr_new_supply_curve_slope`                                     |
    | | *Defined over*: :code:`DR_NEW_PTS`                                    |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's slope for each point (section) in the piecewise linear    |
    | supply cost curve, in $ per MWh.                                        |
    +-------------------------------------------------------------------------+
    | | :code:`dr_new_supply_curve_intercept`                                 |
    | | *Defined over*: :code:`DR_NEW_PTS`                                    |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's intercept for each point (section) in the piecewise       |
    | linear supply cost curve, in $.                                         |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`DRNew_Build_MWh`                                               |
    | | *Defined over*: :code:`DR_NEW_OPR_PRDS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Determines how much shiftable load capacity (in MWh) is built in each   |
    | operational period.                                                     |
    +-------------------------------------------------------------------------+
    | | :code:`DRNew_Cost`                                                    |
    | | *Defined over*: :code:`DR_NEW_OPR_PRDS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The cost of new shiftable load capacity in each operational period.     |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`DRNew_Energy_Capacity_MWh`                                     |
    | | *Defined over*: :code:`DR_NEW_OPR_PRDS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's total energy capacity (in MWh) in each operational period |
    | is the sum of the new-built energy capacity in all of the previous      |
    | periods.                                                                |
    +-------------------------------------------------------------------------+
    | | :code:`DRNew_Power_Capacity_MW`                                       |
    | | *Defined over*: :code:`DR_NEW_OPR_PRDS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's total power capacity (in MW) in each operational period   |
    | is equal to the total energy capacity in that period, divided by the    |
    | project's minimum duraiton (in hours).                                  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`DRNew_Cost_Constraint`                                         |
    | | *Defined over*: :code:`DR_NEW_PTS*PERIODS`                            |
    |                                                                         |
    | Ensures that the project's cost in each operational period is larger    |
    | than the calculated piecewise linear cost in each segment. Only one     |
    | segment will bind at a time.                                            |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.DR_NEW = Set()

    m.DR_NEW_OPR_PRDS = Set(
        dimen=2,
        initialize=m.DR_NEW*m.PERIODS
    )

    m.DR_NEW_PTS = Set(
        dimen=2,
        within=m.DR_NEW*list(range(1, 1001))
    )

    # Required Params
    ###########################################################################

    m.dr_new_min_duration = Param(
        m.DR_NEW,
        within=NonNegativeReals
    )

    m.dr_new_min_cumulative_new_build_mwh = Param(
        m.DR_NEW, m.PERIODS,  # TODO: change to DR_NEW_OPR_PRDS?
        within=NonNegativeReals
    )

    m.dr_new_max_cumulative_new_build_mwh = Param(
        m.DR_NEW, m.PERIODS,  # TODO: change to DR_NEW_OPR_PRDS?
        within=NonNegativeReals
    )

    m.dr_new_supply_curve_slope = Param(
        m.DR_NEW_PTS,
        within=NonNegativeReals
    )

    m.dr_new_supply_curve_intercept = Param(
        m.DR_NEW_PTS,
        within=Reals
    )

    # Variables
    ###########################################################################

    m.DRNew_Build_MWh = Var(
        m.DR_NEW, m.PERIODS,  # TODO: change to DR_NEW_OPR_PRDS?
        within=NonNegativeReals
    )

    m.DRNew_Cost = Var(
        m.DR_NEW_OPR_PRDS,
        within=NonNegativeReals
    )

    # Expressions
    ###########################################################################

    m.DRNew_Energy_Capacity_MWh = Expression(
        m.DR_NEW_OPR_PRDS,
        rule=dr_new_energy_capacity_rule
    )

    m.DRNew_Power_Capacity_MW = Expression(
        m.DR_NEW_OPR_PRDS,
        rule=dr_new_power_capacity_rule
    )

    # Constraints
    ###########################################################################

    m.DRNew_Cost_Constraint = Constraint(
        m.DR_NEW_PTS*m.PERIODS,  # TODO: define new set?
        rule=cost_rule
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "DR_NEW_OPR_PRDS",
    )
    # Add to list of sets we'll join to get the final
    # STOR_OPR_PRDS set
    # We'll include shiftable load with storage
    getattr(d, storage_only_capacity_type_operational_period_sets).append(
        "DR_NEW_OPR_PRDS",
    )


# Expression Rules
###############################################################################

def dr_new_energy_capacity_rule(mod, g, p):
    """
    **Expression Name**: DRNew_Energy_Capacity_MWh
    **Defined Over**: DR_NEW_OPR_PRDS

    Total energy capacity in each period is the sum of all new build over the
    previous periods (including the current period).

    Vintages = all periods
    """
    return sum(
        mod.DRNew_Build_MWh[g, prev_p]
        for prev_p in mod.PERIODS if prev_p <= p
    )


def dr_new_power_capacity_rule(mod, g, p):
    """
    **Expression Name**: DRNew_Power_Capacity_MW
    **Defined Over**: DR_NEW_OPR_PRDS

    Vintages = all periods
    """
    return mod.DRNew_Energy_Capacity_MWh[g, p] / mod.dr_new_min_duration[g]


# Constraint Formulation Rules
###############################################################################

def cost_rule(mod, project, point, period):
    """
    **Constraint Name**: DRNew_Cost_Constraint
    **Enforced Over**: m.DR_NEW_PTS*m.PERIODS

    For each segment on the piecewise linear curve, the cost variable is
    constrained to be equal to or larger than the calculated value on the
    curve. Depending on the cumulative build (*DRNew_Energy_Capacity_MWh*)
    only one segment is active at a time. The supply curve is assumed to be
    convex, i.e. costs increase at an increasing rate as you move up the
    curve.
    """
    return mod.DRNew_Cost[project, period] \
        >= mod.dr_new_supply_curve_slope[project, point] \
        * mod.DRNew_Energy_Capacity_MWh[project, period] \
        + mod.dr_new_supply_curve_intercept[project, point]


# Capacity Type Methods
###############################################################################

def capacity_rule(mod, g, p):
    """
    The total power capacity of dr_new operational in period p.
    """
    return mod.DRNew_Power_Capacity_MW[g, p]


def energy_capacity_rule(mod, g, p):
    """
    The total energy capacity of dr_new operational in period p.
    """
    return mod.DRNew_Energy_Capacity_MWh[g, p]


def capacity_cost_rule(mod, g, p):
    """
    """
    return mod.DRNew_Cost[g, p]


def new_capacity_rule(mod, g, p):
    """
    New capacity built at project g in period p.
    """
    return mod.DRNew_Power_Capacity_MW[g, p]


# Input-Output
###############################################################################

def load_module_specific_data(
        m, data_portal, subproblem_stage_directory
):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    def determine_projects():
        projects = list()
        max_fraction = dict()

        df = pd.read_csv(
            os.path.join(scenario_directory, str(subproblem), str(stage),
                         "inputs", "projects.tab"),
            sep="\t",
            usecols=["project", "capacity_type", "minimum_duration_hours"]
        )
        for r in zip(df["project"],
                     df["capacity_type"],
                     df["minimum_duration_hours"]):
            if r[1] == "dr_new":
                projects.append(r[0])
                max_fraction[r[0]] = float(r[2])
            else:
                pass

        return projects, max_fraction

    data_portal.data()["DR_NEW"] = {None: determine_projects()[0]}
    data_portal.data()["dr_new_min_duration"] = determine_projects()[1]

    data_portal.load(
        filename=os.path.join(
            subproblem_stage_directory, "inputs",
            "new_shiftable_load_supply_curve.tab"
        ),
        index=m.DR_NEW_PTS,
        select=("project", "point", "slope", "intercept"),
        param=(m.dr_new_supply_curve_slope,
               m.dr_new_supply_curve_intercept)
    )

    data_portal.load(
        filename=os.path.join(
            subproblem_stage_directory, "inputs",
            "new_shiftable_load_supply_curve_potential.tab"
        ),
        param=(m.dr_new_min_cumulative_new_build_mwh,
               m.dr_new_max_cumulative_new_build_mwh)
    )


def export_module_specific_results(
        subproblem_stage_directory, m, d
):
    """
    Export new DR results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "results",
                           "capacity_dr_new.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "technology", "load_zone",
                         "new_build_mw", "new_build_mwh"])
        for (prj, p) in m.DR_NEW_OPR_PRDS:
            writer.writerow([
                prj,
                p,
                m.technology[prj],
                m.load_zone[prj],
                value(m.DRNew_Build_MWh[prj, p] / m.dr_new_min_duration[prj]),
                value(m.DRNew_Build_MWh[prj, p])
            ])


def summarize_module_specific_results(
    scenario_directory, subproblem_stage_directory, summary_results_file
):
    """
    Summarize new DR capacity results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param summary_results_file:
    :return:
    """

    # Get the results CSV as dataframe
    capacity_results_df = pd.read_csv(
        os.path.join(subproblem_stage_directory,
                     "results", "capacity_dr_new.csv")
    )

    capacity_results_agg_df = capacity_results_df.groupby(
        by=["load_zone", "technology", 'period'],
        as_index=True
    ).sum()

    # Get all technologies with new build DR power OR energy capacity
    new_build_df = pd.DataFrame(
        capacity_results_agg_df[
            (capacity_results_agg_df["new_build_mw"] > 0) |
            (capacity_results_agg_df["new_build_mwh"] > 0)
        ][["new_build_mw", "new_build_mwh"]]
    )

    # Get the power and energy units from the units.csv file
    units_df = pd.read_csv(os.path.join(scenario_directory, "units.csv"),
                           index_col="metric")
    power_unit = units_df.loc["power", "unit"]
    energy_unit = units_df.loc["energy", "unit"]

    # Rename column header
    new_build_df.columns = ["New DR Power Capacity ({})".format(power_unit),
                            "New DR Energy Capacity ({})".format(energy_unit)]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> New DR Capacity <--\n")
        if new_build_df.empty:
            outfile.write("No new DR was built.\n")
        else:
            new_build_df.to_string(outfile, float_format="{:,.2f}".format)
            outfile.write("\n")


# Database
###############################################################################

def get_module_specific_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    if subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID is None:
        raise ValueError("Maximum potential must be specified for new "
                         "shiftable load supply curve projects.")

    c1 = conn.cursor()
    min_max_builds = c1.execute(
        """SELECT project, period, 
        min_cumulative_new_build_mwh, max_cumulative_new_build_mwh
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        LEFT OUTER JOIN
        (SELECT project, period,
        min_cumulative_new_build_mw, min_cumulative_new_build_mwh,
        max_cumulative_new_build_mw, max_cumulative_new_build_mwh
        FROM inputs_project_new_potential
        WHERE project_new_potential_scenario_id = {}) as potential
        USING (project, period) 
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = '{}';""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            "dr_new"
        )
    )

    c2 = conn.cursor()
    supply_curve_count = c2.execute(
        """SELECT project, COUNT(DISTINCT(supply_curve_scenario_id))
        FROM inputs_project_portfolios
        LEFT OUTER JOIN inputs_project_new_cost
        USING (project)
        WHERE project_portfolio_scenario_id = {}
        AND project_new_cost_scenario_id = {}
        AND capacity_type = '{}'
        GROUP BY project;""".format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            "dr_new"
        )
    )

    c3 = conn.cursor()
    supply_curve_id = c3.execute(
        """SELECT DISTINCT supply_curve_scenario_id
        FROM inputs_project_portfolios
        LEFT OUTER JOIN inputs_project_new_cost
        USING (project)
        WHERE project_portfolio_scenario_id = {}
        AND project_new_cost_scenario_id = {}
        AND project = 'Shift_DR';""".format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID
        )
    ).fetchone()[0]

    c4 = conn.cursor()
    supply_curve = c4.execute(
        """SELECT project, supply_curve_point, supply_curve_slope, 
        supply_curve_intercept
        FROM inputs_project_shiftable_load_supply_curve
        WHERE supply_curve_scenario_id = {}""".format(
            supply_curve_id
        )
    )

    return min_max_builds, supply_curve_count, supply_curve_id, supply_curve


def write_module_specific_model_inputs(
        scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    new_shiftable_load_supply_curve_potential.tab and
    new_shiftable_load_supply_curve.tab files

    Max potential is required for this module, so
    PROJECT_NEW_POTENTIAL_SCENARIO_ID can't be NULL

    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    min_max_builds, supply_curve_count, supply_curve_id, supply_curve = \
        get_module_specific_inputs_from_database(
            scenario_id, subscenarios, subproblem, stage, conn)

    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "new_shiftable_load_supply_curve_potential.tab"),
              "w", newline="") as potentials_tab_file:
        writer = csv.writer(potentials_tab_file, delimiter="\t", lineterminator="\n")

        writer.writerow([
            "project", "period",
            "min_cumulative_new_build_mwh", "max_cumulative_new_build_mwh"
        ])

        for row in min_max_builds:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    # Supply curve
    # No supply curve periods for now, so check that we have only specified
    # a single supply curve for all periods in inputs_project_new_cost
    with open(os.path.join(scenario_directory, str(subproblem), str(stage), "inputs",
                           "new_shiftable_load_supply_curve.tab"),
              "w", newline="") as supply_curve_tab_file:
        writer = csv.writer(supply_curve_tab_file, delimiter="\t", lineterminator="\n")

        writer.writerow([
            "project", "point", "slope", "intercept"
        ])

        for proj in supply_curve_count:
            project = proj[0]
            if proj[1] > 1:
                raise ValueError("Only a single supply curve can be specified "
                                 "for project {} because no vintages have "
                                 "been implemented for "
                                 "'dr_new' capacity "
                                 "type.".format(project))
            else:

                for row in supply_curve:
                    writer.writerow(row)


def import_module_specific_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    # Capacity
    if not quiet:
        print("project new DR")
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_project_capacity_dr_new",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory, "capacity_dr_new.csv"),
              "r") as capacity_file:
        reader = csv.reader(capacity_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            technology = row[2]
            load_zone = row[3]
            new_build_mw = row[4]
            new_build_mwh = row[5]

            results.append(
                (scenario_id, project, period, subproblem, stage,
                 technology, load_zone, new_build_mw, new_build_mwh)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_project_capacity_dr_new{}
        (scenario_id, project, period, subproblem_id, stage_id,
        technology, load_zone, new_build_mw, new_build_mwh)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""".format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_project_capacity_dr_new
        (scenario_id, project, period, subproblem_id, stage_id, 
        technology, load_zone, new_build_mw, new_build_mwh)
        SELECT
        scenario_id, project, period, subproblem_id, stage_id, 
        technology, load_zone, new_build_mw, new_build_mwh
        FROM temp_results_project_capacity_dr_new{}
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


# Validation
###############################################################################

def validate_module_specific_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    min_max_builds, supply_curve_count, supply_curve_id, supply_curve = \
        get_module_specific_inputs_from_database(
            scenario_id, subscenarios, subproblem, stage, conn)
    projects = get_projects(conn, scenario_id, subscenarios, "capacity_type", "dr_new")

    # Convert input data into pandas DataFrame
    df = cursor_to_df(min_max_builds)
    df_sc = cursor_to_df(supply_curve)

    dr_projects = df_sc["project"].unique()

    # Check for missing project potential inputs
    cols = ["min_cumulative_new_build_mwh", "max_cumulative_new_build_mwh"]
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_new_potential",
        severity="High",
        errors=validate_missing_inputs(df, cols)
    )

    # Check for missing supply curve inputs
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_shiftable_load_supply_curve",
        severity="High",
        errors=validate_idxs(actual_idxs=dr_projects,
                             req_idxs=projects,
                             idx_label="project")
    )

