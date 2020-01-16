import { Component, OnInit, NgZone } from '@angular/core';
const electron = ( window as any ).require('electron');

import { SettingsService } from './settings.service';


@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})


export class SettingsComponent implements OnInit {

  currentScenariosDirectory: string;
  currentGridPathDB: string;
  currentPythonDirectory: string;
  currentSolver1Executable: string;
  currentSolver2Name: string;
  currentSolver2Executable: string;
  currentSolver3Executable: string;

  requestedScenariosDirectory: string;
  requestedGridPathDB: string;
  requestedPythonDirectory: string;
  requestedSolver1Executable: string;
  requestedSolver2Name: string;
  requestedSolver2Executable: string;
  requestedSolver3Executable: string;

  // TODO: add solver status
  directoryStatus: string;
  databaseStatus: string;
  pythonStatus: string;

  solver2Status: string;

  constructor(
    private zone: NgZone,
    private settingsService: SettingsService
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

    this.currentSolver2Name = 'CPLEX';
  }

  getSettingsFromElectron(data) {
    // In order to get the view to update immediately upon selection,
    // we need to set the variables inside the Angular zone (we are outside
    // Angular when using 'electron')
    this.zone.run(() => {
      this.currentScenariosDirectory = data.currentScenariosDirectory.value;
      this.currentGridPathDB = data.currentGridPathDatabase.value;
      this.currentPythonDirectory = data.currentPythonEnvironment.value;
      this.currentSolver1Executable = data.currentSolver1Executable.value;
      this.currentSolver2Executable = data.currentSolver2Executable.value;
      this.currentSolver3Executable = data.currentSolver3Executable.value;
      this.requestedScenariosDirectory = data.requestedScenariosDirectory.value;
      this.requestedGridPathDB = data.requestedGridPathDatabase.value;
      this.requestedPythonDirectory = data.requestedPythonEnvironment.value;
      this.requestedSolver1Executable = data.requestedSolver1Executable.value;
      this.requestedSolver2Executable = data.requestedSolver2Executable.value;
      this.requestedSolver3Executable = data.requestedSolver3Executable.value;
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

  browsePythonEnvironment() {
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
        electron.ipcRenderer.send('setPythonEnvironmentSetting', folderPath[0]);
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

  browseSolver1Executable() {
    // Open an Electron dialog to select the file
    electron.remote.dialog.showOpenDialog(
      {title: 'Select the Solver1 executable',
        properties: ['openFile']},
      (filePath) => {
      // Don't do anything if no file selected
      if (filePath === undefined) {
          return;
      } else {
        // Send Electron the selected folder
        electron.ipcRenderer.send('setSolver1ExecutableSetting', filePath[0]);
        // Update the Angular component
        this.zone.run( () => {
          this.requestedSolver1Executable = filePath[0];
        // TODO: add status
        });
      }
    });
  }

  browseSolver2Executable() {
    // Open an Electron dialog to select the file
    electron.remote.dialog.showOpenDialog(
      {title: 'Select the Solver2 executable',
        properties: ['openFile']},
      (filePath) => {
      // Don't do anything if no file selected
      if (filePath === undefined) {
          return;
      } else {
        // Send Electron the selected folder
        electron.ipcRenderer.send('setSolver2ExecutableSetting', filePath[0]);
        // Update the Angular component
        this.zone.run( () => {
          this.requestedSolver2Executable = filePath[0];
        // TODO: add status
        });
      }
    });
  }

  browseSolver3Executable() {
    // Open an Electron dialog to select the file
    electron.remote.dialog.showOpenDialog(
      {title: 'Select the Solver3 executable',
        properties: ['openFile']},
      (filePath) => {
      // Don't do anything if no file selected
      if (filePath === undefined) {
          return;
      } else {
        // Send Electron the selected folder
        electron.ipcRenderer.send('setSolver3ExecutableSetting', filePath[0]);
        // Update the Angular component
        this.zone.run( () => {
          this.requestedSolver3Executable = filePath[0];
        // TODO: add status
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

  changeSolver2NameStatus() {
    console.log(this.requestedSolver2Name);
    this.solver2Status = 'name status';
  }
}
