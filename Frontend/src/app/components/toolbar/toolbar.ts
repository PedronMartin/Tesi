import {Component} from '@angular/core';
import {MatIconModule} from '@angular/material/icon';
import {MatButtonModule} from '@angular/material/button';
import {MatToolbarModule} from '@angular/material/toolbar';

/**
 * @title Toolbar overview
 */
@Component({
  selector: 'app-toolbar',
  templateUrl: 'toolbar.html',
  styleUrl: 'toolbar.css',
  imports: [MatToolbarModule, MatButtonModule, MatIconModule],
})
export class Toolbar {}