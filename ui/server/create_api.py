# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

# RESTful API api
from ui.server.api.home import ServerStatus
from ui.server.api.scenario_detail import ScenarioDetailAPI
from ui.server.api.scenario_results import \
  ScenarioResultsOptions, ScenarioResultsDispatchPlot, \
  ScenarioResultsCapacityNewPlot, ScenarioResultsCapacityRetiredPlot, \
  ScenarioResultsCapacityTotalPlot, ScenarioResultsEnergyPlot, \
  ScenarioResultsCostPlot, ScenarioResultsCapacityFactorPlot, \
  ScenarioResultsTable, ScenarioResultsIncludedTables, ScenarioResultsPlot, \
  ScenarioResultsIncludedPlots
from ui.server.api.scenario_new import ScenarioNewAPI
from ui.server.api.scenarios import Scenarios
from ui.server.api.view_data import ViewDataTemporalTimepoints, \
  ViewDataGeographyLoadZones, ViewDataProjectLoadZones, \
  ViewDataTransmissionLoadZones, ViewDataSystemLoad, ViewDataProjectPortfolio, \
  ViewDataProjectExistingCapacity, ViewDataProjectExistingFixedCost, \
  ViewDataProjectNewPotential, ViewDataProjectNewCost, \
  ViewDataProjectAvailability, ViewDataProjectOpChar, ViewDataFuels, \
  ViewDataFuelPrices, ViewDataTransmissionPortfolio, \
  ViewDataTransmissionExistingCapacity, ViewDataTransmissionOpChar, \
  ViewDataTransmissionHurdleRates, ViewDataTransmissionSimFlowLimits, \
  ViewDataTransmissionSimFlowLimitsLineGroups, ViewDataLFUpBAs, \
  ViewDataProjectLFUpBAs, ViewDataLFUpReq, ViewDataLFDownBAs, \
  ViewDataProjectLFDownBAs, ViewDataLFDownReq, ViewDataRegUpBAs, \
  ViewDataProjectRegUpBAs, ViewDataRegUpReq, ViewDataRegDownBAs, \
  ViewDataProjectRegDownBAs, ViewDataRegDownReq, ViewDataSpinBAs, \
  ViewDataProjectSpinBAs, ViewDataSpinReq, ViewDataFreqRespBAs, \
  ViewDataProjectFreqRespBAs, ViewDataFreqRespReq, ViewDataRPSBAs, \
  ViewDataProjectRPSBAs, ViewDataRPSReq, ViewDataCarbonCapBAs, \
  ViewDataProjectCarbonCapBAs, ViewDataTransmissionCarbonCapBAs, \
  ViewDataCarbonCapReq, ViewDataPRMBAs, ViewDataProjectPRMBAs, \
  ViewDataPRMReq, ViewDataProjectELCCChars, ViewDataELCCSurface, \
  ViewDataEnergyOnly, ViewDataLocalCapacityBAs, \
  ViewDataProjectLocalCapacityBAs, ViewDataLocalCapacityReq, \
  ViewDataProjectLocalCapacityChars, ViewDataTuning, ViewDataValidation


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
    add_view_data_resources(api=api, db_path=db_path)
    add_home_resource(api=api)


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


def add_view_data_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API for the Angular 'view-data' component.
    """
    api.add_resource(
        ViewDataTemporalTimepoints,
        '/view-data/temporal-timepoints/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ViewDataGeographyLoadZones,
        '/view-data/geography-load-zones/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ViewDataProjectLoadZones,
        '/view-data/project-load-zones',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionLoadZones,
        '/view-data/transmission-load-zones/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataSystemLoad,
        '/view-data/system-load/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectPortfolio,
        '/view-data/project-portfolio/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectExistingCapacity,
        '/view-data/project-existing-capacity/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
      ViewDataProjectExistingFixedCost,
      '/view-data/project-fixed-cost/<scenario_id>',
      resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectNewPotential,
        '/view-data/project-new-potential/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectNewCost,
        '/view-data/project-new-cost/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectAvailability,
        '/view-data/project-availability/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectOpChar,
        '/view-data/project-opchar/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataFuels,
        '/view-data/fuels/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataFuelPrices,
        '/view-data/fuel-prices/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionPortfolio,
        '/view-data/transmission-portfolio/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionExistingCapacity,
        '/view-data/transmission-existing-capacity/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionOpChar,
        '/view-data/transmission-opchar/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionHurdleRates,
        '/view-data/transmission-hurdle-rates/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionSimFlowLimits,
        '/view-data/transmission-sim-flow-limits/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionSimFlowLimitsLineGroups,
        '/view-data/transmission-sim-flow-limit-line-groups/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataLFUpBAs,
        '/view-data/geography-lf-up-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectLFUpBAs,
        '/view-data/project-lf-up-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataLFUpReq,
        '/view-data/system-lf-up-req/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataLFDownBAs,
        '/view-data/geography-lf-down-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectLFDownBAs,
        '/view-data/project-lf-down-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataLFDownReq,
        '/view-data/system-lf-down-req/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataRegUpBAs,
        '/view-data/geography-reg-up-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectRegUpBAs,
        '/view-data/project-reg-up-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataRegUpReq,
        '/view-data/system-reg-up-req/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataRegDownBAs,
        '/view-data/geography-reg-down-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectRegDownBAs,
        '/view-data/project-reg-down-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataRegDownReq,
        '/view-data/system-reg-down-req/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataSpinBAs,
        '/view-data/geography-spin-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectSpinBAs,
        '/view-data/project-spin-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataSpinReq,
        '/view-data/system-spin-req/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataFreqRespBAs,
        '/view-data/geography-freq-resp-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectFreqRespBAs,
        '/view-data/project-freq-resp-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataFreqRespReq,
        '/view-data/system-freq-resp-req/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataRPSBAs,
        '/view-data/geography-rps-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectRPSBAs,
        '/view-data/project-rps-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataRPSReq,
        '/view-data/system-rps-req/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataCarbonCapBAs,
        '/view-data/geography-carbon-cap-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectCarbonCapBAs,
        '/view-data/project-carbon-cap-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionCarbonCapBAs,
        '/view-data/transmission-carbon-cap-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataCarbonCapReq,
        '/view-data/system-carbon-cap-req/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataPRMBAs,
        '/view-data/geography-prm-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectPRMBAs,
        '/view-data/project-prm-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataPRMReq,
        '/view-data/system-prm-req/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectELCCChars,
        '/view-data/project-elcc-chars/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataELCCSurface,
        '/view-data/project-elcc-surface/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataEnergyOnly,
        '/view-data/project-energy-only/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataLocalCapacityBAs,
        '/view-data/geography-local-capacity-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectLocalCapacityBAs,
        '/view-data/project-local-capacity-bas/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataLocalCapacityReq,
        '/view-data/local-capacity-req/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectLocalCapacityChars,
        '/view-data/project-local-capacity-chars/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTuning,
        '/view-data/tuning/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ViewDataValidation,
        '/view-data/validation/<scenario_id>',
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
        '/scenarios/<scenario_id>/results/<plot>/<load_zone>/<period>/'
        '<horizon>/<timepoint>/<ymax>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsIncludedPlots,
        '/scenarios/<scenario_id>/results/plots',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsDispatchPlot,
        '/scenarios/<scenario_id>/results-dispatch-plot/<load_zone>/<horizon>/'
        '<ymax>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsCapacityNewPlot,
        '/scenarios/<scenario_id>/results-capacity-plot/new/<load_zone>/<ymax>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsCapacityRetiredPlot,
        '/scenarios/<scenario_id>/results-capacity-plot/retired/<load_zone>/'
        '<ymax>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsCapacityTotalPlot,
        '/scenarios/<scenario_id>/results-capacity-plot/total/<load_zone>/'
        '<ymax>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsEnergyPlot,
        '/scenarios/<scenario_id>/results-energy-plot/<load_zone>/<stage>/'
        '<ymax>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsCostPlot,
        '/scenarios/<scenario_id>/results-cost-plot/<load_zone>/<stage>/'
        '<ymax>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsCapacityFactorPlot,
        '/scenarios/<scenario_id>/results-capacity-factor-plot/<load_zone>/'
        '<stage>/<ymax>',
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
