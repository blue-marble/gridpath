# Copyright 2016-2020 Blue Marble Analytics LLC.
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

import os.path
import pandas as pd
from pyomo.environ import Param, PercentFraction, Constraint

from gridpath.auxiliary.auxiliary import get_required_subtype_modules
from gridpath.project.operations.common_functions import load_operational_type_modules
import gridpath.project.operations.operational_types as op_type


def generic_add_model_components(
    m,
    d,
    scenario_directory,
    subproblem,
    stage,
    reserve_projects_set,
    reserve_project_operational_timepoints_set,
    reserve_provision_variable_name,
    reserve_provision_ramp_rate_limit_param,
    reserve_provision_ramp_rate_limit_constraint,
):
    """
    Reserve-related components that will be used by the operational_type
    modules
    :param m:
    :param d:
    :param reserve_projects_set:
    :param reserve_project_operational_timepoints_set:
    :param reserve_provision_variable_name:
    :param reserve_provision_ramp_rate_limit_param:
    :param reserve_provision_ramp_rate_limit_constraint:
    :return:
    """

    # Ramp rate reserve limit (response time reserve limit)
    # Some reserve products may require that generators respond within a
    # certain amount of time, e.g. 1 minute, 10 minutes, etc.
    # The maximum amount of reserves that a generator can provide is
    # therefore limited by its ramp rate, e.g. if it can ramp up 60 MW an hour,
    # then it will only be able to provide 10 MW of upward reserve for a
    # reserve product with a 10-minute response requirement \
    # Here, this derate param is specified as a fraction of generator capacity
    # Defaults to 1 if not specified
    setattr(
        m,
        reserve_provision_ramp_rate_limit_param,
        Param(getattr(m, reserve_projects_set), within=PercentFraction, default=1),
    )

    # Import needed operational modules
    required_operational_modules = get_required_subtype_modules(
        scenario_directory=scenario_directory,
        subproblem=subproblem,
        stage=stage,
        which_type="operational_type",
    )

    imported_operational_modules = load_operational_type_modules(
        required_operational_modules
    )

    def reserve_provision_ramp_rate_limit_rule(mod, g, tmp):
        """
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        gen_op_type = mod.operational_type[g]
        online_capacity = (
            imported_operational_modules[gen_op_type].online_capacity_rule(mod, g, tmp)
            if hasattr(
                imported_operational_modules[gen_op_type], "online_capacity_rule"
            )
            else op_type.online_capacity_rule(mod, g, tmp)
        )

        return (
            getattr(mod, reserve_provision_variable_name)[g, tmp]
            <= getattr(mod, reserve_provision_ramp_rate_limit_param)[g]
            * online_capacity
        )

    setattr(
        m,
        reserve_provision_ramp_rate_limit_constraint,
        Constraint(
            getattr(m, reserve_project_operational_timepoints_set),
            rule=reserve_provision_ramp_rate_limit_rule,
        ),
    )


def generic_load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    subproblem,
    stage,
    ramp_rate_limit_column_name,
    reserve_provision_ramp_rate_limit_param,
):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param ramp_rate_limit_column_name:
    :param reserve_provision_ramp_rate_limit_param:
    :return:
    """

    columns_to_import = ("project",)
    params_to_import = ()
    projects_file_header = pd.read_csv(
        os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs", "projects.tab"
        ),
        sep="\t",
        header=None,
        nrows=1,
    ).values[0]

    # Import reserve provision ramp rate limit parameter only if
    # column is present
    # Otherwise, the ramp rate limit param goes to its default of 1
    if ramp_rate_limit_column_name in projects_file_header:
        columns_to_import += (ramp_rate_limit_column_name,)
        params_to_import += (getattr(m, reserve_provision_ramp_rate_limit_param),)

    # Load the needed data
    data_portal.load(
        filename=os.path.join(
            scenario_directory, subproblem, stage, "inputs", "projects.tab"
        ),
        select=columns_to_import,
        param=params_to_import,
    )
