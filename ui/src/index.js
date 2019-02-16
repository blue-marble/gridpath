'use strict';

const { remote } = require('electron');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const dialog = remote.require('electron').dialog;
const BrowserWindow = remote.require('electron').BrowserWindow;


// Spawn a Python child process
const TestPythonButton = document.getElementById('TestPythonButton');
// We need to find the Python script when we are in both
// a production environment and a development environment
// We do that by looking up app.isPackaged (this is a renderer process, so we
// need to do it via remote)
// In development, the script is in the py directory under root
// In production, we package the script in the 'py' directory under the app's
// Contents/Resources by including extraResources under "build" in package.json
function baseDirectoryAdjustment() {
    if (remote.app.isPackaged) {
      return path.join(process.resourcesPath)
    } else {
      return path.join(__dirname, "..")
    }
  }
const baseDirectory = baseDirectoryAdjustment();
const PyScriptPath = path.join(
 baseDirectory, "/py/hello_world_from_python.py"
);

// Bind the TestPythonButton with an "event listener" for a click
//  Open dialog and have user select the write path for the Python script
//  .txt write file
TestPythonButton.addEventListener('click', function (event) {
    // Write where
    let python_write_path = dialog.showOpenDialog({
        properties: ['openDirectory']
    });
    // Spawn a python child process
    let python_child = require('child_process').spawn(
    'python',
    [PyScriptPath, '--write_dir', python_write_path]
    );
});

// Create and access an SQLite database
const TestSQLiteButton = document.getElementById('TestSQLiteButton');

function createandAccessSQLite(db_dir) {
    let db_file = path.join(db_dir[0], 'hello_world_from_sqlite.db');
    let db = new sqlite3.Database(db_file);
    db.serialize(() => {
        db.run("CREATE TABLE sample_table (\n" +
        "id INTEGER PRIMARY KEY AUTOINCREMENT,\n" +
        "input_value VARCHAR(32)\n" +
        ");")
        .run("INSERT INTO sample_table VALUES (1, 'it worked!')");
    });
    db.close();
  }
// Bind the TestSQLiteButton with an "event listener" for a click
//  Open dialog and have user select the write path for the database
TestSQLiteButton.addEventListener('click', function (event) {
    let db_dir = dialog.showOpenDialog({
        properties: ['openDirectory']
    });
    createandAccessSQLite(db_dir)

});

// Make a list of scenarios
let scenarios = [
    "Scenario_1", "Scenario_2", "Scenario_3", "Scenario_4", "Scenario_5"
];
// Create the html for an unordered list
let unordered_list = '<ul>';
scenarios.forEach(function(scenario) {
  unordered_list += '<li>'+ scenario + '</li>';
});
unordered_list += '</ul>';

// Create the html for a button group
let scenarioListButtons = '<div class="btn-group">\n';
scenarios.forEach(function(scenario) {
    let button_id = "scenario"+scenario+"DetailButton";
    let html_string =
        '<button id='+button_id+'><b>'+ scenario + '</b></button>\n';
  scenarioListButtons += html_string;
});
scenarioListButtons += '<div class="btn-group">';

console.log(scenarioListButtons);

document.getElementById("scenariosButtonList").innerHTML =
    scenarioListButtons;

// Open scenario detail
function openNewWindow(html_path) {
    let newWindow = new BrowserWindow({ width: 400, height: 400 });
        newWindow.on('close', function () { newWindow = null });
        newWindow.loadFile(html_path);
        newWindow.once('ready-to-show', () => {
            newWindow.show()
        });
  }

function showScenarioDetail() {
   const scenario_detail_html_path = path.join(
      __dirname, 'scenario_detail.html'
  );
  console.log(scenario_detail_html_path);
  openNewWindow(scenario_detail_html_path)
}

scenarios.forEach(function(scenario) {
    let ScenarioDetailButton =
    document.getElementById(('scenario'+scenario+'DetailButton'));
    ScenarioDetailButton.addEventListener('click', function (event) {
  showScenarioDetail()
});
});



// New scenario
const NewScenarioButton =
    document.getElementById('NewScenarioButton');

NewScenarioButton.addEventListener('click', function (event) {
  const scenario_detail_html_path = path.join(
      __dirname, 'scenario_new.html'
  );
  console.log(scenario_detail_html_path);
  openNewWindow(scenario_detail_html_path)
});


