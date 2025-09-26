import { Component, AfterViewInit, PLATFORM_ID, Inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-map-layer',
  templateUrl: './map-layer.html',
  styleUrls: ['./map-layer.css']
})
export class MapLayerComponent implements AfterViewInit {

  private map: any;

  constructor(@Inject(PLATFORM_ID) private platformId: Object) { }

  //inizializzo mappa caricando il layer da OSM
  ngAfterViewInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      import('leaflet').then(L => {
        this.map = L.map('map', {
          center: [ 45.464664, 9.188540 ],
          zoom: 13
        });

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 30
        }).addTo(this.map);
        this.map.setMaxZoom(30);
      });
    }

    /*
    TODO: vedere se esiste modo di potenziare il rendering della mappa per caricare più veloce spostamenti dell'utente e zoom vari
    */
  }
}