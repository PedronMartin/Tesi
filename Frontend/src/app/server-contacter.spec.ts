import { TestBed } from '@angular/core/testing';

import { ServerContacter } from './server-contacter';

describe('ServerContacter', () => {
  let service: ServerContacter;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ServerContacter);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
