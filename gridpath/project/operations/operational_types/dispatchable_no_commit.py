#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of no-commit generators.
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Param, Set, Var, Constraint, \
    Expression, NonNegativeReals, PercentFraction, value

from gridpath.auxiliary.auxiliary import generator_subset_init
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables


def add_module_specific_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Sets
    m.DISPATCHABLE_NO_COMMIT_GENERATORS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type", "dispatchable_no_commit")
    )

    m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.DISPATCHABLE_NO_COMMIT_GENERATORS))

    # Variables
    m.Provide_Power_DispNoCommit_MW = \
        Var(m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    # Operational constraints
    def max_power_rule(mod, g, tmp):
        """
        Power plus upward services cannot exceed capacity.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_DispNoCommit_MW[g, tmp] + \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, headroom_variables)[g]) \
            <= mod.Capacity_MW[g, mod.period[tmp]] \
            * mod.availability_derate[g, mod.horizon[tmp]]
    m.DispNoCommit_Max_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=max_power_rule
        )

    def min_power_rule(mod, g, tmp):
        """
        Power minus downward services cannot be below 0 (no commitment variable).
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Power_DispNoCommit_MW[g, tmp] - \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, footroom_variables)[g]) \
            >= 0
    m.DispNoCommit_Min_Power_Constraint = \
        Constraint(
            m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=min_power_rule
        )

    # Optional ramp constraints

    # Ramp rates can be optionally specified and will default to 1 if not
    m.dispnocommit_ramp_up_rate = \
        Param(m.DISPATCHABLE_NO_COMMIT_GENERATORS, within=PercentFraction,
              default=1)
    m.dispnocommit_ramp_down_rate = \
        Param(m.DISPATCHABLE_NO_COMMIT_GENERATORS, within=PercentFraction,
              default=1)

    # Constrain ramps
    m.DispNoCommit_Ramp_MW = Expression(
        m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
        rule=ramp_rule
    )

    def ramp_up_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        elif mod.dispnocommit_ramp_up_rate[g] == 1:
            return Constraint.Skip
        else:
            return mod.DispNoCommit_Ramp_MW[g, tmp] \
                   <= \
                   mod.dispnocommit_ramp_up_rate[g] \
                   * mod.Capacity_MW[g, mod.period[tmp]] \
                   * mod.availability_derate[g, mod.horizon[tmp]]

    m.DispNoCommit_Ramp_Up_Constraint = \
        Constraint(
            m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=ramp_up_rule
        )

    def ramp_down_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            return Constraint.Skip
        elif mod.dispnocommitramp_down_rate[g] == 1:
            return Constraint.Skip
        else:
            return mod.DispNoCommit_Ramp_MW[g, tmp] \
                   >= \
                   - mod.dispnocommit_ramp_down_rate[g] \
                   * mod.Capacity_MW[g, mod.period[tmp]] \
                   * mod.availability_derate[g, mod.horizon[tmp]]

    m.DispNoCommit_Ramp_Down_Constraint = \
        Constraint(
            m.DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS,
            rule=ramp_down_rule
        )


def power_provision_rule(mod, g, tmp):
    """
    Power provision from dispatchable generators is an endogenous variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispNoCommit_MW[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since no commitment, all capacity assumed online
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Capacity_MW[g, mod.period[tmp]] \
        * mod.availability_derate[g, mod.horizon[tmp]]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision from dispatchable generators, if eligible, is an endogenous
    variable.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Provide_Power_DispNoCommit_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    No 'curtailment' -- simply dispatch down
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


# TODO: ignoring subhourly behavior for dispatchable gens for now
def subhourly_curtailment_rule(mod, g, tmp):
    """
    
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return 0


# TODO: add data check that minimum_input_mmbtu_per_hr is 0 for no-commit gens
def fuel_burn_rule(mod, g, tmp, error_message):
    """
    Fuel use in terms of an IO curve with an incremental heat rate above
    the minimum stable level, which is 0 for no-commit generators, so just
    multiply power by the incremental heat rate
    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        return mod.Provide_Power_DispNoCommit_MW[g, tmp] \
            * mod.inc_heat_rate_mmbtu_per_mwh[g]
    else:
        raise ValueError(error_message)


def startup_shutdown_rule(mod, g, tmp):
    """
    No commit variables, so shouldn't happen
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        return None
    else:
        return mod.Provide_Power_DispNoCommit_MW[g, tmp] - \
            mod.Provide_Power_DispNoCommit_MW[g, mod.previous_timepoint[tmp]]


def ramp_rule(mod, g, tmp):
    """

    :param mod: 
    :param g: 
    :param tmp: 
    :return: 
    """
    if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
            and mod.boundary[mod.horizon[tmp]] == "linear":
        pass
    else:
        return mod.Provide_Power_DispNoCommit_MW[g, tmp] - \
               mod.Provide_Power_DispNoCommit_MW[
                   g, mod.previous_timepoint[tmp]
               ]


def load_module_specific_data(mod, data_portal, scenario_directory,
                              horizon, stage):
    """

    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # Ramp rate limits are optional, will default to 1 if not specified
    ramp_up_rate = dict()
    ramp_down_rate = dict()
    header = pd.read_csv(os.path.join(scenario_directory, "inputs",
                                      "projects.tab"),
                         sep="\t", header=None, nrows=1).values[0]

    optional_columns = ["ramp_up_when_on_rate",
                        "ramp_down_when_on_rate"]
    used_columns = [c for c in optional_columns if c in header]

    dynamic_components = \
        pd.read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t",
            usecols=["project", "operational_type"] + used_columns
        )

    # Optional ramp rates
    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_up_when_on_rate"]):
            if row[1] == "dispatchable_no_commit" and row[2] != ".":
                ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispnocommit_ramp_up_rate"] = \
            ramp_up_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components["ramp_down_when_on_rate"]):
            if row[1] == "dispatchable_no_commit" and row[2] != ".":
                ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "dispnocommit_ramp_down_rate"] = \
            ramp_down_rate


# TODO: remove this since redundant with dispatch_all?
def export_module_specific_results(mod, d, scenario_directory, horizon, stage):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "dispatch_no_commit.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "horizon_weight", "number_of_hours_in_timepoint",
                         "technology", "load_zone", "power_mw"
                         ])

        for (p, tmp) \
                in mod. \
                DISPATCHABLE_NO_COMMIT_GENERATOR_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.horizon[tmp],
                tmp,
                mod.horizon_weight[mod.horizon[tmp]],
                mod.number_of_hours_in_timepoint[tmp],
                mod.technology[p],
                mod.load_zone[p],
                value(mod.Provide_Power_DispNoCommit_MW[p, tmp])
            ])


# TODO: remove this since redundant with dispatch_all?
def import_module_specific_results_to_database(
        scenario_id, c, db, results_directory
):
    """

    :param scenario_id:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    print("project dispatch no commit")
    # dispatch_no_commit.csv
    c.execute(
        """DELETE FROM results_project_dispatch_no_commit
        WHERE scenario_id = {};""".format(
            scenario_id
        )
    )
    db.commit()

    # Create temporary table, which we'll use to sort results and then drop
    c.execute(
        """DROP TABLE IF EXISTS
        temp_results_project_dispatch_no_commit"""
        + str(scenario_id) + """;"""
    )
    db.commit()

    c.execute(
        """CREATE TABLE temp_results_project_dispatch_no_commit"""
        + str(scenario_id) + """(
            scenario_id INTEGER,
            project VARCHAR(64),
            period INTEGER,
            horizon INTEGER,
            timepoint INTEGER,
            horizon_weight FLOAT,
            number_of_hours_in_timepoint FLOAT,
            load_zone VARCHAR(32),
            technology VARCHAR(32),
            power_mw FLOAT,
            PRIMARY KEY (scenario_id, project, timepoint)
                );"""
    )
    db.commit()

    # Load results into the temporary table
    with open(os.path.join(
            results_directory, "dispatch_no_commit.csv"), "r") \
            as cc_dispatch_file:
        reader = csv.reader(cc_dispatch_file)

        next(reader)  # skip header
        for row in reader:
            project = row[0]
            period = row[1]
            horizon = row[2]
            timepoint = row[3]
            horizon_weight = row[4]
            number_of_hours_in_timepoint = row[5]
            load_zone = row[7]
            technology = row[6]
            power_mw = row[8]
            c.execute(
                """INSERT INTO temp_results_project_dispatch_no_commit"""
                + str(scenario_id) + """
                    (scenario_id, project, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    load_zone, technology, power_mw)
                    VALUES ({}, '{}', {}, {}, {}, {}, {}, '{}', '{}',
                    {});""".format(
                    scenario_id, project, period, horizon, timepoint,
                    horizon_weight, number_of_hours_in_timepoint,
                    load_zone, technology, power_mw
                )
            )
    db.commit()

    # Insert sorted results into permanent results table
    c.execute(
        """INSERT INTO results_project_dispatch_no_commit
        (scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw)
        SELECT
        scenario_id, project, period, horizon, timepoint,
        horizon_weight, number_of_hours_in_timepoint,
        load_zone, technology, power_mw
        FROM temp_results_project_dispatch_no_commit""" + str(
            scenario_id) + """
            ORDER BY scenario_id, project, timepoint;"""
    )
    db.commit()

    # Drop the temporary table
    c.execute(
        """DROP TABLE temp_results_project_dispatch_no_commit""" + str(
            scenario_id) +
        """;"""
    )
    db.commit()
