# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

# RESTful API resources
from ui.api.resources.home import ServerStatus
from ui.api.resources.scenario_detail import ScenarioDetailName, \
  ScenarioDetailAll, ScenarioDetailFeatures, ScenarioDetailTemporal, \
  ScenarioDetailGeographyLoadZones, ScenarioDetailLoad, \
  ScenarioDetailProjectCapacity, ScenarioDetailProjectOpChars, \
  ScenarioDetailFuels, ScenarioDetailTransmissionCapacity, \
  ScenarioDetailTransmissionOpChars, ScenarioDetailTransmissionHurdleRates, \
  ScenarioDetailTransmissionSimFlow, ScenarioDetailLoadFollowingUp, \
  ScenarioDetailLoadFollowingDown, ScenarioDetailRegulationUp, \
  ScenarioDetailRegulationDown, ScenarioDetailSpinningReserves, \
  ScenarioDetailFrequencyResponse, ScenarioDetailRPS, ScenarioDetailCarbonCap, \
  ScenarioDetailPRM, ScenarioDetailLocalCapacity
from ui.api.resources.scenario_results import \
  ScenarioResultsProjectCapacity, ScenarioResultsProjectRetirements
from ui.api.resources.scenario_new import SettingTemporal, SettingLoadZones, \
  SettingProjectLoadZones, SettingTxLoadZones, SettingSystemLoad, \
  SettingProjectPorftolio, SettingProjectExistingCapacity, \
  SettingProjectExistingFixedCost, SettingProjectNewCost, \
  SettingProjectNewPotential, SettingProjectAvailability, SettingProjectOpChar, \
  SettingFuels, SettingFuelPrices, SettingTransmissionPortfolio, \
  SettingTransmissionExistingCapacity, SettingTransmissionOpChar, \
  SettingTransmissionHurdleRates, SettingTransmissionSimFlowLimits, \
  SettingTransmissionSimFlowLimitGroups, SettingLFReservesUpBAs, \
  SettingProjectLFReservesUpBAs, SettingLFReservesUpRequirement, \
  SettingLFReservesDownBAs, SettingProjectLFReservesDownBAs, \
  SettingLFReservesDownRequirement, SettingRegulationUpBAs, \
  SettingProjectRegulationUpBAs, SettingRegulationUpRequirement, \
  SettingRegulationDownBAs, SettingProjectRegulationDownBAs, \
  SettingRegulationDownRequirement, SettingSpinningReservesBAs, \
  SettingProjectSpinningReservesBAs, SettingSpinningReservesRequirement, \
  SettingFrequencyResponseBAs, SettingProjectFrequencyResponseBAs, \
  SettingFrequencyResponseRequirement, SettingRPSAreas, SettingProjectRPSAreas, \
  SettingRPSRequirement, SettingCarbonCapAreas, SettingProjectCarbonCapAreas, \
  SettingTransmissionCarbonCapAreas, SettingCarbonCapRequirement, \
  SettingPRMAreas, SettingPRMRequirement, SettingProjectPRMAreas, \
  SettingProjectELCCChars, SettingProjectPRMEnergyOnly, SettingELCCSurface, \
  SettingLocalCapacityAreas, SettingLocalCapacityRequirement, \
  SettingProjectLocalCapacityAreas, SettingProjectLocalCapacityChars, \
  SettingTuning
from ui.api.resources.scenarios import Scenarios
from ui.api.resources.view_data import ViewDataTemporalTimepoints, \
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
  ViewDataLocalCapacityReq, ViewDataProjectLocalCapacityChars


# Create API routes
def add_api_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add all needed API resources.
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

    Add the API resources for the Angular 'scenarios' component.
    """
    # Scenario list
    api.add_resource(Scenarios, '/scenarios/',
                     resource_class_kwargs={'db_path': db_path}
                     )


def add_scenario_detail_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API resources for the Angular 'scenario-detail' component.
    """
    # Name
    # TODO: is this used?
    api.add_resource(
        ScenarioDetailName,
        '/scenarios/<scenario_id>/name',
        resource_class_kwargs={'db_path': db_path}
    )
    # All
    api.add_resource(
        ScenarioDetailAll,
        '/scenarios/<scenario_id>',
        resource_class_kwargs={'db_path': db_path}
    )
    # Features
    api.add_resource(
        ScenarioDetailFeatures,
        '/scenarios/<scenario_id>/features',
        resource_class_kwargs={'db_path': db_path}
    )
    # Temporal
    api.add_resource(
        ScenarioDetailTemporal,
        '/scenarios/<scenario_id>/temporal',
        resource_class_kwargs={'db_path': db_path}
    )
    # Geography load zones
    api.add_resource(
        ScenarioDetailGeographyLoadZones,
        '/scenarios/<scenario_id>/geography-load-zones',
        resource_class_kwargs={'db_path': db_path}
    )
    # System load
    api.add_resource(
        ScenarioDetailLoad,
        '/scenarios/<scenario_id>/load',
        resource_class_kwargs={'db_path': db_path}
    )
    # Project capacity
    api.add_resource(
        ScenarioDetailProjectCapacity,
        '/scenarios/<scenario_id>/project-capacity',
        resource_class_kwargs={'db_path': db_path}
    )
    # Project operating characteristics
    api.add_resource(
        ScenarioDetailProjectOpChars,
        '/scenarios/<scenario_id>/project-opchars',
        resource_class_kwargs={'db_path': db_path}
    )
    # Fuels
    api.add_resource(
        ScenarioDetailFuels,
        '/scenarios/<scenario_id>/fuels',
        resource_class_kwargs={'db_path': db_path}
    )
    # Transmission capacity
    api.add_resource(
        ScenarioDetailTransmissionCapacity,
        '/scenarios/<scenario_id>/transmission-capacity',
        resource_class_kwargs={'db_path': db_path}
    )
    # Transmission operating characteristics
    api.add_resource(
        ScenarioDetailTransmissionOpChars,
        '/scenarios/<scenario_id>/transmission-opchars',
        resource_class_kwargs={'db_path': db_path}
    )
    # Transmission hurdle rates
    api.add_resource(
        ScenarioDetailTransmissionHurdleRates,
        '/scenarios/<scenario_id>/transmission-hurdle-rates',
        resource_class_kwargs={'db_path': db_path}
    )
    # Transmission simultaneous flow limits
    api.add_resource(
        ScenarioDetailTransmissionSimFlow,
        '/scenarios/<scenario_id>/transmission-sim-flow',
        resource_class_kwargs={'db_path': db_path}
    )
    # Reserves
    api.add_resource(
        ScenarioDetailLoadFollowingUp,
        '/scenarios/<scenario_id>/lf-up',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ScenarioDetailLoadFollowingDown,
        '/scenarios/<scenario_id>/lf-down',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ScenarioDetailRegulationUp,
        '/scenarios/<scenario_id>/reg-up',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ScenarioDetailRegulationDown,
        '/scenarios/<scenario_id>/reg-down',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ScenarioDetailSpinningReserves,
        '/scenarios/<scenario_id>/spin',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ScenarioDetailFrequencyResponse,
        '/scenarios/<scenario_id>/freq-resp',
        resource_class_kwargs={'db_path': db_path}
    )
    # Policy and reliability
    api.add_resource(
        ScenarioDetailRPS,
        '/scenarios/<scenario_id>/rps',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ScenarioDetailCarbonCap,
        '/scenarios/<scenario_id>/carbon-cap',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ScenarioDetailPRM,
        '/scenarios/<scenario_id>/prm',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        ScenarioDetailLocalCapacity,
        '/scenarios/<scenario_id>/local-capacity',
        resource_class_kwargs={'db_path': db_path}
    )


def add_scenario_new_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API resources for the Angular 'scenario-new' component.
    """
    api.add_resource(
        SettingTemporal, '/scenario-settings/temporal',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingLoadZones,
        '/scenario-settings/load-zones',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectLoadZones,
        '/scenario-settings/project-load-zones',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingTxLoadZones,
        '/scenario-settings/tx-load-zones',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingSystemLoad,
        '/scenario-settings/system-load',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectPorftolio,
        '/scenario-settings/project-portfolio',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectExistingCapacity,
        '/scenario-settings/project-existing-capacity',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectExistingFixedCost,
        '/scenario-settings/project-existing-fixed-cost',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectNewCost,
        '/scenario-settings/project-new-cost',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectNewPotential,
        '/scenario-settings/project-new-potential',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectAvailability,
        '/scenario-settings/project-availability',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectOpChar,
        '/scenario-settings/project-opchar',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingFuels,
        '/scenario-settings/fuels',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingFuelPrices,
        '/scenario-settings/fuel-prices',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingTransmissionPortfolio,
        '/scenario-settings/transmission-portfolio',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingTransmissionExistingCapacity,
        '/scenario-settings/transmission-existing-capacity',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingTransmissionOpChar,
        '/scenario-settings/transmission-opchar',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingTransmissionHurdleRates,
        '/scenario-settings/transmission-hurdle-rates',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingTransmissionSimFlowLimits,
        '/scenario-settings/transmission-simflow-limits',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingTransmissionSimFlowLimitGroups,
        '/scenario-settings/transmission-simflow-limit-groups',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingLFReservesUpBAs,
        '/scenario-settings/lf-reserves-up-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectLFReservesUpBAs,
        '/scenario-settings/project-lf-reserves-up-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingLFReservesUpRequirement,
        '/scenario-settings/lf-reserves-up-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingLFReservesDownBAs,
        '/scenario-settings/lf-reserves-down-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectLFReservesDownBAs,
        '/scenario-settings/project-lf-reserves-down-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingLFReservesDownRequirement,
        '/scenario-settings/lf-reserves-down-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingRegulationUpBAs,
        '/scenario-settings/regulation-up-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectRegulationUpBAs,
        '/scenario-settings/project-regulation-up-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingRegulationUpRequirement,
        '/scenario-settings/regulation-up-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingRegulationDownBAs,
        '/scenario-settings/regulation-down-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectRegulationDownBAs,
        '/scenario-settings/project-regulation-down-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingRegulationDownRequirement,
        '/scenario-settings/regulation-down-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingSpinningReservesBAs,
        '/scenario-settings/spin-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectSpinningReservesBAs,
        '/scenario-settings/project-spin-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingSpinningReservesRequirement,
        '/scenario-settings/spin-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingFrequencyResponseBAs,
        '/scenario-settings/freq-resp-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectFrequencyResponseBAs,
        '/scenario-settings/project-freq-resp-bas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingFrequencyResponseRequirement,
        '/scenario-settings/freq-resp-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingRPSAreas,
        '/scenario-settings/rps-areas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectRPSAreas,
        '/scenario-settings/project-rps-areas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingRPSRequirement,
        '/scenario-settings/rps-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingCarbonCapAreas,
        '/scenario-settings/carbon-cap-areas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectCarbonCapAreas,
        '/scenario-settings/project-carbon-cap-areas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingTransmissionCarbonCapAreas,
        '/scenario-settings/transmission-carbon-cap-areas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingCarbonCapRequirement,
        '/scenario-settings/carbon-cap-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingPRMAreas,
        '/scenario-settings/prm-areas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingPRMRequirement,
        '/scenario-settings/prm-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectPRMAreas,
        '/scenario-settings/project-prm-areas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingELCCSurface,
        '/scenario-settings/elcc-surface',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectELCCChars,
        '/scenario-settings/project-elcc-chars',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectPRMEnergyOnly,
        '/scenario-settings/project-energy-only',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingLocalCapacityAreas,
        '/scenario-settings/local-capacity-areas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectLocalCapacityAreas,
        '/scenario-settings/project-local-capacity-areas',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingLocalCapacityRequirement,
        '/scenario-settings/local-capacity-req',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingProjectLocalCapacityChars,
        '/scenario-settings/project-local-capacity-chars',
        resource_class_kwargs={'db_path': db_path}
    )
    api.add_resource(
        SettingTuning,
        '/scenario-settings/tuning',
        resource_class_kwargs={'db_path': db_path}
    )


def add_view_data_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API resources for the Angular 'view-data' component.
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


def add_home_resource(api):
    """
    :param api:

    Add resources for Angular 'home' component
    """
    # Server status
    api.add_resource(ServerStatus, '/server-status')


def add_scenario_results_resources(api, db_path):
    """
    :param api:
    :param db_path:

    Add the API resources for the Angular 'scenario-results' component.
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
