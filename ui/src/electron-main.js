'use strict';


const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const storage = require('electron-json-storage');


// Keep a global reference of each window object; if we don't, the window will
// be closed automatically when the JavaScript object is garbage-collected.
let mainWindow;

// // Main window //
function createMainWindow () {
    // Create the browser window.
    mainWindow = new BrowserWindow({
        width: 1200, height: 800, title: 'GridPath UI Sandbox', show: false
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
    (event, userRequestedScenarioName) => {
        console.log(
            `Received request for ${userRequestedScenarioName} scenario detail`
        );
        // We need to listen for an explict request for the scenario name
        // from the scenario detail renderer (I couldn't figure out another
        // way)
        ipcMain.on(
            'Scenario-Detail-Window-Requests-Scenario-Name',
            (event) => {
                // When request received, send the scenario name
                event.sender.send(
                    'Main-Relays-Scenario-Name',
                    userRequestedScenarioName
                )
            }
        );

        // // TODO: should the scenario detail view be a separate window
        // scenarioDetailWindow = new BrowserWindow({
        //     width: 600, height: 600, title: 'Scenario Detail', show: false
        // });

        // // Open the DevTools.
        // scenarioDetailWindow.webContents.openDevTools();

        mainWindow.loadFile('./src/scenario_detail.html');
        // mainWindow.once('ready-to-show', () => {
        //     mainWindow.show()
        // });
    }
);


// Run a scenario //
// Spawn a Python process to run a scenario when the 'Run Scenario' button
// in the scenario detail window is clicked

// We need to find the Python script when we are in both
// a production environment and a development environment
// We do that by looking up app.isPackaged (this is a renderer process, so we
// need to do it via remote)
// In development, the script is in the py directory under root
// In production, we package the script in the 'py' directory under the app's
// Contents/Resources by including extraResources under "build" in package.json
const baseDirectory = () => {
    if (app.isPackaged) {
        return path.join(process.resourcesPath)
    } else {
        return path.join(__dirname, "..")
    }
};

// TODO: how to get the GP python code? Should we have the user specify
//  where it is? We're not packaging up Python for now.
// const PyScriptPath = path.join(baseDirectory(), '../run_start_to_end.py');
ipcMain.on(
    'User-Requests-to-Run-Scenario',
    (event, userRequestedScenarioName) => {
        console.log(`Received user request for ${userRequestedScenarioName}`);

        storage.get(
            'gridPathDirectory',
            (error, data) => {
                if (error) throw error;
                const gridPathDirectoryPath = data['gridPathDirectory'][0];
                        // Spawn Python process
                console.log(`Running ${userRequestedScenarioName}...`);
                console.log(gridPathDirectoryPath);

                const PyScriptPath = path.join(gridPathDirectoryPath, 'run_start_to_end.py');
                console.log(PyScriptPath);
                // Spawn a python child process
                // Options:
                // 1) cwd changes directory to the root
                // 2) setting stdio to 'inherit' in order to display child process
                // stdout output 'live' (it's buffered otherwise); other options I
                // found include flushing stdout with sys.stdout.flush() in the
                // Python code or spawning the Python child process with the
                // unbuffered (-u) flag (python -u python_script.py); sticking with
                // 'inherit' for now as it's simplest and produces the most
                // faithful output in a limited set of experiments
                const runScenarioPythonChild = require('child_process').spawn(
                    'python',
                    [PyScriptPath, '--scenario', userRequestedScenarioName],
                    {
                        cwd: gridPathDirectoryPath,
                        stdio: 'inherit',
                        shell: true
                    }
                );
                // runScenarioPythonChild.stdout.on('data', function(data) {
                //     console.log('stdout: ' + data.toString());
                // });
                // runScenarioPythonChild.stderr.on('data', function(data) {
                //     console.log('stderr: ' + data.toString());
                // });
                runScenarioPythonChild.on('close', function(code) {
                    console.log('Python process closing code: ' + code.toString());
                });

                }
        );
    }
);


// General methods //
// Go back to index view if user requests it; maybe this can be reused
ipcMain.on(
    'User-Requests-Index-View',
    (event) => {
        console.log('Received user request for index view');
        mainWindow.loadFile('./src/index.html');
    }
);

// New scenario view //
ipcMain.on(
    'User-Requests-New-Scenario-View',
    (event) => {
        console.log('Received user request for new scenario');
        mainWindow.loadFile('./src/scenario_new.html');
    }
);


// Settings view //
ipcMain.on(
    'User-Requests-Settings-View',
    (event) => {
        console.log('Received user request for settings view');
        mainWindow.loadFile('./src/settings.html');
    }
);
