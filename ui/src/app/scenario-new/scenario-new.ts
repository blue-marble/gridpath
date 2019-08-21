export class SettingsTable {
  uiTableNameInDB: string;
  tableCaption: string;
  settingRows: SettingRow[];
}

export class SettingRow {
  uiRowNameInDB: string;
  rowName: string;
  rowFormControlName: string;
  settingOptions: Setting[];
}

export class Setting {
  id: number;
  name: string;
}
