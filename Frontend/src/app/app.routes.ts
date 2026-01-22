import { Routes } from '@angular/router';
import { HomePage } from './home-page/home-page';
import { ResultPage } from './result-page/result-page';

export const routes: Routes = [
  { path: '', component: HomePage },
  { path: 'calcolo', component: ResultPage },
];
