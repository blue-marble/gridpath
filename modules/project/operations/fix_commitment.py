#!/usr/bin/env python

"""

"""
from csv import writer
import os.path
from pandas import read_csv
from pyomo.environ import Set, Param, NonNegativeReals, Expression

from modules.auxiliary.dynamic_components import required_operational_modules
from modules.auxiliary.auxiliary import load_operational_type_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # The generators for which the current stage is the final commitment stage
    m.FINAL_COMMITMENT_PROJECTS = Set()

    m.FINAL_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.FINAL_COMMITMENT_PROJECTS))

    # Import needed operational modules
    # TODO: import only
    imported_operational_modules = \
        load_operational_type_modules(
            getattr(d, required_operational_modules)
        )

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

    # TODO: is there a need to subdivide into binary and continuous?
    # The generators that have already had their commitment fixed in a prior
    # commitment stage
    m.FIXED_COMMITMENT_PROJECTS = Set()
    m.fixed_commitment = Param(m.FIXED_COMMITMENT_PROJECTS, m.TIMEPOINTS,
                               within=NonNegativeReals)

    m.FIXED_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.FIXED_COMMITMENT_PROJECTS))


def fix_variables(m, d):
    """

    :param m:
    :return:
    """

    # Import needed operational modules
    imported_operational_modules = load_operational_type_modules(
        d.required_operational_modules)

    for g in m.FIXED_COMMITMENT_PROJECTS:
        op_m = m.operational_type[g]
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "fix_commitment"):
            for tmp in m.TIMEPOINTS:
                imp_op_m.fix_commitment(m, g, tmp)


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # FINAL_COMMITMENT_GENERATORS
    def determine_final_commitment_projects():
        """
        Get the list of generators for which the current stage is the final
        commitment stage
        """
        final_commitment_projects = list()
        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project",
                                   "last_commitment_stage"]
                )

        for row in zip(dynamic_components["project"],
                       dynamic_components["last_commitment_stage"]):
            if row[1] == stage:
                final_commitment_projects.append(row[0])
            else:
                pass

        return final_commitment_projects

    data_portal.data()["FINAL_COMMITMENT_PROJECTS"] = {
        None: determine_final_commitment_projects()
    }

    # FIXED_COMMITMENT_GENERATORS
    def determine_fixed_commitment_projects():
        """
        Get the list of generators whose commitment has already been fixed and
        the fixed commitment
        """
        fixed_commitment_df = \
            read_csv(os.path.join(scenario_directory, horizon,
                                  "pass_through_inputs",
                                  "fixed_commitment.tab"),
                     sep='\t')

        fixed_commitment_projects = \
            set(fixed_commitment_df["project"].tolist())

        return fixed_commitment_projects

    # Load data only if we have projects that have already been committed
    # Otherwise, leave uninitialized
    if len(determine_fixed_commitment_projects()) > 0:
        data_portal.data()["FIXED_COMMITMENT_PROJECTS"] = {
            None: determine_fixed_commitment_projects()
        }

        # Generators that whose final commitment was in a prior stage
        # The fixed commitment by project and timepoint
        data_portal.load(filename=os.path.join(scenario_directory,
                                               horizon, "pass_through_inputs",
                                               "fixed_commitment.tab"),
                         select=("project", "timepoint", "commitment"),
                         param=m.fixed_commitment,
                         )
    else:
        pass


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
            "pass_through_inputs", "fixed_commitment.tab"), "ab") \
            as fixed_commitment_file:
        fixed_commitment_writer = writer(fixed_commitment_file, delimiter="\t")
        for (g, tmp) in m.FINAL_COMMITMENT_PROJECT_OPERATIONAL_TIMEPOINTS:
            fixed_commitment_writer.writerow(
                [g, tmp, stage, m.Commitment[g, tmp].expr.value]
            )
