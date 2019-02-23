'use strict';

const { ipcRenderer, remote }= require('electron');
const Database = require('better-sqlite3');
const path = require('path');

// Listen for a scenario name
ipcRenderer.send("Scenario-Detail-Window-Requests-Scenario-Name");
ipcRenderer.on('Main-Relays-Scenario-Name', (event, scenario_name) => {
    console.log("Scenario Detail Window received message.");
    console.log(scenario_name);

    // Create the HTML for the scenario name
    document.getElementById('ScenarioName').innerHTML = scenario_name;
    createScenarioDetailTable(scenario_name);
    document.getElementById("scenarioDetailTable").innerHTML =
    createScenarioDetailTable(scenario_name);

    // TODO: spawn from main process not here
    const runScenarioButton = document.getElementById("runScenarioButton");
    runScenarioButton.addEventListener('click', function (event) {
    console.log("Running " + scenario_name);
    console.log(PyScriptPath);
    // Spawn a python child process
    const python_child = require('child_process').spawn(
    'python',
    [PyScriptPath, '--scenario', scenario_name],
    {shell: true, cwd: process.cwd(), detached: true}
    );
    python_child.stdout.on('data', function(data) {
    console.log('stdout: ' + data);
    //Here is where the output goes
    });
    python_child.stderr.on('data', function(data) {
        console.log('stderr: ' + data);
        //Here is where the error output goes
    });
    python_child.on('close', function(code) {
        console.log('closing code: ' + code);
        //Here you can get the exit code of the script
});
});
});

// Create the html for the scenario detail table
function createScenarioDetailTable(scenario) {

    const scenario_params_dict = getScenarioDetails(scenario);
    console.log(scenario_params_dict);
    let scenarioDetailTable = '<table style="width:100%">';
    Object.keys(scenario_params_dict).forEach(function (key) {

        scenarioDetailTable += '<tr>';
        scenarioDetailTable += '<td>' + key + '</td>';
        scenarioDetailTable += '<td>' + scenario_params_dict[key] + '</td>';
        scenarioDetailTable += '</tr>';
    });
    scenarioDetailTable += '</table>';
    console.log(scenarioDetailTable);
    return scenarioDetailTable
}


function getScenarioDetails(scenario) {
    const io_file = path.join(__dirname, "../db/io.db");
    const io = new Database (io_file, {fileMustExist: true});
    const scenarioDetails = {};
    scenarioDetails["scenario_name"] = scenario;


    const get_ids = io.prepare(
        "SELECT project_portfolio_scenario_id, " +
        "project_operational_chars_scenario_id, load_scenario_id, " +
        "fuel_price_scenario_id" +
        " FROM scenarios WHERE scenario_name = ?;")
        .get(scenario);

    scenarioDetails["project_portfolio_scenario_id"] =
        get_ids.project_portfolio_scenario_id;
    scenarioDetails["project_operational_chars_scenario_id"] =
        get_ids.project_operational_chars_scenario_id;
    scenarioDetails["load_scenario_id"] = get_ids.load_scenario_id;
    scenarioDetails["fuel_price_scenario_id"] = get_ids.fuel_price_scenario_id;

    console.log(scenarioDetails);
    io.close();
    return scenarioDetails

}


// Run scenario
// Spawn a Python child process
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
 baseDirectory, "../run_scenario.py"
);
