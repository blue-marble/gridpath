# Welcome

Welcome to the GridPath user interface!

# Installation

## Python
See the `README.md` file in the root GridPath directory for Python 
installation instructions. Python is required for the GridPath UI server and
 core engine that builds the optimization problems.
 
## Python packages
You will also need to install the required Python packages to run GridPath
and the UI server. To do so, navigate to the GridPath root directory and 
run:
```bash
pip install -e .[ui]
```

## NodeJS
To edit the UI code, or build and compile the app from source, you will
need NodeJS. Install [here](https://nodejs.org/en/).

## Node packages
To install the required node packages, run the following from this directory.
```bash
npm install
``` 

# Scripts
To build the Angular app and open it in Electron, run:
```bash
npm run angel
```

To build the Angular app only without opening it in Electron, run:
```bash
npm run build 
```

To open Electron without building the Angular app, run:
```bash
npm run electron
```

To compile the project for distribution, run:
```bash
npm run dist
```
