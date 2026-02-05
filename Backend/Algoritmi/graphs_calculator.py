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

def calculate_pedestrian_path(edifici, aree_verdi, grafo):
    
    print("Avvio analisi pedonale.")
    
    #copio i GDF per lavorare in sicurezza
    copia_edifici = edifici.copy()
    copia_aree_verdi = aree_verdi.copy()


    #valore convenzionale usato per chi è oltre la distanza massima (cutoff). In caso di errore, pre-assegno a tutti questo valore.
    infinity_dist = 999
    copia_edifici['distanza_pedonale'] = infinity_dist

    #se non ho dati, ritorno subito
    if copia_edifici.empty or copia_aree_verdi.empty:
        print("Nessun edificio o area verde per il calcolo.")
        return copia_edifici

    #il grafo G è già in metri da graphs_manager. Proiettiamo anche edifici e aree verdi
    graph_crs = grafo.graph['crs']
    try:
        edifici_proj = copia_edifici.to_crs(graph_crs)
        verdi_proj = copia_aree_verdi.to_crs(graph_crs)
    except Exception as e:
        print(f"Errore proiezione CRS: {e}")
        return copia_edifici

    #prendiamo i centroidi delle aree verdi e troviamo il nodo del grafo più vicino a ognuno
    print("Mappatura aree verdi sul grafo.")
    centroids = verdi_proj.geometry.centroid
    #osmnx.nearest_nodes vuole coordinate x e y separate
    green_nodes = ox.nearest_nodes(grafo, centroids.x, centroids.y)
    #per best-practice, elimino i nodi duplicati per ottimizzare Dijkstra. I nodi dei grafi potrebbero effettivamente ripetersi in quanto 
    #sono dove le strade si intersecano, e più aree verdi potrebbero essere mappate sullo stesso nodo.
    sources=list(set(green_nodes))

    #calcoliamo la distanza di TUTTI i nodi del grafo verso il set di nodi verdi in un colpo solo.
    #cutoff=350: ottimizzazione ---> l'algoritmo smette di cercare oltre i 350 metri.
    #mettiamo 350 invece di 300 per tolleranza sulla mappatura iniziale area_verde - nodo grafo
    #la funzione ritorna una mappa {nodo: distanza}
    print("Calcolo percorsi minimi (Dijkstra).")
    try:
        distanze_calcolate = nx.multi_source_dijkstra_path_length(
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
    results = []
    
    #ciclo i nodi degli edifici. Se sono nel dizionario delle distanze calcolate, aggiungo la distanza. Altrimenti significa che è > cutoff
    for node in edifici_nodes:
        dist = distanze_calcolate.get(node, infinity_dist)
        results.append(dist)

    #aggiungo i risultati al GDF originale
    copia_edifici['distanza_pedonale'] = results

    #statistiche per debug script
    soddisfatti = (copia_edifici['distanza_pedonale'] <= 300).sum()
    print(f"Risultato: {soddisfatti}/{len(copia_edifici)} edifici soddisfano la regola 300m.")

    #gestiamo la compilazione dei campi in comune per la regola nel main regola300, in modo da essere uniformi con la versione standard degli edifici.
    return copia_edifici