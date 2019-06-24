import { Component, OnInit, NgZone } from '@angular/core';
const electron = (<any>window).require('electron');

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})


export class SettingsComponent implements OnInit {

  constructor(private zone: NgZone) {
    console.log("Constructing the settings...");

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
          zone.run(() => this.gridPathFolder = folderPath);
        }
        console.log(`GridPath folder set to ${this.gridPathFolder[0]}`);
        // Tell Electron about the setting, so that it can store it and
        // tell the server
        electron.ipcRenderer.send(
          "setGridPathFolderSetting",
          this.gridPathFolder
        )
      });
		});

    // Set GridPath database setting via Electron dialog
    electron.ipcRenderer.on('onClickGridPathDatabaseSettingAngular', (event) => {
			electron.remote.dialog.showOpenDialog(
      {title: 'Select a the GridPath database file', properties: ['openFile']},
      (dbFilePath) => {
        if (dbFilePath === undefined){
            console.log("No file selected");
            return;
        }
        // We must run this inside the Angular zone to get Angular to
        // detect the change and update the view immediately
        else {
          zone.run( () => this.gridPathDB = dbFilePath);
        }
        console.log(`GridPath database set to ${this.gridPathDB[0]}`);
        // Tell Electron about the setting, so that it can store it and
        // tell the server
        electron.ipcRenderer.send(
          "setGridPathDatabaseSetting",
          this.gridPathDB
        );
      });
		});
  }

  ngOnInit() {
    console.log("Initializing settings...")
  }

  // Set the GridPath folder and database settings: we do this by browsing
  // for the folder/database-file via Electron's 'dialog' functionality. In
  // order to get the view to update immediately upon selection, we need to
  // set gridPathFolder/gridPathDB inside the Angular zone. We are outside
  // Angular when using 'electron', so we need to explicitly run inside the
  // Angular zone (using NgZone), but this can only happen in the
  // 'constructor' method. Therefore, the dialog functionality is included
  // in the 'constructor' above; here we tell the Electron main that the
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
}
