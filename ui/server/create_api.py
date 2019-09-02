# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

# RESTful API api
from ui.server.api.home import ServerStatus
from ui.server.api.scenario_detail import ScenarioDetailAPI
from ui.server.api.scenario_results import \
  ScenarioResultsOptions, ScenarioResultsTable, \
  ScenarioResultsIncludedTables, ScenarioResultsPlot, \
  ScenarioResultsIncludedPlots
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
    add_home_resource(api=api)
    add_view_data_resources(api=api, db_path=db_path)


def add_scenarios_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API api for the Angular 'scenarios' component.
    """
    # Scenario list
    api.add_resource(Scenarios, '/scenarios/',
                     resource_class_kwargs={'db_path': db_path}
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
        '/scenarios/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )


def add_scenario_new_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API for the Angular 'scenario-new' component.
    """
    api.add_resource(
        ScenarioNewAPI,
        '/scenario-new',
        resource_class_kwargs={'db_path': db_path}
    )


def add_scenario_inputs_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API for the Angular 'scenario-inputs' component.
    """
    api.add_resource(
        ScenarioInputs,
        '/scenarios/<scenario_id>/<table_type>/<table>/<row>',
        resource_class_kwargs={'db_path': db_path}
    )


def add_home_resource(api):
    """
    :param api:

    Add API for the Angular 'home' component.
    """
    # Server status
    api.add_resource(ServerStatus, '/server-status')


def add_scenario_results_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API for the Angular 'scenario-results' component.
    """

    api.add_resource(
        ScenarioResultsOptions,
        '/scenarios/<scenario_id>/scenario-results-options',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsPlot,
        '/scenarios/<scenario_id>/results/<plot>/<load_zone>/<rps_zone>'
        '/<carbon_cap_zone>/<period>/<horizon>/<stage>/<project>/<ymax>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsIncludedPlots,
        '/scenarios/results/plots',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsIncludedTables,
        '/scenarios/results/tables',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsTable,
        '/scenarios/<scenario_id>/results/<table>',
        resource_class_kwargs={'db_path': db_path}
    )


def add_view_data_resources(api, db_path):
    """

    :param api:
    :param db_path:
    :return:
    """
    api.add_resource(
      ViewDataAPI,
      '/scenarios/<scenario_id>/<table>',
      resource_class_kwargs={'db_path': db_path}
    )
