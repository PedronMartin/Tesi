# ------------------------------------------------------------------------------
# Author: Martin Pedron Giuseppe
# Tesi "GreenRatingAlgorithm: un algoritmo per la valutazione automatica della regola 3-30-300 sul verde urbano di prossimità"
# University of Verona - Tesi di Laurea CdL in Informatica, a.a. 2024/2025
# Relatore: Prof. Davide Quaglia
# ------------------------------------------------------------------------------

"""
Script per il download e la pulizia dei grafi stradali pedonali da OpenStreetMap tramite OSMnx,
utilizzando i confini delle città definiti nel file geojson city_boundaries.json.
I grafi vengono salvati in formato GraphML nella cartella di output specificata.
Ogni volta che si vuole aggiungere una città, basta aggiungerla al file city_boundaries.json con i dati corretti
e rieseguire questo script. Porre attenzione al sistema di coordinate (CRS) usato nei confini (deve essere EPSG:4326).
Le città già presenti non verranno riscaricate.
"""


import osmnx as ox
import networkx as nx
import geopandas as gpd
import os
import numpy as np
from shapely.geometry import LineString

#I/O
inputFile = "./../city_boundaries.json"
outputFolder = "./"

"""
Genera un ID intero univoco basato sulle coordinate.
Arrotonda a 7 cifre per coerenza con gli id originali del grafo, crea una stringa unica e ne calcola l'hash, restituendo un intero positivo.
Questo sistema serve a gestire casi estremi di errori negli id dei nodi che aggiungiamo, in quanto gli id originali non seguono una struttura coerente,
per tanto non è possibile aggiungerne senza incappare in errori typografici o di conversione (es: 3, "3", 3.0, "3.0" sono tutti lo stesso nodo).
"""
def get_node_id_from_coords(x, y):
    val_str = f"{x:.7f}_{y:.7f}"
    return abs(hash(val_str))

"""
    I grafi scaricabili da OSMnx spesso contengono dati sporchi o inutili.
    Questa funzione serve a pulire i dati, mantenendo solo la rete stradale scelta principale,
    rimuovendo vicoli ciechi isolati e pezzi di grafo non connessi.
    Inoltre, gestisce versioni diverse di OSMnx.
"""
def get_largest_component_safe(G):
    #strongly serve a mantenere l'orientamento delle strade, anche se con le pedonali non dovrebbe essere necessario
    return ox.truncate.largest_component(G, strongly=True)

"""
Funzione ausiliaria per addensare il grafo con un maggiore numero di nodi.
I nodi del grafo stradale/pedonale di OSMnx possono essere molto distanti tra loro, soprattutto su strade rettilinee lunghe.
Questo rende l'individuazione dello 'nearest node' molto impreciso, con errori di decine di metri. Spezzare gli archi lunghi in segmenti più corti migliora
drasticamente la precisione, riducendo l'errore a pochi metri.
La funzione aggiunge nodi intermedi ogni 'max_distance' metri lungo gli archi più lunghi di questa soglia.
"""
def densify_graph(G, max_distance=20):

    G_dense = G.copy()
    
    #itero su una lista statica degli archi perché modificheremo il grafo
    for u, v, data in list(G_dense.edges(data=True)):

        #inizializzo parametri
        length = 0.0
        line = None
        
        #se esiste la geometria, la uso per calcolare la lunghezza. Altrimenti, assumo linea dritta tra i nodi (sulle prime 4 città è capitato per Genova).
        if 'geometry' in data:
            line = data['geometry']
            length = line.length
        else:
            #calcolo lunghezza se non c'è geometria esplicita (linea dritta)
            p_u = G_dense.nodes[u]
            p_v = G_dense.nodes[v]
            line = LineString([(p_u['x'], p_u['y']), (p_v['x'], p_v['y'])])
            length = data.get('length', line.length)

        #se l'arco è più lungo della soglia, lo spezziamo
        if length > max_distance:
            G_dense.remove_edge(u, v)
            
            #calcolo il numero di segmenti da aggiungere
            num_segments = int(np.ceil(length / max_distance))
            
            #genero punti intermedi lungo la linea
            points = [line.interpolate(i/float(num_segments), normalized=True) 
                      for i in range(1, num_segments)]
            
            prev_node = u
            for point in points:
                    #genero id univoco basato sulle coordinate hashate
                    new_node_id = get_node_id_from_coords(point.x, point.y)
                    
                    G_dense.add_node(new_node_id, x=point.x, y=point.y)
                    
                    new_edge_data = data.copy()
                    if 'geometry' in new_edge_data:
                        del new_edge_data['geometry']
                    new_edge_data['length'] = length / num_segments
                    
                    G_dense.add_edge(prev_node, new_node_id, **new_edge_data)
                    prev_node = new_node_id
            
            #collego l'ultimo nodo al nodo finale v
            new_edge_data = data.copy()
            if 'geometry' in new_edge_data:
                del new_edge_data['geometry']
            new_edge_data['length'] = length / num_segments
            G_dense.add_edge(prev_node, v, **new_edge_data)

    return G_dense

#main function: scarica i grafi pedonali per ogni città, li pulisce e li salva in formato GraphML
def download_graphs():
    
    #assunta cartella output già esistente

    #leggo confini nel file di input
    try:
        cities_gdf = gpd.read_file(inputFile)
    except Exception as e:
        print(f"Errore apertura file: {e}")
        return

    #ciclo le città presenti
    for idx, row in cities_gdf.iterrows():
        city_name = row.get('city_name', f"City_{idx}")
        geometry = row.geometry

        #il buffer(0) risolve il 99% dei problemi dovuti a geometrie sporche (self-intersections o altri errori generati da Shapely)
        if not geometry.is_valid:
            print(f"Geometria invalida per {city_name}. Provo fix automatico.")
            geometry = geometry.buffer(0)
        
        #nome di salvataggio sicuro
        safe_name = city_name.replace(" ", "_").replace(",", "")
        file_path = os.path.join(outputFolder, f"{safe_name}.graphml")
        
        print(f"Elaborazione: {city_name}")
        
        #se esiste già per X città, salto
        if os.path.exists(file_path):
            print(f"File già esistente. Non ricalcolo.")
            continue
            
        try:
            
            #download grafo pedonale. La flag simplify riduce i nodi inutili
            print("Download grafo pedonale da OSM (attendere)")
            G = ox.graph_from_polygon(geometry, network_type='walk', simplify=True)

            #proiezione in sistema metrico
            G_proj = ox.project_graph(G)
            
            #aggiungo nodi sui rettilinei
            G_dense = densify_graph(G_proj, max_distance=20)
            
            #riproietto indietro crs
            G_final = ox.project_graph(G_dense, to_crs="EPSG:4326")

            #ricalcolo l'id hash per TUTTI i nodi (anche quelli originali del grafo)
            #così siamo sicuri al 100% che siano tutti interi dello stesso tipo
            mapping = {}
            for n, data in G_final.nodes(data=True):
                try:
                    x = float(data['x'])
                    y = float(data['y'])
                    new_id = get_node_id_from_coords(x, y)
                    mapping[n] = int(new_id)
                except Exception as e:
                    print(f"Errore convertendo nodo {n}: {e}")
                    #se proprio fallisce uso un hash
                    mapping[n] = abs(hash(str(n)))
            
            #rinomino tutti i nodi nel grafo con i nuovi id puliti
            G_final = nx.relabel_nodes(G_final, mapping)

            """
            BUG FIX IMPORTANTE: data sanifications.
            Durante le operazioni di proiezione (ox.project_graph) e densificazione, gli attributi originari dei nodi (come 'street_count')
            subiscono spesso un casting implicito da Integer a Float (es. 3 -> 3.0) a causa della gestione dei valori mancanti (NaN) nei nuovi nodi
            creati o delle operazioni vettoriali di Pandas/NumPy.
            Quando il grafo viene salvato in graphml, questi valori vengono serializzati come stringhe (es. "3.0").
            Al momento del ricaricamento nel backend, OSMnx tenta di convertire queste stringhe in int, ma Python solleva un ValueError per stringhe 
            contenenti decimali (int("3.0") -> Crash).
            Il seguente blocco normalizza forzatamente questi attributi, riportandoli a interi puri o rimuovendoli se corrotti.
            """
            for n, data in G_final.nodes(data=True):
                if 'street_count' in data:
                    try:
                        data['street_count'] = int(float(data['street_count']))
                    except:
                        del data['street_count']
                
                #normalizzo coordinate
                if 'x' in data: data['x'] = float(data['x'])
                if 'y' in data: data['y'] = float(data['y'])
            
            #pulisco dati con funzione ausiliaria predefinita: rimuove pezzi di grafo non connessi e/o vicoli ciechi isolati
            G_clean = get_largest_component_safe(G_final)
            
            #salvo in file
            print(f"Salvataggio in {safe_name}.graphml")
            ox.save_graphml(G_clean, file_path)
            
        except Exception as e:
            print(f"ERRORE elaborando {city_name}: {e}")
            raise e 

#MAIN
if __name__ == "__main__":
    download_graphs()

"""
COPIA E INCOLLA LA PARTE QUI SOTTO PER VEDERE I GRAFI USATI SU OVERPASS TURBO
/*
  Query per visualizzare la "strada percorribile da un pedone" (simile a OSMnx network_type='walk' che scarichiamo per il progetto).
  Include sia i sentieri puri che le strade urbane percorribili a piedi.
*/
[out:json][timeout:25];

(
  //include: marciapiedi, sentieri, ciclabili, scalinate, zone pedonali, strade residenziali condivise
  way["highway"~"footway|path|steps|pedestrian|living_street|track|cycleway"]({{bbox}});

  //include: residenziali, di servizio, terziarie, secondarie, primarie.
  //esclude: Autostrade, superstrade e strade dove il tag 'foot' è 'no' (vietato).
  way["highway"~"residential|service|unclassified|tertiary|secondary|primary"]
     ["highway"!~"motorway|motorway_link|trunk|trunk_link"] // Niente autostrade
     ["foot"!~"no"] // Niente strade vietate ai pedoni
     ({{bbox}});
);

out body;
>;
out skel qt;
"""