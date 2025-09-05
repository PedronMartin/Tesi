import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InstCardList } from './inst-card-list';

describe('InstCardList', () => {
  let component: InstCardList;
  let fixture: ComponentFixture<InstCardList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InstCardList]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InstCardList);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
