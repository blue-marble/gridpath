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
  gridPathFolder: Array<string>;
  gridPathDB: Array<string>;
  pythonBinary: Array<string>;

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
      // Handle situation if no value is set
      if (data.gridPathDirectory.value === null) {
        this.gridPathFolder = null;
      } else {
        this.gridPathFolder =
          data.gridPathDirectory.value[0];
      }

      if (data.gridPathDatabase.value === null) {
        this.gridPathDB = null;
      } else {
        this.gridPathDB =
          data.gridPathDatabase.value[0];
      }

      if (data.pythonBinary.value === null) {
        this.pythonBinary = null;
      } else {
        this.pythonBinary =
          data.pythonBinary.value[0];
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
          this.gridPathFolder = folderPath;
        });
      }
      console.log(`GridPath folder set to ${this.gridPathFolder}`);
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
        electron.ipcRenderer.send('setGridPathDatabaseSetting', dbFilePath);
        // Update the Angular component
        this.zone.run( () => {
          this.gridPathDB = dbFilePath;
        });
      }
      console.log(`GridPath database set to ${this.gridPathDB}`);
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
        electron.ipcRenderer.send('setPythonBinarySetting', folderPath);
        // Update the Angular component
        this.zone.run( () => {
          this.pythonBinary = folderPath;
        });
      }
      console.log(`Python binary set to ${this.pythonBinary}`);
    });
  }
}
