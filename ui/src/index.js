'use strict';

const path = require('path');
const Database = require('better-sqlite3');
const { ipcRenderer } = require('electron');
const storage = require('electron-json-storage');


//// Settings ////
const settingsButton = document.getElementById(('settingsButton'));

function sendSettingsRequest() {
    console.log("User requests new scenario ");
    ipcRenderer.send('User-Requests-Settings-View');
}

settingsButton.addEventListener('click', function (event) {
  sendSettingsRequest()
});


//// Make list of clickable scenarios ////
// Get scenarios from database
function getScenarioList(dbFilePath) {
    const db = new Database (dbFilePath, {fileMustExist: true});
    const scenariosList = [];
    // TODO: how should these be ordered
    const statement = db.prepare("SELECT scenario_name FROM scenarios;");
    for (const scenario of statement.iterate()) {
        scenariosList.push(scenario.scenario_name)
    }
    db.close();
    return scenariosList

}

// Make a list of scenarios; each scenario is a button with a unique ID
// We need to get the user-defined database file path
storage.get(
    'dbFilePath',
    function(error, data) {
        if (error) throw error;
        const dbFilePath = data['dbFilePath'];

        console.log(dbFilePath[0]);
        const scenarios = getScenarioList(dbFilePath[0]);
        console.log(scenarios);
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
        // Bind the what-to-do-when-clicked function to the respective scenario button
        scenarios.forEach(function(scenario) {
            // Get appropriate button
            const ScenarioDetailButton =
            document.getElementById(('scenarioDetailButton'+scenario));
            // Bind the function with the correct scenario name as parameter
            ScenarioDetailButton.addEventListener('click', function (event) {
                sendScenarioName(scenario)
            });
        });
        }
    );


// Define what to do when a scenario button is clicked (send scenario name to
// the main process)
function sendScenarioName(scenario_name) {
   console.log("User requests scenario " + scenario_name);
   ipcRenderer.send('User-Requests-Scenario-Detail', scenario_name);
}

//// Create new scenario /////
function sendNewScenarioRequest() {
    console.log("User requests new scenario ");
    ipcRenderer.send('User-Requests-New-Scenario');
}
const NewScenarioButton =
    document.getElementById('NewScenarioButton');

NewScenarioButton.addEventListener('click', function (event) {
  sendNewScenarioRequest()
});

