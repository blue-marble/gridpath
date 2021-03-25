# Copyright 2016-2021 Blue Marble Analytics LLC.
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
This operational type is the same as the *gen_commit_bin* operational type,
but the commitment decisions are declared as continuous (with bounds of 0 to
1) instead of binary, so 'partial' generators can be committed. This
linear relaxation treatment can be helpful in situations when mixed-integer
problem run-times are long and is similar to loosening the MIP gap (but can
target specific generators). Please refer to the *gen_commit_bin* module for
more information on the formulation.
"""

from gridpath.project.operations.operational_types.common_functions import \
    update_dispatch_results_table, validate_opchars
import gridpath.project.operations.operational_types.gen_commit_unit_common \
    as gen_commit_unit_common


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    See the formulation documentation in the
    gen_commit_unit_common.add_model_components().
    """

    gen_commit_unit_common.add_model_components(
        m=m, d=d,
        scenario_directory=scenario_directory,
        subproblem=subproblem, stage=stage,
        bin_or_lin_optype="gen_commit_lin"
    )
    

# Operational Type Methods
###############################################################################

def power_provision_rule(mod, g, tmp):
    """
    Power provision for gen_commit_lin generators is a variable constrained
    constrained to be between the generator's minimum stable level and its
    capacity if the generator is committed and 0 otherwise.
    """
    return gen_commit_unit_common.power_provision_rule(
        mod, g, tmp, "Lin"
    )


def commitment_rule(mod, g, tmp):
    """
    Commitment decision in each timepoint
    """
    return gen_commit_unit_common.commitment_rule(
        mod, g, tmp, "Lin"
    )


def online_capacity_rule(mod, g, tmp):
    """
    Capacity online in each timepoint.
    """
    return gen_commit_unit_common.online_capacity_rule(
        mod, g, tmp, "Lin"
    )


def variable_om_cost_rule(mod, g, tmp):
    """
    Variable O&M cost has two components which are additive:
    1. A fixed variable O&M rate (cost/MWh) that doesn't change with loading
       levels: :code:`variable_om_cost_per_mwh`.
    2. A variable variable O&M rate that changes with the loading level,
       similar to the heat rates. The idea is to represent higher variable cost
       rates at lower loading levels. This is captured in the
       :code:`GenCommitLin_Variable_OM_Cost_By_LL` decision variable. If no
       variable O&M curve inputs are provided, this component will be zero.

    Most users will only use the first component, which is specified in the
    operational characteristics table.  Only operational types with
    commitment decisions can have the second component.

    We need to explicitly have the op type method here because of auxiliary
    consumption. The default method takes Power_Provision_MW multiplied by
    the variable cost, and Power_Provision_MW is equal to Provide_Power_MW
    minus the auxiliary consumption. The variable cost should be applied to
    the gross power.
    """
    return gen_commit_unit_common.variable_om_cost_rule(
        mod, g, tmp, "Lin"
    )


def variable_om_cost_by_ll_rule(mod, g, tmp, s):
    """
    Variable O&M cost has two components which are additive:
    1. A fixed variable O&M rate (cost/MWh) that doesn't change with loading
       levels: :code:`variable_om_cost_per_mwh`.
    2. A variable variable O&M rate that changes with the loading level,
       similar to the heat rates. The idea is to represent higher variable cost
       rates at lower loading levels. This is captured in the
       :code:`GenCommitLin_Variable_OM_Cost_By_LL` decision variable. If no
       variable O&M curve inputs are provided, this component will be zero.

    Most users will only use the first component, which is specified in the
    operational characteristics table.  Only operational types with
    commitment decisions can have the second component.
    """
    return gen_commit_unit_common.variable_om_cost_by_ll_rule(
        mod, g, tmp, s, "Lin"
    )


def startup_cost_simple_rule(mod, g, tmp):
    """
    Simple startup costs are applied in each timepoint based on the amount of
    capacity (in MW) that is started up in that timepoint and the startup cost
    parameter.
    """
    return gen_commit_unit_common.startup_cost_simple_rule(
        mod, g, tmp, "Lin"
    )


def startup_cost_by_st_rule(mod, g, tmp):
    """
    Startup costs are applied in each timepoint based on the amount of capacity
    (in MW) that is started up in that timepoint for a given startup type and
    the startup cost parameter for that startup type. We take the sum across
    all startup types since only one startup type is active at the same time.
    """
    return gen_commit_unit_common.startup_cost_by_st_rule(
        mod, g, tmp, "LIN", "Lin"
    )


def shutdown_cost_rule(mod, g, tmp):
    """
    Shutdown costs are applied in each timepoint based on the amount of
    capacity (in Mw) that is shut down in that timepoint and the shutdown
    cost parameter.
    """
    return gen_commit_unit_common.shutdown_cost_rule(
        mod, g, tmp, "Lin"
    )


def fuel_burn_by_ll_rule(mod, g, tmp, s):
    """
    """
    return gen_commit_unit_common.fuel_burn_by_ll_rule(
        mod, g, tmp, s, "Lin"
    )


def startup_fuel_burn_rule(mod, g, tmp):
    """
    Startup fuel burn is applied in each timepoint based on the amount of
    capacity (in MW) that is started up in that timepoint and the startup
    fuel parameter. This does not vary by startup type.
    """
    return gen_commit_unit_common.startup_fuel_burn_rule(
        mod, g, tmp, "Lin"
    )


def power_delta_rule(mod, g, tmp):
    """
    Ramp between this timepoint and the previous timepoint.
    Actual ramp rate in MW/hr depends on the duration of the timepoints.
    This is only used in tuning costs, so fine to skip for linked horizon's
    first timepoint.
    """
    return gen_commit_unit_common.power_delta_rule(
        mod, g, tmp, "Lin"
    )


def fix_commitment(mod, g, tmp):
    """
    """
    return gen_commit_unit_common.fix_commitment(
        mod, g, tmp, "Lin"
    )


def operational_violation_cost_rule(mod, g, tmp):
    """

    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return gen_commit_unit_common.operational_violation_cost_rule(
        mod, g, tmp, "lin", "Lin"
    )


# Input-Output
###############################################################################

def load_model_data(
    mod, d, data_portal, scenario_directory, subproblem, stage
):
    """
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    gen_commit_unit_common.load_model_data(
        mod=mod, d=d, data_portal=data_portal,
        scenario_directory=scenario_directory, subproblem=subproblem,
        stage=stage, bin_or_lin_optype="gen_commit_lin", bin_or_lin="lin",
        BIN_OR_LIN="LIN"
    )


def export_results(
    mod, d, scenario_directory, subproblem, stage
):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param mod:
    :param d:
    :return:
    """
    gen_commit_unit_common.export_results(
        mod=mod, d=d, scenario_directory=scenario_directory,
        subproblem=subproblem, stage=stage, BIN_OR_LIN="LIN",
        Bin_or_Lin="Lin", bin_or_lin="lin",
        results_filename="dispatch_continuous_commit.csv"
    )


# Database
###############################################################################

def import_model_results_to_database(
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
    if not quiet:
        print("project dispatch continuous commit")

    update_dispatch_results_table(
        db=db, c=c, results_directory=results_directory,
        scenario_id=scenario_id, subproblem=subproblem, stage=stage,
        results_file="dispatch_continuous_commit.csv"
    )


# Validation
###############################################################################

def validate_inputs(
    scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and validate the inputs

    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    # Validate operational chars table inputs
    opchar_df = validate_opchars(
        scenario_id, subscenarios, subproblem, stage, conn, "gen_commit_lin"
    )
