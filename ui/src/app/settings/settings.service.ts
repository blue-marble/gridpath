import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SettingsService {

  directoryStatusSubject = new BehaviorSubject('set');
  databaseStatusSubject = new BehaviorSubject('set');
  pythonStatusSubject = new BehaviorSubject('set');

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
}

