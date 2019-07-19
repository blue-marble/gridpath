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
  // Set the GridPath folder and database settings: we do this by browsing
  // for the folder/database-file via Electron's 'dialog' functionality. In
  // order to get the view to update immediately upon selection, we need to
  // set gridPathFolder/gridPathDB/pythonBinary inside the Angular zone. We are
  // outside Angular when using 'electron', so we need to explicitly run
  // inside the Angular zone (using NgZone), but this can only happen in the
  // 'constructor' method. Therefore, the dialog functionality is included
  // in the 'constructor' below; here we tell the Electron main that the
  // user is requesting to select the folder path; the 'constructor' method
  // includes listeners for the main's response and, on detecting the
  // response, 1) runs the Electron dialog and 2) sets the selected path
  // inside the Angular zone.
  gridPathFolder: Array<string>;
  browseGPFolder(event) {
    console.log("Request to set GP folder setting...");
    electron.ipcRenderer.send('onClickGridPathFolderSetting');
  }

  gridPathDB: Array<string>;
  browseGPDatabase(event, zone) {
    console.log("Request to set GP database setting...");
    electron.ipcRenderer.send('onClickGridPathDatabaseSetting');
  }

  pythonBinary: Array<string>;
  browsePythonBinary(event, zone) {
    console.log("Request to set Python binary setting...");
    electron.ipcRenderer.send('onClickPythonBinarySetting');
  }

  // The current settings from the Electron main
  currentGridPathFolderSetting: Array<string>;
  currentGridPathDatabaseSetting: Array<string>;
  currentPythonBinarySetting: Array<string>;


  constructor(
    private zone: NgZone,
    private scenarioEditService: ScenarioEditService
  ) {
    console.log("Constructing the settings...");

    // Get current settings from Electron
    this.requestStoredSettings();
    electron.ipcRenderer.on('sendStoredSettings',
        (event, data) => {
          console.log('Got stored settings from Electron main');
          console.log(data);

          zone.run( () => {

            // Handle situation if no value is set
            if (data['gridPathDirectory']['value'] === null) {
              this.currentGridPathFolderSetting = null
            }
            else {
              this.currentGridPathFolderSetting =
                data['gridPathDirectory']['value'][0];
            }

            if (data['gridPathDatabase']['value'] === null) {
              this.currentGridPathDatabaseSetting = null
            }
            else {
              this.currentGridPathDatabaseSetting =
                data['gridPathDatabase']['value'][0];
            }

            if (data['pythonBinary']['value'] === null) {
              this.currentPythonBinarySetting = null
            }
            else {
              this.currentPythonBinarySetting =
                data['pythonBinary']['value'][0];
            }

          })
        }
    );

    // TODO: treatment is very similar for different settings, so could be
    //  re-factored

    // When a setting button is clicked by sending, a message is first sent
    // to the Electron main, which then communicates back to the renderer
    // on the channels included in the 'constructor' method, so that we can
    // set the paths inside the Angular zone (which can happen in
    // the 'constructor' method only)

    // Set GridPath folder setting via Electron dialog
    electron.ipcRenderer.on('onClickGridPathFolderSettingAngular', (event) => {
			electron.remote.dialog.showOpenDialog(
      {title: 'Select a the GridPath folder', properties: ['openDirectory']},
      (folderPath) => {
        if (folderPath === undefined){
            console.log("No folder selected");
            return;
        }
        // We must run this inside the Angular zone to get Angular to
        // detect the change and update the view immediately
        else {
          // Send Electron the new value
          console.log("Sending GridPath folder setting to Electron");
          electron.ipcRenderer.send(
            "setGridPathFolderSetting",
            folderPath
          );

          // Ask Electron for the value it stored (double-check value is
          // the same as what we just selected)
          this.requestStoredSettings();
          // Electron responds on this channel
          electron.ipcRenderer.on('sendStoredSettings',
            (event, data) => {
              console.log('Got stored settings from Electron main');
              console.log(data);

              // Set the new value for currentGridPathFolderSetting in Angular
              zone.run( () => {
                if (data['gridPathDirectory']['value'] === null) {
                  this.currentGridPathFolderSetting = null
                }
                else {
                  this.currentGridPathFolderSetting =
                    data['gridPathDirectory']['value'][0];
                }
                console.log(
                  `Setting current GP folder to ${this.currentGridPathFolderSetting} in Angular`
                );

                // Also update the selection box with what we just selected
                // This provides a visual confirmation that Angular and
                // Electron are seeing the same value
                // TODO: write a check that the two values are the same
                this.gridPathFolder = folderPath;
              })
            }
          );
        }
        console.log(`GridPath folder set to ${this.gridPathFolder}`);
      });
		});

    // Set GridPath database setting via Electron dialog
    electron.ipcRenderer.on('onClickGridPathDatabaseSettingAngular',
        (event) => {
        electron.remote.dialog.showOpenDialog(
          {title: 'Select a the GridPath database file',
          properties: ['openFile']},
          (dbFilePath) => {
            if (dbFilePath === undefined){
                console.log("No file selected");
                return;
            }
            // We must run this inside the Angular zone to get Angular to
            // detect the change and update the view immediately
            else {
              // Send Electron the new value
              console.log("Sending GridPath database setting to Electron");
              electron.ipcRenderer.send(
                "setGridPathDatabaseSetting",
                dbFilePath
              );

              // Ask Electron for the value it stored (double-check value is
              // the same as what we just selected)
              this.requestStoredSettings();
              // Electron responds on this channel
              electron.ipcRenderer.on('sendStoredSettings',
                (event, data) => {
                  console.log('Got stored settings from Electron main');
                  console.log(data);

                  // Set the new value for currentGridPathDatabaseSetting in Angular
                  zone.run( () => {
                    if (data['gridPathDatabase']['value'] === null) {
                      this.currentGridPathDatabaseSetting = null
                    }
                    else {
                      this.currentGridPathDatabaseSetting =
                        data['gridPathDatabase']['value'][0];
                    }
                    console.log(
                      `Setting current GP database to ${this.currentGridPathDatabaseSetting} in Angular`
                    );

                    // Also update the selection box with what we just selected
                    // This provides a visual confirmation that Angular and
                    // Electron are seeing the same value
                    // TODO: write a check that the two values are the same
                    this.gridPathDB = dbFilePath;
                  })
                }
              );
            }
            console.log(`GridPath database set to ${this.gridPathDB[0]}`);
          }
        );
      }
    );


    // Set Python binary directory setting via Electron dialog
    electron.ipcRenderer.on('onClickPythonBinarySettingAngular',
        (event) => {
        electron.remote.dialog.showOpenDialog(
          {title: 'Select a the Python binary file',
          properties: ['openDirectory']},
          (pythonBinaryPath) => {
            if (pythonBinaryPath === undefined){
                console.log("No file selected");
                return;
            }
            // We must run this inside the Angular zone to get Angular to
            // detect the change and update the view immediately
            else {
              // Send Electron the new value
              console.log("Sending Python binary directory setting to" +
                " Electron");
              electron.ipcRenderer.send(
                "setPythonBinarySetting", pythonBinaryPath
              );

              // Ask Electron for the value it stored (double-check value is
              // the same as what we just selected)
              this.requestStoredSettings();
              // Electron responds on this channel
              electron.ipcRenderer.on('sendStoredSettings',
                (event, data) => {
                  console.log('Got stored settings from Electron main');
                  console.log(data);

                  // Set the new value for currentPythonBinarySetting in Angular
                  zone.run( () => {
                    if (data['pythonBinary']['value'] === null) {
                      this.currentPythonBinarySetting = null
                    }
                    else {
                      this.currentPythonBinarySetting =
                        data['pythonBinary']['value'][0];
                    }
                    console.log(
                      `Setting current Python binary directory to ${this.currentPythonBinarySetting} in Angular`
                    );

                    // Also update the selection box with what we just selected
                    // This provides a visual confirmation that Angular and
                    // Electron are seeing the same value
                    // TODO: write a check that the two values are the same
                    this.pythonBinary = pythonBinaryPath;
                  })
                }
              );
            }
            console.log(`Python binary set to ${this.pythonBinary[0]}`);
          }
        );
      }
    );
  }



  ngOnInit() {
    console.log('Initializing settings...');

    // TODO: this should happen on navigating away from scenario-new
    this.scenarioEditService.changeStartingScenario(emptyStartingValues);
  }

  requestStoredSettings() {
    console.log('Requesting stored settings from Electron main...');
    electron.ipcRenderer.send('requestStoredSettings')
  }
}
