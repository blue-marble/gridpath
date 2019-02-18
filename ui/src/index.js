'use strict';

const { remote } = require('electron');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const bettersqlite3 = require('better-sqlite3');
const Database = require('better-sqlite3');
const dialog = remote.require('electron').dialog;
const BrowserWindow = remote.require('electron').BrowserWindow;
const {ipcRenderer} = require('electron');

// // Spawn a Python child process
// const TestPythonButton = document.getElementById('TestPythonButton');
// // We need to find the Python script when we are in both
// // a production environment and a development environment
// // We do that by looking up app.isPackaged (this is a renderer process, so we
// // need to do it via remote)
// // In development, the script is in the py directory under root
// // In production, we package the script in the 'py' directory under the app's
// // Contents/Resources by including extraResources under "build" in package.json
// function baseDirectoryAdjustment() {
//     if (remote.app.isPackaged) {
//       return path.join(process.resourcesPath)
//     } else {
//       return path.join(__dirname, "..")
//     }
//   }
// const baseDirectory = baseDirectoryAdjustment();
// const PyScriptPath = path.join(
//  baseDirectory, "/py/hello_world_from_python.py"
// );
//
// // Bind the TestPythonButton with an "event listener" for a click
// //  Open dialog and have user select the write path for the Python script
// //  .txt write file
// TestPythonButton.addEventListener('click', function (event) {
//     // Write where
//     let python_write_path = dialog.showOpenDialog({
//         properties: ['openDirectory']
//     });
//     // Spawn a python child process
//     let python_child = require('child_process').spawn(
//     'python',
//     [PyScriptPath, '--write_dir', python_write_path]
//     );
// });
//
// // Create and access an SQLite database
// const TestSQLiteButton = document.getElementById('TestSQLiteButton');
//
// function createandAccessSQLite(db_dir) {
//     let db_file = path.join(db_dir[0], 'hello_world_from_sqlite.db');
//     let db = new bettersqlite3(db_file);
//     db.exec("CREATE TABLE sample_table (\n" +
//             "id INTEGER PRIMARY KEY AUTOINCREMENT,\n" +
//             "input_value VARCHAR(32)\n" +
//             ");");
//     db.exec("INSERT INTO sample_table VALUES (1, 'it worked!')");
//     db.close();
//   }
// // Bind the TestSQLiteButton with an "event listener" for a click
// //  Open dialog and have user select the write path for the database
// TestSQLiteButton.addEventListener('click', function (event) {
//     let db_dir = dialog.showOpenDialog({
//         properties: ['openDirectory']
//     });
//     createandAccessSQLite(db_dir)
//
// });

//////////////////////// END DEMOS ##############
// New window general function
function openNewWindow(html_path) {
    let newWindow = new BrowserWindow({ width: 400, height: 400 });
        newWindow.on('close', function () { newWindow = null });
        newWindow.loadFile(html_path);
        newWindow.once('ready-to-show', () => {
            newWindow.show()
        });
    return newWindow
  }

//// Make list of clickable scenarios ////
// Get scenarios from database
function getScenarioList() {
    const io_file = path.join(__dirname, "../db/io.db");
    const io = new Database (io_file, {fileMustExist: true});
    const scenariosList = [];
    const statement = io.prepare("SELECT scenario_name FROM scenarios;");
    for (const scenario of statement.iterate()) {
        scenariosList.push(scenario.scenario_name)
    }
    return scenariosList

}

// Make a list of scenarios; each scenario is a button with a unique ID
const scenarios = getScenarioList();
// Create the html for a button group for the scenarios
let scenarioListHTML = '<div class="btn-group">\n';
scenarios.forEach(function(scenario) {
    let button_id = "scenarioDetailButton"+scenario;
    let html_string =
        '<button id='+button_id+'><b>'+ scenario + '</b></button>\n';
  scenarioListHTML += html_string;
});
scenarioListHTML += '<div class="btn-group">';

// Add the HTML to the index.html file
document.getElementById("scenarioListButtons").innerHTML =
    scenarioListHTML;

// Define what to do when a scenario button is clicked (open a new window with
// the scenario_detail.html view)
function sendScenarioName(scenario_name) {
   console.log("User requests scenario " + scenario_name);
   ipcRenderer.send('User-Requests-Scenario-Detail', scenario_name);
}

// Bind the what-to-do function to the respective scenario button
scenarios.forEach(function(scenario) {
    // Get appropriate button
    let ScenarioDetailButton =
    document.getElementById(('scenarioDetailButton'+scenario));
    // Bind the function with the correct scenario name as parameter
    ScenarioDetailButton.addEventListener('click', function (event) {
        sendScenarioName(scenario)
    });
});




//
// // New scenario
// const NewScenarioButton =
//     document.getElementById('NewScenarioButton');
//
// NewScenarioButton.addEventListener('click', function (event) {
//   const new_scenario_html_path = path.join(
//       __dirname, 'scenario_new.html'
//   );
//   console.log(new_scenario_html_path);
//   openNewWindow(new_scenario_html_path)
// });


// ipcRenderer.on('test', (event, message) => {
//     console.log("Test relayed and received.");
//     console.log(message);
// });

// console.log(ipcRenderer.sendSync(
//     'synchronous-message', 'ping')) // prints "pong"
//
// ipcRenderer.on('asynchronous-reply', (event, arg) => {
//   console.log(arg) // prints "pong"
// })
// ipcRenderer.send('asynchronous-message', 'ping')
