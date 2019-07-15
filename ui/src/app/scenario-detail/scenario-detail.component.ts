import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';

const electron = (<any>window).require('electron');

import { ScenarioDetail } from './scenario-detail'
import { ScenarioDetailService } from './scenario-detail.service'

@Component({
  selector: 'app-scenario-detail',
  templateUrl: './scenario-detail.component.html',
  styleUrls: ['./scenario-detail.component.css']
})

export class ScenarioDetailComponent implements OnInit {

  scenarioDetail: ScenarioDetail[];
  scenarioDetailFeatures: ScenarioDetail[];
  scenarioDetailTemporal: ScenarioDetail[];
  scenarioDetailGeographyLoadZones: ScenarioDetail[];
  scenarioDetailLoad: ScenarioDetail[];
  scenarioDetailProjectCapacity: ScenarioDetail[];
  scenarioDetailProjectOpChars: ScenarioDetail[];
  scenarioDetailFuels: ScenarioDetail[];
  scenarioDetailTransmissionCapacity: ScenarioDetail[];
  scenarioDetailTransmissionOpChars: ScenarioDetail[];
  scenarioDetailTransmissionHurdleRates: ScenarioDetail[];
  scenarioDetailTransmissionSimFlow: ScenarioDetail[];
  scenarioDetailLFUp: ScenarioDetail[];
  scenarioDetailLFDown: ScenarioDetail[];
  scenarioDetailRegUp: ScenarioDetail[];
  scenarioDetailRegDown: ScenarioDetail[];
  scenarioDetailSpin: ScenarioDetail[];
  scenarioDetailFreqResp: ScenarioDetail[];
  scenarioDetailRPS: ScenarioDetail[];
  scenarioDetailCarbonCap: ScenarioDetail[];
  scenarioDetailPRM: ScenarioDetail[];
  scenarioDetailLocalCapacity: ScenarioDetail[];
  id: number;
  private sub: any;

  constructor(private route: ActivatedRoute,
    private scenarioDetailService: ScenarioDetailService,
    private location: Location) {
  }

  ngOnInit(): void {
    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to in order to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.id = +params['id'];
       console.log(`Scenario ID is ${this.id}`)
    });
    this.getScenarioDetailAll(this.id);
    this.getScenarioDetailFeatures(this.id);
    this.getScenarioDetailTemporal(this.id);
    this.getScenarioDetailGeographyLoadZones(this.id);
    this.getScenarioDetailLoad(this.id);
    this.getScenarioDetailProjectCapacity(this.id);
    this.getScenarioDetailProjectOpChars(this.id);
    this.getScenarioDetailFuels(this.id);
    this.getScenarioDetailTransmissionCapacity(this.id);
    this.getScenarioDetailTransmissionOpChars(this.id);
    this.getScenarioDetailTransmissionHurdleRates(this.id);
    this.getScenarioDetailTransmissionSimFlow(this.id);
    this.getScenarioDetailLFup(this.id);
    this.getScenarioDetailLFDown(this.id);
    this.getScenarioDetailRegUp(this.id);
    this.getScenarioDetailRegDown(this.id);
    this.getScenarioDetailSpin(this.id);
    this.getScenarioDetailFreqResp(this.id);
    this.getScenarioDetailRPS(this.id);
    this.getScenarioDetailCarbonCap(this.id);
    this.getScenarioDetailPRM(this.id);
    this.getScenarioDetailLocalCapacity(this.id);
  }

  getScenarioDetailAll(id): void {
    this.scenarioDetailService.getScenarioDetailAll(id)
      .subscribe(scenarioDetail => this.scenarioDetail = scenarioDetail);
  }

  getScenarioDetailFeatures(id): void {
    this.scenarioDetailService.getScenarioDetailFeatures(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailFeatures = scenarioDetail
      );
  }

  getScenarioDetailTemporal(id): void {
    this.scenarioDetailService.getScenarioDetailTemporal(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailTemporal = scenarioDetail
      );
  }

  getScenarioDetailGeographyLoadZones(id): void {
    this.scenarioDetailService.getScenarioDetailGeographyLoadZones(id)
      .subscribe(
        scenarioDetail =>
          this.scenarioDetailGeographyLoadZones = scenarioDetail
      );
  }

  getScenarioDetailLoad(id): void {
    this.scenarioDetailService.getScenarioDetailLoad(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailLoad = scenarioDetail
      );
  }

  getScenarioDetailProjectCapacity(id): void {
    this.scenarioDetailService.getScenarioDetailProjectCapacity(id)
      .subscribe(
        scenarioDetail =>
          this.scenarioDetailProjectCapacity = scenarioDetail
      );
  }

  getScenarioDetailProjectOpChars(id): void {
    this.scenarioDetailService.getScenarioDetailProjectOpChars(id)
      .subscribe(
        scenarioDetail =>
          this.scenarioDetailProjectOpChars = scenarioDetail
      );
  }

  getScenarioDetailFuels(id): void {
    this.scenarioDetailService.getScenarioDetailFuels(id)
      .subscribe(
        scenarioDetail =>
          this.scenarioDetailFuels = scenarioDetail
      );
  }

  getScenarioDetailTransmissionCapacity(id): void {
    this.scenarioDetailService.getScenarioDetailTransmissionCapacity(id)
      .subscribe(
        scenarioDetail =>
          this.scenarioDetailTransmissionCapacity = scenarioDetail
      );
  }

  getScenarioDetailTransmissionOpChars(id): void {
    this.scenarioDetailService.getScenarioDetailTransmissionOpChars(id)
      .subscribe(
        scenarioDetail =>
          this.scenarioDetailTransmissionOpChars = scenarioDetail
      );
  }

  getScenarioDetailTransmissionHurdleRates(id): void {
    this.scenarioDetailService.getScenarioDetailTransmissionHurdleRates(id)
      .subscribe(
        scenarioDetail =>
          this.scenarioDetailTransmissionHurdleRates = scenarioDetail
      );
  }

  getScenarioDetailTransmissionSimFlow(id): void {
    this.scenarioDetailService.getScenarioDetailTransmissionSimFlow(id)
      .subscribe(
        scenarioDetail =>
          this.scenarioDetailTransmissionSimFlow = scenarioDetail
      );
  }

  getScenarioDetailLFup(id): void {
    this.scenarioDetailService.getScenarioDetailLFUp(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailLFUp = scenarioDetail
      );
  }

  getScenarioDetailLFDown(id): void {
    this.scenarioDetailService.getScenarioDetailLFDown(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailLFDown = scenarioDetail
      );
  }

  getScenarioDetailRegUp(id): void {
    this.scenarioDetailService.getScenarioDetailRegUp(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailRegUp = scenarioDetail
      );
  }

  getScenarioDetailRegDown(id): void {
    this.scenarioDetailService.getScenarioDetailRegDown(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailRegDown = scenarioDetail
      );
  }

  getScenarioDetailSpin(id): void {
    this.scenarioDetailService.getScenarioDetailSpin(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailSpin = scenarioDetail
      );
  }

  getScenarioDetailFreqResp(id): void {
    this.scenarioDetailService.getScenarioDetailFreqResp(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailFreqResp = scenarioDetail
      );
  }

  getScenarioDetailRPS(id): void {
    this.scenarioDetailService.getScenarioDetailRPS(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailRPS = scenarioDetail
      );
  }

  getScenarioDetailCarbonCap(id): void {
    this.scenarioDetailService.getScenarioDetailCarbonCap(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailCarbonCap = scenarioDetail
      );
  }

  getScenarioDetailPRM(id): void {
    this.scenarioDetailService.getScenarioDetailPRM(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailPRM = scenarioDetail
      );
  }

  getScenarioDetailLocalCapacity(id): void {
    this.scenarioDetailService.getScenarioDetailLocalCapacity(id)
      .subscribe(
        scenarioDetail => this.scenarioDetailLocalCapacity = scenarioDetail
      );
  }

  goBack(): void {
    this.location.back();
  }

  runScenario(id): void {
    console.log(`Running scenario ${id}`);
    electron.ipcRenderer.send('runScenario', id)
  }

}
