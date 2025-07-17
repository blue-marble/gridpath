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
import math
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
    | | :code:`energy_spec_power_capacity_mwh`                            |
    | | *Defined over*: :code:`GEN_ENERGY_SPEC_OPR_PRDS`                      |
    | | *Within*: :code:`NonNegativeReals`                                    |
    | | *Default*: :code:`Infinity`                                           |
    |                                                                         |
    | The project's specified power capacity (in MW) in each operational      |
    | period. Defaults to infinity in if not specified.                       |
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

    m.energy_spec_energy_mwh = Param(
        m.GEN_ENERGY_SPEC_OPR_PRDS, within=NonNegativeReals
    )

    # Will need to go through capacity.py if we allow shaping capacity for
    # candidate energy resources eventually
    m.shaping_capacity_mw = Param(
        m.GEN_ENERGY_SPEC_OPR_PRDS, within=NonNegativeReals, default=0
    )

    # Any fixed costs associated with the energy purchased
    m.energy_spec_fixed_cost_per_energy_mwh_yr = Param(
        m.GEN_ENERGY_SPEC_OPR_PRDS, within=NonNegativeReals
    )

    m.fixed_cost_per_shaping_mw_yr = Param(
        m.GEN_ENERGY_SPEC_OPR_PRDS, within=NonNegativeReals, default=0
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


def energy_rule(mod, g, p):
    """ """
    return mod.energy_spec_energy_mwh[g, p]


def fixed_cost_rule(mod, g, p):
    """
    The fixed cost of projects of the *gen_energy* capacity type is a
    pre-specified number equal to the energy times the per-mwh fixed cost for
    of the project's operational periods.
    """
    return (
        mod.energy_spec_energy_mwh[g, p]
        * mod.energy_spec_fixed_cost_per_energy_mwh_yr[g, p]
        + mod.shaping_capacity_mw[g, p] * mod.fixed_cost_per_shaping_mw_yr[g, p]
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
        capacity_type="energy_spec",
    )

    data_portal.data()["GEN_ENERGY_SPEC_OPR_PRDS"] = {None: project_period_list}

    data_portal.data()["energy_spec_energy_mwh"] = spec_params_dict[
        "specified_energy_mwh"
    ]

    data_portal.data()["energy_spec_fixed_cost_per_energy_mwh_yr"] = spec_params_dict[
        "fixed_cost_per_energy_mwh_yr"
    ]

    # TODO: it's ugly to handle the default 0 here; figure out how to pass
    #  "no value" and default to the 0 per the model formulation
    for k in spec_params_dict["shaping_capacity_mw"].keys():
        if math.isnan(spec_params_dict["shaping_capacity_mw"][k]):
            spec_params_dict["shaping_capacity_mw"][k] = 0
        if math.isnan(spec_params_dict["fixed_cost_per_shaping_mw_yr"][k]):
            spec_params_dict["fixed_cost_per_shaping_mw_yr"][k] = 0
    data_portal.data()["shaping_capacity_mw"] = spec_params_dict["shaping_capacity_mw"]
    data_portal.data()["fixed_cost_per_shaping_mw_yr"] = spec_params_dict[
        "fixed_cost_per_shaping_mw_yr"
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
        conn=conn,
        subscenarios=subscenarios,
        subproblem=subproblem,
        capacity_type="energy_spec",
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
