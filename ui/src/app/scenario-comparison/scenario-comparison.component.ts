import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { ScenarioDetailService } from '../scenario-detail/scenario-detail.service';
import { SettingsTable } from '../scenario-new/scenario-new';
import { ScenarioNewService } from '../scenario-new/scenario-new.service';
import { StartingValues } from '../scenario-detail/scenario-detail';

@Component({
  selector: 'app-scenario-comparison',
  templateUrl: './scenario-comparison.component.html',
  styleUrls: ['./scenario-comparison.component.css']
})
export class ScenarioComparisonComponent implements OnInit {

  baseScenarioID: number;
  scenariosIDsToCompare: number[];
  settingTables: SettingsTable[];
  baseScenarioValues: StartingValues;
  scenariosToCompareValues: StartingValues[];

  constructor(
    private location: Location,
    private scenarioNewService: ScenarioNewService,
    private scenarioDetailService: ScenarioDetailService
  ) { }

  ngOnInit() {

    // Get these from form
    this.baseScenarioID = 1;
    this.scenariosIDsToCompare = [2, 3, 4];

    this.settingTables = [];
    this.getSettingTables();

    this.baseScenarioValues = {} as StartingValues;
    this.getBaseScenarioValues(this.baseScenarioID);

    this.scenariosToCompareValues = [] as StartingValues[];
    this.getScenariosToCompareValues(this.scenariosIDsToCompare);
  }

  getSettingTables(): void {
    this.scenarioNewService.getScenarioNewAPI()
      .subscribe(
        scenarioNewAPI => {
          this.settingTables = scenarioNewAPI.SettingsTables;
        }
      );
  }

  getBaseScenarioValues(scenarioID): void {
    this.scenarioDetailService.getScenarioDetailAPI(scenarioID)
      .subscribe(
        scenarioDetail => {
            this.baseScenarioValues = scenarioDetail.editScenarioValues;
        }
      );
  }

  getScenariosToCompareValues(scenarioIDsToCompare): void {
    for (const scenarioID of scenarioIDsToCompare) {
      this.scenarioDetailService.getScenarioDetailAPI(scenarioID)
        .subscribe(
          scenarioDetail => {
              this.scenariosToCompareValues.push(
                scenarioDetail.editScenarioValues
              );
          }
        );
    }
  }


  goBack(): void {
    this.location.back();
  }
}
