'use strict';

const { remote } = require('electron');
const path = require('path');
const Database = require('better-sqlite3');
const {ipcRenderer} = require('electron');


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
    io.close();
    return scenariosList

}

// Make a list of scenarios; each scenario is a button with a unique ID
const scenarios = getScenarioList();
// Create the HTML string for a button group for the scenarios
let scenarioListHTML = '<div class="btn-group">\n';
scenarios.forEach(function(scenario) {
    const button_id = "scenarioDetailButton"+scenario;
    const html_string =
        '<button id='+button_id+'><b>'+ scenario + '</b></button>\n';
  scenarioListHTML += html_string;
});
scenarioListHTML += '<div class="btn-group">';

// Add the HTML string to the index.html file
document.getElementById("scenarioListButtons").innerHTML =
    scenarioListHTML;

// Define what to do when a scenario button is clicked (send scenario name to
// the main process)
function sendScenarioName(scenario_name) {
   console.log("User requests scenario " + scenario_name);
   ipcRenderer.send('User-Requests-Scenario-Detail', scenario_name);
}

// Bind the what-to-do function to the respective scenario button
scenarios.forEach(function(scenario) {
    // Get appropriate button
    const ScenarioDetailButton =
    document.getElementById(('scenarioDetailButton'+scenario));
    // Bind the function with the correct scenario name as parameter
    ScenarioDetailButton.addEventListener('click', function (event) {
        sendScenarioName(scenario)
    });
});



//// Create new scenario /////
function sendNewScenarioRequest() {
    console.log("User requests new scenario ");
    ipcRenderer.send('User-Requests-New-Scenario');
}
const NewScenarioButton =
    document.getElementById('NewScenarioButton');

NewScenarioButton.addEventListener('click', function (event) {
  const new_scenario_html_path = path.join(
      __dirname, 'scenario_new.html'
  );
  sendNewScenarioRequest()
});

