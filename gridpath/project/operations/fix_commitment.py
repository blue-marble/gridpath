#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This module exports the commitment variables that must be fixed in the next
stage and imports the variables that were fixed in the previous stage.
"""

from builtins import zip
from csv import writer
import os.path
from pandas import read_csv
from pyomo.environ import Set, Param, NonNegativeReals, Expression

from gridpath.auxiliary.dynamic_components import required_operational_modules
from gridpath.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Import needed operational modules
    # TODO: import only
    imported_operational_modules = \
        load_operational_type_modules(
            getattr(d, required_operational_modules)
        )

    # Sets
    # The generators for which the current stage or any of the previous stages
    # is the final commitment stage
    m.FINAL_COMMITMENT_PROJECTS = Set()

    m.FINAL_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.FINAL_COMMITMENT_PROJECTS))

    # The generators that have already had their commitment fixed in a prior
    # commitment stage
    m.FIXED_COMMITMENT_PROJECTS = Set()

    m.FIXED_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.FIXED_COMMITMENT_PROJECTS))

    # Params
    m.fixed_commitment = Param(
        m.FIXED_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals)

    # Expressions
    def commitment_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type].\
            commitment_rule(mod, g, tmp)
    m.Commitment = Expression(m.FINAL_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS,
                              rule=commitment_rule)


def fix_variables(m, d):
    """

    :param m:
    :return:
    """

    # Import needed operational modules
    imported_operational_modules = load_operational_type_modules(
        d.required_operational_modules)

    # Fix commitment if there are any fixed commitment projects
    for g in m.FIXED_COMMITMENT_PROJECTS:
        op_m = m.operational_type[g]
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "fix_commitment"):
            for tmp in m.TIMEPOINTS:
                imp_op_m.fix_commitment(m, g, tmp)


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    stages = read_csv(
        os.path.join(scenario_directory, subproblem, "subproblems.csv"),
        dtype={"subproblems": str}
    )['subproblems'].tolist()

    fixed_commitment_df = read_csv(
        os.path.join(scenario_directory, subproblem,
                     "pass_through_inputs", "fixed_commitment.tab"),
        sep='\t',
        dtype={"stage": str}
    )

    # fixed_commitment_df["stage"] = fixed_commitment_df["stage"].astype(str)

    # FINAL_COMMITMENT_GENERATORS
    def determine_final_commitment_projects():
        """
        Get the list of generators for which the current stage is the final
        commitment stage or for which any of the previous stages was the
        final commitment stage.
        """
        final_commitment_projects = list()
        df = read_csv(
            os.path.join(scenario_directory, subproblem, stage,
                         "inputs", "projects.tab"),
            sep="\t",
            usecols=["project", "last_commitment_stage"],
            dtype={"last_commitment_stage": str}
        )
        # df["last_commitment_stage"] = df["last_commitment_stage"].astype(str)
        for prj, s in zip(df["project"], df["last_commitment_stage"]):
            if s == ".":
                pass
            elif s == stage or stages.index(s) < stages.index(stage):
                final_commitment_projects.append(prj)
            else:
                pass
        return final_commitment_projects

    data_portal.data()["FINAL_COMMITMENT_PROJECTS"] = {
        None: determine_final_commitment_projects()
    }

    # FIXED_COMMITMENT_GENERATORS
    fixed_commitment_projects = set(fixed_commitment_df["project"].tolist())
    # Load data only if we have projects that have already been committed
    # Otherwise, leave uninitialized
    if len(fixed_commitment_projects) > 0:
        # For projects whose final commitment was in a prior stage, get the
        # fixed commitment of the previous stage (by project and timepoint)
        fixed_commitment_df["stage_index"] = fixed_commitment_df.apply(
            lambda row: stages.index(row["stage"]), axis=1)
        relevant_commitment_df = fixed_commitment_df[
            fixed_commitment_df["stage_index"] == stages.index(stage) - 1
        ]
        projects_timepoints = list(zip(relevant_commitment_df["project"],
                                       relevant_commitment_df["timepoint"]))
        fixed_commitment_dict = dict(zip(projects_timepoints,
                                         relevant_commitment_df["commitment"]))

        data_portal.data()["FIXED_COMMITMENT_PROJECTS"] = {
            None: fixed_commitment_projects
        }
        data_portal.data()[
            "FIXED_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS"
        ] = {None: projects_timepoints}
        data_portal.data()["fixed_commitment"] = fixed_commitment_dict
    else:
        pass


def export_pass_through_inputs(scenario_directory, subproblem, stage, m, d):
    """

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    df = read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "last_commitment_stage"]
    )
    final_commitment_stage_dict = dict(
        zip(df["project"], df["last_commitment_stage"])
    )

    with open(os.path.join(
            scenario_directory, subproblem,
            "pass_through_inputs", "fixed_commitment.tab"), "a") \
            as fixed_commitment_file:
        fixed_commitment_writer = writer(fixed_commitment_file, delimiter="\t")
        for (g, tmp) in m.FINAL_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS:
            fixed_commitment_writer.writerow(
                [g, tmp, stage, final_commitment_stage_dict[g],
                 m.Commitment[g, tmp].expr.value]
            )
