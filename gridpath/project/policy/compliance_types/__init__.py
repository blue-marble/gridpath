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

"""

from pyomo.environ import Set

from gridpath.auxiliary.auxiliary import (
    get_required_subtype_modules,
    load_subtype_modules,
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
    """ """
    # Import needed operational modules
    required_compliance_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        which_type="compliance_type",
    )

    imported_compliance_modules = load_subtype_modules(
        required_subtype_modules=required_compliance_modules,
        package="gridpath.project.policy.compliance_types",
        required_attributes=[],
    )

    # Add any components specific to the operational modules
    for comp_m in required_compliance_modules:
        imp_op_m = imported_compliance_modules[comp_m]
        if hasattr(imp_op_m, "add_model_components"):
            imp_op_m.add_model_components(
                m,
                d,
                scenario_directory,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
            )


# Compliance Type Module Method Defaults
###############################################################################


def contribution_in_timepoint(mod, prj, policy, tmp):
    """
    Defaults to 0
    """
    return 0


def contribution_in_horizon(mod, prj, policy, bt, h):
    """
    Defaults to 0
    """
    return 0
