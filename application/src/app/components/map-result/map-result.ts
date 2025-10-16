import { Component, PLATFORM_ID, Inject, Input } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-map-result',
  imports: [],
  templateUrl: './map-result.html',
  styleUrl: './map-result.css'
})
export class MapResult {

  //campi
  private L: any;
  private map: any;
  @Input() dati: any;
  @Input() polygon: number[][] = [];

  //costruttore
  constructor(@Inject(PLATFORM_ID) private platformId: Object) { }

  //appena caricato il layer della mappa, andiamo a inizializzarla con i dati ricevuti
  ngAfterViewInit(): void {

    if(isPlatformBrowser(this.platformId)) {
      import('leaflet').then(L => {
        let mapDiv: HTMLElement | null = document.getElementById("map");
        if(!mapDiv) {
          console.error("Impossibile trovare il div della mappa con id 'map'");
          return;
        }
        this.L = L;

        //carico OSM
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 30
        }).addTo(this.map);
        this.map.setMaxZoom(30);

        //inizializzo la mappa
        if(this.polygon){
          const latlngs = this.polygon.map(coord => L.latLng(coord[1], coord[0]));
          const bounds = L.latLngBounds(latlngs);
          this.map.fitBounds(bounds);
        }
      });
    }
  }
}
