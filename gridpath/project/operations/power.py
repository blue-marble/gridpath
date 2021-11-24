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
The **gridpath.project.capacity.capacity** module is a project-level
module that adds to the formulation components that describe the amount of
power that a project is providing in each study timepoint.
"""

from __future__ import division
from __future__ import print_function

from builtins import next
from builtins import str
import csv
import os.path
import pandas as pd
from pyomo.environ import Expression, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import get_required_subtype_modules_from_projects_file
from gridpath.project.operations.common_functions import load_operational_type_modules
import gridpath.project.operations.operational_types as op_type_init


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Power_Provision_MW`                                            |
    | | *Defined over*: :code:`PRJ_OPR_TMPS`                                  |
    |                                                                         |
    | Defines the power a project is producing in each of its operational     |
    | timepoints. The exact formulation of the expression depends             |
    | on the project's *operational_type*. For each project, we call its      |
    | *capacity_type* module's *power_provision_rule* method in order to      |
    | formulate the expression. E.g. a project of the  *gen_must_run*         |
    | operational_type will be producing power equal to its capacity while a  |
    | dispatchable project will have a variable in its power provision        |
    | expression. This expression will then be used by other modules.         |
    +-------------------------------------------------------------------------+

    """

    # Dynamic Inputs
    ###########################################################################

    required_operational_modules = get_required_subtype_modules_from_projects_file(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        which_type="operational_type",
    )

    imported_operational_modules = load_operational_type_modules(
        required_operational_modules
    )

    # Expressions
    ###########################################################################

    def power_provision_rule(mod, prj, tmp):
        """
        **Expression Name**: Power_Provision_MW
        **Defined Over**: PRJ_OPR_TMPS

        Power provision is a variable for some generators, but not others; get
        the appropriate expression for each generator based on its operational
        type.
        """
        gen_op_type = mod.operational_type[prj]
        if hasattr(imported_operational_modules[gen_op_type], "power_provision_rule"):
            return imported_operational_modules[gen_op_type].power_provision_rule(
                mod, prj, tmp
            )
        else:
            return op_type_init.power_provision_rule(mod, prj, tmp)

    m.Power_Provision_MW = Expression(m.PRJ_OPR_TMPS, rule=power_provision_rule)


# Input-Output
###############################################################################


def export_results(scenario_directory, subproblem, stage, m, d):
    """
    Export operations results.
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

    # First power
    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "dispatch_all.csv",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "project",
                "period",
                "horizon",
                "timepoint",
                "operational_type",
                "balancing_type",
                "timepoint_weight",
                "number_of_hours_in_timepoint",
                "load_zone",
                "technology",
                "power_mw",
            ]
        )
        for (p, tmp) in m.PRJ_OPR_TMPS:
            writer.writerow(
                [
                    p,
                    m.period[tmp],
                    m.horizon[tmp, m.balancing_type_project[p]],
                    tmp,
                    m.operational_type[p],
                    m.balancing_type_project[p],
                    m.tmp_weight[tmp],
                    m.hrs_in_tmp[tmp],
                    m.load_zone[p],
                    m.technology[p],
                    value(m.Power_Provision_MW[p, tmp]),
                ]
            )


def summarize_results(scenario_directory, subproblem, stage):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:

    Summarize operational results
    """

    summary_results_file = os.path.join(
        scenario_directory, subproblem, stage, "results", "summary_results.txt"
    )

    # Open in 'append' mode, so that results already written by other
    # modules are not overridden
    with open(summary_results_file, "a") as outfile:
        outfile.write("\n### OPERATIONAL RESULTS ###\n")

    # Next, our goal is to get a summary table of power production by load
    # zone, technology, and period
    # Note: this includes power from spinup_or_lookahead timepoints as well!

    # Get the results CSV as dataframe
    operational_results_df = pd.read_csv(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "dispatch_all.csv",
        )
    )

    operational_results_df["weighted_power_mwh"] = (
        operational_results_df["power_mw"] * operational_results_df["timepoint_weight"]
    )

    # Aggregate total power results by load_zone, technology, and period
    operational_results_agg_df = pd.DataFrame(
        operational_results_df.groupby(
            by=["load_zone", "period", "technology"], as_index=True
        ).sum()["weighted_power_mwh"]
    )

    operational_results_agg_df.columns = ["weighted_power_mwh"]

    # Aggregate total power by load_zone and period -- we'll need this
    # to find the percentage of total power by technology (for each load
    # zone and period)
    lz_period_power_df = pd.DataFrame(
        operational_results_df.groupby(by=["load_zone", "period"], as_index=True).sum()[
            "weighted_power_mwh"
        ]
    )

    # Name the power column
    operational_results_agg_df.columns = ["weighted_power_mwh"]
    # Add a column with the percentage of total power by load zone and tech
    operational_results_agg_df["percent_total_power"] = pd.Series(
        index=operational_results_agg_df.index, dtype="float64"
    )

    # Calculate the percent of total power for each tech (by load zone
    # and period)
    for indx, row in operational_results_agg_df.iterrows():
        if lz_period_power_df.weighted_power_mwh[indx[0], indx[1]] == 0:
            pct = 0
        else:
            pct = (
                operational_results_agg_df.weighted_power_mwh[indx]
                / lz_period_power_df.weighted_power_mwh[indx[0], indx[1]]
                * 100.0
            )
        operational_results_agg_df.percent_total_power[indx] = pct

    # Get the energy units from the units.csv file
    units_df = pd.read_csv(
        os.path.join(scenario_directory, "units.csv"), index_col="metric"
    )
    energy_unit = units_df.loc["energy", "unit"]
    # units_dict = dict(zip(units_df["metric"], units_df["unit"]))

    # Rename the columns for the final table
    operational_results_agg_df.columns = [
        "Annual Energy ({})".format(energy_unit),
        "% Total Power",
    ]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> Energy Production <--\n")
        operational_results_agg_df.to_string(outfile, float_format="{:,.2f}".format)
        outfile.write("\n")


# Database
###############################################################################


def import_results_into_database(
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
    pass


def process_results(db, c, scenario_id, subscenarios, quiet):
    """
    Aggregate dispatch by technology
    Aggregate dispatch by technology and period
    :param db:
    :param c:
    :param subscenarios:
    :param quiet:
    :return:
    """
    if not quiet:
        print("aggregate dispatch by technology")

    # Delete old dispatch by technology
    del_sql = """
        DELETE FROM results_project_dispatch_by_technology 
        WHERE scenario_id = ?
        """
    spin_on_database_lock(
        conn=db, cursor=c, sql=del_sql, data=(scenario_id,), many=False
    )

    # Aggregate dispatch by technology
    agg_sql = """
        INSERT INTO results_project_dispatch_by_technology
        (scenario_id, subproblem_id, stage_id, period, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, spinup_or_lookahead,
        load_zone, technology, power_mw)
        SELECT
        scenario_id, subproblem_id, stage_id, period, timepoint, 
        timepoint_weight, number_of_hours_in_timepoint, spinup_or_lookahead,
        load_zone, technology, sum(power_mw) AS power_mw
        FROM results_project_dispatch
        WHERE scenario_id = ?
        GROUP BY subproblem_id, stage_id, timepoint, 
        load_zone, technology
        ORDER BY subproblem_id, stage_id, timepoint, 
        load_zone, technology;"""
    spin_on_database_lock(
        conn=db, cursor=c, sql=agg_sql, data=(scenario_id,), many=False
    )

    if not quiet:
        print("aggregate dispatch by technology-period")

    # Delete old dispatch by technology
    del_sql = """
        DELETE FROM results_project_dispatch_by_technology_period 
        WHERE scenario_id = ?
        """
    spin_on_database_lock(
        conn=db, cursor=c, sql=del_sql, data=(scenario_id,), many=False
    )

    # Aggregate dispatch by technology, period, and spinup_or_lookahead
    agg_sql = """
        INSERT INTO results_project_dispatch_by_technology_period
        (scenario_id, subproblem_id, stage_id, period, load_zone, technology, 
        spinup_or_lookahead, energy_mwh)
        SELECT
        scenario_id, subproblem_id, stage_id, period, load_zone, technology, 
        spinup_or_lookahead,
        SUM(power_mw * timepoint_weight * number_of_hours_in_timepoint ) AS 
        energy_mwh 
        FROM results_project_dispatch_by_technology
        WHERE scenario_id = ?
        GROUP BY subproblem_id, stage_id, period, load_zone, technology, 
        spinup_or_lookahead
        ORDER BY subproblem_id, stage_id, period, load_zone, technology, 
        spinup_or_lookahead;"""
    spin_on_database_lock(
        conn=db, cursor=c, sql=agg_sql, data=(scenario_id,), many=False
    )
