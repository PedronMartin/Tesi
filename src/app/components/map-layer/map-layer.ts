import { Component, AfterViewInit, PLATFORM_ID, Inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { SharedService } from '../../shared';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-map-layer',
  templateUrl: './map-layer.html',
  styleUrls: ['./map-layer.css']
})
export class MapLayerComponent implements AfterViewInit {

  //sottoscrizione eventlistener per la cattura
  private catturaSub!: Subscription;
  private map: any;
  //servizio di condivisione dati
  constructor(@Inject(PLATFORM_ID) private platformId: Object, private SharedService: SharedService) { }

  ngOnInit() {
    this.catturaSub = this.SharedService.catturaPerimetro$.subscribe(() => {
      const captureData = this.onCapture();
      this.SharedService.set(captureData);
    });
  }

  ngOnDestroy() {
    if (this.catturaSub) {
      this.catturaSub.unsubscribe();
    }
  }

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

  //funzione per catturare i dati della mappa
  private onCapture(): any[] {
    const datiCatturati = [];
		const map = document.getElementById('map');
		if (this.map) {
			datiCatturati[0] = (this.map as any).getBounds();
			datiCatturati[1] = (this.map as any).getCenter();
			datiCatturati[2] = (this.map as any).getZoom();
		} else {
			datiCatturati[0] = null;
			datiCatturati[1] = null;
			datiCatturati[2] = null;
			console.warn("Elemento 'map' non trovato o 'getBounds' non disponibile.");
		}
    return datiCatturati;
  }
}