import { TestBed } from '@angular/core/testing';

import { ViewDataService } from './view-data.service';

describe('ViewDataService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ViewDataService = TestBed.get(ViewDataService);
    expect(service).toBeTruthy();
  });
});
