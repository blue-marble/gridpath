'use strict';


const { ipcRenderer } = require('electron');


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
// Listen for the scenario list
ipcRenderer.send('Index-Requests-Scenario-List');
ipcRenderer.on(
    'Main-Relays-Scenario-List',
    (event, scenarioList) => {
        console.log('Index window received scenario list');
        console.log(scenarioList);

        // Create the HTML string for a button group for the scenarios
        let scenarioListHTML = '<div class="btn-group">\n';
        scenarioList.forEach(
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
        scenarioList.forEach(
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

