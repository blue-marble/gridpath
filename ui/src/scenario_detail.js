'use strict';

const { ipcRenderer, remote }= require('electron');
const Database = require('better-sqlite3');
const storage = require('electron-json-storage');

// Listen for a scenario name
ipcRenderer.send('Scenario-Detail-Window-Requests-Scenario-Name');
ipcRenderer.on(
    'Main-Relays-Scenario-Name',
    (event, scenarioName) => {
        console.log('Scenario Detail Window received message');
        console.log(scenarioName);

        // Create the HTML for the scenario name
        document.getElementById('scenarioName').innerHTML =
            scenarioName;

        storage.get(
            'dbFilePath',
            (error, data) => {
                if (error) throw error;
                const dbFilePath = data['dbFilePath'][0];


                // Create the scenario detail HTML
                document.getElementById(
                    'scenarioDetailTable'
                ).innerHTML =
                    createScenarioDetailTable(scenarioName, dbFilePath);
            }
        );



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

// Create the html for the scenario detail table
const createScenarioDetailTable = (scenario, dbFilePath) => {
    const scenarioParamsDict = getScenarioDetails(scenario, dbFilePath);

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


const getScenarioDetails = (scenario, dbFilePath) => {
    const db = new Database (dbFilePath, {fileMustExist: true});

    const getSubscenarioNames =
        db.prepare(
            `SELECT
            subscenarios_project_portfolios.name as portfolio, 
            subscenarios_project_operational_chars.name as operating_chars, 
            subscenarios_system_load.name as load_profile, 
            subscenarios_project_fuel_prices.name as fuel_prices
            FROM scenarios 
            JOIN subscenarios_project_portfolios 
            USING (project_portfolio_scenario_id)
            JOIN subscenarios_project_operational_chars 
            USING (project_operational_chars_scenario_id)
            JOIN subscenarios_system_load 
            USING (load_scenario_id)
            JOIN subscenarios_project_fuel_prices 
            USING (fuel_price_scenario_id)
            WHERE scenario_name = ?`
        ).get(scenario);

    db.close();
    return getSubscenarioNames
};
