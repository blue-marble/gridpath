# Copyright 2016-2024 Blue Marble Analytics LLC.
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
Specified energy-only project. The energy will be shaped by the operational 
type.

"""

import os.path
import pandas as pd
from pyomo.environ import Set, Param, NonNegativeReals

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.dynamic_components import capacity_type_operational_period_sets
from gridpath.auxiliary.validations import (
    get_projects,
    get_expected_dtypes,
    write_validation_to_database,
    validate_dtypes,
    validate_values,
    validate_idxs,
    validate_missing_inputs,
)
from gridpath.project.capacity.capacity_types.common_methods import (
    spec_get_inputs_from_database,
    spec_write_tab_file,
    spec_determine_inputs,
)


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
    | | :code:`GEN_ENERGY_SPEC_OPR_PRDS`                                     |
    |                                                                         |
    | Two-dimensional set of project-period combinations that helps describe  |
    | the project capacity available in a given period. This set is added to  |
    | the list of sets to join to get the final :code:`PRJ_OPR_PRDS` set      |
    | defined in **gridpath.project.capacity.capacity**.                      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_energy_spec_power_capacity_mwh`                            |
    | | *Defined over*: :code:`GEN_ENERGY_SPEC_OPR_PRDS`                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`Infinity`                                           |
    |                                                                         |
    | The project's specified power capacity (in MW) in each operational      |
    | period. Defaults to infinity in if not specified.                       |
    +-------------------------------------------------------------------------+
    | | :code:`gen_energy_energy_capacity_mwh`                                |
    | | *Defined over*: :code:`GEN_ENERGY_SPEC_OPR_PRDS`                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's specified energy capacity (in MWh) in each                |
    | operational period.                                                     |
    +-------------------------------------------------------------------------+
    | | :code:`gen_energy_fixed_cost_per_mw_yr`                               |
    | | *Defined over*: :code:`GEN_ENERGY_SPEC_OPR_PRDS`                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's fixed cost for the power components (in $ per             |
    | MW-yr.) in each operational period. This cost will be added to the      |
    | objective function but will not affect optimization decisions.          |
    +-------------------------------------------------------------------------+
    | | :code:`gen_energy_fixed_cost_per_stor_mwh_yr`                              |
    | | *Defined over*: :code:`GEN_ENERGY_SPEC_OPR_PRDS`                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's fixed cost for the energy components (in $ per            |
    | MWh-yr.) in each operational period. This cost will be added to the     |
    | objective function but will not affect optimization decisions.          |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.GEN_ENERGY_SPEC_OPR_PRDS = Set(dimen=2)

    # Required Params
    ###########################################################################

    # TODO: possibly remove the power param for this type and have the
    #  shaping be done entirely by the operational params
    m.gen_energy_spec_power_capacity_mw = Param(
        m.GEN_ENERGY_SPEC_OPR_PRDS, within=NonNegativeReals, default=float("inf")
    )

    m.gen_energy_spec_energy_mwh = Param(
        m.GEN_ENERGY_SPEC_OPR_PRDS, within=NonNegativeReals
    )

    m.gen_energy_spec_fixed_cost_per_mw_yr = Param(
        m.GEN_ENERGY_SPEC_OPR_PRDS, within=NonNegativeReals
    )

    m.gen_energy_spec_fixed_cost_per_energy_mwh_yr = Param(
        m.GEN_ENERGY_SPEC_OPR_PRDS, within=NonNegativeReals
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "GEN_ENERGY_SPEC_OPR_PRDS",
    )


# Capacity Type Methods
###############################################################################


def capacity_rule(mod, g, p):
    """
    The power capacity of projects of the *gen_energy* capacity type is a
    pre-specified number for each of the project's operational periods.
    """
    return mod.gen_energy_spec_power_capacity_mw[g, p]


def energy_rule(mod, g, p):
    """ """
    return mod.gen_energy_spec_energy_mwh[g, p]


def energy_stor_capacity_rule(mod, g, p):
    """
    The energy capacity of projects of the *gen_energy* capacity type is a
    pre-specified number for each of the project's operational periods.
    """
    return 0


def fixed_cost_rule(mod, g, p):
    """
    The fixed cost of projects of the *gen_energy* capacity type is a
    pre-specified number equal to the power capacity times the per-mw fixed
    cost plus the energy capacity times the per-mwh fixed cost for each of
    the project's operational periods.
    """
    return (
        mod.gen_energy_spec_power_capacity_mw[g, p]
        * mod.gen_energy_spec_fixed_cost_per_mw_yr[g, p]
        + mod.gen_energy_spec_energy_mwh[g, p]
        * mod.gen_energy_spec_fixed_cost_per_energy_mwh_yr[g, p]
    )


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
    project_period_list, spec_params_dict = spec_determine_inputs(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        capacity_type="gen_energy",
    )

    data_portal.data()["GEN_ENERGY_SPEC_OPR_PRDS"] = {None: project_period_list}

    data_portal.data()["gen_energy_spec_power_capacity_mw"] = spec_params_dict[
        "specified_capacity_mw"
    ]

    data_portal.data()["gen_energy_energy_capacity_mwh"] = spec_params_dict[
        "specified_capacity_mwh"
    ]

    data_portal.data()["gen_energy_fixed_cost_per_mw_yr"] = spec_params_dict[
        "fixed_cost_per_mw_yr"
    ]

    data_portal.data()["gen_energy_fixed_cost_per_stor_mwh_yr"] = spec_params_dict[
        "fixed_cost_per_stor_mwh_yr"
    ]


# Database
###############################################################################


def get_model_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    spec_params = spec_get_inputs_from_database(
        conn=conn, subscenarios=subscenarios, capacity_type="gen_energy"
    )
    return spec_params


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    Get inputs from database and write out the model input .tab file
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    spec_project_params = get_model_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )

    # If spec_capacity_period_params.tab file already exists, append
    # rows to it
    spec_write_tab_file(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        spec_project_params=spec_project_params,
    )
