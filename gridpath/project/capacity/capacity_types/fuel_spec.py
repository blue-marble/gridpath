# Copyright 2016-2022 Blue Marble Analytics LLC.
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
This capacity type describes fuel production facilities with exogenously specified
capacity characteristics.
"""

from pyomo.environ import Set, Param, NonNegativeReals

from gridpath.auxiliary.dynamic_components import capacity_type_operational_period_sets
from gridpath.project.capacity.capacity_types.common_methods import \
    spec_determine_inputs


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """ """
    # Sets
    m.FUEL_SPEC_OPR_PRDS = Set(dimen=2)

    # Params
    m.fuel_spec_fuel_production_capacity_fuelunitperhour = Param(
        m.FUEL_SPEC_OPR_PRDS, within=NonNegativeReals
    )

    m.fuel_spec_fuel_release_capacity_fuelunitperhour = Param(
        m.FUEL_SPEC_OPR_PRDS, within=NonNegativeReals
    )

    m.fuel_spec_fuel_storage_capacity_fuelunit = Param(
        m.FUEL_SPEC_OPR_PRDS, within=NonNegativeReals
    )

    m.fuel_spec_fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr = Param(
        m.FUEL_SPEC_OPR_PRDS, within=NonNegativeReals
    )

    m.fuel_spec_fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr = Param(
        m.FUEL_SPEC_OPR_PRDS, within=NonNegativeReals
    )

    m.fuel_spec_fuel_storage_capacity_fixed_cost_per_fuelunit_yr = Param(
        m.FUEL_SPEC_OPR_PRDS, within=NonNegativeReals
    )

    # Dynamic Components
    ####################################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "FUEL_SPEC_OPR_PRDS",
    )


# Capacity Type Methods
########################################################################################


def fuel_prod_capacity_rule(mod, prj, prd):
    """
    Fuel production capacity.
    """
    return mod.fuel_spec_fuel_production_capacity_fuelunitperhour[prj, prd]


def fuel_release_capacity_rule(mod, prj, prd):
    """
    Fuel release capacity.
    """
    return mod.fuel_spec_fuel_release_capacity_fuelunitperhour[prj, prd]


def fuel_storage_capacity_rule(mod, prj, prd):
    """
    Fuel storage capacity.
    """
    return mod.fuel_spec_fuel_storage_capacity_fuelunit[prj, prd]


def capacity_cost_rule(mod, prj, prd):
    """
    The capacity cost of projects of the *fuel_spec* capacity type is a
    pre-specified number with the following costs:
    * fuel production capacity x fuel production fixed cost (per production unit-year);
    * fuel release capacity x fuel release fixed cost (per release unit-year);
    * fuel storage capacity x fuel storage fixed cost (per storage unit-year).
    """
    return (
        mod.fuel_spec_fuel_production_capacity_fuelunitperhour[prj, prd]
        * mod.fuel_spec_fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr[
            prj, prd
        ]
        + mod.fuel_spec_fuel_release_capacity_fuelunitperhour[prj, prd]
        * mod.fuel_spec_fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr[
            prj, prd
        ]
        + mod.fuel_spec_fuel_storage_capacity_fuelunit[prj, prd]
        * mod.fuel_spec_fuel_storage_capacity_fixed_cost_per_fuelunit_yr[prj, prd]
    )


# Input-Output
###############################################################################


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    project_period_list, spec_params_dict = spec_determine_inputs(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        capacity_type="fuel_spec",
    )

    data_portal.data()["FUEL_SPEC_OPR_PRDS"] = {None: project_period_list}

    data_portal.data()["fuel_spec_fuel_production_capacity_fuelunitperhour"] = spec_params_dict[
        "fuel_production_capacity_fuelunitperhour"
    ]

    data_portal.data()["fuel_spec_fuel_release_capacity_fuelunitperhour"] = spec_params_dict[
        "fuel_release_capacity_fuelunitperhour"
    ]

    data_portal.data()["fuel_spec_fuel_storage_capacity_fuelunit"] = spec_params_dict[
        "fuel_storage_capacity_fuelunit"
    ]

    data_portal.data()["fuel_spec_fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr"] = spec_params_dict[
        "fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr"
    ]

    data_portal.data()["fuel_spec_fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr"] = spec_params_dict[
        "fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr"
    ]

    data_portal.data()["fuel_spec_fuel_storage_capacity_fixed_cost_per_fuelunit_yr"] = spec_params_dict[
        "fuel_storage_capacity_fixed_cost_per_fuelunit_yr"
    ]
