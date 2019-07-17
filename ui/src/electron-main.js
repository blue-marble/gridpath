'use strict';

const { app, BrowserWindow, ipcMain } = require('electron');
const storage = require('electron-json-storage');

const { spawn } = require('child_process');

// // Socket IO
const io = require('socket.io-client');

// Keep a global reference of each window object; if we don't, the window will
// be closed automatically when the JavaScript object is garbage-collected.
let mainWindow;

// Keep a global reference to the server process
let serverChildProcess;


// // Main window //
function createMainWindow () {

    // Start the server
    startServer();

    // Create the browser window.
    mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      title: 'GridPath UI Sandbox',
      show: false,
      webPreferences: {nodeIntegration: true, contextIsolation: false}  // to
      // get 'require' to work in
      // both main and renderer processes in Electron 5+
    });


    // and load the index.html of the app.
    mainWindow.loadFile('./ng-build/index.html');

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

app.on('before-quit', () => {
  serverChildProcess.kill('SIGINT')
});

app.on('activate', () => {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (mainWindow === null) {
        createMainWindow()
    }
});


// Settings

// Set the GridPath folder setting based on Angular input
ipcMain.on('onClickGridPathFolderSetting', (event) => {
  console.log(`GridPath folder settings button clicked`);
  // Tell renderer to proceed (message is sent to listeners in 'constructor'
  // method, so that we can run inside the Angular zone for immediate view
  // update)
  event.sender.send('onClickGridPathFolderSettingAngular')
});
// Get setting from renderer and store it
ipcMain.on('setGridPathFolderSetting', (event, gpfolder) => {
	console.log(`GridPath folder set to ${gpfolder}`);
	// TODO: do we need to keep in storage?
  // Set the GridPath directory path in Electron JSON storage
  storage.set(
      'gridPathDirectory',
      { 'value': gpfolder },
      (error) => {if (error) throw error;}
  );
  const socket = connectToServer();
  socket.emit('set_gridpath_directory', gpfolder[0])
});

// Set the GridPath database setting based on Angular input
ipcMain.on('onClickGridPathDatabaseSetting', (event) => {
  console.log(`GridPath database settings button clicked`);
  // Tell renderer to proceed (message is sent to listeners in 'constructor'
  // method, so that we can run inside the Angular zone for immediate view
  // update)
  event.sender.send('onClickGridPathDatabaseSettingAngular')
});
// Get setting from renderer, store it, and send it to the server
ipcMain.on('setGridPathDatabaseSetting', (event, gpDB) => {
	console.log(`GridPath database set to ${gpDB}`);

	// TODO: do we need to keep in storage?
  // Set the database file path in Electron JSON storage
  storage.set(
      'gridPathDatabase',
      { 'value': gpDB },
      (error) => {if (error) throw error;}
  );

  // TODO: set this from Electron storage for consistency
  const socket = connectToServer();
  socket.emit('set_database_path', gpDB[0]);
});

// Set the Python binary setting based on Angular input
ipcMain.on('onClickPythonBinarySetting', (event) => {
  console.log(`Python binary settings button clicked`);
  // Tell renderer to proceed (message is sent to listeners in 'constructor'
  // method, so that we can run inside the Angular zone for immediate view
  // update)
  event.sender.send('onClickPythonBinarySettingAngular')
});
// Get setting from renderer and store it
ipcMain.on('setPythonBinarySetting', (event, pythonbinary) => {
	console.log(`Python binary directory set to ${pythonbinary}`);
	// TODO: do we need to keep in storage?
  // Set the Python binary path in Electron JSON storage
  storage.set(
      'pythonBinary',
      { 'value': pythonbinary },
      (error) => {if (error) throw error;}
  );
});


// Flask server
function startServer () {
  console.log("Starting server...");

  storage.getMany(
    ['gridPathDirectory', 'pythonBinary'],
    (error, data) => {
      if (error) throw error;
      console.log(data);

      let options = {
        pythonPath: `${data['pythonBinary']['value'][0]}/python`,
        scriptPath: data['gridPathDirectory']['value'][0],
      };

      if (options.pythonPath == null || options.scriptPath == null) {
        console.log("No Python path and server script path set.")
      }
      else {
        // Start Flask server
        serverChildProcess = spawn(
           options.pythonPath,
          [`${options.scriptPath}/flask_local_server.py`],
          {stdio: 'inherit'}
        );
        serverChildProcess.on('error', function(error) {
          console.log("Server process failed to spawn");
          console.log(error)
        });
        serverChildProcess.on('close', function(exit_code) {
            console.log('Python process closing code: ' + exit_code.toString());
        });

      }
    }
  );

  // Update the server database and GP directory globals
  updateServerDatabaseGlobal ();
  updateServerGPDirectoryGlobal ();
}

// Connect to server and update the database global
function updateServerDatabaseGlobal () {
  console.log("Updating server database global");
  // Update global variables
  storage.get(
    'gridPathDatabase',
    (error, data) => {
        if (error) throw error;
        const socket = connectToServer();
        socket.emit('set_database_path', data.value[0]);
    }
  );
}

function updateServerGPDirectoryGlobal () {
  console.log("Updating server GridPath directory global");
  // Update global variables
  storage.get(
    'gridPathDirectory',
    (error, data) => {
        if (error) throw error;
        const socket = connectToServer();
        socket.emit('set_gridpath_directory', data.value[0]);
    }
  );
}



function connectToServer () {
  const socket = io.connect('http://localhost:8080/');
  socket.on('connect', function() {
      console.log(`Connection established: ${socket.connected}`);
  });
  return socket
}

// Send stored settings to Angular if requested
ipcMain.on('requestStoredSettings', (event) => {
    storage.getMany(
      ['gridPathDirectory', 'gridPathDatabase', 'pythonBinary'],
      (error, data) => {
        if (error) throw error;
        console.log("Sending stored settings to Angular");
        console.log(data);
        event.sender.send('sendStoredSettings', data)
      }
    );
});

// Tell server to run scenario if signal received from Angular
ipcMain.on(
    'runScenario',
    (event, userRequestedScenarioName) => {
        console.log(`Received user request to run ${userRequestedScenarioName}`);

        // Send message to server to run scenario
        // Connect to server
        const socket = connectToServer();
        // Tell the server to start a scenario process
        socket.emit(
            'launch_scenario_process',
            {scenario: userRequestedScenarioName}
        );
        // Keep track of process ID for this scenario run
        socket.on('scenario_already_running', function (msg) {
            console.log('in scenario_already_running');
            console.log (msg);
        });
    }
);
