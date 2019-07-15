import { Component, OnInit } from '@angular/core';

import { FormControl, FormGroup } from '@angular/forms';

const io = (<any>window).require('socket.io-client');

import { Setting, ScenarioNewService } from './scenario-new.service'

@Component({
  selector: 'app-scenario-new',
  templateUrl: './scenario-new.component.html',
  styleUrls: ['./scenario-new.component.css']
})


export class ScenarioNewComponent implements OnInit {

  // The final structure we'll iterate over
  ScenarioNewStructure: SettingsTable[];

  // Setting elements

  // For the features
  // TODO: can we consolidate with structure for settings below?
  features: Feature[];
  featureSelectionOption: string[];

  // Temporal settings
  temporalSettingsTable: SettingsTable;
  temporalSettingOptions: Setting[];

  // Load zone settings
  loadZoneSettingsTable: SettingsTable;
  geographyLoadZonesSettingOptions: Setting[];
  projectLoadZonesSettingOptions: Setting[];
  transmissionLoadZonesSettingOptions: Setting[];

  // System load settings
  systemLoadSettingsTable: SettingsTable;
  systemLoadSettingOptions: Setting[];

  // Project capacity settings
  projectCapacitySettingsTable: SettingsTable;
  projectPortfolioSettingOptions: Setting[];
  projectExistingCapacitySettingOptions: Setting[];
  projectExistingFixedCostSettingOptions: Setting[];
  projectNewCostSettingOptions: Setting[];
  projectNewPotentialSettingOptions: Setting[];
  projectAvailabilitySettingOptions: Setting[];

  // Project operational characteristics settings
  projectOperationalCharsSettingsTable: SettingsTable;
  projectOperationalCharsSettingOptions: Setting[];

  // Fuel settings
  fuelSettingsTable: SettingsTable;
  fuelSettingOptions: Setting[];
  fuelPricesSettingOptions: Setting[];

  // Transmission capacity settings
  transmissionCapacitySettingsTable: SettingsTable;
  transmissionPortfolioSettingOptions: Setting[];
  transmissionExistingCapacitySettingOptions: Setting[];

  // Transmission operational characteristics
  transmissionOperationalCharsSettingsTable: SettingsTable;
  transmissionOperationalCharsSettingOptions: Setting[];

  // Transission hurdle rates settings
  transmissionHurdleRatesSettingsTable: SettingsTable;
  transmissionHurdleRatesSettingOptions: Setting[];

  // Transmission simultaneous flow limits settings
  transmissionSimultaneousFlowLimitsSettingsTable: SettingsTable;
  transmissionSimultaneousFlowLimitsSettingOptions: Setting[];
  transmissionSimultaneousFlowLimitLineGroupsSettingOptions: Setting[];

  // Load-following-up settings
  loadFollowingUpSettingsTable: SettingsTable;
  geographyLoadFollowingUpBAsSettingOptions: Setting[];
  loadFollowingUpRequirementSettingOptions: Setting[];
  projectLoadFollowingUpBAsSettingOptions: Setting[];

  // Load-following-down settings
  loadFollowingDownSettingsTable: SettingsTable;
  geographyLoadFollowingDownBAsSettingOptions: Setting[];
  loadFollowingDownRequirementSettingOptions: Setting[];
  projectLoadFollowingDownBAsSettingOptions: Setting[];

  // Regulation up settings
  regulationUpSettingsTable: SettingsTable;
  geographyRegulationUpBAsSettingOptions: Setting[];
  regulationUpRequirementSettingOptions: Setting[];
  projectRegulationUpBAsSettingOptions: Setting[];

  // Regulation down settings
  regulationDownSettingsTable: SettingsTable;
  geographyRegulationDownBAsSettingOptions: Setting[];
  regulationDownRequirementSettingOptions: Setting[];
  projectRegulationDownBAsSettingOptions: Setting[];

  // Spinning reserves settings
  spinningReservesSettingsTable: SettingsTable;
  geographySpinningReservesBAsSettingOptions: Setting[];
  spinningReservesRequirementSettingOptions: Setting[];
  projectSpinningReservesBAsSettingOptions: Setting[];

  // Frequency response settings
  frequencyResponseSettingsTable: SettingsTable;
  geographyFrequencyResponseBAsSettingOptions: Setting[];
  frequencyResponseRequirementSettingOptions: Setting[];
  projectFrequencyResponseBAsSettingOptions: Setting[];

  // RPS settings
  rpsSettingsTable: SettingsTable;
  geographyRPSAreasSettingOptions: Setting[];
  rpsTargetSettingOptions: Setting[];
  projectRPSAreasSettingOptions: Setting[];

  // Carbon cap settings
  carbonCapSettingsTable: SettingsTable;
  geographyCarbonCapAreasSettingOptions: Setting[];
  carbonCapTargetSettingOptions: Setting[];
  projectCarbonCapAreasSettingOptions: Setting[];
  transmissionCarbonCapAreasSettingOptions: Setting[];

  // PRM settings
  prmSettingsTable: SettingsTable;
  geographyPRMAreasSettingOptions: Setting[];
  prmRequirementSettingOptions: Setting[];
  projectPRMAreasSettingOptions: Setting[];
  projectELCCCharsSettingOptions: Setting[];
  elccSurfaceSettingOptions: Setting[];
  projectPRMEnergyOnlySettingOptions: Setting[];

  // Local capacity settings
  localCapacitySettingsTable: SettingsTable;
  geographyLocalCapacityAreasSettingOptions: Setting[];
  localCapacityRequirementSettingOptions: Setting[];
  projectLocalCapacityAreasSettingOptions: Setting[];
  projectLocalCapacityCharsSettingOptions: Setting[];

  // Tuning settings
  tuningSettingsTable: SettingsTable;
  tuningSettingOptions: Setting[];

  // Create the form
  newScenarioForm = new FormGroup({
    scenarioName: new FormControl(''),
    scenarioDescription: new FormControl(''),
    featureFuels: new FormControl(''),
    featureTransmission: new FormControl(''),
    featureTransmissionHurdleRates: new FormControl(''),
    featureSimFlowLimits: new FormControl(''),
    featureLFUp: new FormControl(''),
    featureLFDown: new FormControl(''),
    featureRegUp: new FormControl(''),
    featureRegDown: new FormControl(''),
    featureSpin: new FormControl(''),
    featureFreqResp: new FormControl(''),
    featureRPS: new FormControl(''),
    featureCarbonCap: new FormControl(''),
    featureTrackCarbonImports: new FormControl(''),
    featurePRM: new FormControl(''),
    featureELCCSurface: new FormControl(''),
    featureLocalCapacity: new FormControl(''),
    temporalSetting: new FormControl(''),
    geographyLoadZonesSetting: new FormControl(''),
    geographyProjectLoadZonesSetting: new FormControl(''),
    geographyTxLoadZonesSetting: new FormControl(''),
    systemLoadSetting: new FormControl(''),
    projectPortfolioSetting: new FormControl(''),
    projectExistingCapacitySetting: new FormControl(''),
    projectExistingFixedCostSetting: new FormControl(''),
    projectNewCostSetting: new FormControl(''),
    projectNewPotentialSetting: new FormControl(''),
    projectAvailabilitySetting: new FormControl(''),
    projectOperationalCharsSetting: new FormControl(''),
    projectFuelsSetting: new FormControl(''),
    fuelPricesSetting: new FormControl(''),
    transmissionPortfolioSetting: new FormControl(''),
    transmissionExistingCapacitySetting: new FormControl(''),
    transmissionOperationalCharsSetting: new FormControl(''),
    transmissionHurdleRatesSetting: new FormControl(''),
    transmissionSimultaneousFlowLimitsSetting: new FormControl(''),
    transmissionSimultaneousFlowLimitLineGroupsSetting: new FormControl(''),
    geographyLoadFollowingUpBAsSetting: new FormControl(''),
    loadFollowingUpRequirementSetting: new FormControl(''),
    projectLoadFollowingUpBAsSetting: new FormControl(''),
    geographyLoadFollowingDownBAsSetting: new FormControl(''),
    loadFollowingDownRequirementSetting: new FormControl(''),
    projectLoadFollowingDownBAsSetting: new FormControl(''),
    geographyRegulationUpBAsSetting: new FormControl(''),
    regulationUpRequirementSetting: new FormControl(''),
    projectRegulationUpBAsSetting: new FormControl(''),
    geographyRegulationDownBAsSetting: new FormControl(''),
    regulationDownRequirementSetting: new FormControl(''),
    projectRegulationDownBAsSetting: new FormControl(''),
    geographySpinningReservesBAsSetting: new FormControl(''),
    spinningReservesRequirementSetting: new FormControl(''),
    projectSpinningReservesBAsSetting: new FormControl(''),
    geographyFrequencyResponseBAsSetting: new FormControl(''),
    frequencyResponseRequirementSetting: new FormControl(''),
    projectFrequencyResponseBAsSetting: new FormControl(''),
    geographyRPSAreasSetting: new FormControl(''),
    rpsTargetSetting: new FormControl(''),
    projectRPSAreasSetting: new FormControl(''),
    geographyCarbonCapAreasSetting: new FormControl(''),
    carbonCapTargetSetting: new FormControl(''),
    projectCarbonCapAreasSetting: new FormControl(''),
    transmissionCarbonCapAreasSetting: new FormControl(''),
    geographyPRMAreasSetting: new FormControl(''),
    prmRequirementSetting: new FormControl(''),
    projectPRMAreasSetting: new FormControl(''),
    projectELCCCharsSetting: new FormControl(''),
    elccSurfaceSetting: new FormControl(''),
    projectPRMEnergyOnlySetting: new FormControl(''),
    geographyLocalCapacityAreasSetting: new FormControl(''),
    localCapacityRequirementSetting: new FormControl(''),
    projectLocalCapacityAreasSetting: new FormControl(''),
    projectLocalCapacityCharsSetting: new FormControl(''),
    tuningSetting: new FormControl('')
    });

  constructor(private scenarioNewService: ScenarioNewService) {
    this.features = [];
    const featureFuels = new Feature();
    featureFuels.featureName = 'feature_fuels';
    featureFuels.formControlName = 'featureFuels';
    this.features.push(featureFuels);

    const featureTransmission = new Feature();
    featureTransmission.featureName = 'feature_transmission';
    featureTransmission.formControlName = 'featureTransmission';
    this.features.push(featureTransmission);

    const featureTransmissionHurdleRates = new Feature();
    featureTransmissionHurdleRates.featureName =
      'feature_transmission_hurdle_rates';
    featureTransmissionHurdleRates.formControlName =
      'featureTransmissionHurdleRates';
    this.features.push(featureTransmissionHurdleRates);

    const featureSimFlowLimits = new Feature();
    featureSimFlowLimits.featureName = 'feature_simultaneous_flow_limits';
    featureSimFlowLimits.formControlName = 'featureSimFlowLimits';
    this.features.push(featureSimFlowLimits);

    const featureLFUp = new Feature();
    featureLFUp.featureName = 'feature_load_following_up';
    featureLFUp.formControlName = 'featureLFUp';
    this.features.push(featureLFUp);

    const featureLFDown = new Feature();
    featureLFDown.featureName = 'feature_load_following_down';
    featureLFDown.formControlName = 'featureLFDown';
    this.features.push(featureLFDown);

    const featureRegDown = new Feature();
    featureRegDown.featureName = 'feature_regulation_down';
    featureRegDown.formControlName = 'featureRegDown';
    this.features.push(featureRegDown);

    const featureRegUp = new Feature();
    featureRegUp.featureName = 'feature_regulation_up';
    featureRegUp.formControlName = 'featureRegUp';
    this.features.push(featureRegUp);

    const featureSpin = new Feature();
    featureSpin.featureName = 'feature_spinning_reserves';
    featureSpin.formControlName = 'featureSpin';
    this.features.push(featureSpin);

    const featureFreqResp = new Feature();
    featureFreqResp.featureName = 'feature_frequency_response';
    featureFreqResp.formControlName = 'featureFreqResp';
    this.features.push(featureFreqResp);

    const featureRPS = new Feature();
    featureRPS.featureName = 'feature_rps';
    featureRPS.formControlName = 'featureRPS';
    this.features.push(featureRPS);

    const featureCarbonCap = new Feature();
    featureCarbonCap.featureName = 'feature_carbon_cap';
    featureCarbonCap.formControlName = 'featureCarbonCap';
    this.features.push(featureCarbonCap);

    const featureTrackCarbonImports = new Feature();
    featureTrackCarbonImports.featureName = 'feature_track_carbon_imports';
    featureTrackCarbonImports.formControlName = 'featureTrackCarbonImports';
    this.features.push(featureTrackCarbonImports);

    const featurePRM = new Feature();
    featurePRM.featureName = 'feature_prm';
    featurePRM.formControlName = 'featurePRM';
    this.features.push(featurePRM);

    const featureELCCSurface = new Feature();
    featureELCCSurface.featureName = 'feature_elcc_surface';
    featureELCCSurface.formControlName = 'featureELCCSurface';
    this.features.push(featureELCCSurface);

    const featureLocalCapacity = new Feature();
    featureLocalCapacity.featureName = 'feature_local_capacity';
    featureLocalCapacity.formControlName = 'featureLocalCapacity';
    this.features.push(featureLocalCapacity);


    this.featureSelectionOption = featureSelectionOptions();


  }

  ngOnInit() {
    this.ScenarioNewStructure = [];
    this.getSettingOptionsTemporal();
    this.getSettingOptionsLoadZones();
    this.getSettingOptionsLoad();
    this.getSettingOptionsProjectCapacity();
    this.getSettingOptionsProjectOperationalChars();
    this.getSettingOptionsFuels();
    this.getSettingOptionsTransmissionCapacity();
    this.getSettingOptionsTransmissionOperationalChars();
    this.getSettingOptionsTransmissionHurdleRates();
    this.getSettingOptionsTransmissionSimultaneousFlowLimits();
    this.getSettingOptionsLFReservesUp();
    this.getSettingOptionsLFReservesDown();
    this.getSettingOptionsRegulationUp();
    this.getSettingOptionsRegulationDown();
    this.getSettingOptionsSpinningReserves();
    this.getSettingOptionsFrequencyResponse();
    this.getSettingOptionsRPS();
    this.getSettingOptionsCarbonCap();
    this.getSettingOptionsPRM();
    this.getSettingOptionsLocalCapacity();
    this.getSettingOptionsTuning();
  }

  getSettingOptionsTemporal(): void {
    // Set the setting table captions
    this.temporalSettingsTable = new SettingsTable();
    this.temporalSettingsTable.tableCaption = 'Temporal settings';
    this.temporalSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingTemporal()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.temporalSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'temporal',
            'temporalSetting',
             this.temporalSettingOptions
          );

          // Add the row to the table
          this.temporalSettingsTable.settingRows.push(newRow);
        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.temporalSettingsTable);
  }

  getSettingOptionsLoadZones(): void {
    // Set the setting table captions
    this.loadZoneSettingsTable = new SettingsTable();
    this.loadZoneSettingsTable.tableCaption = 'Load zone settings';
    this.loadZoneSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingLoadZones()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyLoadZonesSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'geography_load_zones',
            'geographyLoadZonesSetting',
            this.geographyLoadZonesSettingOptions
          );

          // Add the row to the table
          this.loadZoneSettingsTable.settingRows.push(newRow);


        }
      );

    this.scenarioNewService.getSettingProjectLoadZones()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectLoadZonesSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_load_zones',
            'geographyProjectLoadZonesSetting',
            this.projectLoadZonesSettingOptions
          );

          // Add the row to the table
          this.loadZoneSettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingTransmissionLoadZones()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.transmissionLoadZonesSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'transmission_load_zones',
            'geographyTxLoadZonesSetting',
            this.transmissionLoadZonesSettingOptions
          );

          // Add the row to the table
          this.loadZoneSettingsTable.settingRows.push(newRow);

        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.loadZoneSettingsTable);

  }

  getSettingOptionsLoad(): void {
    // Set the setting table captions
    this.systemLoadSettingsTable = new SettingsTable();
    this.systemLoadSettingsTable.tableCaption = 'System load';
    this.systemLoadSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingSystemLoad()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.systemLoadSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'load_profile',
            'systemLoadSetting',
            this.systemLoadSettingOptions
          );

          // Add the row to the table
          this.systemLoadSettingsTable.settingRows.push(newRow);


        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.systemLoadSettingsTable);

  }

  getSettingOptionsProjectCapacity(): void {
    // Set the setting table captions
    this.projectCapacitySettingsTable = new SettingsTable();
    this.projectCapacitySettingsTable.tableCaption = 'Project capacity';
    this.projectCapacitySettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingProjectPortfolio()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectPortfolioSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_portfolio',
            'projectPortfolioSetting',
            this.projectPortfolioSettingOptions
          );

          // Add the row to the table
          this.projectCapacitySettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingProjectExistingCapacity()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectExistingCapacitySettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_existing_capacity',
            'projectExistingCapacitySetting',
            this.projectExistingCapacitySettingOptions
          );

          // Add the row to the table
          this.projectCapacitySettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingProjectExistingFixedCost()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectExistingFixedCostSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_existing_fixed_cost',
            'projectExistingFixedCostSetting',
            this.projectExistingFixedCostSettingOptions
          );

          // Add the row to the table
          this.projectCapacitySettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingProjectNewCost()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectNewCostSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_new_cost',
            'projectNewCostSetting',
            this.projectNewCostSettingOptions
          );

          // Add the row to the table
          this.projectCapacitySettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingProjectNewPotential()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectNewPotentialSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_new_potential',
            'projectNewPotentialSetting',
            this.projectNewPotentialSettingOptions
          );

          // Add the row to the table
          this.projectCapacitySettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingProjectAvailability()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectAvailabilitySettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_availability',
            'projectAvailabilitySetting',
            this.projectAvailabilitySettingOptions
          );

          // Add the row to the table
          this.projectCapacitySettingsTable.settingRows.push(newRow);
        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.projectCapacitySettingsTable);

  }

  getSettingOptionsProjectOperationalChars(): void {
    // Set the setting table captions
    this.projectOperationalCharsSettingsTable = new SettingsTable();
    this.projectOperationalCharsSettingsTable.tableCaption =
      'Project operational characteristics';
    this.projectOperationalCharsSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingProjectOpChar()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectOperationalCharsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_operational_characteristics',
            'projectOperationalCharsSetting',
            this.projectOperationalCharsSettingOptions
          );

          // Add the row to the table
          this.projectOperationalCharsSettingsTable.settingRows.push(newRow);


        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.projectOperationalCharsSettingsTable);

  }

  getSettingOptionsFuels(): void {
    // Set the setting table captions
    this.fuelSettingsTable = new SettingsTable();
    this.fuelSettingsTable.tableCaption ='Fuels settings';
    this.fuelSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingFuels()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.fuelSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'fuel_characteristics',
            'projectFuelsSetting',
            this.fuelSettingOptions
          );

          // Add the row to the table
          this.fuelSettingsTable.settingRows.push(newRow);


        }
      );

    this.scenarioNewService.getSettingFuelPrices()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.fuelPricesSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'fuel_prices',
            'fuelPricesSetting',
            this.fuelPricesSettingOptions
          );

          // Add the row to the table
          this.fuelSettingsTable.settingRows.push(newRow);


        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.fuelSettingsTable);

  }
  
  getSettingOptionsTransmissionCapacity(): void {
    // Set the setting table captions
    this.transmissionCapacitySettingsTable = new SettingsTable();
    this.transmissionCapacitySettingsTable.tableCaption =
      'Transmission capacity';
    this.transmissionCapacitySettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingTransmissionPortfolio()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.transmissionPortfolioSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'transmission_portfolio',
            'transmissionPortfolioSetting',
            this.transmissionPortfolioSettingOptions
          );

          // Add the row to the table
          this.transmissionCapacitySettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingTransmissionExistingCapacity()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.transmissionExistingCapacitySettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'transmission_existing_capacity',
            'transmissionExistingCapacitySetting',
            this.transmissionExistingCapacitySettingOptions
          );

          // Add the row to the table
          this.transmissionCapacitySettingsTable.settingRows.push(newRow);
        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.transmissionCapacitySettingsTable);

  }
  
  getSettingOptionsTransmissionOperationalChars(): void {
    // Set the setting table captions
    this.transmissionOperationalCharsSettingsTable = new SettingsTable();
    this.transmissionOperationalCharsSettingsTable.tableCaption =
      'Transmission operational characteristics';
    this.transmissionOperationalCharsSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingTransmissionOpChar()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.transmissionOperationalCharsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'transmission_operational_characteristics',
            'transmissionOperationalCharsSetting',
            this.transmissionOperationalCharsSettingOptions
          );

          // Add the row to the table
          this.transmissionOperationalCharsSettingsTable.settingRows.push(
            newRow
          );


        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.transmissionOperationalCharsSettingsTable);

  }
  
  getSettingOptionsTransmissionHurdleRates(): void {
    // Set the setting table captions
    this.transmissionHurdleRatesSettingsTable = new SettingsTable();
    this.transmissionHurdleRatesSettingsTable.tableCaption =
      'Transmission hurdle rates';
    this.transmissionHurdleRatesSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingTransmissionHurdleRates()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.transmissionHurdleRatesSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'transmission_hurdle_rates',
            'transmissionHurdleRatesSetting',
            this.transmissionHurdleRatesSettingOptions
          );

          // Add the row to the table
          this.transmissionHurdleRatesSettingsTable.settingRows.push(
            newRow
          );
        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.transmissionHurdleRatesSettingsTable);
  }

  getSettingOptionsTransmissionSimultaneousFlowLimits(): void {
    // Set the setting table captions
    this.transmissionSimultaneousFlowLimitsSettingsTable = new SettingsTable();
    this.transmissionSimultaneousFlowLimitsSettingsTable.tableCaption =
      'Transmission simultaneous flow limits';
    this.transmissionSimultaneousFlowLimitsSettingsTable.settingRows = [];

    // Get the settings
    this.scenarioNewService.getSettingTransmissionSimFlowLimits()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.transmissionSimultaneousFlowLimitsSettingOptions =
            scenarioSetting;

          // Create the row
          const newRow = createRow(
            'transmission_simultaneous_flow_limits',
            'transmissionSimultaneousFlowLimitsSetting',
            this.transmissionSimultaneousFlowLimitsSettingOptions
          );

          // Add the row to the table
          this.transmissionSimultaneousFlowLimitsSettingsTable.settingRows
            .push(newRow);
        }
      );

    this.scenarioNewService.getSettingTransmissionSimFlowLimitGroups()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.transmissionSimultaneousFlowLimitLineGroupsSettingOptions =
            scenarioSetting;

          // Create the row
          const newRow = createRow(
            'transmission_simultaneous_flow_limit_line_groups',
            'transmissionSimultaneousFlowLimitLineGroupsSetting',
            this.transmissionSimultaneousFlowLimitLineGroupsSettingOptions
          );

          // Add the row to the table
          this.transmissionSimultaneousFlowLimitsSettingsTable.settingRows
            .push(newRow);
        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(
      this.transmissionSimultaneousFlowLimitsSettingsTable
    );
  }

  getSettingOptionsLFReservesUp(): void {
    // Set the setting table captions
    this.loadFollowingUpSettingsTable = new SettingsTable();
    this.loadFollowingUpSettingsTable.tableCaption = 'Load following up settings';
    this.loadFollowingUpSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingLFReservesUpBAs()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyLoadFollowingUpBAsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'geography_load_following_up_bas',
            'geographyLoadFollowingUpBAsSetting',
            this.geographyLoadFollowingUpBAsSettingOptions
          );

          // Add the row to the table
          this.loadFollowingUpSettingsTable.settingRows.push(newRow);


        }
      );

    this.scenarioNewService.getSettingProjectLFReservesUpBAs()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectLoadFollowingUpBAsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_load_following_up_bas',
            'projectLoadFollowingUpBAsSetting',
            this.projectLoadFollowingUpBAsSettingOptions
          );

          // Add the row to the table
          this.loadFollowingUpSettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingLFReservesUpRequirement()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.loadFollowingUpRequirementSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'load_following_up_requirement',
            'loadFollowingUpRequirementSetting',
            this.loadFollowingUpRequirementSettingOptions
          );

          // Add the row to the table
          this.loadFollowingUpSettingsTable.settingRows.push(newRow);

        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.loadFollowingUpSettingsTable);

  }
  
  getSettingOptionsLFReservesDown(): void {
    // Set the setting table captions
    this.loadFollowingDownSettingsTable = new SettingsTable();
    this.loadFollowingDownSettingsTable.tableCaption = 'Load following down settings';
    this.loadFollowingDownSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingLFReservesDownBAs()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyLoadFollowingDownBAsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'geography_load_following_down_bas',
            'geographyLoadFollowingDownBAsSetting',
            this.geographyLoadFollowingDownBAsSettingOptions
          );

          // Add the row to the table
          this.loadFollowingDownSettingsTable.settingRows.push(newRow);


        }
      );

    this.scenarioNewService.getSettingProjectLFReservesDownBAs()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectLoadFollowingDownBAsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_load_following_down_bas',
            'projectLoadFollowingDownBAsSetting',
            this.projectLoadFollowingDownBAsSettingOptions
          );

          // Add the row to the table
          this.loadFollowingDownSettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingLFReservesDownRequirement()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.loadFollowingDownRequirementSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'load_following_down_requirement',
            'loadFollowingDownRequirementSetting',
            this.loadFollowingDownRequirementSettingOptions
          );

          // Add the row to the table
          this.loadFollowingDownSettingsTable.settingRows.push(newRow);

        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.loadFollowingDownSettingsTable);

  }
  
  getSettingOptionsRegulationUp(): void {
    // Set the setting table captions
    this.regulationUpSettingsTable = new SettingsTable();
    this.regulationUpSettingsTable.tableCaption = 'Regulation up settings';
    this.regulationUpSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingRegulationUpBAs()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyRegulationUpBAsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'geography_regulation_up_bas',
            'geographyRegulationUpBAsSetting',
            this.geographyRegulationUpBAsSettingOptions
          );

          // Add the row to the table
          this.regulationUpSettingsTable.settingRows.push(newRow);


        }
      );

    this.scenarioNewService.getSettingProjectRegulationUpBAs()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectRegulationUpBAsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_regulation_up_bas',
            'projectRegulationUpBAsSetting',
            this.projectRegulationUpBAsSettingOptions
          );

          // Add the row to the table
          this.regulationUpSettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingRegulationUpRequirement()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.regulationUpRequirementSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'regulation_up_requirement',
            'regulationUpRequirementSetting',
            this.regulationUpRequirementSettingOptions
          );

          // Add the row to the table
          this.regulationUpSettingsTable.settingRows.push(newRow);

        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.regulationUpSettingsTable);

  }
  
  getSettingOptionsRegulationDown(): void {
    // Set the setting table captions
    this.regulationDownSettingsTable = new SettingsTable();
    this.regulationDownSettingsTable.tableCaption = 'Regulation down settings';
    this.regulationDownSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingRegulationDownBAs()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyRegulationDownBAsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'geography_regulation_down_bas',
            'geographyRegulationDownBAsSetting',
            this.geographyRegulationDownBAsSettingOptions
          );

          // Add the row to the table
          this.regulationDownSettingsTable.settingRows.push(newRow);


        }
      );

    this.scenarioNewService.getSettingProjectRegulationDownBAs()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectRegulationDownBAsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_regulation_down_bas',
            'projectRegulationDownBAsSetting',
            this.projectRegulationDownBAsSettingOptions
          );

          // Add the row to the table
          this.regulationDownSettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingRegulationDownRequirement()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.regulationDownRequirementSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'regulation_down_requirement',
            'regulationDownRequirementSetting',
            this.regulationDownRequirementSettingOptions
          );

          // Add the row to the table
          this.regulationDownSettingsTable.settingRows.push(newRow);

        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.regulationDownSettingsTable);

  }
  
  getSettingOptionsSpinningReserves(): void {
    // Set the setting table captions
    this.spinningReservesSettingsTable = new SettingsTable();
    this.spinningReservesSettingsTable.tableCaption = '' +
      'Spinning reserves settings';
    this.spinningReservesSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingSpinningReservesBAs()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographySpinningReservesBAsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'geography_spinning_reserves_bas',
            'geographySpinningReservesBAsSetting',
            this.geographySpinningReservesBAsSettingOptions
          );

          // Add the row to the table
          this.spinningReservesSettingsTable.settingRows.push(newRow);


        }
      );

    this.scenarioNewService.getSettingProjectSpinningReservesBAs()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectSpinningReservesBAsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_spinning_reserves_bas',
            'projectSpinningReservesBAsSetting',
            this.projectSpinningReservesBAsSettingOptions
          );

          // Add the row to the table
          this.spinningReservesSettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingSpinningReservesRequirement()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.spinningReservesRequirementSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'spinning_reserves_requirement',
            'spinningReservesRequirementSetting',
            this.spinningReservesRequirementSettingOptions
          );

          // Add the row to the table
          this.spinningReservesSettingsTable.settingRows.push(newRow);

        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.spinningReservesSettingsTable);

  }
  
  getSettingOptionsFrequencyResponse(): void {
    // Set the setting table captions
    this.frequencyResponseSettingsTable = new SettingsTable();
    this.frequencyResponseSettingsTable.tableCaption =
      'Frequency response settings';
    this.frequencyResponseSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingFrequencyResponseBAs()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyFrequencyResponseBAsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'geography_frequency_response_bas',
            'geographyFrequencyResponseBAsSetting',
            this.geographyFrequencyResponseBAsSettingOptions
          );

          // Add the row to the table
          this.frequencyResponseSettingsTable.settingRows.push(newRow);


        }
      );

    this.scenarioNewService.getSettingProjectFrequencyResponseBAs()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectFrequencyResponseBAsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_frequency_response_bas',
            'projectFrequencyResponseBAsSetting',
            this.projectFrequencyResponseBAsSettingOptions
          );

          // Add the row to the table
          this.frequencyResponseSettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingFrequencyResponseRequirement()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.frequencyResponseRequirementSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'frequency_response_requirement',
            'frequencyResponseRequirementSetting',
            this.frequencyResponseRequirementSettingOptions
          );

          // Add the row to the table
          this.frequencyResponseSettingsTable.settingRows.push(newRow);

        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.frequencyResponseSettingsTable);

  }
  
  getSettingOptionsRPS(): void {
    // Set the setting table captions
    this.rpsSettingsTable = new SettingsTable();
    this.rpsSettingsTable.tableCaption =
      'RPS settings';
    this.rpsSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingRPSAreas()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyRPSAreasSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'rps_areas',
            'geographyRPSAreasSetting',
            this.geographyRPSAreasSettingOptions
          );

          // Add the row to the table
          this.rpsSettingsTable.settingRows.push(newRow);


        }
      );

    this.scenarioNewService.getSettingProjectRPSAreas()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectRPSAreasSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_rps_areas',
            'projectRPSAreasSetting',
            this.projectRPSAreasSettingOptions
          );

          // Add the row to the table
          this.rpsSettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingRPSRequirement()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.rpsTargetSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'rps_target',
            'rpsTargetSetting',
            this.rpsTargetSettingOptions
          );

          // Add the row to the table
          this.rpsSettingsTable.settingRows.push(newRow);

        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.rpsSettingsTable);

  }
  
  getSettingOptionsCarbonCap(): void {
    // Set the setting table captions
    this.carbonCapSettingsTable = new SettingsTable();
    this.carbonCapSettingsTable.tableCaption =
      'CarbonCap settings';
    this.carbonCapSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingCarbonCapAreas()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyCarbonCapAreasSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'carbon_cap_areas',
            'geographyCarbonCapAreasSetting',
            this.geographyCarbonCapAreasSettingOptions
          );

          // Add the row to the table
          this.carbonCapSettingsTable.settingRows.push(newRow);


        }
      );

    this.scenarioNewService.getSettingProjectCarbonCapAreas()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectCarbonCapAreasSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_carbon_cap_areas',
            'projectCarbonCapAreasSetting',
            this.projectCarbonCapAreasSettingOptions
          );

          // Add the row to the table
          this.carbonCapSettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingTransmissionCarbonCapAreas()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.transmissionCarbonCapAreasSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'transmission_carbon_cap_areas',
            'transmissionCarbonCapAreasSetting',
            this.transmissionCarbonCapAreasSettingOptions
          );

          // Add the row to the table
          this.carbonCapSettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingCarbonCapRequirement()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.carbonCapTargetSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'carbon_cap_target',
            'carbonCapTargetSetting',
            this.carbonCapTargetSettingOptions
          );

          // Add the row to the table
          this.carbonCapSettingsTable.settingRows.push(newRow);

        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.carbonCapSettingsTable);

  }
  
  getSettingOptionsPRM(): void {
    // Set the setting table captions
    this.prmSettingsTable = new SettingsTable();
    this.prmSettingsTable.tableCaption =
      'PRM settings';
    this.prmSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingPRMAreas()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyPRMAreasSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'prm_areas',
            'geographyPRMAreasSetting',
            this.geographyPRMAreasSettingOptions
          );

          // Add the row to the table
          this.prmSettingsTable.settingRows.push(newRow);


        }
      );

    this.scenarioNewService.getSettingProjectPRMAreas()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectPRMAreasSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_prm_areas',
            'projectPRMAreasSetting',
            this.projectPRMAreasSettingOptions
          );

          // Add the row to the table
          this.prmSettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingPRMRequirement()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.prmRequirementSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'prm_requirement',
            'prmRequirementSetting',
            this.prmRequirementSettingOptions
          );

          // Add the row to the table
          this.prmSettingsTable.settingRows.push(newRow);

        }
      );

    this.scenarioNewService.getSettingELCCSurface()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.elccSurfaceSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'elcc_surface',
            'elccSurfaceSetting',
            this.elccSurfaceSettingOptions
          );

          // Add the row to the table
          this.prmSettingsTable.settingRows.push(newRow);

        }
      );

    this.scenarioNewService.getSettingProjectELCCChars()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectELCCCharsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_elcc_chars',
            'projectELCCCharsSetting',
            this.projectELCCCharsSettingOptions
          );

          // Add the row to the table
          this.prmSettingsTable.settingRows.push(newRow);

        }
      );

    this.scenarioNewService.getSettingProjectEnergyOnly()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectPRMEnergyOnlySettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_energy_only',
            'projectPRMEnergyOnlySetting',
            this.projectPRMEnergyOnlySettingOptions
          );

          // Add the row to the table
          this.prmSettingsTable.settingRows.push(newRow);

        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.prmSettingsTable);

  }
  
  getSettingOptionsLocalCapacity(): void {
    // Set the setting table captions
    this.localCapacitySettingsTable = new SettingsTable();
    this.localCapacitySettingsTable.tableCaption =
      'Local capacity settings';
    this.localCapacitySettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingLocalCapacityAreas()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyLocalCapacityAreasSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'local_capacity_areas',
            'geographyLocalCapacityAreasSetting',
            this.geographyLocalCapacityAreasSettingOptions
          );

          // Add the row to the table
          this.localCapacitySettingsTable.settingRows.push(newRow);


        }
      );

    this.scenarioNewService.getSettingProjectLocalCapacityAreas()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectLocalCapacityAreasSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_local_capacity_areas',
            'projectLocalCapacityAreasSetting',
            this.projectLocalCapacityAreasSettingOptions
          );

          // Add the row to the table
          this.localCapacitySettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingLocalCapacityRequirement()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.localCapacityRequirementSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'local_capacity_requirement',
            'localCapacityRequirementSetting',
            this.localCapacityRequirementSettingOptions
          );

          // Add the row to the table
          this.localCapacitySettingsTable.settingRows.push(newRow);

        }
      );

    this.scenarioNewService.getSettingProjectLocalCapacityChars()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.projectLocalCapacityCharsSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_local_capacity_chars',
            'projectLocalCapacityCharsSetting',
            this.projectLocalCapacityCharsSettingOptions
          );

          // Add the row to the table
          this.localCapacitySettingsTable.settingRows.push(newRow);

        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.localCapacitySettingsTable);

  }

  getSettingOptionsTuning(): void {
    // Set the setting table captions
    this.tuningSettingsTable = new SettingsTable();
    this.tuningSettingsTable.tableCaption = 'Tuning settings';
    this.tuningSettingsTable.settingRows = [];


    // Get the settings
    this.scenarioNewService.getSettingTuning()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.tuningSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'tuning',
            'tuningSetting',
             this.tuningSettingOptions
          );

          // Add the row to the table
          this.tuningSettingsTable.settingRows.push(newRow);
        }
      );

    // Add the table to the scenario structure
    this.ScenarioNewStructure.push(this.tuningSettingsTable);
  }

  saveNewScenario() {
    const socket = io.connect('http://127.0.0.1:8080/');
    socket.on('connect', function() {
        console.log(`Connection established: ${socket.connected}`);
    });
    socket.emit('add_new_scenario', this.newScenarioForm.value);
  }

}


class Feature {
  featureName: string;
  formControlName: string;
}

class SettingsTable {
  tableCaption: string;
  settingRows: SettingRow[]
}

class SettingRow {
  rowName: string;
  rowFormControlName: string;
  settingOptions: Setting[]
}

function featureSelectionOptions() {
    return ['', 'yes', 'no']
  }

function createRow(rowName: string,
            rowFormControlName: string,
            settingOptions: Setting[]) {
      const settingRow = new SettingRow();
      settingRow.rowName = rowName;
      settingRow.rowFormControlName = rowFormControlName;
      settingRow.settingOptions = settingOptions;

      return settingRow
  }
