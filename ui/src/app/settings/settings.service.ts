import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SettingsService {

  directoryStatusSubject = new BehaviorSubject('set');
  databaseStatusSubject = new BehaviorSubject('set');
  pythonStatusSubject = new BehaviorSubject('set');

  solver1NameStatusSubject = new BehaviorSubject('set');
  solver1ExecutableStatusSubject = new BehaviorSubject('set');
  solver2NameStatusSubject = new BehaviorSubject('set');
  solver2ExecutableStatusSubject = new BehaviorSubject('set');
  solver3NameStatusSubject = new BehaviorSubject('set');
  solver3ExecutableStatusSubject = new BehaviorSubject('set');

  constructor() { }

  changeDirectoryStatus(settingsStatus: string) {
    console.log('Changing directory setting status to ', settingsStatus);
    this.directoryStatusSubject.next(settingsStatus);
  }

  changeDatabaseStatus(settingsStatus: string) {
    console.log('Changing database setting status to ', settingsStatus);
    this.databaseStatusSubject.next(settingsStatus);
  }

  changePythonStatus(settingsStatus: string) {
    console.log('Changing python setting status to ', settingsStatus);
    this.pythonStatusSubject.next(settingsStatus);
  }

  changeSolver1NameStatus(settingsStatus: string) {
    console.log('Changing solver 1 name setting status to ', settingsStatus);
    this.solver1NameStatusSubject.next(settingsStatus);
  }

  changeSolver1ExecutableStatus(settingsStatus: string) {
    console.log('Changing solver 1 executable setting status to ', settingsStatus);
    this.solver1ExecutableStatusSubject.next(settingsStatus);
  }

  changeSolver2NameStatus(settingsStatus: string) {
    console.log('Changing solver 2 name setting status to ', settingsStatus);
    this.solver2NameStatusSubject.next(settingsStatus);
  }

  changeSolver2ExecutableStatus(settingsStatus: string) {
    console.log('Changing solver 2 executable setting status to ', settingsStatus);
    this.solver2ExecutableStatusSubject.next(settingsStatus);
  }

  changeSolver3NameStatus(settingsStatus: string) {
    console.log('Changing solver 3 name setting status to ', settingsStatus);
    this.solver3NameStatusSubject.next(settingsStatus);
  }

  changeSolver3ExecutableStatus(settingsStatus: string) {
    console.log('Changing solver 3 executable setting status to ', settingsStatus);
    this.solver3ExecutableStatusSubject.next(settingsStatus);
  }
}

