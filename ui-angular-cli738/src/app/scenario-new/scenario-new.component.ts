import { Component, OnInit } from '@angular/core';

import { FormControl, FormGroup } from '@angular/forms';

const io = (<any>window).require('socket.io-client');


@Component({
  selector: 'app-scenario-new',
  templateUrl: './scenario-new.component.html',
  styleUrls: ['./scenario-new.component.css']
})
export class ScenarioNewComponent implements OnInit {

  features: Features[];

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
    featureLocalCapacity: new FormControl('')
  });

  yesNo: string[];

  constructor() {
    this.features = [
      {featureName: 'feature_fuels', formControlName: 'featureFuels'},
      {featureName: 'feature_transmission',
        formControlName: 'featureTransmission'},
      {featureName: 'feature_transmission_hurdle_rates',
        formControlName: 'featureTransmissionHurdleRates'},
      {featureName: 'feature_simultaneous_flow_limits',
        formControlName: 'featureSimFlowLimits'},
      {featureName: 'feature_load_following_up',
        formControlName: 'featureLFUp'},
      {featureName: 'feature_load_following_down',
        formControlName: 'featureLFDown'},
      {featureName: 'feature_regulation_up', formControlName: 'featureRegUp'},
      {featureName: 'feature_regulation_down',
        formControlName: 'featureRegDown'},
      {featureName: 'feature_spinning_reserves',
        formControlName: 'featureSpin'},
      {featureName: 'feature_frequency_response',
        formControlName: 'featureFreqResp'},
      {featureName: 'feature_rps', formControlName: 'featureRPS'},
      {featureName: 'feature_carbon_cap', formControlName: 'featureCarbonCap'},
      {featureName: 'feature_track_carbon_imports',
        formControlName: 'featureTrackCarbonImports'},
      {featureName: 'feature_prm', formControlName: 'featurePRM'},
      {featureName: 'feature_elcc_surface',
        formControlName: 'featureELCCSurface'},
      {featureName: 'feature_local_capacity',
        formControlName: 'featureLocalCapacity'}
      ];
    this.yesNo = this.getYesNo()
  }

  ngOnInit() {
  }

  saveNewScenario() {
    console.log("In saveNewScenario");
    console.log(this.newScenarioForm.value);

    const socket = io.connect('http://127.0.0.1:8080/');
    socket.on('connect', function() {
        console.log(`Connection established: ${socket.connected}`);
    });
    socket.emit('add_new_scenario', this.newScenarioForm.value);
  }

  getYesNo() {
    return ['', 'yes', 'no']
  }

  getTemporal() {

  }

}


export class Features {
  featureName: string;
  formControlName: string;
}
