import { Routes } from '@angular/router';
import { HomePage } from './home-page/home-page';
import { CatturaPage } from './cattura-page/cattura-page';

export const routes: Routes = [
  { path: '', component: HomePage },
  { path: 'cattura', component: CatturaPage },
];
