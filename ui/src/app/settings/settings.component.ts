import { Component, OnInit, NgZone } from '@angular/core';
const electron = ( window as any ).require('electron');

import { SettingsService } from './settings.service';
import { ScenarioEditService } from '../scenario-detail/scenario-edit.service';
import { emptyStartingValues } from '../scenario-new/scenario-new.component';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})


export class SettingsComponent implements OnInit {

  currentScenariosDirectory: string;
  currentGridPathDB: string;
  currentPythonDirectory: string;

  requestedScenariosDirectory: string;
  requestedGridPathDB: string;
  requestedPythonDirectory: string;

  directoryStatus: string;
  databaseStatus: string;
  pythonStatus: string;

  constructor(
    private zone: NgZone,
    private settingsService: SettingsService,
    private scenarioEditService: ScenarioEditService
  ) { }



  ngOnInit() {
    console.log('Initializing settings...');

    this.directoryStatus = '';
    this.databaseStatus = '';
    this.pythonStatus = '';

    // Ask Electron for any current settings
    electron.ipcRenderer.send('requestStoredSettings');
    electron.ipcRenderer.on('sendStoredSettings',
      (event, data) => {
        this.getSettingsFromElectron(data);
      }
    );

    // TODO: this should happen on navigating away from scenario-new
    this.scenarioEditService.changeStartingScenario(emptyStartingValues);
  }

  getSettingsFromElectron(data) {
    // In order to get the view to update immediately upon selection,
    // we need to set the variables inside the Angular zone (we are outside
    // Angular when using 'electron')
    this.zone.run(() => {
      this.currentScenariosDirectory = data.currentScenariosDirectory.value;
      this.currentGridPathDB = data.currentGridPathDatabase.value;
      this.currentPythonDirectory = data.currentPythonBinary.value;
      this.requestedScenariosDirectory = data.requestedScenariosDirectory.value;
      this.requestedGridPathDB = data.requestedGridPathDatabase.value;
      this.requestedPythonDirectory = data.requestedPythonBinary.value;
    });
  }

  browseScenariosDirectory() {
    // Open an Electron dialog to select the folder
    electron.remote.dialog.showOpenDialog(
      {title: 'Select a the scenarios folder',
        properties: ['openDirectory']},
      (folderPath) => {
      // Don't do anything if no folder selected
      if (folderPath === undefined) {
          return;
      } else {
        // Send Electron the selected folder
        electron.ipcRenderer.send('setScenariosDirectorySetting', folderPath[0]);
        // Update the Angular component
        this.zone.run( () => {
          this.requestedScenariosDirectory = folderPath[0];
          // If the requested directory differs from the current directory, alert
          // the user by setting the setting status to 'restart required'
          console.log('Requested: ', this.requestedScenariosDirectory);
          console.log('Current: ', this.currentScenariosDirectory);
          if (this.requestedScenariosDirectory !== this.currentScenariosDirectory) {
            this.directoryStatus = 'restart required';
            this.changeDirectoryStatus();
          } else {
            this.directoryStatus = 'set';
            this.changeDirectoryStatus();
          }
        });
      }
    });
  }

  browseGPDatabase() {
    // Open an Electron dialog to select the file
    electron.remote.dialog.showOpenDialog(
      {title: 'Select a the GridPath database file',
        properties: ['openFile']},
      (dbFilePath) => {
      // Don't do anything if no folder selected
      if (dbFilePath === undefined) {
          return;
      } else {
        // Send Electron the selected folder
        electron.ipcRenderer.send('setGridPathDatabaseSetting', dbFilePath[0]);
        // Update the Angular component
        this.zone.run( () => {
          this.requestedGridPathDB = dbFilePath[0];
          // If the requested directory differs from the current directory, alert
          // the user by setting the setting status to 'restart required'
          if (this.requestedGridPathDB !== this.currentGridPathDB) {
            this.databaseStatus = 'restart required';
            this.changeDatabaseStatus();
          } else {
            this.databaseStatus = 'set';
            this.changeDatabaseStatus();
          }
        });
      }
    });
  }

  browsePythonBinary() {
    // Open an Electron dialog to select the folder
    electron.remote.dialog.showOpenDialog(
      {title: 'Select a the Python environment directory',
        properties: ['openDirectory']},
      (folderPath) => {
      // Don't do anything if no folder selected
      if (folderPath === undefined) {
          return;
      } else {
        // Send Electron the selected folder
        electron.ipcRenderer.send('setPythonBinarySetting', folderPath[0]);
        // Update the Angular component
        this.zone.run( () => {
          this.requestedPythonDirectory = folderPath[0];
          // If the requested directory differs from the current directory, alert
          // the user by setting the setting status to 'restart required'
          if (this.requestedPythonDirectory !== this.currentPythonDirectory) {
            this.pythonStatus = 'restart required';
            this.changePythonStatus();
          } else {
            this.pythonStatus = 'set';
            this.changePythonStatus();
          }
        });
      }
    });
  }

  changeDirectoryStatus() {
    this.settingsService.changeDirectoryStatus(this.directoryStatus);
  }

  changeDatabaseStatus() {
    this.settingsService.changeDatabaseStatus(this.databaseStatus);
  }

  changePythonStatus() {
    this.settingsService.changePythonStatus(this.pythonStatus);
  }
}
