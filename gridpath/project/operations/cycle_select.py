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
The **gridpath.project.operations.cycle_select** module is a project-level
module that adds to the formulation components that describe cycle selection 
constraints, i.e. mutually exclusive syncing of projects. An example might be a plant 
that can be operated in either simple cycle or combined cycle mode. This plant would 
be described by multiple projects with mutually exclusive Sync variables, i.e. only 
one of the projects can be synced at any time.
"""

import csv
import os.path
from pyomo.environ import Set, Constraint


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
    The tables below list the Pyomo model components defined in the
    'gen_commit_bin' module followed below by the respective components
    defined in the 'gen_commit_lin" module.

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`GEN_W_CYCLE_SELECT`                                            |
    | | *Within*: :code:`GEN_COMMIT_BINLIN`                                   |
    |                                                                         |
    | Projects that have "cycle select" constraints.                          |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_CYCLE_SELECT_BY_GEN`                                       |
    | | *Defined over*: :code:`GEN_W_CYCLE_SELECT`                            |
    | | *Within*: :code:`GEN_COMMIT_BINLIN`                                   |
    |                                                                         |
    | Indexed set that describes each project's list of "cycle select" --     |
    | projects that cannot be 'synced' when this project is synced, e.g. when |
    | choosing simple-cycle vs. combined cycle operational model.             |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_W_GEN_CYCLE_SELECT_OPR_TMPS`                               |
    |                                                                         |
    | Three-dimensional set with generators of the respective operational     |
    | type, their "cycle select" projects, and their their operational        |
    | timepoints. Note that projects that don't have "cycle select" projects  |
    | are not included in this set.                                           |
    +-------------------------------------------------------------------------+

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +-------------------------------------------------------------------------+
    | | :code:`Gen_Commit_BinLin_Select_Cycle_Constraint`                     |
    | | *Defined over*: :code:`GEN_W_GEN_CYCLE_SELECT_OPR_TMPS`               |
    |                                                                         |
    | This generator can only be synced if the "cycle select" generator is    |
    | not synced (the sum of the Sync variables of the two must be less than  |
    | or equal to 1.                                                          |
    +-------------------------------------------------------------------------+

    """

    # Sets

    m.GEN_W_CYCLE_SELECT = Set(within=m.GEN_COMMIT_BINLIN)

    m.GEN_CYCLE_SELECT_BY_GEN = Set(m.GEN_W_CYCLE_SELECT, within=m.GEN_COMMIT_BINLIN)

    m.GEN_W_GEN_CYCLE_SELECT_OPR_TMPS = Set(
        dimen=3,
        initialize=lambda mod: [
            (g, g_cycle, tmp)
            for g in mod.GEN_W_CYCLE_SELECT
            for p in mod.OPR_PRDS_BY_PRJ[g]
            for tmp in mod.TMPS_IN_PRD[p]
            for g_cycle in mod.GEN_CYCLE_SELECT_BY_GEN[g]
        ],
    )

    # Constraints
    def select_cycle_constraint_rule(mod, g, g_cycle_select, tmp):
        """ """
        # Find the optye for g
        bin_or_lin_optype = mod.operational_type[g]
        if bin_or_lin_optype == "gen_commit_bin":
            g_optype = "Bin"
        elif bin_or_lin_optype == "gen_commit_lin":
            g_optype = "Lin"
        else:
            raise ValueError(
                """GridPath ERROR:
            Allowed types are 'gen_commit_bin' or 'gen_commit_lin'.
            You used {}.""".format(
                    bin_or_lin_optype
                )
            )

        # Find the optype for g_cycle_select (this may be different from g's optype)
        if mod.operational_type[g_cycle_select] == "gen_commit_bin":
            g_cycle_optype = "Bin"
        elif mod.operational_type[g_cycle_select] == "gen_commit_lin":
            g_cycle_optype = "Lin"
        else:
            raise ValueError(
                "Cycle selection can only apply to projects of the "
                "gen_commit_bin and gen_commit_lin operational types. "
                "The operational type of {} is {}.".format(
                    g_cycle_select, mod.operational_type[g_cycle_select]
                )
            )

        return (
            getattr(mod, "GenCommit{}_Synced".format(g_optype))[g, tmp]
            + getattr(mod, "GenCommit{}_Synced".format(g_cycle_optype))[
                g_cycle_select, tmp
            ]
            <= 1
        )

    m.Gen_Commit_BinLin_Select_Cycle_Constraint = Constraint(
        m.GEN_W_GEN_CYCLE_SELECT_OPR_TMPS, rule=select_cycle_constraint_rule
    )


def load_model_data(
    mod,
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
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    # Load any projects for cycle selection
    cycle_selection_tab_file = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "cycle_selection.tab",
    )

    cycle_selection_by_project = {}
    if os.path.exists(cycle_selection_tab_file):
        with open(cycle_selection_tab_file) as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)  # skip header
            for row in reader:
                [g, cycle_select_g] = row
                if g in cycle_selection_by_project.keys():
                    cycle_selection_by_project[g].append(cycle_select_g)
                else:
                    cycle_selection_by_project[g] = [cycle_select_g]

        data_portal.data()["GEN_W_CYCLE_SELECT"] = sorted(
            list(set(cycle_selection_by_project.keys()))
        )

        data_portal.data()["GEN_CYCLE_SELECT_BY_GEN"] = cycle_selection_by_project
