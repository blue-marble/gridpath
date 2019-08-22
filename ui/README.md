# Welcome

Welcome to the GridPath user interface!

# Installation

## Python
See the `README.md` file in the root GridPath directory for Python 
installation instructions. Python is required for the GridPath UI server and
 core engine that builds the optimization problems.

## NodeJS
To edit the UI code, or build and compile the app from source, you will
need NodeJS. Install [here](https://nodejs.org/en/).

## Packages
To install the required node packages, run the following from this directory.

```bash
npm run install
``` 

# Scripts
To build the Angular app and open it in Electron, run:
```bash
npm run angel
```

To build the Angular app only without opening it in Electron, run:
```bash
npm build 
```

To open Electron without building the Angular app, run:
```bash
npm electron
```

To compile the project for distribution, run:
```bash
npm build
```
