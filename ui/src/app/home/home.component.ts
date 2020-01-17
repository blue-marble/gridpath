import {Component, OnInit, NgZone, OnDestroy} from '@angular/core';
import { HomeService} from './home.service';
import { SettingsService } from '../settings/settings.service';

const electron = ( window as any ).require('electron');


@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit, OnDestroy {

  serverStatus: string;
  refreshServerStatus: any;

  directoryStatus: string;
  databaseStatus: string;
  pythonStatus: string;

  solver1NameStatus: string;
  solver1ExecutableStatus: string;
  solver2NameStatus: string;
  solver2ExecutableStatus: string;
  solver3NameStatus: string;
  solver3ExecutableStatus: string;

  solver1Status: string;
  solver2Status: string;
  solver3Status: string;

  scenarioRunStatus: [][];
  refreshRunStatus: any;

  scenarioValidationStatus: [][];
  refreshValidationStatus: any;

  constructor(
    private homeService: HomeService,
    private settingsService: SettingsService,
    private zone: NgZone
  ) { }

  ngOnInit() {
    // Get the server status and refresh every 5 seconds
    this.getServerStatus();
    this.refreshServerStatus = setInterval(() => {
        this.getServerStatus();
    }, 5000);

    // Get setting status
    this.getDirectoryStatus();
    this.getDatabaseStatus();
    this.getPythonStatus();
    this.determineSolver1Status();
    this.determineSolver2Status();
    this.determineSolver3Status();

    // TODO: is this necessary now that we check this in Settings
    // If any of the settings are null, we'll overwrite the status from
    // the settings service with 'not set'
    // For the solvers, we'll overwrite if either the name or the executable
    // is not set
    // Ask Electron for the current settings
    electron.ipcRenderer.send('requestStoredSettings');
    electron.ipcRenderer.on('sendStoredSettings',
      (event, data) => {
        console.log('Got data ', data);
        if (data.currentScenariosDirectory.value == null) {
          this.zone.run(() => this.directoryStatus = 'not set');
        }
        if (data.currentGridPathDatabase.value === null) {
          this.zone.run(() => this.databaseStatus = 'not set');
        }
        if (data.currentPythonEnvironment.value === null) {
          this.zone.run(() => this.pythonStatus = 'not set');
        }
        if (data.currentSolver1Name.value === null
          || data.currentSolver1Executable.value === null) {
          this.zone.run(() => this.solver1Status = 'not set');
        }
        if (data.currentSolver2Name.value === null
          || data.currentSolver2Executable.value === null) {
          this.zone.run(() => this.solver2Status = 'not set');
        }
        if (data.currentSolver3Name.value === null
          || data.currentSolver3Executable.value === null) {
          this.zone.run(() => this.solver3Status = 'not set');
        }
      }
    );

    // Scenario run status
    this.getScenarioRunStatus();
    this.refreshRunStatus = setInterval(() => {
        this.getScenarioRunStatus();
    }, 5000);

    // Scenario validation status
    this.getScenarioValidationStatus();
    this.refreshValidationStatus = setInterval(() => {
        this.getScenarioValidationStatus();
    }, 5000);
  }

  ngOnDestroy() {
    // Clear status refresh intervals (stop refreshing) on component destroy
    clearInterval(this.refreshServerStatus);
    clearInterval(this.refreshRunStatus);
    clearInterval(this.refreshValidationStatus);
  }

  getServerStatus(): void {
    this.homeService.getServerStatus()
      .subscribe(
        status => this.serverStatus = status,
        error => {
          console.log('HTTP Error caught', error);
          this.serverStatus = 'down';
        }
      );
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

  getSolver1NameStatus(): void {
    this.settingsService.solver1NameStatusSubject
      .subscribe((settingsStatus: string) => {
        this.solver1NameStatus = settingsStatus;
      }
    );
  }

  determineSolver1Status(): void {
    this.settingsService.solver1NameStatusSubject.subscribe((nameStatus: string) => {
      this.solver1NameStatus = nameStatus;
      this.settingsService.solver1ExecutableStatusSubject.subscribe((executableStatus: string) => {
        this.solver1ExecutableStatus = executableStatus;
        if (this.solver1NameStatus === 'not set' || this.solver1ExecutableStatus === 'not set') {
          this.solver1Status = 'not set';
        } else {
          if (this.solver1NameStatus === 'restart required' || this.solver1ExecutableStatus === 'restart required') {
            this.solver1Status = 'restart required';
          } else {
            this.solver1Status = 'set';
          }
        }
      });
      }
    );
  }

  determineSolver2Status(): void {
    this.settingsService.solver2NameStatusSubject.subscribe((nameStatus: string) => {
      this.solver2NameStatus = nameStatus;
      this.settingsService.solver2ExecutableStatusSubject.subscribe((executableStatus: string) => {
        this.solver2ExecutableStatus = executableStatus;
        if (this.solver2NameStatus === 'not set' || this.solver2ExecutableStatus === 'not set') {
          this.solver2Status = 'not set';
        } else {
          if (this.solver2NameStatus === 'restart required' || this.solver2ExecutableStatus === 'restart required') {
            this.solver2Status = 'restart required';
          } else {
            this.solver2Status = 'set';
          }
        }
      });
      }
    );
  }

  determineSolver3Status(): void {
    this.settingsService.solver3NameStatusSubject.subscribe((nameStatus: string) => {
      this.solver3NameStatus = nameStatus;
      this.settingsService.solver3ExecutableStatusSubject.subscribe((executableStatus: string) => {
        this.solver3ExecutableStatus = executableStatus;
        if (this.solver3NameStatus === 'not set' || this.solver3ExecutableStatus === 'not set') {
          this.solver3Status = 'not set';
        } else {
          if (this.solver3NameStatus === 'restart required' || this.solver3ExecutableStatus === 'restart required') {
            this.solver3Status = 'restart required';
          } else {
            this.solver3Status = 'set';
          }
        }
      });
      }
    );
  }

  getScenarioRunStatus(): void {
    this.homeService.getRunStatus()
      .subscribe(
        status => this.scenarioRunStatus = status
      );
  }

  getScenarioValidationStatus(): void {
    this.homeService.getValidationStatus()
      .subscribe(
        status => this.scenarioValidationStatus = status
      );
  }
}
