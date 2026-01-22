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
  private baseLayer: any;             //mappa base (OSM)
  private resultsLayer: any;          //edifici conformi a tutte le regole
  private treesLayer: any;            //tutti gli alberi in input
  private greenAreasLayer: any;       //tutte le aree verdi in input
  private lightedLayers: any;         //layer attivi sulla mappa

  //input ricevuti
  @Input() dati: any;
  @Input() polygon: number[][] = [];

  //costruttore
  constructor(@Inject(PLATFORM_ID) private platformId: Object) { }

  //appena caricato il layer della mappa, andiamo a inizializzarla con i dati ricevuti
  ngAfterViewInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      import('leaflet').then(module => {
        //estraggo la libreria vera, gestendo sia il caso sviluppo che produzione
        const L = module.default || module;

        let mapDiv: HTMLElement | null = document.getElementById("map");
        if (!mapDiv) {
          console.error("Impossibile trovare il div della mappa con id 'map'");
          return;
        }
        this.L = L;

        //previene errori se il componente viene ricaricato (es. hot-reload)
        if (this.map) {
          this.map.remove();
          this.map = null;
        }

        let bounds: any;
        
        //controllo se il poligono esiste e ha almeno un punto
        if (this.polygon && this.polygon.length > 0) {
          const latlngs = this.polygon.map((coord: number[]) => L.latLng(coord[0], coord[1]));
          bounds = L.latLngBounds(latlngs);
        } else {
          //fallback: Roma
          const fallbackCenter = L.latLng(41.9028, 12.4964);
          //creo un "bounds" fittizio per il fallback zoomando sul centro
          bounds = fallbackCenter.toBounds(100000); //100km di raggio
        }

        //inizializzo la mappa sul div
        this.map = L.map('map');

        //inizializzo subito il layer di evidenziazione che starà sopra a tutto (inizialmente vuoto)
        this.lightedLayers = L.layerGroup().addTo(this.map);

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
        //stile dinamico in base al valore di is_conforme (1 verde, 0 rosso)
        style: (feature: any) => {
          if(feature.properties && feature.properties.is_conforme == 1)
            return styles.conformi;
          else
            return styles.nonConformi;
        },
        //popup informativo per ogni edificio
        onEachFeature: (feature: any, layer: any) => {
          if(feature.properties) {
            const props = feature.properties;
            let popupContent = `<b>Edificio ID: ${props.id}</b><br>`;

            //dati edificio di OSM
            if (props.name) 
                popupContent += `<b>Nome:</b> ${props.name}<br>`;
            
            if (props.building && props.building !== 'yes') 
                popupContent += `<b>Tipo:</b> ${props.building}<br>`;
            
            //via e num. civico se presenti
            if (props['addr:street']) {
                popupContent += `<b>Indirizzo:</b> ${props['addr:street']}`;
                if (props['addr:housenumber']) popupContent += `, ${props['addr:housenumber']}`;
                popupContent += `<br>`;
            }

            if (props['building:levels']) 
                popupContent += `<b>Piani:</b> ${props['building:levels']}<br>`;
            
            if (props.amenity) 
                popupContent += `<b>Funzione:</b> ${props.amenity}<br>`;

            //separatore per evidenziare i dati di valutazione dell'algoritmo
            popupContent += `<hr style="margin: 5px 0; border-top: 1px solid #ccc;">`;

            //punteggi GreenRatingAlgorithm
            
            const colorTrees = props.visible_trees_count >= 3 ? 'green' : '#d9534f';
            popupContent += `Alberi visibili: <b style="color:${colorTrees}">${props.visible_trees_count}</b><br>`;

            const colorPark = props.score_300 === 1 ? 'green' : '#d9534f';
            popupContent += `Accesso Parco (300m): <b style="color:${colorPark}">${props.score_300 === 1 ? 'Sì' : 'No'}</b><br>`;

            const colorCover = props.coverage_percentage >= 30.0 ? 'green' : '#d9534f';
            popupContent += `Copertura Zona: <b style="color:${colorCover}">${props.coverage_percentage.toFixed(2)}%</b>`;

            layer.bindPopup(popupContent);
          }

          //gestione della selezione di un edificio da parte dell'utente
          layer.on('click', () => {

            //centro l'edificio selezionato
            const bounds = layer.getBounds();
            this.map.fitBounds(bounds, {
                padding: [100, 100],
                maxZoom: 19,
                animate: true,
                duration: 0.8
            });

            //nascondo gli altri edifici del layer
            if(this.resultsLayer)
                this.resultsLayer.eachLayer((l: any) => {
                    if(l !== layer)
                        l.setStyle({ opacity: 0, fillOpacity: 0, interactive: false }); 
                });
            
            //spengo le selezioni precedenti (se ce ne sono)
            if(this.lightedLayers)
                this.lightedLayers.clearLayers();

            //recupero i dati dell'edificio selezionato (id aree verdi e alberi)
            const greenAreaIdList = feature.properties.green_areas_id;
            const treesIdList = feature.properties.visible_trees_id;

            //se non ci sono elementi collegati o se il layer aree verdi non esiste, mi fermo per le aree verdi
            if(greenAreaIdList && greenAreaIdList.length > 0 && this.greenAreasLayer){

              //converto in stringhe per evitare problemi di confronto tra tipi diversi
              const greenAreaListString = greenAreaIdList.map((id: any) => String(id));

              //itero su tutte le aree verdi caricate
              this.greenAreasLayer.eachLayer((greenLayer: any) => {
                  const greenProps = greenLayer.feature.properties;
                  
                  //match id area verde con id collegati all'edificio selezionato
                  if(greenProps && greenAreaListString.includes(String(greenProps.id))) {
                      //creo un clone json usando la geometria originale e lo stile evidenziato
                      //in questo modo non si necessitano altri layer selezionati dall'utente per vedere evidenziati gli elementi collegati ad un edificio scelto
                      const clone = this.L.geoJSON(greenLayer.feature, {
                          style: styles.highlight
                      });
                      clone.addTo(this.lightedLayers);
                  }
              });
            }

            //se non ci sono elementi collegati o se il layer alberi non esiste, mi fermo per gli alberi
            if(treesIdList && treesIdList.length > 0 && this.treesLayer){

              //conversione in stringhe per evitare problemi di confronto tra tipi diversi
              const treeListString = treesIdList.map((id: any) => String(id));

              //itero su tutti gli alberi caricati
              this.treesLayer.eachLayer((treeLayer: any) => {
                  const treeProps = treeLayer.feature.properties;
                  if(treeProps && treeListString.includes(String(treeProps.id))) {
                      
                      //controllo se è un punto o Poligono (albero o bosco)
                      if(treeLayer.getLatLng){
                        const latlng = treeLayer.getLatLng();
                        const highlightCircle = this.L.circleMarker(latlng, {
                            radius: 8,
                            color: "#FFFF00",
                            weight: 3,
                            opacity: 1,
                            fillOpacity: 0.8,
                            fillColor: "#FFFF00"
                          });
                        highlightCircle.addTo(this.lightedLayers);
                      }
                      else{
                        const clone = this.L.geoJSON(treeLayer.feature, {
                          style: styles.highlight
                        });
                        clone.addTo(this.lightedLayers);
                      }
                  }
              });
            }
          });

          //quando viene chiuso il popup, ripristino la mappa
          layer.on('popupclose', () => {
            
            //visibilità edifici
            if (this.resultsLayer)
                this.resultsLayer.eachLayer((l: any) => {
                    this.resultsLayer.resetStyle(l);
                });

            //visibilità layer evidenziati
            if (this.lightedLayers)
                this.lightedLayers.clearLayers();
          });
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
        conformi: {
            color: "#00FF00", weight: 2, opacity: 1, fillOpacity: 0.3
        },
        nonConformi: {
            color: "#FF0000", weight: 2, opacity: 1, fillOpacity: 0.3
        },
        //tutti gli alberi in input
        trees: {
            color: "#0c0c0bff", weight: 1, opacity: 0.8, fillOpacity: 0.3
        },
        //tutte le aree verdi in input
        greenAreas: {
            color: "#286d0cff", weight: 1, opacity: 0.7, fillOpacity: 0.3
        },
        highlight: {
            color: "#FFFF00", weight: 4, opacity: 1, fillOpacity: 0.7
        }
    };
  }
}
