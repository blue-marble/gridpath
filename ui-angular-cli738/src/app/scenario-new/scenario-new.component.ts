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
  geographyProjectLoadZonesSettingOptions: Setting[];
  geographyTxLoadZonesSettingOptions: Setting[];

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
  loadFollowingUpProfileSettingsTable: SettingsTable;
  loadFollowingUpProfileSettingOptions: Setting[];
  projectLoadFollowingUpBAsSettingOptions: Setting[];

  // Load-following-down settings
  loadFollowingDownProfileSettingsTable: SettingsTable;
  loadFollowingDownProfileSettingOptions: Setting[];
  projectLoadFollowingDownBAsSettingOptions: Setting[];

  // Regulation up settings
  regulationUpProfileSettingsTable: SettingsTable;
  regulationUpProfileSettingOptions: Setting[];
  projectRegulationUpBAsSettingOptions: Setting[];

  // Regulation down settings
  regulationDownProfileSettingsTable: SettingsTable;
  regulationDownProfileSettingOptions: Setting[];
  projectRegulationDownBAsSettingOptions: Setting[];

  // Spinning reserves settings
  spinningReservesProfileSettingsTable: SettingsTable;
  spinningReservesProfileSettingOptions: Setting[];
  projectSpinningReservesBAsSettingOptions: Setting[];

  // Frequency response settings
  frequencyResponseSettingsTable: SettingsTable;
  frequencyResponseSettingOptions: Setting[];
  projectFrequencyResponseBAsSettingOptions: Setting[];

  // RPS settings
  rpsTargetSettingsTable: SettingsTable;
  rpsTargetSettingOptions: Setting[];
  projectRPSAreasSettingOptions: Setting[];

  // Carbon cap settings
  carbonCapSettingsTable: SettingsTable;
  carbonCapSettingOptions: Setting[];
  projectCarbonCapAreasSettingOptions: Setting[];
  transmissionCarbonCapAreasSettingOptions: Setting[];

  // PRM settings
  prmRequirementSettingsTable: SettingsTable;
  prmRequirementSettingOptions: Setting[];
  projectPRMAreasSettingOptions: Setting[];
  projectELCCCharsSettingOptions: Setting[];
  elccSurfaceSettingOptions: Setting[];
  projectPRMEnergyOnlySettingOptions: Setting[];

  // Local capacity settings
  localCapacityRequirementSettingsTable: SettingsTable;
  localCapacityRequirementSettingOptions: Setting[];
  projectLocalCapacityAreasSettingOptions: Setting[];
  projectLocalCapacityCharsSettingOptions: Setting[];

  // Tuning settings


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
    loadFollowingUpProfileSetting: new FormControl(''),
    projectLoadFollowingUpBAsSetting: new FormControl(''),
    loadFollowingDownProfileSetting: new FormControl(''),
    projectLoadFollowingDownBAsSetting: new FormControl(''),
    regulationUpProfileSetting: new FormControl(''),
    projectRegulationUpBAsSetting: new FormControl(''),
    regulationDownProfileSetting: new FormControl(''),
    projectRegulationDownBAsSetting: new FormControl(''),
    spinningReservesProfileSetting: new FormControl(''),
    projectSpinningReservesBAsSetting: new FormControl(''),
    frequencyResponseSetting: new FormControl(''),
    projectFrequencyResponseBAsSetting: new FormControl(''),
    rpsTargetSetting: new FormControl(''),
    projectRPSAreasSetting: new FormControl(''),
    carbonCapSetting: new FormControl(''),
    projectCarbonCapAreasSetting: new FormControl(''),
    transmissionCarbonCapAreasSetting: new FormControl(''),
    prmRequirementSetting: new FormControl(''),
    projectPRMAreasSetting: new FormControl(''),
    projectELCCCharsSetting: new FormControl(''),
    elccSurfaceSetting: new FormControl(''),
    projectPRMEnergyOnlySetting: new FormControl(''),
    localCapacityRequirementSetting: new FormControl(''),
    projectLocalCapacityAreasSetting: new FormControl(''),
    projectLocalCapacityCharsSetting: new FormControl(''),
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
          this.geographyProjectLoadZonesSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'project_load_zones',
            'geographyProjectLoadZonesSetting',
            this.geographyProjectLoadZonesSettingOptions
          );

          // Add the row to the table
          this.loadZoneSettingsTable.settingRows.push(newRow);
        }
      );

    this.scenarioNewService.getSettingTransmissionLoadZones()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyTxLoadZonesSettingOptions = scenarioSetting;

          // Create the row
          const newRow = createRow(
            'transmission_load_zones',
            'geographyTxLoadZonesSetting',
            this.geographyTxLoadZonesSettingOptions
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
