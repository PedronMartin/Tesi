import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MapLayer } from './map-layer';

describe('MapLayer', () => {
  let component: MapLayer;
  let fixture: ComponentFixture<MapLayer>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MapLayer]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MapLayer);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
