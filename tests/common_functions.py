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

from pyomo.environ import AbstractModel, DataPortal
from gridpath.auxiliary.dynamic_components import DynamicComponents


def add_model_components(
    prereq_modules,
    module_to_test,
    model,
    d,
    test_data_dir,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """
    Create abstract model, add components from prerequisite modules, add
    components from the module being tested
    :param prereq_modules:
    :param module_to_test:
    :param model:
    :param dynamic_inputs:
    :return:
    """
    for m in prereq_modules:
        if hasattr(m, "add_model_components"):
            m.add_model_components(
                model,
                d,
                test_data_dir,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
            )
    if hasattr(module_to_test, "add_model_components"):
        module_to_test.add_model_components(
            model,
            d,
            test_data_dir,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
        )

    return model


def create_abstract_model(
    prereq_modules,
    module_to_test,
    test_data_dir,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """
    Determine dynamic components and build abstract model
    :param prereq_modules:
    :param module_to_test:
    :param test_data_dir:
    :param stage:
    :param stage:
    :return:
    """
    d = DynamicComponents()
    m = AbstractModel()
    add_model_components(
        prereq_modules,
        module_to_test,
        m,
        d,
        test_data_dir,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
    )

    return m, d


def add_components_and_load_data(
    prereq_modules,
    module_to_test,
    test_data_dir,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """
    Test that data are loaded with no errors
    :return:
    """

    m, d = create_abstract_model(
        prereq_modules,
        module_to_test,
        test_data_dir,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
    )
    data = DataPortal()
    for mod in prereq_modules:
        if hasattr(mod, "load_model_data"):
            mod.load_model_data(
                m,
                d,
                data,
                test_data_dir,
                weather_iteration,
                hydro_iteration,
                availability_iteration,
                subproblem,
                stage,
            )
    if hasattr(module_to_test, "load_model_data"):
        module_to_test.load_model_data(
            m,
            d,
            data,
            test_data_dir,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
        )

    return m, data
