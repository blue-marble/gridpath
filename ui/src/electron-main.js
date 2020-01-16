'use strict';

const { app, BrowserWindow, ipcMain } = require('electron');
const storage = require('electron-json-storage');
const process = require('process');
const path = require('path');
const { spawn, exec } = require('child_process');

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
          'currentPythonEnvironment',
          'requestedGridPathDatabase',
          'requestedScenariosDirectory',
          'requestedPythonEnvironment',
        ];

        // TODO: should a solver be required; currently not (user can
        //  browse without running scenarios)
        const optionalKeys = [
          'currentSolver1Name',
          'currentSolver1Executable',
          'currentSolver2Name',
          'currentSolver2Executable',
          'currentSolver3Name',
          'currentSolver3Executable',
          'requestedSolver1Name',
          'requestedSolver1Executable',
          'requestedSolver2Name',
          'requestedSolver2Executable',
          'requestedSolver3Name',
          'requestedSolver3Executable'
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

    // Warn user on closing the app
    mainWindow.on('close', function(e) {
      let choice = require('electron').dialog.showMessageBox(this,
          {
            type: 'question',
            buttons: ['Yes', 'No'],
            title: 'Confirm',
            message: 'Are you sure you want to quit? Any scenarios still' +
              ' running will be stopped.'
         });
         if(choice === 1) {
           e.preventDefault();  // prevent default behavior, which is to close
         }
      });

    // Emitted when the window is closed.
    mainWindow.on('closed', () => {
        // Dereference the window object, usually you would store windows
        // in an array if your app supports multi windows, this is the time
        // when you should delete the corresponding element.
        mainWindow = null
    });

    // Open external links in default browser
    // Source: https://stackoverflow.com/questions/32402327/how-can-i-force-external-links-from-browser-window-to-open-in-a-default-browser
    mainWindow.webContents.on(
      'new-window', function(e, url
      ) {
      e.preventDefault();
      require('electron').shell.openExternal(url);
    });
}


// // App behavior //
// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createMainWindow);

// Quit when all windows are closed.
app.on('window-all-closed', () => {
  app.quit()
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
      // Signals don't work on Windows, so we can't use them to shut
      // down the server process: see
      // https://stackoverflow.com/questions/35772001/how-to-handle-the-signal-in-python-on-windows-machine
      // Instead we'll use taskkill
      // Note: for this to work, we need to spawn the server child process via
      // the GridPath entry point script and with we need
      // shell: false, detached: true
      exec('taskkill /pid ' + serverChildProcess.pid + ' /T /F')

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

// Set the Python environment setting based on Angular input
// Get setting from renderer and store it
ipcMain.on('setPythonEnvironmentSetting', (event, pythonenvironment) => {
	console.log(`Python environment directory set to ${pythonenvironment}`);
	// TODO: do we need to keep in storage?
  // Set the Python environment path in Electron JSON storage
  storage.set(
      'requestedPythonEnvironment',
      { 'value': pythonenvironment },
      (error) => {if (error) throw error;}
  );
});

// Set the Solver1 executable setting based on Angular input
// Get setting from renderer, store it, and send it to the server
ipcMain.on('setSolver1ExecutableSetting', (event, msg) => {
	console.log(`Solver1 executable set to ${msg}`);

	// TODO: do we need to keep in storage?
  // Set the database file path in Electron JSON storage
  storage.set(
      'requestedSolver1Executable',
      { 'value': msg },
      (error) => {if (error) throw error;}
  );
});

// Set the Solver2 executable setting based on Angular input
// Get setting from renderer, store it, and send it to the server
ipcMain.on('setSolver2ExecutableSetting', (event, msg) => {
	console.log(`Solver2 executable set to ${msg}`);

	// TODO: do we need to keep in storage?
  // Set the database file path in Electron JSON storage
  storage.set(
      'requestedSolver2Executable',
      { 'value': msg },
      (error) => {if (error) throw error;}
  );
});

// Set the Solver3 executable setting based on Angular input
// Get setting from renderer, store it, and send it to the server
ipcMain.on('setSolver3ExecutableSetting', (event, msg) => {
	console.log(`Solver3 executable set to ${msg}`);

	// TODO: do we need to keep in storage?
  // Set the database file path in Electron JSON storage
  storage.set(
      'requestedSolver3Executable',
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
      'currentPythonEnvironment',
      'currentSolver1Name',
      'currentSolver1Executable',
      'currentSolver2Name',
      'currentSolver2Executable',
      'currentSolver3Name',
      'currentSolver3Executable',
      'requestedGridPathDatabase',
      'requestedScenariosDirectory',
      'requestedPythonEnvironment',
      'requestedSolver1Name',
      'requestedSolver1Executable',
      'requestedSolver2Name',
      'requestedSolver2Executable',
      'requestedSolver3Name',
      'requestedSolver3Executable'
    ],
    (error, data) => {
      if (error) throw error;

      console.log(data);

      // When we first start the server, we will set the 'current' settings
      // the last-requested settings; we will then use the 'current'
      // settings to start the server and send the appropriate environment
      // variables. New settings will therefore require a server restart to
      // take effect. The user will see both the 'current' and 'requested'
      // settings and will be informed of the need to restart.

      const settingPairs = [
        {'current': 'currentGridPathDatabase',
          'requested': 'requestedGridPathDatabase'},
        {'current': 'currentScenariosDirectory',
          'requested': 'requestedScenariosDirectory'},
        {'current': 'currentPythonEnvironment',
          'requested': 'requestedPythonEnvironment'},
        {'current': 'currentSolver1Executable',
          'requested': 'requestedSolver1Executable'},
        {'current': 'currentSolver2Executable',
          'requested': 'requestedSolver1Executable'},
        {'current': 'currentSolver3Executable',
          'requested': 'requestedSolver1Executable'},
      ];

      for (let pair of settingPairs) {
        check_and_set_setting(data, pair['current'], pair['requested']);
      }

      const dbPath = data['requestedGridPathDatabase']['value'];
      const scenariosDir = data['requestedScenariosDirectory']['value'];
      const pyDir = data['requestedPythonEnvironment']['value'];
      const solver1Exec = data['requestedSolver1Executable']['value'];
      const solver2Exec = data['requestedSolver2Executable']['value'];
      const solver3Exec = data['requestedSolver3Executable']['value'];

      // The server entry point based on the Python directory and the
      // executables directory ('Scripts' on Windows, 'bin' otherwise)
      const executablesDirectory = (isWindows === true) ? 'Scripts' : 'bin';
      const serverEntryPoint = path.join(
        pyDir, executablesDirectory, 'gridpath_run_server'
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
          // Server process spawned via the server entry point
          // OMG: https://github.com/nodejs/node/issues/21825
          // To kill the server process with taskkill when exiting
          // Electron, we need shell: false, detached: true (WTF)
          // windowsHide does not appear to be working, so the server
          // console window will be visible on Windows
          // NOTE: the PID returned is that of the CMD shell in
          // detached: false mode, but the Python process is not killed
          // NOTE: the PID returned is that of the gridpath_run_server
          // script when using shell=false, detached=false
          // NOTE: I don't know what the PID returned is when using
          // shell=false, detached=true, but it appears that way we can
          // kill the gridpath_run_server process tree on Electron exit
          // with taskkill
          serverChildProcess = spawn(
           serverEntryPoint, [],
            {
              shell: false, detached: true, windowsHide: true,
              env: {
                GRIDPATH_DATABASE_PATH: dbPath,
                SCENARIOS_DIRECTORY: scenariosDir,
                SOLVER1_EXECUTABLE: solver1Exec,
                SOLVER2_EXECUTABLE: solver2Exec,
                SOLVER3_EXECUTABLE: solver3Exec
              }
            },
            );
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
                SOLVER1_EXECUTABLE: solver1Exec,
                SOLVER2_EXECUTABLE: solver2Exec,
                SOLVER3_EXECUTABLE: solver3Exec
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

function check_and_set_setting(
  settings_data, setting_name_current, setting_name_requested
) {
  if (settings_data[setting_name_current]['value']
    === settings_data[setting_name_requested]['value']) {
  } else {
    storage.set(
      setting_name_current,
      { 'value': settings_data[setting_name_requested]['value'] },
      (error) => {
        if (error) throw error;
      }
    );
  }
}

// //// IPC Communication //// //

// Send stored settings to Angular if requested
ipcMain.on('requestStoredSettings', (event) => {
    storage.getMany(
      ['currentScenariosDirectory', 'requestedScenariosDirectory',
        'currentGridPathDatabase', 'requestedGridPathDatabase',
        'currentPythonEnvironment', 'requestedPythonEnvironment',
        'currentSolver1Name', 'requestedSolver1Name',
        'currentSolver1Executable', 'requestedSolver1Executable',
        'currentSolver2Name', 'requestedSolver2Name',
        'currentSolver2Executable', 'requestedSolver2Executable',
        'currentSolver3Name', 'requestedSolver3Name',
        'currentSolver3Executable', 'requestedSolver3Executable'

      ],
      (error, data) => {
        if (error) throw error;
        event.sender.send('sendStoredSettings', data)
      }
    );
});

ipcMain.on('requestStoredScenarioDirectoryForLog', (event) => {
    storage.getMany(
      ['currentScenariosDirectory'],
      (error, data) => {
        if (error) throw error;
        event.sender.send('sendStoredScenarioDirectoryForLog', data)
      }
    );
});
