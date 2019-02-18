'use strict';

const { remote } = require('electron');
const {ipcRenderer }= require('electron');

console.log("Scenario Detail window is associated with scenario_detail.js.")
// Listen for a scenario name
ipcRenderer.send("Scenario-Detail-Window-Requests-Scenario-Name");
ipcRenderer.on('Main-Relays-Scenario-Name', (event, scenario_name) => {
    console.log("Scenario Detail Window received message.");
    console.log(scenario_name);
    createScenarioDetailTable(scenario_name)
    document.getElementById("scenarioDetailTable").innerHTML =
    createScenarioDetailTable(scenario_name);
});

// Create the html for a table
function createScenarioDetailTable(scenario) {
        let scenario_params_dict = {
            "scenario_name": scenario,
        "project_portfolio_subcenario_id": 1,
    };
    let scenarioDetailTable = '<table style="width:100%">';
    Object.keys(scenario_params_dict).forEach(function (key) {
        scenarioDetailTable += '<tr>';
        scenarioDetailTable += '<td>' + key + '</td>';
        scenarioDetailTable += '<td>' + scenario_params_dict[key] + '</td>';
        scenarioDetailTable += '</tr>';
    });
    scenarioDetailTable += '</table>';
    return scenarioDetailTable
}




