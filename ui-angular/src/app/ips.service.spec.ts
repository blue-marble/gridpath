import { TestBed } from '@angular/core/testing';

import { IpsService } from './ips.service';

describe('IpsService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: IpsService = TestBed.get(IpsService);
    expect(service).toBeTruthy();
  });
});
