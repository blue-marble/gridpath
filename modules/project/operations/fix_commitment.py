#!/usr/bin/env python

"""

"""
import os.path
from pandas import read_csv
from csv import writer

from pyomo.environ import Set, Param, NonNegativeReals, Expression, BuildAction

from modules.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    def determine_final_commitment_generators(mod):
        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project",
                                   "last_commitment_stage"]
                )

        for row in zip(dynamic_components["project"],
                       dynamic_components["last_commitment_stage"]):
            if row[1] == stage:
                mod.FINAL_COMMITMENT_PROJECTS.add(row[0])
            else:
                pass
    # The generators for which the current stage is the final commitment stage
    m.FINAL_COMMITMENT_PROJECTS = \
        Set(initialize=[])
    m.FinalCommitmentGeneratorsBuild = BuildAction(
        rule=determine_final_commitment_generators)

    m.FINAL_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.FINAL_COMMITMENT_PROJECTS))

    # Import needed operational modules
    # TODO: import only
    imported_operational_modules = \
        load_operational_type_modules(d.required_operational_modules)

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
    m.Commitment = Expression(m.FINAL_COMMITMENT_PROJECTS, m.TIMEPOINTS,
                              rule=commitment_rule)

    def determine_fixed_commitment_generators(mod):
        """

        :param mod:
        :return:
        """
        # Get the list of generators whose commitment has already been fixed and
        # the fixed commitment
        fixed_commitment_df = \
            read_csv(os.path.join(scenario_directory, horizon,
                                  "pass_through_inputs",
                                  "fixed_commitment.csv"))

        fixed_commitment_generators = \
            set(fixed_commitment_df["generator"].tolist())
        for g in fixed_commitment_generators:
            mod.FIXED_COMMITMENT_PROJECTS.add(g)

        fixed_commitment_dict = \
            dict([((g, tmp), c)
                  for g, tmp, c in zip(fixed_commitment_df.generator,
                                       fixed_commitment_df.timepoint,
                                       fixed_commitment_df.commitment)])
        for (g, tmp) in fixed_commitment_dict.keys():
            mod.fixed_commitment[g, tmp] = fixed_commitment_dict[g, tmp]

    # TODO: is there a need to subdivide into binary and continuous?
    # The generators that have already had their commitment fixed in a prior
    # commitment stage
    m.FIXED_COMMITMENT_PROJECTS = \
        Set(initialize=[])
    m.fixed_commitment = Param(m.FIXED_COMMITMENT_PROJECTS, m.TIMEPOINTS,
                               within=NonNegativeReals, mutable=True,
                               initialize={})
    m.FixedCommitmentGeneratorsBuild = BuildAction(
        rule=determine_fixed_commitment_generators)

    m.FIXED_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.FIXED_COMMITMENT_PROJECTS))


def fix_variables(m):
    """

    :param m:
    :return:
    """

    # Import needed operational modules
    imported_operational_modules = load_operational_type_modules(m)

    for g in m.FIXED_COMMITMENT_PROJECTS:
        op_m = m.operational_type[g]
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "fix_commitment"):
            for tmp in m.TIMEPOINTS:
                imp_op_m.fix_commitment(m, g, tmp)


def export_results(scenario_directory, horizon, stage, m, d):
    """

    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    with open(os.path.join(
            scenario_directory, horizon,
            "pass_through_inputs", "fixed_commitment.csv"), "ab") \
            as fixed_commitment_file:
        fixed_commitment_writer = writer(fixed_commitment_file)
        for (g, tmp) in m.FINAL_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS:
            fixed_commitment_writer.writerow(
                [g, tmp, stage, m.Commitment[g, tmp].expr.value])

