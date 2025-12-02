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
  private alberi: any;
  private aree_verdi: any;
  private result: any;

  //layer della mappa
  private baseLayer: any;       //mappa base (OSM)
  private resultsLayer: any;    //edifici conformi a tutte le regole
  private treesLayer: any;      //tutti gli alberi in input
  private greenAreasLayer: any; //tutte le aree verdi in input

  //input ricevuti
  @Input() dati: any;
  @Input() polygon: number[][] = [];

  //costruttore
  constructor(@Inject(PLATFORM_ID) private platformId: Object) { }

  //appena caricato il layer della mappa, andiamo a inizializzarla con i dati ricevuti
  ngAfterViewInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      import('leaflet').then(L => {
        let mapDiv: HTMLElement | null = document.getElementById("map");
        if (!mapDiv) {
          console.error("Impossibile trovare il div della mappa con id 'map'");
          return;
        }
        this.L = L;

        // --- FIX: Distruggi la mappa se esiste già ---
        // Previene errori se il componente viene ricaricato (es. Hot-Reload)
        if (this.map) {
          this.map.remove();
          this.map = null;
        }

        // --- FIX: Logica Bounds e Fallback migliorata ---
        let bounds: any;
        
        // Controlla se il poligono esiste E ha almeno un punto
        if (this.polygon && this.polygon.length > 0) {
          const latlngs = this.polygon.map((coord: number[]) => L.latLng(coord[0], coord[1]));
          bounds = L.latLngBounds(latlngs);
        } else {
          // fallback: centro Italia (Roma)
          const fallbackCenter = L.latLng(41.9028, 12.4964);
          // Creiamo un "bounds" fittizio per il fallback zoomando sul centro
          bounds = fallbackCenter.toBounds(100000); // 100km di raggio
        }

        //inizializzo la mappa sul div
        this.map = L.map('map');

        //aggiungo sfondo OSM alla mappa
        this.baseLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 30,
          maxNativeZoom: 30
        }).addTo(this.map);

        //centro la mappa con i dati ricevuti e regolo lo zoom
        this.map.fitBounds(bounds);
        this.map.setZoom(this.map.getZoom() - 1);
        this.loadData();
      });
    }
  }

private loadData(){

    //verifica dei dati
    if(!this.dati || !this.map || !this.L) {
      console.error("Dati non validi o mappa non inizializzata");
      return;
    }
    
    //estraggo e preparo i dati
    const data = this.extractData();

    //pulisco layer precedenti (se esistono)
    this.clearLayer();

    //definisco gli stili per i vari layer
    const styles = this.colorLayers();

    //creo i layer di output (il primo a caricare)
    if(this.result && this.result.features && this.result.features.length > 0) {
      this.resultsLayer = this.L.geoJSON(this.result, {
        style: styles.results,
        onEachFeature: (feature: any, layer: any) => {
          if(feature.properties){
            const props = feature.properties;
            let popupContent = `<b>Edificio ID: ${props.id}</b><br>`;
            if(props.name) popupContent += `Nome: ${props.name}<br>`;
            popupContent += `Alberi visibili: ${props.visible_trees_count}<br>`;
            popupContent += `Score 300m: ${props.score_300 === 1 ? 'Sì' : 'No'}<br>`;
            popupContent += `Copertura Zona: ${props.coverage_percentage.toFixed(2)}%`;
            layer.bindPopup(popupContent);
          }
        }
      }).addTo(this.map);
    }

    //layer alberi di input
    if (this.alberi && this.alberi.features && this.alberi.features.length > 0){

      //definizione icona personalizzata
      const treeIcon = this.L.icon({
        iconUrl: 'assets/treePopUp.png',
        iconSize: [25, 25],                 //dimensione icona
        iconAnchor: [12, 25],               //posizione popup rispetto al punto
      });

      this.treesLayer = this.L.geoJSON(this.alberi, {
        
        //gestione delle zone arboree grandi (boschi e foreste)
        style: styles.trees,
        
        //gestione degli alberi puntiformi (Leaflet di default inserisce i popup standard)
        pointToLayer: (_feature: any, latlng: any) => {
          return this.L.marker(latlng, {icon: treeIcon});
        }
      });
    }

    //layer aree verdi di input
    if (this.aree_verdi && this.aree_verdi.features && this.aree_verdi.features.length > 0)
      this.greenAreasLayer = this.L.geoJSON(this.aree_verdi, { style: styles.greenAreas });

    //definisco i gruppi di controllo degli output
    const baseLayers = {
      "Mappa base": this.baseLayer
    };

    //spacchettamento delle caselle selezionate, aggiungendo solo quelle esistenti
    /*
    ... ---> aggiunge solo se esiste
    this.<nomeLayer> ---> verifica se il layer esiste
    && ---> se esiste, aggiunge l'oggetto con nome e layer
    */
    const overlayLayers = {
      ...(this.resultsLayer && {"Edifici Conformi": this.resultsLayer}),
      ...(this.treesLayer && {"Alberi": this.treesLayer}),
      ...(this.greenAreasLayer && {"Aree Verdi": this.greenAreasLayer})
    };

    //aggiungo il Layer alla mappa
    this.L.control.layers(baseLayers, overlayLayers, {
      position: 'topright',
      collapsed: false
    }).addTo(this.map);
  }

  //funzione ausiliaria per estrapolare i dati
  private extractData(){
    this.alberi = JSON.parse(this.dati['alberi']);
    this.aree_verdi = JSON.parse(this.dati['aree_verdi']);
    this.result = JSON.parse(this.dati['risultati']);
  }

  //funzione ausiliaria per pulire i layer precedenti
  private clearLayer(){
    if(this.resultsLayer) this.map.removeLayer(this.resultsLayer);
    if(this.treesLayer) this.map.removeLayer(this.treesLayer);
    if(this.greenAreasLayer) this.map.removeLayer(this.greenAreasLayer);
  }

  //funzione ausiliaria per definire gli stili dei layer
  private colorLayers(){
    return {
        //edifici conformi alle regole
        results: {
            color: "#00FF00", weight: 2, opacity: 1, fillOpacity: 0.3
        },
        //tutti gli alberi in input
        trees: {
            color: "#dfdb0aff", weight: 1, opacity: 0.8, fillOpacity: 0.4
        },
        //tutte le aree verdi in input
        greenAreas: {
            color: "#286d0cff", weight: 1, opacity: 0.7, fillOpacity: 0.3
        }
    };
  }
}
