export class SettingsTable {
  tableCaption: string;
  settingRows: SettingRow[];
}

export class SettingRow {
  rowName: string;
  rowFormControlName: string;
  settingOptions: Setting[];
}

export class Setting {
  id: number;
  name: string;
}
