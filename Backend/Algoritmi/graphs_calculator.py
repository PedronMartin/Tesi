# ------------------------------------------------------------------------------
# Author: Martin Pedron Giuseppe
# Tesi "GreenRatingAlgorithm: un algoritmo per la valutazione automatica della regola 3-30-300 sul verde urbano di prossimità"
# University of Verona - Tesi di Laurea CdL in Informatica, a.a. 2024/2025
# Relatore: Prof. Davide Quaglia
# ------------------------------------------------------------------------------

"""
Calcola la regola 300 usando il grafo pedonale (distanza reale) delle città YOLO.
Questa funzione sostituisce il semplice calcolo geometrico (buffer) quando siamo in una città 'premium'.

@param edifici: GDF degli edifici (EPSG:4326)
@param aree_verdi: GDF delle aree verdi (EPSG:4326)
@param grafo: grafo NetworkX della città (già proiettato in metri da graphs_manager)
@return: GDF degli edifici arricchito con le colonne .... (NB, se aggiungiamo i metri reali, dobbiamo aggiungerla anche per la versione geometrica per coerenza)
"""

import networkx as nx
import osmnx as ox
from shapely.geometry import Polygon, MultiPolygon, LineString
import json
from shapely.geometry import mapping
import geopandas as gpd
import numpy as np

infinity_dist = -1

def calculate_pedestrian_path(edifici, aree_verdi, grafo):
    
    print("Avvio analisi pedonale.")
    
    #copio i GDF per lavorare in sicurezza
    copia_edifici = edifici.copy()
    copia_aree_verdi = aree_verdi.copy()


    #valore convenzionale usato per chi è oltre la distanza massima (cutoff). In caso di errore, pre-assegno a tutti questo valore.
    copia_edifici['distanza_pedonale'] = infinity_dist
    copia_edifici['percorso_pedonale'] = None

    #se non ho dati, ritorno subito
    if copia_edifici.empty or copia_aree_verdi.empty:
        print("Nessun edificio o area verde per il calcolo con grafi.")
        return copia_edifici

    #il grafo G è già in metri da graphs_manager. Proiettiamo anche edifici e aree verdi
    graph_crs = grafo.graph['crs']
    try:
        edifici_proj = copia_edifici.to_crs(graph_crs)
        verdi_proj = copia_aree_verdi.to_crs(graph_crs)
    except Exception as e:
        print(f"Errore proiezione CRS: {e}")
        return copia_edifici

    #prendiamo i centroidi delle aree verdi e troviamo il nodo del grafo più vicino a ognuno...#un punto ogni tot metri lungo il perimetro
    """
    Precedentemente, consideravamo il centroide dell'area verde come nodo di partenza/arrivo. Tuttavia, questo potrebbe non essere rappresentativo
    della reale accessibilità pedonale, specialmente per aree verdi che hanno un percorso pedonale interno tracciato da OSM (linee rosse tratteggiate).
    In quel caso, il nodo più vicino al centroide potrebbe essere DENTRO l'area verde, e quindi non rappresentare un punto di accesso pedonale reale.
    Per migliorare la mappatura, campioniamo punti ogni tot metri SUL perimetro dell'area verde, che è più probabile rappresentino punti di accesso
    pedonale reali. In questo modo, se c'è un percorso pedonale interno tracciato da OSM, i nodi più vicini saranno su quel percorso, ma non all'interno.
    """
    print("Mappatura aree verdi sul grafo.")
    green_boundary_points_x = []
    green_boundary_points_y = []
    sampling_distance = 40

    #itero sulle aree verdi
    for geom in verdi_proj.geometry:
        #uso MultiPolygon perchè alcuni parchi sono spezzati in sottopoligoni
        if isinstance(geom, MultiPolygon):
            polys = list(geom.geoms)
        else:
            polys = [geom]
        
        #itero sui sottopoligoni
        for poly in polys:

            #estraggo il perimetro e ne calcolo la lunghezza
            boundary = poly.exterior
            if boundary is None: continue
            length = boundary.length
            
            #se il perimetro è molto piccolo, prendo solo il centroide
            #il caso di perimetro piccolo è raro perchè abbiamo già filtrato area>=1ettaro, ma riguarda possibili sotto-porzioni di aree verdi grandi
            if length < sampling_distance:
                pt = poly.centroid
                green_boundary_points_x.append(pt.x)
                green_boundary_points_y.append(pt.y)
            #normalmente, campiono punti ogni tot metri lungo il perimetro
            else:
                distances = np.arange(0, length, sampling_distance)
                for d in distances:
                    #prende il punto a distanza d dal punto iniziale (mappato 0) lungo il perimetro
                    pt = boundary.interpolate(d)
                    green_boundary_points_x.append(pt.x)
                    green_boundary_points_y.append(pt.y)




    #osmnx.nearest_nodes vuole coordinate x e y separate
    green_nodes = ox.nearest_nodes(grafo, green_boundary_points_x, green_boundary_points_y)
    #per best-practice, elimino i nodi duplicati per ottimizzare Dijkstra. I nodi dei grafi potrebbero effettivamente ripetersi in quanto 
    #sono dove le strade si intersecano, e più aree verdi potrebbero essere mappate sullo stesso nodo.
    sources=list(set(green_nodes))

    #calcoliamo la distanza di TUTTI i nodi del grafo verso il set di nodi verdi in un colpo solo.
    #cutoff=350: ottimizzazione ---> l'algoritmo smette di cercare oltre i 350 metri.
    #mettiamo 350 invece di 300 per tolleranza sulla mappatura iniziale area_verde - nodo grafo
    #return: (distances, paths) dove paths è {target_node: [source, ..., target]}, e distances è {target_node: distance}.
    print("Calcolo percorsi minimi (Dijkstra).")
    try:
        distanze, percorsi = nx.multi_source_dijkstra(
            grafo, 
            sources, 
            weight='length',
            cutoff=350 
        )
    except Exception as e:
        print(f"Errore nel calcolo dei percorsi: {e}")
        return copia_edifici

    #mappo edifici sui nodi
    print("Mappatura edifici sul grafo.")
    edifici_centroids = edifici_proj.geometry.centroid
    edifici_nodes = ox.nearest_nodes(grafo, edifici_centroids.x, edifici_centroids.y)
    results_distances = []
    results_paths = []
    
    #ciclo i nodi degli edifici. Se sono nel dizionario delle distanze calcolate, aggiungo la distanza. Altrimenti significa che è > cutoff
    for node in edifici_nodes:
        dist = distanze.get(node, infinity_dist)
        results_distances.append(dist)

        #inizializzo il percorso a None
        path_json = None
        try:
            if(node in percorsi):
                lista = percorsi[node]
                #se il percorso esiste e ha almeno un nodo area verde e un nodo edificio (il minimo), lo salvo. Altrimenti, rimane None.
                if(len(lista) >= 2):
                    #estraggo coordinate di tutti i nodi e ci creo delle LineString che li collegano (Shapely)
                    coords = [(grafo.nodes[n]['x'], grafo.nodes[n]['y']) for n in lista]
                    linea = LineString(coords)

                    #proietto la linea in lat/lon (crs 4326) perché il frontend userà quello (uso GDF temporaneo)
                    linea_gdf = gpd.GeoDataFrame(geometry=[linea], crs=graph_crs)
                    linea_proiettata = linea_gdf.to_crs("EPSG:4326").geometry.iloc[0]

                    #converto in geojson string (usando mapping di shapely)
                    path_json = json.dumps(mapping(linea_proiettata))

        except Exception as e:
            print(f"Errore nel recupero del percorso per nodo {node}: {e}")
            
        #salvo risultato nella lista, che sia None o meno, per coerenza con le operazioni generali agli edifici
        results_paths.append(path_json)


    #aggiungo i risultati al GDF originale
    copia_edifici['distanza_pedonale'] = results_distances
    copia_edifici['percorso_pedonale'] = results_paths

    #statistiche per debug script
    soddisfatti = (copia_edifici['distanza_pedonale'] <= 300).sum()
    print(f"Risultato: {soddisfatti}/{len(copia_edifici)} edifici soddisfano la regola 300m con grafo.")

    #gestiamo la compilazione dei campi in comune per la regola nel main regola300, in modo da essere uniformi con la versione standard degli edifici.
    return copia_edifici