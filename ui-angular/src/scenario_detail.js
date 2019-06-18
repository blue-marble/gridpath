'use strict';

const { ipcRenderer, remote }= require('electron');
const Database = require('better-sqlite3');
const storage = require('electron-json-storage');

// Listen for a scenario name
ipcRenderer.send('Scenario-Detail-Window-Requests-Scenario-Detail');
ipcRenderer.on(
    'Main-Relays-Scenario-Detail',
    (event, scenarioDetail) => {
        const scenarioName = scenarioDetail['scenario_name'];
        const runStatus = scenarioDetail['run_status'];

        console.log(`Scenario Detail Window received detail for ${scenarioName}`);

        // Create the HTML for the scenario name
        document.getElementById('scenarioName').innerHTML =
            `<b>${scenarioName}</b>`;

        // Create the run status HTML
        document.getElementById('runStatus').innerHTML =
            `<b>Status: ${runStatus}</b>`;

        const scenarioParams = scenarioDetail;
        delete scenarioParams['scenario_name'];
        delete scenarioParams['run_status'];
        // Create the scenario detail table
        document.getElementById('scenarioDetailTable').innerHTML =
            createScenarioDetailTable(scenarioParams);


        // TODO: create button to run scenario here, not in html file?
        // If runScenarioButton is clicked, send scenario name to main process
        const runScenarioButton =
            document.getElementById('runScenarioButton');

        runScenarioButton.addEventListener(
            'click',
            (event) => {
                console.log(`User requests to run scenario ${scenarioName}`);
                ipcRenderer.send(
                    'User-Requests-to-Run-Scenario', scenarioName
                );
            }
        );
    }
);

// Request to go back to scenario list
const backtoScenariosListButton =
    document.getElementById('backtoScenariosListButton');
backtoScenariosListButton.addEventListener(
    'click',
    (event) => {
        ipcRenderer.send('User-Requests-Index-View');
    }
);

// Create the html for the scenario detail table
const createScenarioDetailTable = (scenarioParamsDict) => {

    console.log("Building params table");
    console.log(scenarioParamsDict);
    let scenarioDetailTable = '<table align="center">';
    Object.keys(scenarioParamsDict).forEach(
        (key) => {
            scenarioDetailTable += '<tr>';
            scenarioDetailTable += `<td>${key}</td>`;
            scenarioDetailTable += `<td>${scenarioParamsDict[key]}</td>`;
            scenarioDetailTable += '</tr>';
        }
    );
    scenarioDetailTable += '</table>';

    return scenarioDetailTable
};
