'use strict';

// This is the boilerplate Electron back-end


const { app, BrowserWindow, ipcMain } = require('electron');


// Keep a global reference of each window object; if we don't, the window will
// be closed automatically when the JavaScript object is garbage-collected.
let mainWindow;
let scenarioDetailWindow;

// // Main window //
function createMainWindow () {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 800, height: 600, title: 'GridPath UI Sandbox', show: false
  });

  // and load the index.html of the app.
  mainWindow.loadFile('./src/index.html');

  // // Open the DevTools.
  // mainWindow.webContents.openDevTools();

  mainWindow.once('ready-to-show', () => {
     mainWindow.show()
 });

  // Emitted when the window is closed.
  mainWindow.on('closed', () => {
    // Dereference the window object, usually you would store windows
    // in an array if your app supports multi windows, this is the time
    // when you should delete the corresponding element.
    mainWindow = null
  });

}


// // App behavior //
// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createMainWindow);

// Quit when all windows are closed.
app.on('window-all-closed', () => {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit()
  }
});

app.on('activate', () => {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (mainWindow === null) {
    createMainWindow()
  }
});

// // Other views/windows // //

// Scenario Detail window //

// The Scenario Detail window opens when a signal from the main window is sent
// (i.e. a scenario button is clicked)
ipcMain.on(
    'User-Requests-Scenario-Detail',
    function(event, user_requested_scenario_name) {
    console.log("Received user request for scenario " + user_requested_scenario_name);
    // We need to listen for an explict request from the Scenario Detail window
    ipcMain.on(
        'Scenario-Detail-Window-Requests-Scenario-Name',
        function(event) {
        console.log("Received request from scenario detail window");
        console.log(
            "About the send scenario name " + user_requested_scenario_name
        );
        // When request received, send the message
        event.sender.send(
            "Main-Relays-Scenario-Name", user_requested_scenario_name)
    });
    scenarioDetailWindow = new BrowserWindow({
        width: 600, height: 600, title: 'Scenario Detail', show: false});

    // Open the DevTools.
    scenarioDetailWindow.webContents.openDevTools();

    // and load the index.html of the app.
    // scenarioDetailWindow.webContents.send(
    //     'relay-scenario-name', "here's a scenario");
    scenarioDetailWindow.loadFile('./src/scenario_detail.html');
    scenarioDetailWindow.once('ready-to-show', () => {scenarioDetailWindow.show()
    });
    }
);


// New scenario view //
ipcMain.on(
    'User-Requests-New-Scenario',
    function(event, user_requested_scenario_name) {
        console.log("Received user request for new scenario ");
        mainWindow.loadFile('./src/scenario_new.html');
});

// Go back to index view if google requests it; maybe this can be reused
ipcMain.on(
    'Scenario-New-Window-Requests-Back-to-Scenarios',
    function(event, user_requested_scenario_name) {
        console.log("Received user request for go back to scenario list ");
        mainWindow.loadFile('./src/index.html');
});

// Go back to index view if google requests it; maybe this can be reused
ipcMain.on(
    'Save-New-Scenario',
    function(event, params) {
        console.log("Received save new scenario request ");
        console.log(params);
});

