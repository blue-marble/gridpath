import { Component, OnInit, NgZone } from '@angular/core';
import { HomeService} from './home.service';
import { SettingsService } from '../settings/settings.service';

const electron = ( window as any ).require('electron');

import { ScenarioEditService } from '../scenario-detail/scenario-edit.service';
import { emptyStartingValues } from '../scenario-new/scenario-new.component';


@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {

  serverStatus: string;
  directoryStatus: string;
  databaseStatus: string;
  pythonStatus: string;

  constructor(
    private homeService: HomeService,
    private settingsService: SettingsService,
    private scenarioEditService: ScenarioEditService,
    private zone: NgZone
  ) { }

  ngOnInit() {
    // TODO: this should happen on navigating away from scenario-new
    this.scenarioEditService.changeStartingScenario(emptyStartingValues);

    // Get the server status
    this.getServerStatus();
    this.getDirectoryStatus();
    this.getDatabaseStatus();
    this.getPythonStatus();

    // If any of the settings are null, we'll overwrite the status from
    // the settings service with 'not set'
    // Ask Electron for the current settings
    electron.ipcRenderer.send('requestStoredSettings');
    electron.ipcRenderer.on('sendStoredSettings',
      (event, data) => {
        console.log('Got data ', data);
        if (data.requestedScenariosDirectory.value == null) {
          this.zone.run(() => this.directoryStatus = 'not set');
        }
        if (data.requestedGridPathDatabase.value === null) {
          this.zone.run(() => this.databaseStatus = 'not set');
        }
        if (data.requestedPythonBinary.value === null) {
          this.zone.run(() => this.pythonStatus = 'not set');
        }
      }
    );
  }

  getServerStatus(): void {
    console.log('Getting server status...');
    this.homeService.getScenarios()
      .subscribe(
        status => this.serverStatus = status,
        error => {
          console.log('HTTP Error caught', error);
          this.serverStatus = 'down';
        }
      );
  }

  updateServerStatus(): void {
    console.log('Updating server status...');
    this.getServerStatus();
  }

  getDirectoryStatus(): void {
    this.settingsService.directoryStatusSubject
      .subscribe((settingsStatus: string) => {
        this.directoryStatus = settingsStatus;
      }
    );
  }

  getDatabaseStatus(): void {
    this.settingsService.databaseStatusSubject
      .subscribe((settingsStatus: string) => {
        this.databaseStatus = settingsStatus;
      }
    );
  }

  getPythonStatus(): void {
    this.settingsService.pythonStatusSubject
      .subscribe((settingsStatus: string) => {
        this.pythonStatus = settingsStatus;
      }
    );
  }
}
