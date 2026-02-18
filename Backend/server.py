# Copyright 2026 [Martin Pedron Giuseppe]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#import
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
from osm2geojson import json2geojson
import geopandas as gpd
import pandas as pd
from Algoritmi.analizzatore_centrale import run_full_analysis
import logging
from shapely.geometry import Polygon
from graphsManager import graphs_manager

#costante in metri quadrati, 10000 m^2 = 1 ettaro
SOGLIA_MINIMA = 10000

# global var per riutilizzo poligono di input
input_polygon_shapely = None


#####################################################################################
############################Configurazione server Flask##############################
#####################################################################################
app = Flask(__name__)
# abilita CORS per permettere ad Angular (che è su un'altra porta) di chiamare l'API
CORS(app, resources={r"/api/*": {"origins": "*"}})

# configura il logging una sola volta per l'intera applicazione
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

##############################################################################
############################Funzioni di supporto##############################
##############################################################################

# funzione per costruire la query a Overpass API in base al tipo di dato richiesto
"""
la libreria python OSMnx è molto utile per lavorare con dati OSM, in particolare per un'analisi e visualizzazione avanzata,
ossia quello che abbiamo fatto con geopandas negli algoritmi. Come database da cui solo estrapolare i dati OSM,
Overpass API è più efficiente e veloce. Oltre a ciò, dava anche problemi di timeout e incompatibilità.
"""
def build_query(type, poly_str):

    # type 0 = edifici, type 1 = alberi, type 2 = aree verdi
    if type == 0:
        query = f"""
            [out:json][timeout:25];
            (
            way["building"](poly:"{poly_str}");
            relation["building"](poly:"{poly_str}");
            );
            out body;
            >;
            out skel qt;
        """
    elif type == 1:
        query = f"""
            [out:json][timeout:25];
            (
              /* ALBERI SINGOLI O IN FILA */
              node["natural"="tree"](poly:"{poly_str}");
              node["natural"="tree_row"](poly:"{poly_str}");
              way["natural"="tree_row"](poly:"{poly_str}");
              relation["natural"="tree_row"](poly:"{poly_str}");
              way["natural"="tree"](poly:"{poly_str}");
              relation["natural"="tree"](poly:"{poly_str}");
              
              /* BOSCHI E FORESTE */
              way["landuse"="forest"](poly:"{poly_str}");
              relation["landuse"="forest"](poly:"{poly_str}");
              way["natural"="wood"](poly:"{poly_str}");
              relation["natural"="wood"](poly:"{poly_str}");
            );
            out body;
            >;
            out skel qt;
        """
    elif type == 2:
        query = f"""
            [out:json][timeout:25];
            (
              /* PARCHI E GIARDINI */
              way["leisure"="park"](poly:"{poly_str}");
              relation["leisure"="park"](poly:"{poly_str}");
              way["leisure"="garden"](poly:"{poly_str}");
              relation["leisure"="garden"](poly:"{poly_str}");

              /* PRATI E AIUOLE */
              way["landuse"="grass"](poly:"{poly_str}");
              relation["landuse"="grass"](poly:"{poly_str}");
            );
            out body;
            >;
            out skel qt;
        """
    else:
        query = ""
    return query

"""
Questa funzione gestisce il caricamento degli alberi in base alla città. Se la città è 'Premium', ossia ricade dentro i confini noti,
carica gli alberi YOLO corrispondenti. Altrimenti, esegue la query Overpass anche per gli alberi (nello stesso modo di prima).
"""
def getTrees(city_name, buffered_polygon_3):
    #se la città non è 'Premium', eseguo la query Overpass
    if city_name is None:
        app.logger.info("Poligono di input fuori dai confini delle città YOLO. Uso OSM puro.")
        trees_query = build_query(1, buffered_polygon_3)
        return overpass_query(trees_query)
    #altrimenti, carico i corrispondenti alberi YOLO
    else:
        #TODO: integrare VersioneAlessio qui. Per ora faccio la stessa cosa del ramo if
        app.logger.info("Poligono di input dentro i confini di una città YOLO. Richiesta analisi premium effettuata.")
        trees_query = build_query(1, buffered_polygon_3)
        return overpass_query(trees_query)
    
"""
Questa funzione esegue la query Overpass API con gestione di endpoint alternativi in caso di sovraccarico o timeout.
"""
def overpass_query(query):

    # lista di endpoint alternativi per la richiesta (spesso sovvraccaricati)
    overpass_endpoints = [
         #il primo è il principale: reindirizza automaticamente al 3o e 4o, quindi lo provo subito, se non va riprovo singolarmente comunque i due endpoint
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://z.overpass-api.de/api/interpreter",
        "https://osm.hpi.de/overpass/api/interpreter"
    ]
    import time
    for url in overpass_endpoints:
        try:
            response = requests.post(url, query, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result
        except requests.exceptions.Timeout:
            app.logger.warning(f"Timeout su {url}, provo il prossimo endpoint...")
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            app.logger.warning(f"Warning: il seguente server è sovvraccarico o ha generato un errore ---> {url}: {e}")
            time.sleep(2)
    return None

# funzione per aumentare la dimensione del calcolo di una certa distanza, per comprendere gli elementi che rientrano nelle distanze ma non nel poligono
def increasePolygon(gdf_input, rule):
    
    try:
        # definisco la dimensione del buffer in metri in base alla regola
        if rule == 300:
            bufferSize = 300    # buffer di 300 metri
        elif rule == 3:
            bufferSize = 45     # buffer di 45 metri
        
        # proietto in CRS metrico (UTM 32N), calcola buffer, riproietta in lat/lon
        gdf_proj = gdf_input.to_crs("EPSG:32632")
        gdf_proj_buffered = gdf_proj.buffer(bufferSize)
        gdf_buffered_unproj = gdf_proj_buffered.to_crs("EPSG:4326")

        # estraggo le coordinate (lon, lat) dal poligono bufferizzato
        buffered_poly_geom = gdf_buffered_unproj.geometry.iloc[0]
        
        # converto in stringa "lat lon..." per Overpass
        return " ".join([f"{lat} {lon}" for lon, lat in buffered_poly_geom.exterior.coords])

    except Exception as e:
        app.logger.warning(f"Impossibile creare il sovvra-Buffer per la regola 300 o 3: {e}. Uso il poligono di input.")
        # Fallback: usa il poligono originale se il buffer fallisce
        return None
    
"""
    Questa funzione prende i dati GeoJSON e "spacchetta" la colonna 'tags' (che è un dizionario)
    in colonne separate (es. 'natural', 'landuse', ecc.).
    Si è resa necessaria questa funzione dal momento che abbiamo aggiunto diversi elementi all'interno
    delle stesse richieste a Overpass. Fin tanto che ogni query era per un singolo tipo di elemento, es. alberi,
    non c'era bisogno di questa funzione, in quanto ogni GDF aveva una colonna 'tags' con un solo tipo di chiave e
    il convertitore di GeoPandas lo "capiva" da solo, trasformandolo in una colonna separata.
    Ora che abbiamo più tipi di elementi (es. alberi singoli, alberi in fila, boschi, ecc.),
    la colonna 'tags' contiene più chiavi diverse, e GeoPandas non riesce a gestirla da solo.
    Quindi questa funzione usa pandas.json_normalize per "spacchettare" i dizionari in colonne.
"""
def unpack_gdf_features(geojson_data, crs="EPSG:4326"):
    
    #gestisco dati vuoti o senza colonna features
    if not geojson_data or not geojson_data.get("features"):
        return gpd.GeoDataFrame(geometry=[], crs=crs)

    #creo il GDF. Ora ha una colonna 'tags' che è un dict
    gdf = gpd.GeoDataFrame.from_features(geojson_data["features"], crs=crs)

    #se la colonna tags esiste gli elementi non sono uniformi e si prosegue con l'espansione
    if 'tags' not in gdf.columns:
        return gdf

    #estraggo la colonna tags. 
    #fillna({}) sostituisce tutti i 'None' con un dizionario vuoto {}
    tags_series = gdf['tags'].fillna({})

    #json_normalize converte i dizionari in colonne separate (es. 'geometry', 'type', 'id')
    tags_df = tags_series.apply(pd.Series)

    #elimino colonna tags che non serve più
    original_cols_to_keep = gdf.columns.drop('tags')

    #rimuovo le colonne in tags_df che sono duplicati
    cols_to_drop_from_tags = original_cols_to_keep.intersection(tags_df.columns)
    safe_tags_df = tags_df.drop(columns=cols_to_drop_from_tags)

    #ora il join è sicuro, perché non ci sono colonne sovrapposte
    gdf = gdf.drop(columns=['tags']).join(safe_tags_df)
    return gdf




###############################################################
############################MAIN###############################
###############################################################

# Endpoint per l'API
@app.route('/api/greenRatingAlgorithm', methods=['POST'])

# TODO: forse ha senso esporre le sotto funzioni per il calcolo di solo alcune regole?
# TODO: manca la heatMap: da aggiungere qui o nel client?
# TODO: aggiungere autenticazione API key per sicurezza?
# TODO: aggiungere limitazioni di rate limiting per evitare abusi?
# TODO: aggiungere sistema crs dinamico per rendere l'applicazione globale (il sistema metrico è lo stesso per tutti?)
def greenRatingAlgorithm():

    try:
        #ricezione dei dati da client
        dati_ricevuti = request.get_json()
        polygon = dati_ricevuti.get('polygon')
        
        #query per Overpass API
        if(polygon):

            """
            Concateno i punti del poligono in una stringa formattata per le query Overpass;
            da client arrivano in formato json come lista di liste [[lat, lon], [lat, lon], ...],
            mentre a Overpass dobbiamo mandare "lat lon lat lon ...".
            La seconda riga lascia il poligono in formato lista di tuple [(lon, lat), (lon, lat), ...],
            ma invertendo lat e lon, in quanto Shapely Polygon le utilizza così (simile a Leaflet).
            Questa seconda rappresentazione serve alla funzione che aumenta il poligono con il buffer per la Regola 300 e 3, 
            eseguita prima delle query Overpass, in quanto sono regole cui calcolo necessita anche degli elementi
            fuori dal poligono di input.
            """
            formatted_poly = " ".join([f"{lat} {lon}" for lat, lon in polygon])
            #Shapely Polygon vuole coordinate [(lon, lat)], quindi invertite rispetto a prima (simile a Leaflet)
            poly_coords = [(lon, lat) for lat, lon in polygon]

            #creo anche un GDF del poligono in input che servirà alla regola 30 per il calcolo dell'area totale
            #inoltre, lo salvo in globale perchè lo riusiamo anche per il graphs_manager
            try:
                input_polygon_shapely = Polygon(poly_coords)
                polygon_gdf = gpd.GeoDataFrame(
                    [{'geometry': input_polygon_shapely}],
                    crs="EPSG:4326"
                    )
            except Exception as e:
                app.logger.error(f"Errore creazione GDF poligono di input: {e}")
                return jsonify({'errore': 'Poligono di input non valido.'}), 400

            #aumento il poligono in base alla regola
            buffered_polygon_300 = increasePolygon(polygon_gdf, 300)
            buffered_polygon_3 = increasePolygon(polygon_gdf, 3)

            # controllo messo qui per fallback in caso di errore nel buffer con poly_str
            if not buffered_polygon_300 or not buffered_polygon_3:
                app.logger.warning(f"Impossibile creare la sovrapposizione per la regola 300 o 3. Uso il poligono di input.")
                buffered_polygon_300 = formatted_poly
                buffered_polygon_3 = formatted_poly
                app.logger.info(f"Impossibile gonfiare poligono di input: buffer settati esattamente come l'input. Output potrebbe essere incompleto.")

            #analizzo il poligono in input: se la zona richiesta è nei confini dei dati YOLO/OSMnx oppure se proseguire con il modello OSM puro
            #lascio None come default se non trovato; runFullAnalysis gestisce il None per usare OSM puro
            #graphsManager è un singleton, quindi lo creo una volta sola durante l'importazione e lo riuso (l'instanza è graphs_manager)
            city_name = graphs_manager.get_city_from_polygon(input_polygon_shapely)
            grafo = graphs_manager.get_graph(city_name) if city_name else None

            #chiamo la funzione getTrees, che sulla base della città carica gli alberi YOLO, altrimenti esegue la query Overpass
            alberi = getTrees(city_name, buffered_polygon_3)
            
            # costruisco le query e le eseguo
            buildings_query = build_query(0, formatted_poly)
            edifici = overpass_query(buildings_query)
            if edifici is None:
                return jsonify({'errore': 'Nessun edificio selezionato'}), 504
            green_areas_query = build_query(2, buffered_polygon_300)
            aree_verdi = overpass_query(green_areas_query)
        else:
            # http 400 bad request
            return jsonify({'errore': 'Dati geometrici mancanti o non validi'}), 400

        # conversione dei dati da OSM a GeoDataFrame
        try:
            geojson_buildings = json2geojson(edifici)
            edifici = unpack_gdf_features(geojson_buildings)

            geojson_trees = json2geojson(alberi)
            alberi = unpack_gdf_features(geojson_trees)
            
            geojson_green_areas = json2geojson(aree_verdi)
            aree_verdi = unpack_gdf_features(geojson_green_areas)

        except Exception as e:
            return jsonify({'errore': f'Errore nella conversione in GeoDataFrame dei dati OSM: {e}'}), 500
        
        # pulizia dati Edifici
        try:
            """
            Manteniamo solo le colonne utili per l'analisi e scartiamo il resto per ridurre l'overhead di calcolo.
            In questo modo evitiamo anche problemi di serializzazione in GeoJSON dovuti a tipi di dati non standard.
            Filtriamo quindi solo le colonne che esistono effettivamente nel GDF (proiezione) e che verranno visualizzate nel frontend.
            OSM usa '@id', ma noi vogliamo lavorare pulito con 'id' (utile anche per il frontend), quindi rinominiamo per tutti i GDF.
            """
            if '@id' in edifici.columns:
                edifici = edifici.rename(columns={'@id': 'id'})
            colonne_utili = ['geometry', 'id', 'building', 'name', 'addr:street', 'addr:housenumber', 'building:levels', 'amenity']
            cols_to_keep = [c for c in colonne_utili if c in edifici.columns]
            edifici = edifici[cols_to_keep].copy()

            if '@id' in alberi.columns:
                alberi = alberi.rename(columns={'@id': 'id'})
                
            if '@id' in aree_verdi.columns:
                aree_verdi = aree_verdi.rename(columns={'@id': 'id'})

            """
            Proiettiamo le aree verdi nel sistema metrico e scartiamo quelle troppo piccole ai fini del calcolo.
            Inizialmente questa operazione era fatta all'interno della regola 300, ma spostandola qui evitiamo di passare dati inutili alla regola,
            riducendo il carico computazionale.
            Inoltre, eseguendo qui questa parte, evitiamo di mandare al frontend aree verdi che non sono state usate dal calcolo.
            Attenzione: questa parte normalmente genererebbe un warning da parte di Pandas senza la copia esplicita (.copy()),
            in quanto si sta tentando di modificare un DataFrame filtrato. L'uso di .copy() previene questo warning creando una copia indipendente.
            """
            if not aree_verdi.empty:
                aree_verdi_metriche = aree_verdi.to_crs("EPSG:32632")
                mask_grandi = aree_verdi_metriche.geometry.area >= SOGLIA_MINIMA
                aree_verdi = aree_verdi[mask_grandi].copy()

        except Exception as e:
            return jsonify({'errore': f'Errore nella pulizia dei dati: {e}'}), 500

        # esecuzione degli algoritmi
        result, errori = run_full_analysis(edifici, alberi, aree_verdi, polygon_gdf, city_name, grafo)

        # definiamo un GeoJSON vuoto standard da usare come fallback
        empty_geojson_fallback = '{"type": "FeatureCollection", "features": []}'

        # preparazione della risposta in formato GeoJSON (con gestione accurata dei casi particolari)
        alberi_geojson = alberi.to_json() if not alberi.empty else empty_geojson_fallback
        aree_verdi_geojson = aree_verdi.to_json() if not aree_verdi.empty else empty_geojson_fallback

        if result is None or result.empty:
             risultati_geojson = '{"type": "FeatureCollection", "features": []}'
        elif not hasattr(result, 'to_json'):
             #se non è GDF, converti a stringa di errore (improbabile, ma sicuro)
             app.logger.error("Il risultato non è un oggetto serializzabile!")
             risultati_geojson = '{"type": "FeatureCollection", "features": []}'
        else:
             #serializzazione del GDF (Se fallisce qui, il problema è nel GDF stesso)
             risultati_geojson = result.to_json()

        #costruzione del messaggio in base alla presenza di errori non bloccanti
        if errori:
            flag = False
            messaggio = "Analisi completata con errori non bloccanti delle seguenti regole: " + "; ".join(errori)
        else:
            flag = True
            messaggio = "Analisi completata con successo."

        risultato = {
            'EsecuzionePositiva': flag,
            'messaggio': messaggio,
            'alberi': alberi_geojson,
            'aree_verdi': aree_verdi_geojson,
            'risultati': risultati_geojson
        }

        return jsonify(risultato), 200

    except Exception as e:
        # logga l'errore completo per il debug lato server
        app.logger.error(f"Errore durante l'elaborazione: {e}")
        # invia un messaggio di errore generico ad Angular
        return jsonify({'errore': f'Errore del server: {str(e)}'}), 500

if __name__ == '__main__':
    # Esegue il server solo su localhost per sicurezza durante lo sviluppo.
    app.run(host='127.0.0.1', port=5000, debug=True)
    # Esegue il server su tutte le interfacce, così anche altri utenti possono collegarsi
    # app.run(host='0.0.0.0', port=5000, debug=True)
    pass