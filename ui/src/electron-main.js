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

// // Main window //
function createMainWindow () {

    // Start the server
    startServer();

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
    ['gridPathDatabase', 'gridPathDirectory', 'pythonBinary'],
    (error, data) => {
      if (error) throw error;
      console.log(data);

      const dbPath = data['gridPathDatabase']['value'][0];
      const gpDir = data['gridPathDirectory']['value'][0];

      const pythonPath = path.join(
        data['pythonBinary']['value'][0],
        'python'
      );
      const scriptPath = path.join(
        data['gridPathDirectory']['value'][0],
        'ui', 'server',
        'run_server.py'
      );

      const serverEntryPoint = path.join(
        data['pythonBinary']['value'][0],
        'run_gridpath_server'
      );

      console.log(serverEntryPoint);

      const commandToRun = `${pythonPath} ${scriptPath}`;

      if (pythonPath == null || scriptPath == null) {
        console.log("No Python path and server script path set.")
      }
      else {
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
                GRIDPATH_DIRECTORY: gpDir
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
                GRIDPATH_DIRECTORY: gpDir
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
