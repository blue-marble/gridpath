import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { ScenarioDetailService } from '../scenario-detail/scenario-detail.service';
import { SettingsTable } from '../scenario-new/scenario-new';
import { ScenarioNewService } from '../scenario-new/scenario-new.service';
import { StartingValues } from '../scenario-detail/scenario-detail';
import {Router} from "@angular/router";

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
    private router: Router,
    private scenarioNewService: ScenarioNewService,
    private scenarioDetailService: ScenarioDetailService
  ) {
    const navigation = this.router.getCurrentNavigation();
    const state = navigation.extras.state as {
      baseScenarioID: number,
      scenariosIDsToCompare: boolean
    };
  }

  ngOnInit() {

    // Need to get the navigation extras from history (as the state is only
    // available during navigation); we'll use these to change the behavior
    // of the scenario name field
    this.baseScenarioID = history.state.baseScenarioID;
    this.scenariosIDsToCompare = history.state.scenariosIDsToCompare;

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
