import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CatturaPage } from './cattura-page';

describe('CatturaPage', () => {
  let component: CatturaPage;
  let fixture: ComponentFixture<CatturaPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CatturaPage]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CatturaPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
