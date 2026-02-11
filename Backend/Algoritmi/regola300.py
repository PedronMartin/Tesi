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

    if city_name and grafo is not None:
        logger.info(f"Calcolo regola 300 con grafi pedonali per la città: {city_name}")
        candidati = edifici_processati[edifici_processati['score_300'] == 1].copy()
        if not candidati.empty:
            #uso la funzione update di pandas per aggiornare solo la colonna 'distanza_pedonale', mantenendo intatti gli altri campi e gli indici
            edifici_grafo = calculate_pedestrian_path(candidati, aree_verdi, grafo)
            #check di sicurezza sui percorsi
            if 'percorso_pedonale' not in edifici_processati.columns:
                edifici_processati['percorso_pedonale'] = None
            edifici_processati.update(edifici_grafo[['distanza_pedonale', 'percorso_pedonale']])

            #ricalcolo lo score_300 basandomi sulla distanza reale: se prima era 1 (geometrico) ma a piedi sono >300m, deve diventare 0.
            #il valore infinty_dist è -1, quindi aggiungo la condizione che deve essere positivo il valore
            mask = edifici_processati.index.isin(candidati.index)
            condition = (edifici_processati['distanza_pedonale'] >= 0) & (edifici_processati['distanza_pedonale'] <= 300)
            edifici_processati.loc[mask, 'score_300'] = condition.astype(int)

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

#Esempio di utilizzo singolo dell'algoritmo
"""edifici = gpd.read_file("./INPUT/Edifici.geojson")
areeverdi = gpd.read_file("./INPUT/Areeverdi.geojson")
print(run_rule_300(edifici, areeverdi))"""