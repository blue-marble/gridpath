'use strict';


const Database = require('better-sqlite3');
const { ipcRenderer } = require('electron');
const storage = require('electron-json-storage');


//// Settings ////
const settingsButton = document.getElementById(('settingsButton'));

const sendSettingsRequest = () => {
    console.log('User requests new scenario');
    ipcRenderer.send('User-Requests-Settings-View');
};

settingsButton.addEventListener(
    'click',
    (event) => {
        sendSettingsRequest()
    }
);


//// Make list of clickable scenarios ////
// Get scenarios from database
const getScenarioList = (dbFilePath) => {
    const db = new Database (dbFilePath, {fileMustExist: true});
    const scenariosList = [];
    // TODO: how should these be ordered
    const getScenariosSQL = db.prepare('SELECT scenario_name FROM scenarios;');
    for (const scenario of getScenariosSQL.iterate()) {
        scenariosList.push(scenario.scenario_name)
    }
    db.close();
    return scenariosList

};

// Make a list of scenarios; each scenario is a button with a unique ID
// We need to get the user-defined database file path, so this is inside a
// storage.get()
storage.get(
    'dbFilePath',
    (error, data) => {
        if (error) throw error;
        const dbFilePath = data['dbFilePath'];

        console.log(dbFilePath[0]);
        const scenarios = getScenarioList(dbFilePath[0]);
        console.log(scenarios);
        // Create the HTML string for a button group for the scenarios
        let scenarioListHTML = '<div class="btn-group">\n';
        scenarios.forEach(
            (scenario) => {
                const buttonID = `scenarioDetailButton${scenario}`;
                const htmlString =
                    `<button id=${buttonID} class="button"><b>${scenario}</b></button>\n`;
                scenarioListHTML += htmlString;
            }
        );
        scenarioListHTML += '<div class="btn-group">';

        // Add the HTML string to the index.html file
        document.getElementById('scenarioListButtons').innerHTML =
            scenarioListHTML;
        // Bind the what-to-do-when-clicked function to the respective scenario button
        scenarios.forEach(
            (scenario) => {
                // Get appropriate button
                const scenarioDetailButton = document.getElementById(
                    `scenarioDetailButton${scenario}`
                );
                // Bind the function with the correct scenario name as parameter
                scenarioDetailButton.addEventListener(
                    'click',
                    (event) => {
                        sendScenarioName(scenario)
                    }
                );
            }
        );
    }
);


// Define what to do when a scenario button is clicked (send scenario name to
// the main process)
const sendScenarioName = (scenarioName) => {
   console.log(`User requests scenario ${scenarioName}`);
   ipcRenderer.send('User-Requests-Scenario-Detail', scenarioName);
};

//// Create new scenario /////
const sendNewScenarioRequest = () => {
    console.log('User requests new scenario');
    ipcRenderer.send('User-Requests-New-Scenario-View');
};

const newScenarioButton =
    document.getElementById('newScenarioButton');

newScenarioButton.addEventListener(
    'click',
    (event) => {
        sendNewScenarioRequest()
    }
);

