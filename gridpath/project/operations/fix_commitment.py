# Copyright 2016-2023 Blue Marble Analytics LLC.
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
This module exports the commitment variables that must be fixed in the next
stage and imports the commitment variables that were fixed in the previous
stage.
"""

from csv import writer
import os.path
from pandas import read_csv
from pyomo.environ import Set, Param, NonNegativeReals, Expression


from gridpath.auxiliary.auxiliary import (
    get_required_subtype_modules,
    check_for_integer_subdirectories,
    subset_init_by_set_membership,
)
from gridpath.project.operations.common_functions import load_operational_type_modules


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`FNL_COMMIT_PRJS`                                               |
    |                                                                         |
    | The set of generators for which the current stage or any of the         |
    | previous stages is the final commitment stage.                          |
    +-------------------------------------------------------------------------+
    | | :code:`FXD_COMMIT_PRJS`                                               |
    |                                                                         |
    | The set of generators that have already had their commitment fixed in a |
    | prior commitment stage.                                                 |
    +-------------------------------------------------------------------------+
    | | :code:`FNL_COMMIT_PRJS_OPR_TMPS`                                      |
    |                                                                         |
    | Two-dimensional set of all final commitment projects and their          |
    | operational timepoints.                                                 |
    +-------------------------------------------------------------------------+
    | | :code:`FXD_COMMIT_PRJS_OPR_TMPS`                                      |
    |                                                                         |
    | Two-dimensional set of all fixed commitment projects and their          |
    | operational timepoints.                                                 |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Input Params                                                            |
    +=========================================================================+
    | | :code:`fixed_commitment`                                              |
    | | *Defined over*: :code:`FXD_COMMIT_PRJ_OPR_TMPS`                       |
    |                                                                         |
    | This param describes the fixed commitment from the prior commitment     |
    | stage for each fixed commitment project and their operational           |
    | timepoints.                                                             |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`Commitment`                                                    |
    | | *Defined over*: :code:`FNL_COMMIT_PRJ_OPR_TMPS`                       |
    |                                                                         |
    | Describes the commitment for all final commitment projects and their    |
    | operational timepoints. For the :code:`gen_commit_cap` operational      |
    | type, it describes the committed capacity in MW whereas for the         |
    | :code:`gen_commit_lin` and :code:`gen_commit_bin` operational types it  |
    | describes the binary commitment variable. This expression will be       |
    | exported so that the next stage's optimization can read it in through   |
    | the :code:`fixed_commitment` param and fix the commitment to this value.|
    +-------------------------------------------------------------------------+

    """

    # Dynamic Inputs

    required_operational_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        which_type="operational_type",
    )

    imported_operational_modules = load_operational_type_modules(
        required_operational_modules
    )

    # Sets
    ###########################################################################

    m.FNL_COMMIT_PRJS = Set()

    m.FXD_COMMIT_PRJS = Set()

    m.FNL_COMMIT_PRJ_OPR_TMPS = Set(
        dimen=2,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod,
            superset="PRJ_OPR_TMPS",
            index=0,
            membership_set=mod.FNL_COMMIT_PRJS,
        ),
    )

    m.FXD_COMMIT_PRJ_OPR_TMPS = Set(
        dimen=2,
        initialize=lambda mod: subset_init_by_set_membership(
            mod=mod,
            superset="PRJ_OPR_TMPS",
            index=0,
            membership_set=mod.FXD_COMMIT_PRJS,
        ),
    )

    # Input Params
    ###########################################################################

    m.fixed_commitment = Param(m.FXD_COMMIT_PRJ_OPR_TMPS, within=NonNegativeReals)

    # Expressions
    ###########################################################################

    def commitment_rule(mod, g, tmp):
        """
        **Expression Name**: Commitment
        **Defined Over**: FNL_COMMIT_PRJ_OPR_TMPS
        """
        gen_op_type = mod.operational_type[g]
        return imported_operational_modules[gen_op_type].commitment_rule(mod, g, tmp)

    m.Commitment = Expression(m.FNL_COMMIT_PRJ_OPR_TMPS, rule=commitment_rule)


# Commitment Functions
###############################################################################


def fix_variables(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """
    This function fixes the commitment of all fixed commitment projects by
    running the :code:`fix_commitment` function in the appropriate operational
    module.

    :param m:
    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    required_operational_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        which_type="operational_type",
    )

    imported_operational_modules = load_operational_type_modules(
        required_operational_modules
    )

    for g in m.FXD_COMMIT_PRJS:
        op_m = m.operational_type[g]
        imp_op_m = imported_operational_modules[op_m]
        if hasattr(imp_op_m, "fix_commitment"):
            for tmp in m.TMPS:
                imp_op_m.fix_commitment(m, g, tmp)


# Input-Output
###############################################################################


def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    stages = check_for_integer_subdirectories(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
        )
    )

    fixed_commitment_df = read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            "pass_through_inputs",
            "fixed_commitment.tab",
        ),
        sep="\t",
        dtype={"stage": str},
    )

    # FNL_COMMIT_PRJS
    def get_fnl_commit_prjs():
        """
        Get the list of generators for which the current stage is the final
        commitment stage or for which any of the previous stages was the
        final commitment stage.
        """
        fnl_commit_prjs = list()
        df = read_csv(
            os.path.join(
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
                "inputs",
                "projects.tab",
            ),
            sep="\t",
            usecols=["project", "last_commitment_stage"],
            dtype={"last_commitment_stage": str},
        )

        for prj, s in zip(df["project"], df["last_commitment_stage"]):
            if s == ".":
                pass
            elif s == stage or stages.index(s) < stages.index(stage):
                fnl_commit_prjs.append(prj)

        return fnl_commit_prjs

    data_portal.data()["FNL_COMMIT_PRJS"] = {None: get_fnl_commit_prjs()}

    # FXD_COMMIT_PRJS
    fxd_commit_prjs = sorted(list(set(fixed_commitment_df["project"].tolist())))
    # Load data only if we have projects that have already been committed
    # Otherwise, leave uninitialized
    if len(fxd_commit_prjs) > 0:
        # For projects whose final commitment was in a prior stage, get the
        # fixed commitment of the previous stage (by project and timepoint)
        fixed_commitment_df["stage_index"] = fixed_commitment_df.apply(
            lambda row: stages.index(row["stage"]), axis=1
        )
        relevant_commitment_df = fixed_commitment_df[
            fixed_commitment_df["stage_index"] == stages.index(stage) - 1
        ]
        projects_timepoints = list(
            zip(relevant_commitment_df["project"], relevant_commitment_df["timepoint"])
        )
        fixed_commitment_dict = dict(
            zip(projects_timepoints, relevant_commitment_df["commitment"])
        )

        data_portal.data()["FXD_COMMIT_PRJS"] = {None: fxd_commit_prjs}
        data_portal.data()["FXD_COMMIT_PRJ_OPR_TMPS"] = {None: projects_timepoints}
        data_portal.data()["fixed_commitment"] = fixed_commitment_dict


def export_pass_through_inputs(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
):
    """
    This function exports the commitment for all final commitment projects,
    i.e. projects for which the current stage or any of the previous stages
    is the final commitment stage.

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :return:
    """
    df = read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        sep="\t",
        usecols=["project", "last_commitment_stage"],
    )

    final_commitment_stage_dict = dict(zip(df["project"], df["last_commitment_stage"]))

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            "pass_through_inputs",
            "fixed_commitment.tab",
        ),
        "a",
    ) as fixed_commitment_file:
        fixed_commitment_writer = writer(
            fixed_commitment_file, delimiter="\t", lineterminator="\n"
        )
        for g, tmp in m.FNL_COMMIT_PRJ_OPR_TMPS:
            fixed_commitment_writer.writerow(
                [
                    g,
                    tmp,
                    stage,
                    final_commitment_stage_dict[g],
                    m.Commitment[g, tmp].expr.value,
                ]
            )


def write_pass_through_file_headers(pass_through_directory):
    with open(
        os.path.join(pass_through_directory, "fixed_commitment.tab"),
        "w",
        newline="",
    ) as fixed_commitment_file:
        fixed_commitment_writer = writer(
            fixed_commitment_file, delimiter="\t", lineterminator="\n"
        )
        fixed_commitment_writer.writerow(
            [
                "project",
                "timepoint",
                "stage",
                "final_commitment_stage",
                "commitment",
            ]
        )
