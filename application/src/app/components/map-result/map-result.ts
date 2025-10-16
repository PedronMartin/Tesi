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

        // Calcolo bounds e centro dal poligono
            let latlngs: any[] = [];
            let bounds: any;
            if(this.polygon){
              latlngs = this.polygon.map((coord: number[]) => L.latLng(coord[1], coord[0]));
              bounds = L.latLngBounds(latlngs);
            } else {
              // fallback: centro Italia
              bounds = L.latLngBounds([L.latLng(42, 12)]);
            }
            const center = bounds.getCenter();
            const zoom = this.map ? this.map.getBoundsZoom(bounds) : 13;

            // Inizializza la mappa con centro e zoom calcolati
            this.map = L.map('mapId').setView([center.lat, center.lng], zoom);
            if (this.map) {
              L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 30
              }).addTo(this.map);
              this.map.setMaxZoom(30);
              // Adatta la vista al poligono
              if(bounds){
                this.map.fitBounds(bounds);
              }
            }
          });
        }
      }
}
