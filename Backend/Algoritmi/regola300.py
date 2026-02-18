# ------------------------------------------------------------------------------
# Author: Martin Pedron Giuseppe
# Tesi "GreenRatingAlgorithm: un algoritmo per la valutazione automatica della regola 3-30-300 sul verde urbano di prossimità"
# University of Verona - Tesi di Laurea CdL in Informatica, a.a. 2024/2025
# Relatore: Prof. Davide Quaglia
# ------------------------------------------------------------------------------

"""
    Algoritmo per il calcolo della Regola 300:
        Il programma verifica, per ogni edificio, se è presente un'area verde pubblica nel raggio di 300 metri.
        Il calcolo si basa su una "unione spaziale" tra gli edifici e le aree verdi.
            1. Creazione del buffer: per ogni edificio, viene creato un'area di 300 metri (un "buffer"). Questo buffer rappresenta la zona di ricerca.
            2. Unione spaziale (Spatial Join): i buffer degli edifici vengono uniti alle geometrie delle aree verdi.
                Un edificio supera il test se il suo buffer interseca almeno un'area verde.
            3. Attribuzione del punteggio: ogni edificio che interseca un'area verde riceve un punteggio di 1, mentre gli altri ricevono 0.

        NOTE:
            1) E' stato implementato un filtro per considerare solo le aree verdi con superficie maggiore di una soglia minima;
            2) il buffer di 300 metri parte in automatico dal perimetro dell'edificio grazie a geopandas;
            3) considerato che farlo senza Leaflet ha un costo computazionale importante, e non c'è conflitto se li teniamo separati, optiamo per avere
                una divisione tra il backend che valuta la regola (linea d'aria) e il frontend che mostra la realtà (percorso), chiaramente maggiore del primo;
                siccome è stato deciso di avere un precalcolo massiccio nel backend, con salvataggio in un DB, l'aggiunta del percorso pedonale con OSMXML/Graphhopper
                andrebbe fatta in un secondo momento come arricchimento del dato già calcolato;
            4) la query delle aree verdi è stata appositamente gonfiata oltre il poligono dell'utente;
"""

# importazioni
import pandas as pd
import geopandas as gpd
import logging
from .graphs_calculator import calculate_pedestrian_path, infinity_dist

#definisco il logger globale
logger = logging.getLogger("regola300")

def run_rule_300(edifici, aree_verdi, city_name, grafo):

    # controllo input (in caso di errore, restituisco edifici con score 0 e lista vuota)
    if edifici.empty or aree_verdi.empty:
        logger.warning("Dati insufficienti per il calcolo. Assicurati che i GeoDataFrame non siano vuoti.")
        edifici = _return_default(edifici)
        return edifici
    
    """
    Chiamiamo l'algoritmo base, in modo da avere allineato l'incolonnamento dei risultati (score_300, green_areas_id, distanza_pedonale) per tutti.
    inoltre, all'algoritmo con grafo, più pesante, daremo come input solo gli edifici candidati (ovvero quelli che hanno score_300=1)
    in modo da ottimizzare il calcolo pedonale solo su quelli che hanno già superato il test geometrico.
    infinity_dist viene casterizzato a float per coerenza, perchè i risultati con grafi reali saranno in metri e con decimali
    """
    logger.info("Calcolo regola 300 con metodo geometrico.")
    edifici_processati = calculate_buffer_method(edifici, aree_verdi)
    edifici_processati['distanza_pedonale'] = float(infinity_dist)
    edifici_processati['percorso_pedonale'] = None

    if city_name and grafo is not None:
        logger.info(f"Calcolo regola 300 con grafi pedonali per la città: {city_name}")
        candidati = edifici_processati[edifici_processati['score_300'] == 1].copy()
        if not candidati.empty:
            #ritorna una serie con id e distanze
            edifici_ad_accesso_diretto = remove_direct_access(candidati, aree_verdi, grafo.graph['crs'])

            #aggiorno il gdf principale con i risultati degli edifici ad accesso diretto
            if not edifici_ad_accesso_diretto.empty:
                ids_diretti = edifici_ad_accesso_diretto.index
                edifici_processati.loc[ids_diretti, 'distanza_pedonale'] = edifici_ad_accesso_diretto
            #indice vuoto nel caso di nessun edificio ad accesso diretto
            else:
                ids_diretti = pd.Index([])

            #prendo i candidati totali (buffer 300) MENO quelli ad accesso diretto ad un area verde
            ids_da_calcolare = candidati.index.difference(ids_diretti)
            if not ids_da_calcolare.empty:
                candidati_finali = edifici_processati.loc[ids_da_calcolare].copy()
                #uso la funzione update di pandas per aggiornare solo la colonna 'distanza_pedonale', mantenendo intatti gli altri campi e gli indici
                edifici_grafo = calculate_pedestrian_path(candidati_finali, aree_verdi, grafo)
                #check di sicurezza sui percorsi
                if 'percorso_pedonale' not in edifici_processati.columns:
                    edifici_processati['percorso_pedonale'] = None
                edifici_processati.loc[ids_da_calcolare, 'distanza_pedonale'] = edifici_grafo['distanza_pedonale'].values
                edifici_processati.loc[ids_da_calcolare, 'percorso_pedonale'] = edifici_grafo['percorso_pedonale'].values

            #identifico tra i candidati chi ha fallito il test pedonale
            failed_mask = (edifici_processati.index.isin(candidati.index)) & \
                          ((edifici_processati['distanza_pedonale'] > 300) | 
                           (edifici_processati['distanza_pedonale'] < 0))
            
            #svuoto tutti i campi di chi ha fallito, mantenendo però la distanza pedonale che può comunque essere interessante
            if failed_mask.any():
                edifici_processati.loc[failed_mask, 'score_300'] = 0
                edifici_processati.loc[failed_mask, 'percorso_pedonale'] = None
                indici_falliti = edifici_processati[failed_mask].index
                empty_series = pd.Series([[] for _ in range(len(indici_falliti))], index=indici_falliti)
                edifici_processati.loc[failed_mask, 'green_areas_id'] = empty_series
                """
                Per la lista id non si poteva fare assegnazione diretti di lista vuota in quanto pandas non lo permette sempre.
                Generava un errore del tipo: Must have equal len keys and value when setting with an ndarray.
                """

            #per coerenza, confermo a 1 chi ha passato
            passed_mask = (edifici_processati.index.isin(candidati.index)) & \
                          ((edifici_processati['distanza_pedonale'] <= 300) & 
                           (edifici_processati['distanza_pedonale'] >= 0))
            edifici_processati.loc[passed_mask, 'score_300'] = 1

    return edifici_processati

def calculate_buffer_method(edifici, aree_verdi):

    #proietto i CRS in EPSG:32632 per calcoli metrici
    try:
        if edifici.crs is None:
            edifici.set_crs("EPSG:4326", inplace=True)
        if aree_verdi.crs is None:
            aree_verdi.set_crs("EPSG:4326", inplace=True)
        edifici_proj = edifici.to_crs("EPSG:32632")
        aree_verdi_proj = aree_verdi.to_crs("EPSG:32632")

        """
            Creo un buffer di 300 metri intorno ad ogni edificio:
                - creo una copia del GeoDataFrame degli edifici per non modificare l'originale;
                - aggiungo una colonna 'original_index' per tenere traccia dell'indice originale degli edifici;
                - creo il buffer di 300 metri sulla colonna 'geometry' ---> sostituisce il campo geometria con geometry + buffer
        """
        edifici_buffer = edifici_proj.copy()
        edifici_buffer['geometry'] = edifici_buffer.geometry.buffer(300)
        edifici_buffer['original_index'] = edifici_buffer.index

        #unione spaziale tra i buffer degli edifici e le aree verdi (inner è join base, predicate 'intersects' controlla l'intersezione)
        join_result = gpd.sjoin(edifici_buffer, aree_verdi_proj, how="inner", predicate='intersects')

        #creo copia per il risultato finale, inizializzo colonna punteggio a 0 e inizializzo la colonna degli ID come liste vuote
        risultato_finale = edifici.copy()
        risultato_finale['score_300'] = 0
        risultato_finale['green_areas_id'] = [[] for _ in range(len(risultato_finale))]

        #se ci sono intersezioni, si assegna loro il punteggio senza ripetere gli indici originali
        if not join_result.empty:

            #flag SI/NO all'intersezione
            soddisfatti_index = join_result['original_index'].unique()
            risultato_finale.loc[soddisfatti_index, 'score_300'] = 1

            """
            Eseguo un'aggregazione degli ID. Raggruppo per edificio (original_index) e metto gli ID delle aree verdi ('id') in una lista.
            NB: 'id_right' è il nome standard che sjoin dà all'indice/id del secondo dataframe se c'è conflitto (dato che è convensione OSM usare @id
            per cui sia edifici che aree verdi avrebbero lo stesso tipo di id, e sjoin le rinominerebbe).
            Nel primo if, gestiamo il caso in cui ci sia conflitto e l'id delle aree verdi sia rimasto semplicemente '@id' dopo il cambio del server.
            """            
            colonna_target = 'id_right'
            
            #per ogni edificio, creo lista degli id trovati
            if colonna_target in join_result.columns:
                temp = join_result.groupby('original_index')[colonna_target].apply(list)
                #assegno liste con gli id alla colonna del dataframe finale (.loc permette di assegnare solo agli indici con score_300=1)
                risultato_finale.loc[temp.index, 'green_areas_id'] = temp
            else:
                #TODO: rimuovere questo else quando si sarà sicuri che non ci siano conflitti di id
                logger.error(f"Colonna {colonna_target} non trovata. Colonne presenti: {join_result.columns.tolist()}")

    except Exception as e:
        edifici = _return_default(edifici)
    
    return risultato_finale

def _return_default(edifici):
    res = edifici.copy()
    res['score_300'] = 0
    res['green_areas_id'] = pd.Series([[] for _ in range(len(res))], index=res.index)
    res['distanza_pedonale'] = float(infinity_dist)
    return res

"""
Rimuove gli edifici che hanno accesso diretto (in linea d'aria) a un'area verde, senza ostacoli.
Questo perché, se un edificio ha accesso diretto a un'area verde, non ha senso calcolare la distanza pedonale tramite grafo, in quanto è già soddisfatto.
Inoltre, in questi casi, la mappatura iniziale area verde - nodo grafo potrebbe essere inaccurata (nodo del grafo potrebbe essere dentro l'area verde), e quindi 
il calcolo del percorso pedonale potrebbe essere errato o addirittura fallire. Rimuovendo questi casi, ci concentriamo solo sugli edifici che realmente necessitano del calcolo pedonale.
Ritorna: pd.Series (serie) contenente le distanze calcolate, indicizzata con gli id degli edifici ad accesso diretto.
"""
def remove_direct_access(edifici_candidati, aree_verdi, crs):
    
    soglia = 20
    #inizializzo la serie dei risultati con float per distanze
    results = pd.Series(dtype=float)
    
    try:
        #solita proiezione metrica
        cand_proj = edifici_candidati.to_crs(crs)
        verdi_proj = aree_verdi.to_crs(crs)
        
        #calcolo distanza geometrica esatta verso il verde più vicino per ogni edificio (how='left' mantiene tutti gli edifici)
        nearest = gpd.sjoin_nearest(cand_proj, verdi_proj, distance_col="geom_dist", how="left")
        
        #raggruppa per edificio (un edificio può toccare più verdi)
        min_dists = nearest.groupby(nearest.index)['geom_dist'].min()
        
        #maschera per chi soddisfa l'accesso diretto (distanza <= soglia)
        direct_mask = min_dists <= soglia
        
        #ritorno solo la serie degli edifici soddisfatti con le loro distanze
        results = min_dists[direct_mask]
        
    except Exception as e:
        logger.error(f"Errore nel modulo remove_direct_access: {e}. Nessun accesso diretto rilevato.")
        #in caso di errore, restituisco serie vuota, così tutti andranno al grafo (fallback sicuro)
        return pd.Series(dtype=float)
        
    return results



#Esempio di utilizzo singolo dell'algoritmo
"""edifici = gpd.read_file("./INPUT/Edifici.geojson")
areeverdi = gpd.read_file("./INPUT/Areeverdi.geojson")
print(run_rule_300(edifici, areeverdi))"""