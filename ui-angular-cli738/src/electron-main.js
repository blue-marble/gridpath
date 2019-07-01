'use strict';

const { app, BrowserWindow, ipcMain } = require('electron');
const storage = require('electron-json-storage');

// https://github.com/extrabacon/python-shell/issues/148#issuecomment-419120209
let {PythonShell} = require('python-shell');

// // Socket IO
const io = require('socket.io-client');

// Keep a global reference of each window object; if we don't, the window will
// be closed automatically when the JavaScript object is garbage-collected.
let mainWindow;


// // Main window //
function createMainWindow () {

    // Start the server
    startServer();
    // Update server globals with initial Electron values
    updateServerDatabaseGlobal();

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
	console.log(`Python binary set to ${pythonbinary}`);
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

  let options = {
      pythonPath: '/Users/ana/.pyenv/versions/gridpath-w-flask/bin/python',
      scriptPath: '/Users/ana/dev/gridpath-ui-dev/'
  };

  // Start Flask server
  PythonShell.run(
      'flask_local_server.py',
       options,
      function (err) {
          if (err) throw err;
          console.log('error');
      }
  );
}

// Connect to server and update the database global
function updateServerDatabaseGlobal () {
  console.log("Updating server database global");
  // Update global variables
  storage.get(
    'gridPathDatabase',
    (error, data) => {
        if (error) throw error;
        console.log('Database data', data);
        const socket = connectToServer();
        socket.emit('set_database_path', data.value[0]);
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

function checkServerStatus () {
  const socket = io.connect('http://localhost:8080/');
  socket.on('connect', function() {
      return socket.connected()
  });
}


// Send stored settings to Angular if requested

// function sendStoredSettingstoAngular () {
//   storage.getMany(
//     ['gridPathDirectory', 'gridPathDatabase', 'pythonBinary'],
//     (error, data) => {
//       if (error) throw error;
//       console.log("Sending stored settings to Angular");
//       console.log(data);
//       ipcMain.on('requestStoredSettings', (event) => {
//         event.sender.send('sendStoredSettings', data)
//       });
//     }
//   );
// }

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
