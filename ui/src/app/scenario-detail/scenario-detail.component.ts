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

  // The final table structure we'll iterate over
  scenarioDetailStructure: SettingsTable[];

  scenarioName: string;

  // Needed for routing
  scenarioID: number;
  private sub: any;

  constructor(private route: ActivatedRoute,
    private scenarioDetailService: ScenarioDetailService,
    private location: Location) {
  }

  ngOnInit(): void {
    // Scenario-detail structure init with emtpy list
    this.scenarioDetailStructure = [];

    // The ActivatedRoute service provides a params Observable which we can
    // subscribe to in order to get the route parameters
    this.sub = this.route.params.subscribe(params => {
       this.scenarioID = +params['id'];
       console.log(`Scenario ID is ${this.scenarioID}`)
    });

    // Get the scenario detail data
    this.getScenarioName(this.scenarioID);
    this.getScenarioDetailFeatures(this.scenarioID);
    this.getScenarioDetailTemporal(this.scenarioID);
    this.getScenarioDetailGeographyLoadZones(this.scenarioID);
    this.getScenarioDetailLoad(this.scenarioID);
    this.getScenarioDetailProjectCapacity(this.scenarioID);
    this.getScenarioDetailProjectOpChars(this.scenarioID);
    this.getScenarioDetailFuels(this.scenarioID);
    this.getScenarioDetailTransmissionCapacity(this.scenarioID);
    this.getScenarioDetailTransmissionOpChars(this.scenarioID);
    this.getScenarioDetailTransmissionHurdleRates(this.scenarioID);
    this.getScenarioDetailTransmissionSimFlow(this.scenarioID);
    this.getScenarioDetailLFup(this.scenarioID);
    this.getScenarioDetailLFDown(this.scenarioID);
    this.getScenarioDetailRegUp(this.scenarioID);
    this.getScenarioDetailRegDown(this.scenarioID);
    this.getScenarioDetailSpin(this.scenarioID);
    this.getScenarioDetailFreqResp(this.scenarioID);
    this.getScenarioDetailRPS(this.scenarioID);
    this.getScenarioDetailCarbonCap(this.scenarioID);
    this.getScenarioDetailPRM(this.scenarioID);
    this.getScenarioDetailLocalCapacity(this.scenarioID);
  }

  getScenarioName(scenarioID): void {

    this.scenarioDetailService.getScenarioName(scenarioID)
      .subscribe(
        scenarioDetail => {
          this.scenarioName = scenarioDetail;
        }
      );

  }

  getScenarioDetailFeatures(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Features';

    this.scenarioDetailService.getScenarioDetailFeatures(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailTemporal(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Temporal settings';

    this.scenarioDetailService.getScenarioDetailTemporal(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailGeographyLoadZones(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Load zones';

    this.scenarioDetailService.getScenarioDetailGeographyLoadZones(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailLoad(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'System load';

    this.scenarioDetailService.getScenarioDetailLoad(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailProjectCapacity(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Project capacity';

    this.scenarioDetailService.getScenarioDetailProjectCapacity(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailProjectOpChars(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption =
      'Project operational characteristics';

    this.scenarioDetailService.getScenarioDetailProjectOpChars(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailFuels(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Fuels';

    this.scenarioDetailService.getScenarioDetailFuels(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailTransmissionCapacity(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Transmission capacity';

    this.scenarioDetailService.getScenarioDetailTransmissionCapacity(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailTransmissionOpChars(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption =
      'Transmission operational characteristics';

    this.scenarioDetailService.getScenarioDetailTransmissionOpChars(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailTransmissionHurdleRates(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Transmission hurdle rates';

    this.scenarioDetailService.getScenarioDetailTransmissionHurdleRates(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailTransmissionSimFlow(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption =
      'Transmission simultaneous flow limits';

    this.scenarioDetailService.getScenarioDetailTransmissionSimFlow(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailLFup(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Load-following reserves up';

    this.scenarioDetailService.getScenarioDetailLFUp(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailLFDown(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Load-following reserves down';

    this.scenarioDetailService.getScenarioDetailLFDown(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailRegUp(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Regulation up';

    this.scenarioDetailService.getScenarioDetailRegUp(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailRegDown(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Regulation down';

    this.scenarioDetailService.getScenarioDetailRegDown(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailSpin(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Spinning reserves';

    this.scenarioDetailService.getScenarioDetailSpin(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailFreqResp(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Frequency response';

    this.scenarioDetailService.getScenarioDetailFreqResp(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailRPS(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'RPS';

    this.scenarioDetailService.getScenarioDetailRPS(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailCarbonCap(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Carbon cap';

    this.scenarioDetailService.getScenarioDetailCarbonCap(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailPRM(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'PRM';

    this.scenarioDetailService.getScenarioDetailPRM(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  getScenarioDetailLocalCapacity(scenarioID): void {
    const settingsTable = new SettingsTable();
    settingsTable.tableCaption = 'Local capacity';

    this.scenarioDetailService.getScenarioDetailLocalCapacity(scenarioID)
      .subscribe(
        scenarioDetail => {
          settingsTable.settingRows = scenarioDetail;
        }
      );

    this.scenarioDetailStructure.push(settingsTable)
  }

  goBack(): void {
    this.location.back();
  }

  runScenario(scenarioID): void {
    console.log(`Running scenario ${scenarioID}`);
    electron.ipcRenderer.send('runScenario', scenarioID)
  }

}

class SettingsTable {
  tableCaption: string;
  settingRows: ScenarioDetail[]
}
