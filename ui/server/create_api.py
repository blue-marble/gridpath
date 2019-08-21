# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

# RESTful API api
from ui.server.api.home import ServerStatus
from ui.server.api.scenario_detail import ScenarioDetailAPI
from ui.server.api.scenario_results import \
  ScenarioResultsProjectCapacity, ScenarioResultsProjectRetirements, \
  ScenarioResultsProjectNewBuild, ScenarioResultsProjectDispatch, \
  ScenarioResultsProjectCarbon, ScenarioResultsTransmissionCapacity, \
  ScenarioResultsTransmissionFlows, ScenarioResultsImportsExports, \
  ScenarioResultsSystemLoadBalance, ScenarioResultsSystemRPS, \
  ScenarioResultsSystemCarbonCap, ScenarioResultsSystemPRM, \
  ScenarioResultsDispatchPlotOptions, ScenarioResultsDispatchPlot, \
  ScenarioResultsCapacityPlotOptions, ScenarioResultsCapacityNewPlot, \
  ScenarioResultsCapacityRetiredPlot, ScenarioResultsCapacityTotalPlot
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
  ViewDataCarbonCapReq, ViewDataPRMBAs, ViewDataProjectPRMBAs, ViewDataPRMReq, \
  ViewDataProjectELCCChars, ViewDataELCCSurface, ViewDataEnergyOnly, \
  ViewDataLocalCapacityBAs, ViewDataProjectLocalCapacityBAs, \
  ViewDataLocalCapacityReq, ViewDataProjectLocalCapacityChars, ViewDataTuning


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
        '/view-data/temporal-timepoints',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ViewDataGeographyLoadZones,
        '/view-data/geography-load-zones',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ViewDataProjectLoadZones,
        '/view-data/project-load-zones',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionLoadZones,
        '/view-data/transmission-load-zones',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataSystemLoad,
        '/view-data/system-load',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectPortfolio,
        '/view-data/project-portfolio',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectExistingCapacity,
        '/view-data/project-existing-capacity',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
      ViewDataProjectExistingFixedCost,
      '/view-data/project-fixed-cost',
      resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectNewPotential,
        '/view-data/project-new-potential',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectNewCost,
        '/view-data/project-new-cost',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectAvailability,
        '/view-data/project-availability',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectOpChar,
        '/view-data/project-opchar',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataFuels,
        '/view-data/fuels',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataFuelPrices,
        '/view-data/fuel-prices',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionPortfolio,
        '/view-data/transmission-portfolio',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionExistingCapacity,
        '/view-data/transmission-existing-capacity',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionOpChar,
        '/view-data/transmission-opchar',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionHurdleRates,
        '/view-data/transmission-hurdle-rates',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionSimFlowLimits,
        '/view-data/transmission-sim-flow-limits',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionSimFlowLimitsLineGroups,
        '/view-data/transmission-sim-flow-limit-line-groups',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataLFUpBAs,
        '/view-data/geography-lf-up-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectLFUpBAs,
        '/view-data/project-lf-up-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataLFUpReq,
        '/view-data/system-lf-up-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataLFDownBAs,
        '/view-data/geography-lf-down-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectLFDownBAs,
        '/view-data/project-lf-down-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataLFDownReq,
        '/view-data/system-lf-down-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataRegUpBAs,
        '/view-data/geography-reg-up-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectRegUpBAs,
        '/view-data/project-reg-up-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataRegUpReq,
        '/view-data/system-reg-up-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataRegDownBAs,
        '/view-data/geography-reg-down-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectRegDownBAs,
        '/view-data/project-reg-down-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataRegDownReq,
        '/view-data/system-reg-down-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataSpinBAs,
        '/view-data/geography-spin-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectSpinBAs,
        '/view-data/project-spin-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataSpinReq,
        '/view-data/system-spin-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataFreqRespBAs,
        '/view-data/geography-freq-resp-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectFreqRespBAs,
        '/view-data/project-freq-resp-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataFreqRespReq,
        '/view-data/system-freq-resp-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataRPSBAs,
        '/view-data/geography-rps-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectRPSBAs,
        '/view-data/project-rps-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataRPSReq,
        '/view-data/system-rps-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataCarbonCapBAs,
        '/view-data/geography-carbon-cap-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectCarbonCapBAs,
        '/view-data/project-carbon-cap-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTransmissionCarbonCapBAs,
        '/view-data/transmission-carbon-cap-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataCarbonCapReq,
        '/view-data/system-carbon-cap-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataPRMBAs,
        '/view-data/geography-prm-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectPRMBAs,
        '/view-data/project-prm-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataPRMReq,
        '/view-data/system-prm-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectELCCChars,
        '/view-data/project-elcc-chars',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataELCCSurface,
        '/view-data/project-elcc-surface',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataEnergyOnly,
        '/view-data/project-energy-only',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataLocalCapacityBAs,
        '/view-data/geography-local-capacity-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectLocalCapacityBAs,
        '/view-data/project-local-capacity-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataLocalCapacityReq,
        '/view-data/local-capacity-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataProjectLocalCapacityChars,
        '/view-data/project-local-capacity-chars',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ViewDataTuning,
        '/view-data/tuning',
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
        ScenarioResultsProjectCapacity,
        '/scenarios/<scenario_id>/results-project-capacity',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsProjectRetirements,
        '/scenarios/<scenario_id>/results-project-retirements',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsProjectNewBuild,
        '/scenarios/<scenario_id>/results-project-new-build',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsProjectDispatch,
        '/scenarios/<scenario_id>/results-project-dispatch',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsProjectCarbon,
        '/scenarios/<scenario_id>/results-project-carbon',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsTransmissionCapacity,
        '/scenarios/<scenario_id>/results-transmission-capacity',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsTransmissionFlows,
        '/scenarios/<scenario_id>/results-transmission-flows',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsImportsExports,
        '/scenarios/<scenario_id>/results-imports-exports',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsSystemLoadBalance,
        '/scenarios/<scenario_id>/results-system-load-balance',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsSystemRPS,
        '/scenarios/<scenario_id>/results-system-rps',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsSystemCarbonCap,
        '/scenarios/<scenario_id>/results-system-carbon-cap',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsSystemPRM,
        '/scenarios/<scenario_id>/results-system-prm',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsDispatchPlotOptions,
        '/scenarios/<scenario_id>/results-dispatch-plot/options',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsDispatchPlot,
        '/scenarios/<scenario_id>/results-dispatch-plot/<load_zone>/<horizon>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsCapacityPlotOptions,
        '/scenarios/<scenario_id>/results-capacity-plot/options',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsCapacityNewPlot,
        '/scenarios/<scenario_id>/results-capacity-plot/new/<load_zone>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsCapacityRetiredPlot,
        '/scenarios/<scenario_id>/results-capacity-plot/retired/<load_zone>',
        resource_class_kwargs={'db_path': db_path}
    )

    api.add_resource(
        ScenarioResultsCapacityTotalPlot,
        '/scenarios/<scenario_id>/results-capacity-plot/total/<load_zone>',
        resource_class_kwargs={'db_path': db_path}
    )
