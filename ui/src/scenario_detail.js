'use strict';

const {ipcRenderer }= require('electron');
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

