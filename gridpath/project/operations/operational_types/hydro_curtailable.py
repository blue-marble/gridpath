#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operations of curtailable conventional hydro generators
"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Var, Set, Param, Constraint, \
    Expression, NonNegativeReals, PercentFraction, value

from gridpath.auxiliary.auxiliary import generator_subset_init
from gridpath.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables


def add_module_specific_components(m, d):
    """
    Add a capacity commit variable to represent the amount of capacity that is
    on.
    :param m:
    :return:
    """
    # Sets and params
    m.HYDRO_CURTAILABLE_PROJECTS = Set(
        within=m.PROJECTS,
        initialize=
        generator_subset_init("operational_type",
                              "hydro_curtailable")
    )

    m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS = \
        Set(dimen=2)

    m.hydro_curtailable_average_power_mwa = \
        Param(m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)
    m.hydro_curtailable_min_power_mw = \
        Param(m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)
    m.hydro_curtailable_max_power_mw = \
        Param(m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS,
              within=NonNegativeReals)

    m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, within=m.PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.HYDRO_CURTAILABLE_PROJECTS))

    # Ramp rates can be optionally specified and will default to 1 if not
    m.hydro_curtailable_ramp_up_rate = \
        Param(m.HYDRO_CURTAILABLE_PROJECTS, within=PercentFraction, default=1)
    m.hydro_curtailable_ramp_down_rate = \
        Param(m.HYDRO_CURTAILABLE_PROJECTS, within=PercentFraction, default=1)

    # Variables
    m.Hydro_Curtailable_Provide_Power_MW = \
        Var(m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    m.Hydro_Curtailable_Curtail_MW = \
        Var(m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    # Operational constraints
    def hydro_energy_budget_rule(mod, g, h):
        """

        :param mod:
        :param g:
        :param h:
        :return:
        """
        return sum((mod.Hydro_Curtailable_Provide_Power_MW[g, tmp] +
                    mod.Hydro_Curtailable_Curtail_MW[g, tmp])
                   * mod.number_of_hours_in_timepoint[tmp]
                   for tmp in mod.TIMEPOINTS_ON_HORIZON[h]) \
            == \
            sum(mod.hydro_curtailable_average_power_mwa[g, h]
                * mod.number_of_hours_in_timepoint[tmp]
                for tmp in mod.TIMEPOINTS_ON_HORIZON[h])

    m.Curtailable_Hydro_Energy_Budget_Constraint = \
        Constraint(m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS,
                   rule=hydro_energy_budget_rule)

    def max_power_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Hydro_Curtailable_Provide_Power_MW[g, tmp] + \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, headroom_variables)[g]) \
            <= mod.hydro_curtailable_max_power_mw[
                   g, mod.horizon[tmp]
               ]
    m.Hydro_Curtailable_Max_Power_Constraint = \
        Constraint(
            m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=max_power_rule
        )

    def min_power_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Hydro_Curtailable_Provide_Power_MW[g, tmp] - \
            sum(getattr(mod, c)[g, tmp]
                for c in getattr(d, footroom_variables)[g]) \
            >= mod.hydro_curtailable_min_power_mw[
                   g, mod.horizon[tmp]]
    m.Hydro_Curtailable_Min_Power_Constraint = \
        Constraint(
            m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=min_power_rule
        )

    # Constrain ramps
    def ramp_expression_rule(mod, g, tmp):
        if tmp == mod.first_horizon_timepoint[mod.horizon[tmp]] \
                and mod.boundary[mod.horizon[tmp]] == "linear":
            pass
        else:
            return (mod.Hydro_Curtailable_Provide_Power_MW[g, tmp] +
                        mod.Hydro_Curtailable_Curtail_MW[g, tmp]) - \
                       (mod.Hydro_Curtailable_Provide_Power_MW[
                        g, mod.previous_timepoint[tmp]
                        ]
                        + mod.Hydro_Curtailable_Curtail_MW[
                            g, mod.previous_timepoint[tmp]
                        ])

    m.Hydro_Curtailable_Ramp_MW = Expression(
        m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
        rule=ramp_expression_rule
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
        elif mod.hydro_curtailable_ramp_up_rate[g] == 1:
            return Constraint.Skip
        else:
            return mod.Hydro_Curtailable_Ramp_MW[g, tmp] \
                <= \
                mod.hydro_curtailable_ramp_up_rate[g] \
                * mod.Capacity_MW[g, mod.period[tmp]]
    m.Hydro_Curtailable_Ramp_Up_Constraint = \
        Constraint(
            m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
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
        elif mod.hydro_curtailable_ramp_down_rate[g] == 1:
            return Constraint.Skip
        else:
            return mod.Hydro_Curtailable_Ramp_MW[g, tmp] \
                >= \
                - mod.hydro_curtailable_ramp_down_rate[g] \
                * mod.Capacity_MW[g, mod.period[tmp]]
    m.Hydro_Curtailable_Ramp_Down_Constraint = \
        Constraint(
            m.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS,
            rule=ramp_down_rule
        )


def power_provision_rule(mod, g, tmp):
    """
    Power provision from curtailable hydro
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Hydro_Curtailable_Provide_Power_MW[g, tmp]


def online_capacity_rule(mod, g, tmp):
    """
    Since no commitment, all capacity assumed online
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Capacity_MW[g, mod.period[tmp]]


def rec_provision_rule(mod, g, tmp):
    """
    REC provision from curtailable hydro if eligible
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Hydro_Curtailable_Provide_Power_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    This treatment does not allow curtailment
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Hydro_Curtailable_Curtail_MW[g, tmp]


# TODO: ignoring subhourly behavior for hydro for now
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


def fuel_burn_rule(mod, g, tmp, error_message):
    """

    :param mod:
    :param g:
    :param tmp:
    :param error_message:
    :return:
    """
    if g in mod.FUEL_PROJECTS:
        raise (ValueError(
            "ERROR! Curtailable hydro projects should not use fuel." + "\n" +
            "Check input data for project '{}'".format(g) + "\n" +
            "and change its fuel to '.' (no value).")
        )
    else:
        raise ValueError(error_message)


def startup_shutdown_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise (ValueError(
        "ERROR! Hydro generators should not incur startup/shutdown costs." +
        "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup/shutdown costs to '.' (no value).")
    )


def load_module_specific_data(m,
                              data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    # Determine list of projects
    projects = list()

    prj_op_type_df = \
        pd.read_csv(
            os.path.join(scenario_directory, "inputs", "projects.tab"),
            sep="\t", usecols=["project",
                               "operational_type"]
        )

    for row in zip(prj_op_type_df["project"],
                   prj_op_type_df["operational_type"]):
        if row[1] == 'hydro_curtailable':
            projects.append(row[0])
        else:
            pass

    # Determine subset of project-horizons in hydro budgets file
    project_horizons = list()
    mwa = dict()
    min_mw = dict()
    max_mw = dict()

    prj_hor_opchar_df = \
        pd.read_csv(
            os.path.join(scenario_directory, horizon, "inputs",
                         "hydro_conventional_horizon_params.tab"),
            sep="\t", usecols=[
                "hydro_project", "horizon",
                "hydro_average_power_mwa",
                "hydro_min_power_mw",
                "hydro_max_power_mw"
            ]
        )
    for row in zip(prj_hor_opchar_df["hydro_project"],
                   prj_hor_opchar_df["horizon"],
                   prj_hor_opchar_df["hydro_average_power_mwa"],
                   prj_hor_opchar_df["hydro_min_power_mw"],
                   prj_hor_opchar_df["hydro_max_power_mw"]):
        if row[0] in projects:
            project_horizons.append((row[0], row[1]))
            mwa[(row[0], row[1])] = float(row[2])
            min_mw[(row[0], row[1])] = float(row[3])
            max_mw[(row[0], row[1])] = float(row[4])
        else:
            pass

    # Load data
    data_portal.data()[
        "HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_HORIZONS"
    ] = {
        None: project_horizons
    }
    data_portal.data()["hydro_curtailable_average_power_mwa"] = mwa
    data_portal.data()["hydro_curtailable_min_power_mw"] = min_mw
    data_portal.data()["hydro_curtailable_max_power_mw"] = max_mw

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

    if "ramp_up_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components[
                           "ramp_up_when_on_rate"]
                       ):
            if row[1] == "hydro_curtailable" and row[2] != ".":
                ramp_up_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "hydro_curtailable_ramp_up_rate"] = \
            ramp_up_rate

    if "ramp_down_when_on_rate" in used_columns:
        for row in zip(dynamic_components["project"],
                       dynamic_components["operational_type"],
                       dynamic_components[
                           "ramp_down_when_on_rate"]
                       ):
            if row[1] == "hydro_curtailable" and row[2] != ".":
                ramp_down_rate[row[0]] = float(row[2])
            else:
                pass
        data_portal.data()[
            "hydro_curtailable_ramp_down_rate"] = \
            ramp_down_rate


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
                           "dispatch_hydro_curtailable.csv"),
              "wb") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "horizon_weight", "number_of_hours_in_timepoint",
                         "technology", "load_zone",
                         "power_mw", "scheduled_curtailment_mw"
                         ])

        for (p, tmp) in mod.HYDRO_CURTAILABLE_PROJECT_OPERATIONAL_TIMEPOINTS:
            writer.writerow([
                p,
                mod.period[tmp],
                mod.horizon[tmp],
                tmp,
                mod.horizon_weight[mod.horizon[tmp]],
                mod.number_of_hours_in_timepoint[tmp],
                mod.technology[p],
                mod.load_zone[p],
                value(mod.Hydro_Curtailable_Provide_Power_MW[p, tmp]),
                value(mod.Hydro_Curtailable_Curtail_MW[p, tmp])
            ])
