import { Component, OnInit, NgZone } from '@angular/core';
const electron = ( window as any ).require('electron');

import { SettingsService } from './settings.service';


@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})


export class SettingsComponent implements OnInit {

  // Current settings
  currentScenariosDirectory: string;
  currentGridPathDB: string;
  currentPythonDirectory: string;
  currentSolver1Name: string;
  currentSolver1Executable: string;
  currentSolver2Name: string;
  currentSolver2Executable: string;
  currentSolver3Name: string;
  currentSolver3Executable: string;

  // Requested settings
  requestedScenariosDirectory: string;
  requestedGridPathDB: string;
  requestedPythonDirectory: string;
  requestedSolver1Name: string;
  requestedSolver1Executable: string;
  requestedSolver2Name: string;
  requestedSolver2Executable: string;
  requestedSolver3Name: string;
  requestedSolver3Executable: string;

  // Status
  directoryStatus: string;
  databaseStatus: string;
  pythonStatus: string;
  solver1NameStatus: string;
  solver1ExecutableStatus: string;
  solver2NameStatus: string;
  solver2ExecutableStatus: string;
  solver3NameStatus: string;
  solver3ExecutableStatus: string;

  constructor(
    private zone: NgZone,
    private settingsService: SettingsService
  ) { }



  ngOnInit() {
    console.log('Initializing settings...');

    // Ask Electron for any current settings
    electron.ipcRenderer.send('requestStoredSettings');
    electron.ipcRenderer.on('sendStoredSettings',
      (event, data) => {
        this.getSettingsFromElectron(data);

        this.directoryStatus = (
          this.requestedScenariosDirectory !== this.currentScenariosDirectory)
          ? 'restart required'
          :  ((this.currentScenariosDirectory === null) ? 'not set' : 'set');
        this.databaseStatus = (
          this.requestedGridPathDB !== this.currentGridPathDB)
          ? 'restart required'
          : (this.currentGridPathDB === null) ? 'not set' : 'set';
        this.pythonStatus = (
          this.requestedPythonDirectory !== this.currentPythonDirectory)
          ? 'restart required'
          : (this.currentPythonDirectory === null) ? 'not set' : 'set';
        this.solver1NameStatus = (
          this.requestedSolver1Name !== this.currentSolver1Name)
          ? 'restart required'
          : (this.currentSolver1Name === null) ? 'not set' : 'set';
        this.solver1ExecutableStatus = (
          this.requestedSolver1Executable !== this.currentSolver1Executable)
          ? 'restart required' :
          (this.currentSolver1Executable === null) ? 'not set' : 'set';
        this.solver2NameStatus = (
          this.requestedSolver2Name !== this.currentSolver2Name)
          ? 'restart required' :
          (this.currentSolver2Name === null) ? 'not set' : 'set';
        this.solver2ExecutableStatus = (
          this.requestedSolver2Executable !== this.currentSolver2Executable)
          ? 'restart required' :
          (this.currentSolver2Executable === null) ? 'not set' : 'set';
        this.solver3NameStatus = (
          this.requestedSolver3Name !== this.currentSolver3Name)
          ? 'restart required' :
          (this.currentSolver3Name === null) ? 'not set' : 'set';
        this.solver3ExecutableStatus = (
          this.requestedSolver3Executable !== this.currentSolver3Executable)
          ? 'restart required' :
          (this.currentSolver3Executable === null) ? 'not set' : 'set';
      }
    );
  }

  getSettingsFromElectron(data) {
    // In order to get the view to update immediately upon selection,
    // we need to set the variables inside the Angular zone (we are outside
    // Angular when using 'electron')
    this.zone.run(() => {
      this.currentScenariosDirectory = data.currentScenariosDirectory.value;
      this.currentGridPathDB = data.currentGridPathDatabase.value;
      this.currentPythonDirectory = data.currentPythonEnvironment.value;
      this.currentSolver1Name = data.currentSolver1Name.value;
      this.currentSolver1Executable = data.currentSolver1Executable.value;
      this.currentSolver2Name = data.currentSolver2Name.value;
      this.currentSolver2Executable = data.currentSolver2Executable.value;
      this.currentSolver3Name = data.currentSolver3Name.value;
      this.currentSolver3Executable = data.currentSolver3Executable.value;
      this.requestedScenariosDirectory = data.requestedScenariosDirectory.value;
      this.requestedGridPathDB = data.requestedGridPathDatabase.value;
      this.requestedPythonDirectory = data.requestedPythonEnvironment.value;
      this.requestedSolver1Name = data.requestedSolver1Name.value;
      this.requestedSolver1Executable = data.requestedSolver1Executable.value;
      this.requestedSolver2Name = data.requestedSolver2Name.value;
      this.requestedSolver2Executable = data.requestedSolver2Executable.value;
      this.requestedSolver3Name = data.requestedSolver3Name.value;
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
          this.changeDirectoryStatus();
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
          this.changeDatabaseStatus();
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
          this.changePythonStatus();
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
          this.changeSolver1ExecutableStatus();
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
          this.changeSolver2ExecutableStatus();
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
          this.changeSolver3ExecutableStatus();
        });
      }
    });
  }

  // Changes status functions
  // If the requested setting differs from the current setting, alert
  // the user by setting the setting status to 'restart required'

  changeDirectoryStatus() {
    this.directoryStatus = (this.requestedScenariosDirectory !== this.currentScenariosDirectory) ? 'restart required' : 'set';
    this.settingsService.changeDirectoryStatus(this.directoryStatus);
  }

  changeDatabaseStatus() {
    this.databaseStatus = (this.requestedGridPathDB !== this.currentGridPathDB) ? 'restart required' : 'set';
    this.settingsService.changeDatabaseStatus(this.databaseStatus);
  }

  changePythonStatus() {
    this.pythonStatus = (this.requestedPythonDirectory !== this.currentPythonDirectory) ? 'restart required' : 'set';
    this.settingsService.changePythonStatus(this.pythonStatus);
  }

  changeSolver1NameStatus() {
    this.solver1NameStatus = (this.requestedSolver1Name !== this.currentSolver1Name) ? 'restart required' : 'set';
    this.settingsService.changeSolver1NameStatus(this.solver1NameStatus);
  }

  changeSolver1ExecutableStatus() {
    this.solver1ExecutableStatus = (this.requestedSolver1Executable !== this.currentSolver1Executable) ? 'restart required' : 'set';
    this.settingsService.changeSolver1ExecutableStatus(this.solver1ExecutableStatus);
  }

  changeSolver2NameStatus() {
    this.solver2NameStatus = (this.requestedSolver2Name !== this.currentSolver2Name) ? 'restart required' : 'set';
    this.settingsService.changeSolver2NameStatus(this.solver2NameStatus);
  }

  changeSolver2ExecutableStatus() {
    this.solver2ExecutableStatus = (this.requestedSolver2Executable !== this.currentSolver2Executable) ? 'restart required' : 'set';
    this.settingsService.changeSolver2ExecutableStatus(this.solver2ExecutableStatus);
  }

  changeSolver3NameStatus() {
    this.solver3NameStatus = (this.requestedSolver3Name !== this.currentSolver3Name) ? 'restart required' : 'set';
    this.settingsService.changeSolver3NameStatus(this.solver3NameStatus);
  }

  changeSolver3ExecutableStatus() {
    this.solver3ExecutableStatus = (this.requestedSolver3Executable !== this.currentSolver3Executable) ? 'restart required' : 'set';
    this.settingsService.changeSolver3ExecutableStatus(this.solver3ExecutableStatus);
  }
}
