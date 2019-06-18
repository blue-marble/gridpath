'use strict';

const {ipcRenderer, remote} = require('electron');
const storage = require('electron-json-storage');
const dialog = remote.require('electron').dialog;

// Request to go back to scenario list
const backtoScenariosListButton =
    document.getElementById('backtoScenariosListButton');
backtoScenariosListButton.addEventListener(
    'click',
    (event) => {
        ipcRenderer.send('User-Requests-Index-View');
    }
);

// Get the database file
const dbFilePathSettingsButton =
    document.getElementById('dbFilePathSettingsButton');
dbFilePathSettingsButton.addEventListener(
    'click',
    (event) => {
        // Write where
        let dbFilePath = dialog.showOpenDialog(
            {properties: ['openFile']}
        );
        // set the database path
        storage.set(
            'dbFilePath',
            {'dbFilePath': dbFilePath },
            (error) => {if (error) throw error;}
        );
        // re-load settings view
        ipcRenderer.send('User-Requests-Settings-View');
    }
);

storage.get(
    'dbFilePath',
    (error, data) => {
        if (error) throw error;
        console.log(data);
        document.getElementById('currentDBPath').innerHTML =
            data.dbFilePath;
    }
);


// Get the scenarios directory
const scenariosDirectorySettingsButton =
    document.getElementById('scenariosDirectorySettingsButton');
scenariosDirectorySettingsButton.addEventListener(
    'click',
    (event) => {
        // Write where
        let scenariosDirectoryPath = dialog.showOpenDialog(
            { properties: ['openDirectory'] }
        );
        // set the database path
        storage.set(
            'scenariosDirectory',
            { 'scenariosDirectory': scenariosDirectoryPath },
            (error) => {if (error) throw error;}
        );
        // re-load settings view
        ipcRenderer.send('User-Requests-Settings-View');
    }
);

storage.get(
    'scenariosDirectory',
    (error, data) => {
        if (error) throw error;
        console.log(data);
        document.getElementById(
            'currentScenariosDirectory'
        ).innerHTML =
            data.scenariosDirectory;
    }
);


// Get the gridPath directory
const gridPathDirectorySettingsButton =
    document.getElementById('gridPathDirectorySettingsButton');
gridPathDirectorySettingsButton.addEventListener(
    'click',
    (event) => {
        // Write where
        let gridPathDirectoryPath = dialog.showOpenDialog(
            { properties: ['openDirectory'] }
        );
        // set the database path
        storage.set(
            'gridPathDirectory',
            { 'gridPathDirectory': gridPathDirectoryPath },
            (error) => {if (error) throw error;}
        );
        // re-load settings view
        ipcRenderer.send('User-Requests-Settings-View');
    }
);

storage.get(
    'gridPathDirectory',
    (error, data) => {
        if (error) throw error;
        console.log(data);
        document.getElementById(
            'currentGridPathDirectory'
        ).innerHTML =
            data.gridPathDirectory;
    }
);
