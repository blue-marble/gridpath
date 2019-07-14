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
  systemLoadSettingOptions: Setting[];

  // Project capacity settings
  projectPortfolioSettingOptions: Setting[];
  projectExistingCapacitySettingOptions: Setting[];
  projectExistingFixedCostSettingOptions: Setting[];
  projectNewCostSettingOptions: Setting[];
  projectNewPotentialSettingOptions: Setting[];
  projectAvailabilitySettingOptions: Setting[];

  // Project operational characteristics settings
  projectOperationalCharsSettingOptions: Setting[];

  // Fuel settings
  projectFuelsSettingOptions: Setting[];
  fuelPricesSettingOptions: Setting[];

  // Transmission capacity settings
  transmissionPortfolioSettingOptions: Setting[];
  transmissionExistingCapacitySettingOptions: Setting[];

  // Transmission operational characteristics
  transmissionOperationalCharsSettingOptions: Setting[];

  // Transission hurdle rates settings
  transmissionHurdleRatesSettingOptions: Setting[];

  // Transmission simultaneous flow limits settings
  transmissionSimultaneousFlowLimitsSettingOptions: Setting[];
  transmissionSimultaneousFlowLimitLineGroupsSettingOptions: Setting[];

  // Load-following-up settings
  loadFollowingUpProfileSettingOptions: Setting[];
  projectLoadFollowingUpBAsSettingOptions: Setting[];

  // Load-following-down settings
  loadFollowingDownProfileSettingOptions: Setting[];
  projectLoadFollowingDownBAsSettingOptions: Setting[];

  // Regulation up settings
  regulationUpProfileSettingOptions: Setting[];
  projectRegulationUpBAsSettingOptions: Setting[];

  // Regulation down settings
  regulationDownProfileSettingOptions: Setting[];
  projectRegulationDownBAsSettingOptions: Setting[];

  // Spinning reserves settings
  spinningReservesProfileSettingOptions: Setting[];
  projectSpinningReservesBAsSettingOptions: Setting[];

  // Frequency response settings
  frequencyResponseSettingOptions: Setting[];
  projectFrequencyResponseBAsSettingOptions: Setting[];

  // RPS settings
  rpsTargetSettingOptions: Setting[];
  projectRPSAreasSettingOptions: Setting[];

  // Carbon cap settings
  carbonCapSettingOptions: Setting[];
  projectCarbonCapAreasSettingOptions: Setting[];
  transmissionCarbonCapAreasSettingOptions: Setting[];

  // PRM settings
  prmRequirementSettingOptions: Setting[];
  projectPRMAreasSettingOptions: Setting[];
  projectELCCCharsSettingOptions: Setting[];
  elccSurfaceSettingOptions: Setting[];
  projectPRMEnergyOnlySettingOptions: Setting[];

  // Local capacity settings
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


    this.featureSelectionOption = this.featureSelectionOptions();


  }

  ngOnInit() {
    this.ScenarioNewStructure = [];
    this.getSettingOptionsTemporal();
    this.getSettingOptionsLoadZones();
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
          const temporalSettingRow = new SettingRow();
          temporalSettingRow.rowName = 'temporal';
          temporalSettingRow.rowFormControlName = 'temporalSetting';
          temporalSettingRow.settingOptions = this.temporalSettingOptions;

          // Add the row to the table
          this.temporalSettingsTable.settingRows.push(temporalSettingRow);
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
          const loadZoneSettingRow = new SettingRow();
          loadZoneSettingRow.rowName = 'geography_load_zones';
          loadZoneSettingRow.rowFormControlName = 'geographyLoadZonesSetting';
          loadZoneSettingRow.settingOptions =
            this.geographyLoadZonesSettingOptions;

          // Add the row to the table
          this.loadZoneSettingsTable.settingRows.push(loadZoneSettingRow);


        }
      );

    this.scenarioNewService.getSettingProjectLoadZones()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyProjectLoadZonesSettingOptions = scenarioSetting;

          // Create the row
          const projectLoadZoneSettingRow = new SettingRow();
          projectLoadZoneSettingRow.rowName = 'project_load_zones';
          projectLoadZoneSettingRow.rowFormControlName =
            'geographyProjectLoadZonesSetting';
          projectLoadZoneSettingRow.settingOptions =
            this.geographyProjectLoadZonesSettingOptions;

          // Add the row to the table
          this.loadZoneSettingsTable.settingRows.push(projectLoadZoneSettingRow);


        }
      );

    this.scenarioNewService.getSettingTransmissionLoadZones()
      .subscribe(
        scenarioSetting => {
          // Get the settings from the server
          this.geographyTxLoadZonesSettingOptions = scenarioSetting;

          // Create the row
          const transmissionLoadZoneSettingRow = new SettingRow();
          transmissionLoadZoneSettingRow.rowName = 'transmission_load_zones';
          transmissionLoadZoneSettingRow.rowFormControlName =
            'geographyTxLoadZonesSetting';
          transmissionLoadZoneSettingRow.settingOptions =
            this.geographyTxLoadZonesSettingOptions;

          // Add the row to the table
          this.loadZoneSettingsTable.settingRows.push(
            transmissionLoadZoneSettingRow
          );

        }
      );

      // Add the table to the scenario structure
      this.ScenarioNewStructure.push(this.loadZoneSettingsTable);


  }

  saveNewScenario() {
    const socket = io.connect('http://127.0.0.1:8080/');
    socket.on('connect', function() {
        console.log(`Connection established: ${socket.connected}`);
    });
    socket.emit('add_new_scenario', this.newScenarioForm.value);
  }

  featureSelectionOptions() {
    return ['', 'yes', 'no']
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
