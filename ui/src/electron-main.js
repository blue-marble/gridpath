'use strict';

const { app, BrowserWindow, ipcMain } = require('electron');
const storage = require('electron-json-storage');
const process = require('process');
const path = require('path');
const { spawn } = require('child_process');
const io = require('socket.io-client');

// Are we on Windows
const isWindows = process.platform === "win32";

// Keep a global reference of each window object; if we don't, the window will
// be closed automatically when the JavaScript object is garbage-collected.
let mainWindow;

// Keep a global reference to the server process
let serverChildProcess;
let tryToStartServer = true;

// // Main window //
function createMainWindow () {
    storage.keys(function(error, keys) {
        if (error) throw error;

        const requiredKeys = [
          'currentGridPathDatabase',
          'currentScenariosDirectory',
          'currentPythonBinary',
          'requestedGridPathDatabase',
          'requestedScenariosDirectory',
          'requestedPythonBinary',
        ];

        // TODO: should a solver be required; currently not (user can
        //  browse without running scenarios)
        const optionalKeys = [
          'currentCbcExecutable',
          'currentCPLEXExecutable',
          'currentGurobiExecutable',
          'requestedCbcExecutable',
          'requestedCPLEXExecutable',
          'requestedGurobiExecutable'
        ];

        requiredKeys.forEach(function(requiredKey) {
          if (keys.includes(requiredKey)) {
          } else {
              storage.set(
                requiredKey,
                { 'value': null },
                (error) => {if (error) throw error;}
            );
            // If any required keys are missing, don't start the server
            tryToStartServer = false
          }
        });

        optionalKeys.forEach(function(requiredKey) {
          if (keys.includes(requiredKey)) {
          } else {
              storage.set(
                requiredKey,
                { 'value': null },
                (error) => {if (error) throw error;}
            );
          }
        });

        if ( tryToStartServer ) {
          // Start the server
          startServer();
        }
      });

    // Create the browser window.
    mainWindow = new BrowserWindow({
      width: 1600,
      height: 1200,
      title: 'GridPath',
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

  // // Clear all storage; can be useful for debugging, but commenting this
  // // out by default
  // storage.clear(function(error) {
  //   if (error) throw error;
  //   console.log("Clearing storage")
  // });

  // TODO: this could still throw an error if we tried but failed to launch
  //  the server process; need to check that the server actually started
  if ( tryToStartServer ) {
    if (isWindows) {
      // Signals don't really work on Windows, so we can't use them to shut
      // down the server process: see
      // https://stackoverflow.com/questions/35772001/how-to-handle-the-signal-in-python-on-windows-machine
      // TL;DR: just look at the first comment
      // Can't kill process with ps.kill, as serverChildProcess.pid seems to
      // return an incorrect pid here. I don't think this is a closure issue,
      // as it appears the wrong pid is returned even right after the process
      // is spawned whereas on Mac the correct one is returned. Commenting out
      // the ps.kill code since it doesn't work on the wrong PID.
      // TODO: perhaps IPC process communciation will work?
      // For now server must be manually shut down by closing its console window

      // ps.kill(serverChildProcess.pid, ( err ) => {
      //   if (err) {
      //       throw new Error( err );
      //   }
      //   else {
      //       console.log( `Server process pid ${serverChildProcess.pid} has been killed.`);
      //   }
      // });

      // This does not kill the process, even if it's not detached.
      serverChildProcess.kill()
    }
    else {
      serverChildProcess.kill('SIGTERM')
    }
  }
});

app.on('activate', () => {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (mainWindow === null) {
        createMainWindow()
    }
});


// Settings

// Set the scenarios directory setting based on Angular input
// Get setting from renderer and store it
ipcMain.on('setScenariosDirectorySetting', (event, scenariosDir) => {
	console.log(`Scenarios folder set to ${scenariosDir}`);
	// TODO: do we need to keep in storage?
  // Set the scenarios directory path in Electron JSON storage
  storage.set(
      'requestedScenariosDirectory',
      { 'value': scenariosDir },
      (error) => {if (error) throw error;}
  );
});

// Set the GridPath database setting based on Angular input
// Get setting from renderer, store it, and send it to the server
ipcMain.on('setGridPathDatabaseSetting', (event, gpDB) => {
	console.log(`GridPath database set to ${gpDB}`);

	// TODO: do we need to keep in storage?
  // Set the database file path in Electron JSON storage
  storage.set(
      'requestedGridPathDatabase',
      { 'value': gpDB },
      (error) => {if (error) throw error;}
  );
});

// Set the Python binary setting based on Angular input
// Get setting from renderer and store it
ipcMain.on('setPythonBinarySetting', (event, pythonbinary) => {
	console.log(`Python binary directory set to ${pythonbinary}`);
	// TODO: do we need to keep in storage?
  // Set the Python binary path in Electron JSON storage
  storage.set(
      'requestedPythonBinary',
      { 'value': pythonbinary },
      (error) => {if (error) throw error;}
  );
});

// Set the Cbc executable setting based on Angular input
// Get setting from renderer, store it, and send it to the server
ipcMain.on('setCbcExecutableSetting', (event, msg) => {
	console.log(`Cbc executable set to ${msg}`);

	// TODO: do we need to keep in storage?
  // Set the database file path in Electron JSON storage
  storage.set(
      'requestedCbcExecutable',
      { 'value': msg },
      (error) => {if (error) throw error;}
  );
});

// Set the CPLEX executable setting based on Angular input
// Get setting from renderer, store it, and send it to the server
ipcMain.on('setCPLEXExecutableSetting', (event, msg) => {
	console.log(`CPLEX executable set to ${msg}`);

	// TODO: do we need to keep in storage?
  // Set the database file path in Electron JSON storage
  storage.set(
      'requestedCPLEXExecutable',
      { 'value': msg },
      (error) => {if (error) throw error;}
  );
});

// Set the Gurobi executable setting based on Angular input
// Get setting from renderer, store it, and send it to the server
ipcMain.on('setGurobiExecutableSetting', (event, msg) => {
	console.log(`Gurobi executable set to ${msg}`);

	// TODO: do we need to keep in storage?
  // Set the database file path in Electron JSON storage
  storage.set(
      'requestedGurobiExecutable',
      { 'value': msg },
      (error) => {if (error) throw error;}
  );
});

// Flask server
function startServer () {
  storage.getMany(
    [
      'currentGridPathDatabase',
      'currentScenariosDirectory',
      'currentPythonBinary',
      'currentCbcExecutable',
      'currentCPLEXExecutable',
      'currentGurobiExecutable',
      'requestedGridPathDatabase',
      'requestedScenariosDirectory',
      'requestedPythonBinary',
      'requestedCbcExecutable',
      'requestedCPLEXExecutable',
      'requestedGurobiExecutable'
    ],
    (error, data) => {
      if (error) throw error;

      // When we first start the server, we will set the 'current' settings
      // the last-requested settings; we will then use the 'current'
      // settings to start the server and send the appropriate environment
      // variables. New settings will therefore require a server restart to
      // take effect. The user will see both the 'current' and 'requested'
      // settings and will be informed of the need to restart.
      // TODO: refactor
      if (data['currentGridPathDatabase']['value']
        === data['requestedGridPathDatabase']['value']) {
        console.log("Current and requested GP databases match.")
      } else {
        storage.set(
          'currentGridPathDatabase',
          { 'value': data['requestedGridPathDatabase']['value'] },
          (error) => {if (error) throw error;}
        );
      }
      if (data['currentScenariosDirectory']['value']
        === data['requestedScenariosDirectory']['value']) {
        console.log("Current and requested GP directories match.");
      } else {
        storage.set(
          'currentScenariosDirectory',
          { 'value': data['requestedScenariosDirectory']['value'] },
          (error) => {if (error) throw error;}
        );
      }
      if (data['currentPythonBinary']['value']
        === data['requestedPythonBinary']['value']) {
        console.log("Current and requested Python directories match.")
      } else {
        storage.set(
          'currentPythonBinary',
          { 'value': data['requestedPythonBinary']['value'] },
          (error) => {
            if (error) throw error;
          }
        );
      }
      if (data['currentCbcExecutable']['value']
        === data['requestedCbcExecutable']['value']) {
        console.log("Current and requested Cbc executables match.")
      } else {
        storage.set(
          'currentCbcExecutable',
          { 'value': data['requestedCbcExecutable']['value'] },
          (error) => {
            if (error) throw error;
          }
        );
      }
      if (data['currentCPLEXExecutable']['value']
        === data['requestedCPLEXExecutable']['value']) {
        console.log("Current and requested CPLEX executables match.")
      } else {
        storage.set(
          'currentCPLEXExecutable',
          { 'value': data['requestedCPLEXExecutable']['value'] },
          (error) => {
            if (error) throw error;
          }
        );
      }
      if (data['currentGurobiExecutable']['value']
        === data['requestedGurobiExecutable']['value']) {
        console.log("Current and requested Gurobi executables match.")
      } else {
        storage.set(
          'currentGurobiExecutable',
          { 'value': data['requestedGurobiExecutable']['value'] },
          (error) => {
            if (error) throw error;
          }
        );
      }


      const dbPath = data['requestedGridPathDatabase']['value'];
      const scenariosDir = data['requestedScenariosDirectory']['value'];
      const pyDir = data['requestedPythonBinary']['value'];
      const cbcExec = data['requestedCbcExecutable']['value'];
      const cplexExec = data['requestedCPLEXExecutable']['value'];
      const gurobiExec = data['requestedGurobiExecutable']['value'];

      // The server entry point based on the Python directory
      const serverEntryPoint = path.join(
        pyDir, 'gridpath_run_server'
      );

      // Start the server (if Python path is set)
      if (pyDir == null) {
        // TODO: add handling of null here
        console.log("No Python path set.")
      }
      else {
        console.log("Starting server...");
        console.log("...database is ", dbPath);
        // Start Flask server
        // TODO: lots of issues with child_process on Windows.
        //  Enough to switch back to python-shell?
        if (isWindows) {
          // Using Anaconda, the Windows requirements for the server were:
          // commandToRun, shell: true, detached: true
          // With Anaconda, tried:
          // 1. commandToRun, shell: false, detached: false --> ENOENT error
          // 2. commandToRun, shell: true, detached: false -->
          // Python process closing code: 120
          // 3. commandToRun, shell: false, detached: true --> ENOENT error
          // 4. pythonPath, scriptPath, shell: true, detached: true -->
          // Python process closing code: 120
          // The 'Python process closing code: 120' error appears to be that
          // the Anaconda environment is not activated on opening the
          // shell, at least in the case of having a separate command
          // (Python binary path) and arguments (script path); I'm not
          // totally sure why using commandToRun with shell set to true but
          // not detached also results in that error
          // Also, windowsHide does not work:
          // https://github.com/nodejs/node/issues/21825

          // Using Python 3.7 distribution downloaded from python.org and
          // venv for managing environments, 'shell' must be 'true'
          // 1. commandToRun, shell: false, detached: false --> fail with
          // Python process closing code: -4058
          // 2. commandToRun, shell: true, detached: false -->
          // DO THIS LAST
          // 3. commandToRun, shell: false, detached: true --> fail with
          // Python process closing code: -4058
          // 4. pythonPath, scriptPath, shell: true, detached: true -->
          // Python process closing code: 120
          // While the process does not need to be detached with a pyenv
          // environment, I'm leaving it as detached, as I still don't know
          // how to kill the server process upon exit.

          // Process now spawned via the server entry point
          serverChildProcess = spawn(
           serverEntryPoint, [],
            {
              shell: true, detached: true, windowsHide: false,
              env: {
                GRIDPATH_DATABASE_PATH: dbPath,
                SCENARIOS_DIRECTORY: scenariosDir
              }
            },
            );
          // Why are we getting the wrong pid here? On Mac, it's the correct one...
          // How to kill the server process on app exit without knowing its
          // PID?
          console.log(serverChildProcess.pid);
        }
        else {
          serverChildProcess = spawn(
            serverEntryPoint, [],
            {
              stdio: 'inherit',
              env: {
                GRIDPATH_DATABASE_PATH: dbPath,
                SCENARIOS_DIRECTORY: scenariosDir,
                CBC_EXECUTABLE: cbcExec,
                CPLEX_EXECUTABLE: cplexExec,
                GUROBI_EXECUTABLE: gurobiExec
              }
            }
          );
        }
        // Some basic error-tracking
        serverChildProcess.on('error', function(error) {
          console.log("Server process failed to spawn");
        });
        serverChildProcess.on('close', function(exit_code) {
          console.log('Python process closing code: ' + exit_code.toString());
        });

        // Handle 'kill' signals; this is perhaps redundant since we're
        // also catching SIGINT on the server side
        serverChildProcess.on(
          'SIGINT',
          () => { serverChildProcess.exit() }
        ); // catch ctrl-c
        serverChildProcess.on(
          'SIGTERM',
          () => { serverChildProcess.exit() }
        ); // catch kill
      }
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
      ['currentScenariosDirectory', 'requestedScenariosDirectory',
        'currentGridPathDatabase', 'requestedGridPathDatabase',
        'currentPythonBinary', 'requestedPythonBinary',
        'currentCbcExecutable', 'requestedCbcExecutable',
        'currentCPLEXExecutable', 'requestedCPLEXExecutable',
        'currentGurobiExecutable', 'requestedGurobiExecutable'

      ],
      (error, data) => {
        if (error) throw error;
        event.sender.send('sendStoredSettings', data)
      }
    );
});
