import { Component, OnInit, NgZone } from '@angular/core';
const electron = ( window as any ).require('electron');

import { ScenarioEditService } from '../scenario-detail/scenario-edit.service';
import { emptyStartingValues } from '../scenario-new/scenario-new.component';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})


export class SettingsComponent implements OnInit {

  currentGridPathDirectory: string;
  currentGridPathDB: string;
  currentPythonDirectory: string;

  requestedGridPathDirectory: string;
  requestedGridPathDB: string;
  requestedPythonDirectory: string;

  constructor(
    private zone: NgZone,
    private scenarioEditService: ScenarioEditService
  ) { }



  ngOnInit() {
    console.log('Initializing settings...');
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
    // we need to set gridPathFolder/gridPathDB/pythonBinary inside
    // the Angular zone (we are outside Angular when using 'electron')
    this.zone.run(() => {
      if (data.currentGridPathDirectory.value === null) {
        this.currentGridPathDirectory = null;
      } else {
        this.currentGridPathDirectory =
          data.currentGridPathDirectory.value;
      }

      if (data.currentGridPathDatabase.value === null) {
        this.currentGridPathDB = null;
      } else {
        this.currentGridPathDB =
          data.currentGridPathDatabase.value;
      }

      if (data.currentPythonBinary.value === null) {
        this.currentPythonDirectory = null;
      } else {
        this.currentPythonDirectory =
          data.currentPythonBinary.value;
      }

      if (data.requestedGridPathDirectory.value === null) {
        this.requestedGridPathDirectory = null;
      } else {
        this.requestedGridPathDirectory =
          data.requestedGridPathDirectory.value;
      }

      if (data.requestedGridPathDatabase.value === null) {
        this.requestedGridPathDB = null;
      } else {
        this.requestedGridPathDB =
          data.requestedGridPathDatabase.value;
      }

      if (data.requestedPythonBinary.value === null) {
        this.requestedPythonDirectory = null;
      } else {
        this.requestedPythonDirectory =
          data.requestedPythonBinary.value;
      }
    });
  }

  browseGPFolder() {
    // Open an Electron dialog to select the folder
    electron.remote.dialog.showOpenDialog(
      {title: 'Select a the GridPath folder',
        properties: ['openDirectory']},
      (folderPath) => {
      // Don't do anything if no folder selected
      if (folderPath === undefined) {
          return;
      } else {
        // Send Electron the selected folder
        electron.ipcRenderer.send('setGridPathFolderSetting', folderPath);
        // Update the Angular component
        this.zone.run( () => {
          this.requestedGridPathDirectory = folderPath[0];
        });
      }
      console.log(`GridPath folder set to ${this.requestedGridPathDirectory}`);
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
        });
      }
      console.log(`GridPath database set to ${this.requestedGridPathDB}`);
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
        });
      }
      console.log(`Python binary set to ${this.requestedPythonDirectory}`);
    });
  }
}
