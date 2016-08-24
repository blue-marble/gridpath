#!/usr/bin/env python

"""

"""
import os.path
from pandas import read_csv
from csv import writer

from pyomo.environ import Set, Param, PercentFraction, Expression

from auxiliary import load_operational_modules


def determine_dynamic_components(m, inputs_directory):
    """

    :param m:
    :param inputs_directory:
    :return:
    """

    # Figure out what the current stage is (should be the problem directory,
    # which is one level up from the inputs directory
    # TODO: pass the problem directory and figure out the inputs directory from
    # there instead
    m.current_stage = \
        os.path.basename(os.path.normpath(os.path.join(inputs_directory, "..")))

    dynamic_components = \
        read_csv(os.path.join(inputs_directory, "generators.tab"),
                 sep="\t", usecols=["GENERATORS",
                                    "last_commitment_stage"]
                 )

    # Last commitment stage
    m.final_commitment_generators = list()

    for row in zip(dynamic_components["GENERATORS"],
                   dynamic_components["last_commitment_stage"]):
        if row[1] == m.current_stage:
            m.final_commitment_generators.append(row[0])
        else:
            pass

    # Get the list of generators whose commitment has already been fixed and
    # the fixed commitment
    fixed_commitment_df = \
        read_csv(os.path.join(inputs_directory,
                              "../../pass_through_inputs/fixed_commitment.csv"))

    m.fixed_commitment_generators =\
        set(fixed_commitment_df["generator"].tolist())

    m.fixed_commitment_dict = \
        dict([((g, tmp), c)
              for g, tmp, c in zip(fixed_commitment_df.generator,
                                   fixed_commitment_df.timepoint,
                                   fixed_commitment_df.commitment)])


def add_model_components(m):
    """

    :param m:
    :return:
    """

    # Import needed operational modules
    # TODO: import only
    imported_operational_modules = \
        load_operational_modules(m.required_operational_modules)

    # The generators for which the current stage is the final commitment stage
    m.FINAL_COMMITMENT_GENERATORS = \
        Set(within=m.COMMIT_GENERATORS,
            initialize=m.final_commitment_generators)

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
    m.Commitment = Expression(m.FINAL_COMMITMENT_GENERATORS, m.TIMEPOINTS,
                              rule=commitment_rule)

    # TODO: is there a need to subdivide into binary and continuous?
    # The generators that have already had their commitment fixed in a prior
    # commitment stage
    m.FIXED_COMMITMENT_GENERATORS = \
        Set(within=m.COMMIT_GENERATORS,
            initialize=m.fixed_commitment_generators)
    m.fixed_commitment = Param(m.FIXED_COMMITMENT_GENERATORS, m.TIMEPOINTS,
                               within=PercentFraction,
                               initialize=m.fixed_commitment_dict)


def fix_variables(m):
    """

    :param m:
    :return:
    """

    # Import needed operational modules
    # TODO: import only
    imported_operational_modules = \
        load_operational_modules(m.required_operational_modules)

    for g in m.FIXED_COMMITMENT_GENERATORS:
        op_m = m.operational_type[g]
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "fix_commitment"):
            for tmp in m.TIMEPOINTS:
                imp_op_m.fix_commitment(m, g, tmp)


def export_results(problem_directory, m):
    """
    Export operations results.
    :param problem_directory:
    :param m:
    :return:
    """
    with open(os.path.join(
            problem_directory,
            "../pass_through_inputs/fixed_commitment.csv"), "ab") \
            as fixed_commitment_file:
        fixed_commitment_writer = writer(fixed_commitment_file)
        for g in m.FINAL_COMMITMENT_GENERATORS:
            for tmp in m.TIMEPOINTS:
                fixed_commitment_writer.writerow(
                    [g, tmp, m.current_stage, m.Commitment[g, tmp].expr.value])

