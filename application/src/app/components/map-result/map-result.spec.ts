import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MapResult } from './map-result';

describe('MapResult', () => {
  let component: MapResult;
  let fixture: ComponentFixture<MapResult>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MapResult]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MapResult);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
