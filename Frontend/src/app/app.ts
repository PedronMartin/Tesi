import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { SharedService } from './shared';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('greenratingalgorithm');

  //costruisco lo shared in modo che l'html app veda la variabile isLoading durante le richieste api
  constructor(public shared: SharedService) {}
}
