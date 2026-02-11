# ------------------------------------------------------------------------------
# Author: Martin Pedron Giuseppe
# Tesi "GreenRatingAlgorithm: un algoritmo per la valutazione automatica della regola 3-30-300 sul verde urbano di prossimità"
# University of Verona - Tesi di Laurea CdL in Informatica, a.a. 2024/2025
# Relatore: Prof. Davide Quaglia
# ------------------------------------------------------------------------------

"""
    Algoritmo per il calcolo della conformità 3-30-300:
        Il programma esegue una catena di analisi per determinare quali edifici rispettano simultaneamente tre diverse regole di pianificazione urbana:
        1. Regola 3 (Linea di Vista): ogni edificio deve avere almeno 3 alberi visibili nel suo raggio d'azione.
        2. Regola 30 (Copertura Arborea): la percentuale di copertura arborea totale nella zona di studio deve superare una certa soglia.
        3. Regola 300 (Area Verde Vicina): ogni edificio deve trovarsi a una distanza massima di 300 metri da un'area verde pubblica.
        
        L'algoritmo esegue ciascuna di queste regole in modo indipendente e poi esegue una logica di "intersezione"
            per trovare gli edifici che soddisfano tutte le condizioni.
        
        MANCA:
            - proiezione dei risultati in una heatmap.
            - calcolo della media per edificio di soddisfazione della regola, e poi media delle medie per avere le proiezioni a colori sul piano generale;
"""

#importazioni
import pandas as pd
import logging

#importa le funzioni dagli script singoli
from .regola3 import run_rule_3
from .regola30 import run_rule_30
from .regola300 import run_rule_300

# costanti conformità algoritmo
VISIBLE_TREES = 3
COVERAGE_PERCENTAGE = 30.0
MIN_DISTANCE_GREEN_AREA = 300

"""
    Funzione principale che esegue l'analisi completa 3-30-300.
"""
def run_full_analysis(edifici, alberi, aree_verdi, polygon_gdf, city_name, grafo):

    # file di debug output e errori non bloccanti da ritornare al main + inizializzazione logger
    errori_rilevati = []
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("analizzatore_centrale")
    logger.info("Avvio dell'analisi completa 3-30-300...")

    logger.info(f"Numero totale di edifici nel dataset: {len(edifici)}")
    logger.info(f"Numero totale di alberi nel dataset: {len(alberi)}")
    logger.info(f"Numero totale di aree verdi nel dataset: {len(aree_verdi)}")

    #esegue gli algoritmi per ogni regola e ottieni i risultati
    logger.info("--- Esecuzione Regola 3 (Linea di Vista) ---")
    try:
        risultati_3 = run_rule_3(edifici, alberi)
        num_soddisfatti_3 = (risultati_3['visible_trees_count'] >= VISIBLE_TREES).sum()
        logger.info(f"RISULTATO REGOLA 3: {num_soddisfatti_3} edifici soddisfano la regola (su {len(edifici)}).")
    except Exception as e:
        logger.error(f"Errore Regola 3: {e}. Procedo con valori di default.")
        risultati_3 = edifici.copy()
        risultati_3['visible_trees_count'] = 0
        risultati_3['visible_trees_id'] = [[] for _ in range(len(risultati_3))]
        errori_rilevati.append("Regola 3 fallita")

    logger.info("--- Esecuzione Regola 30 (Copertura Arborea) ---")
    try:
        percentage_30 = run_rule_30(edifici, alberi, polygon_gdf)
        logger.info(f"RISULTATO REGOLA 30: La copertura arborea è del {percentage_30:.2f}%.")
        if percentage_30 > COVERAGE_PERCENTAGE:
            logger.info("La regola del 30% è soddisfatta a livello di zona.")
        else:
            logger.info("La regola del 30% NON è soddisfatta a livello di zona.")
    except Exception as e:
        logger.error(f"Errore Regola 30: {e}")
        errori_rilevati.append("Regola 30 fallita")
        percentage_30 = 0.0

    logger.info("--- Esecuzione Regola 300 (Area Verde Vicina) ---")
    try:
        risultati_300 = run_rule_300(edifici, aree_verdi, city_name, grafo)
        num_soddisfatti_300 = (risultati_300['score_300'] >= 1).sum()
        logger.info(f"RISULTATO REGOLA 300: {num_soddisfatti_300} edifici soddisfano la regola (su {len(edifici)}).")
    except Exception as e:
        logger.error(f"Errore Regola 300: {e}")
        errori_rilevati.append("Regola 300 fallita")
        risultati_300 = edifici.copy()
        risultati_300['score_300'] = 0
        risultati_300['green_areas_id'] = [[] for _ in range(len(risultati_300))]
        risultati_300['distanza_pedonale'] = 999
        risultati_300['percorso_pedonale'] = None

    logger.info("Merge dei risultati...")

    #partiamo dal GDF originale
    edifici_finali = edifici.copy()

    """
    Precedentemente avevo usato un join diretto tra i GDF dei risultati e quello degli edifici, ma questo causava problemi se una regola falliva
    causa GDF vuoti (gestito col fallback non causava errore bloccante questa parte). In questo modo, sia edifici_finali che i risultati
    delle singole regole avevano le stesse colonne di arricchimento sulle regole. Seppur coerente con i risultati, il join falliva
    in quanto non riusciva a capire a quale colonna tra le due omonime dare priorità.
    Ora invece, non esegue più un join ma un assegnazione diretta. In questo modo, se una regola fallisce o un GDF è vuoto (es. alberi), 
    e viene prodotto un set di edifici risultato con le colonne omonime a 0, anche edifici_finali è a 0 e semplicemente i risultati vengono sovvrascritti.
    """
    #uniamo i risultati della Regola 3 (visible_trees_count) alla tabella edifici_finali
    #gestiamo anche il caso di ritorno fallback della regola (tutti i risultati a 0 con setting indice uguale)
    edifici_finali['visible_trees_count'] = 0
    edifici_finali['visible_trees_id'] = pd.Series([[] for _ in range(len(edifici_finali))], index=edifici_finali.index)

    #se esistono risultati validi, li uniamo; altrimenti lasciamo i valori di default appena impostati
    if 'visible_trees_count' in risultati_3.columns:
        edifici_finali['visible_trees_count'] = risultati_3['visible_trees_count']
    if 'visible_trees_id' in risultati_3.columns:
        edifici_finali['visible_trees_id'] = risultati_3['visible_trees_id']

    #OLD VERSION con Join
    """
    if 'visible_trees_count' in risultati_3.columns and 'visible_trees_id' in risultati_3.columns:
        edifici_finali = edifici_finali.join(risultati_3[['visible_trees_count', 'visible_trees_id']])
    else:
        edifici_finali['visible_trees_count'] = 0
        edifici_finali['visible_trees_id'] = [[] for _ in range(len(edifici_finali))]
    """

    #identica procedura per le colonne della regola 300 (score_300 e green_areas_id)
    edifici_finali['score_300'] = 0
    edifici_finali['green_areas_id'] = pd.Series([[] for _ in range(len(edifici_finali))], index=edifici_finali.index)
    edifici_finali['distanza_pedonale'] = -1
    edifici_finali['percorso_pedonale'] = None
    if 'score_300' in risultati_300.columns:
        edifici_finali['score_300'] = risultati_300['score_300']
    
    if 'green_areas_id' in risultati_300.columns:
        edifici_finali['green_areas_id'] = risultati_300['green_areas_id']

    if 'distanza_pedonale' in risultati_300.columns:
        edifici_finali['distanza_pedonale'] = risultati_300['distanza_pedonale']

    if 'percorso_pedonale' in risultati_300.columns:
        edifici_finali['percorso_pedonale'] = risultati_300['percorso_pedonale']

    #OLD VERSION con Join
    """
    if 'score_300' in risultati_300.columns:
        colonne_da_unire = ['score_300']
        if 'green_areas_id' in risultati_300.columns:
            colonne_da_unire.append('green_areas_id')
        edifici_finali = edifici_finali.join(risultati_300[colonne_da_unire])
    else:
        edifici_finali['score_300'] = 0
        edifici_finali['green_areas_id'] = [[] for _ in range(len(edifici_finali))]
    """
    
    #uniamo il valore della regola 30 (coverage_percentage) che è uguale per tutti
    edifici_finali['coverage_percentage'] = percentage_30

    #calcolo la conformità finale salvando una flag
    edifici_finali['is_conforme'] = (
        (edifici_finali['visible_trees_count'] >= VISIBLE_TREES) &
        (edifici_finali['score_300'] >= 1) &
        (edifici_finali['coverage_percentage'] >= COVERAGE_PERCENTAGE)
    ).astype(int)

    #log finale del numero di edifici conformi
    num_conformi = edifici_finali['is_conforme'].sum()
    logger.info(f"Analisi completata. Edifici conformi: {num_conformi} su {len(edifici_finali)}")

    return edifici_finali.to_crs(edifici.crs), errori_rilevati

#main rule
if __name__ == "__main__":
    run_full_analysis()