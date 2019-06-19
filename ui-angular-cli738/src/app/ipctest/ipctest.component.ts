import { Component, OnInit, NgZone } from '@angular/core';

// Electron makes itself available to the browser side JavaScript through
// the window global variable. Since the TypeScript compiler is not aware
// of this, window has to be cast to any before accessing the require
// function. Electron provides the ipcRenderer object which implements
// interprocess communication for the renderer. ipcRenderer.on is then used to
// register listeners for IPC messages. Source:
// https://developer.okta.com/blog/2019/03/20/build-desktop-app-with-angular-electron
// An alternative I found that I did not implement was to include `declare
// var electron: any;` here and `const electron = require('electron');`
// inside a `<script>` tag in index.html.
// Also, see here for alternative ways to get electron to be recognized:
// https://stackoverflow.com/questions/36286592/how-to-integrate-electron-ipcrenderer-into-angular-2-app-based-on-typescript
const electron = (<any>window).require('electron');

@Component({
  selector: 'ipctest-component',
  templateUrl: './ipctest.component.html',
  styleUrls: ['./ipctest.component.css']
})
export class IPCTestComponent implements OnInit {
	private ipc_info: string;
	private remote_info: string;
	private count: number;

	constructor(zone: NgZone) {
		this.count = 0;
		this.ipc_info = '';
		this.remote_info = '';

		electron.ipcRenderer.on('get-data-replay', (event, arg) => {
			// console.log('ipc-receive: ' + arg);
			zone.run(() => {
				this.count += 1;
				this.ipc_info = this.count + ' ' + arg + '\n';

				// console.log('remote-data: ', remote.getGlobal('sharedData').deckDef);
				this.remote_info = '';
				for (let i = 0; i < electron.remote.getGlobal('sharedData').deckDef.length; i += 1) {
					this.remote_info += electron.remote.getGlobal('sharedData').deckDef[i] + '\n';
				}
			});
		});
	}
	ngOnInit() {
	}
	sendClick(): void {
		electron.ipcRenderer.send('get-data');
	}
}
