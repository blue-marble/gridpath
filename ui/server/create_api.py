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

# RESTful API api
from ui.server.api.home import ServerStatus, ScenarioRunStatus, ScenarioValidationStatus
from ui.server.api.scenario_detail import ScenarioDetailAPI
from ui.server.api.scenario_results import (
    ScenarioResultsOptions,
    ScenarioResultsTable,
    ScenarioResultsIncludedTables,
    ScenarioResultsPlot,
    ScenarioResultsIncludedPlots,
)
from ui.server.api.scenario_new import ScenarioNewAPI
from ui.server.api.scenarios import Scenarios
from ui.server.api.scenario_inputs import ScenarioInputs
from ui.server.api.view_data import ViewDataAPI


# Create API routes
def add_api_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add all needed API api.
    """
    add_scenarios_resources(api=api, db_path=db_path)
    add_scenario_detail_resources(api=api, db_path=db_path)
    add_scenario_results_resources(api=api, db_path=db_path)
    add_scenario_new_resources(api=api, db_path=db_path)
    add_scenario_inputs_resources(api=api, db_path=db_path)
    add_home_resource(api=api, db_path=db_path)
    add_view_data_resources(api=api, db_path=db_path)


def add_scenarios_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API api for the Angular 'scenarios' component.
    """
    # Scenario list
    api.add_resource(
        Scenarios, "/scenarios/", resource_class_kwargs={"db_path": db_path}
    )


def add_scenario_detail_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API for the Angular 'scenario-detail' component.
    """
    # Refactored
    api.add_resource(
        ScenarioDetailAPI,
        "/scenarios/<scenario_id>",
        resource_class_kwargs={"db_path": db_path},
    )


def add_scenario_new_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API for the Angular 'scenario-new' component.
    """
    api.add_resource(
        ScenarioNewAPI, "/scenario-new", resource_class_kwargs={"db_path": db_path}
    )


def add_scenario_inputs_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API for the Angular 'scenario-inputs' component.
    """
    api.add_resource(
        ScenarioInputs,
        "/scenarios/<scenario_id>/<table_type>/<table>/<row>",
        resource_class_kwargs={"db_path": db_path},
    )


def add_home_resource(api, db_path):
    """
    :param api:
    :param db_path:

    Add API for the Angular 'home' component.
    """
    # Server status
    api.add_resource(ServerStatus, "/server-status")

    # Scenario run status
    api.add_resource(
        ScenarioRunStatus, "/run-status", resource_class_kwargs={"db_path": db_path}
    )

    # Scenario validation status
    api.add_resource(
        ScenarioValidationStatus,
        "/validation-status",
        resource_class_kwargs={"db_path": db_path},
    )


def add_scenario_results_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API for the Angular 'scenario-results' component.
    """

    api.add_resource(
        ScenarioResultsOptions,
        "/scenarios/<scenario_id>/scenario-results-options",
        resource_class_kwargs={"db_path": db_path},
    )

    api.add_resource(
        ScenarioResultsPlot,
        "/scenarios/<scenario_id>/results/<plot>/<load_zone>/<energy_target_zone>"
        "/<carbon_cap_zone>/<period>/<horizon>"
        "/<start_timepoint>/<end_timepoint>"
        "/<subproblem>/<stage>/<project>/<commit_project>/<ymax>",
        resource_class_kwargs={"db_path": db_path},
    )

    api.add_resource(
        ScenarioResultsIncludedPlots,
        "/scenarios/results/plots",
        resource_class_kwargs={"db_path": db_path},
    )

    api.add_resource(
        ScenarioResultsIncludedTables,
        "/scenarios/results/tables",
        resource_class_kwargs={"db_path": db_path},
    )

    api.add_resource(
        ScenarioResultsTable,
        "/scenarios/<scenario_id>/results/<table>",
        resource_class_kwargs={"db_path": db_path},
    )


def add_view_data_resources(api, db_path):
    """

    :param api:
    :param db_path:
    :return:
    """
    api.add_resource(
        ViewDataAPI,
        "/scenarios/<scenario_id>/<table>",
        resource_class_kwargs={"db_path": db_path},
    )
