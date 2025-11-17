"""
    Algoritmo per il calcolo della Regola 300:
        Il programma verifica, per ogni edificio, se è presente un'area verde pubblica nel raggio di 300 metri.
        Il calcolo si basa su una "unione spaziale" tra gli edifici e le aree verdi.
            1. Creazione del buffer: per ogni edificio, viene creato un'area di 300 metri (un "buffer"). Questo buffer rappresenta la zona di ricerca.
            2. Unione spaziale (Spatial Join): i buffer degli edifici vengono uniti alle geometrie delle aree verdi.
                Un edificio supera il test se il suo buffer interseca almeno un'area verde.
            3. Attribuzione del punteggio: ogni edificio che interseca un'area verde riceve un punteggio di 1, mentre gli altri ricevono 0.

        MANCA:
            1) La regola andrebbe perfezionata per distinguere la tipologia di area verde (ad esempio, un grande parco rispetto a una piccola aiuola).
            2) Il calcolo non tiene conto della disponibilità dell'area verde (ad esempio, se è recintata o accessibile al pubblico).
            3) bisogna controllare se il buffer di 300 metri parte dal centro dell'edificio oppure dal perimetro (che sarebbe la versione desiderata).
            4) forse bisogna aggiungere già qui il calcolo del percorso per non sovvraccaricare il frontend con Leaflet;
            5) decidere se contare proprio il numero di aree verdi (e dare più peso alla regola) oppure come fatto fermare la ricerca una volta che se ne trova uno.
            6) in questo momento la ricerca delle aree verdi viene fatta solo sulla zona selezionata in Angular, anche se ci potrebbero essere
                aree verdi nei 300 metri fuori dalla zona selezionata.

        SISTEMATI:
            1) E' stato implementato un filtro per considerare solo le aree verdi con superficie maggiore di una soglia minima;
            2) IN ATTESA DI DATI COMUNALI da Alessio, che potrebbero avere più informazioni rispetto a OSM;
            3) il buffer di 300 metri parte in automatico dal perimetro dell'edificio grazie a geopandas;
            4) considerato che farlo senza Leaflet ha un costo computazionale importante, e non c'è conflitto se li teniamo separati, optiamo per avere
                una divisione tra il backend che valuta la regola (linea d'aria) e il frontend che mostra la realtà (percorso), chiaramente maggiore del primo;
                siccome è stato deciso di avere un precalcolo massiccio nel backend, con salvataggio in un DB, l'aggiunta del percorso pedonale con OSMXML/Graphhopper
                andrebbe fatta in un secondo momento come arricchimento del dato già calcolato;
            5) CHIEDERE A PROFESSORE! ---> la considererei una funzionalità avanzata, perchè richiede aggiunta di campi nel GeoJson che vanno in conflitto con altri usi;
            6) la query delle aree verdi è stata appositamente gonfiata oltre il poligono dell'utente;
"""

# importazioni
import geopandas as gpd
import logging

# costante --- in metri quadrati, 10000 m^2 = 1 ettaro
SOGLIA_MINIMA = 10000

def run_rule_300(edifici, aree_verdi):

    # avvio logger regola
    logger = logging.getLogger("regola300")

    #TODO: controllare che questo controllo non sia ridondante con quello in server.py
    # potrebbe avere senso tenerlo in particolare se si rendono le regole autonome e utilizzabili singolarmente
    # controllo input
    if edifici.empty or aree_verdi.empty:
        logger.warning("Dati insufficienti per il calcolo. Assicurati che i GeoDataFrame non siano vuoti.")
        return edifici.assign(score_300=0)

    # proietto i CRS in EPSG:32632 per calcoli metrici
    try:
        if edifici.crs is None:
            edifici.set_crs("EPSG:4326", inplace=True)
        if aree_verdi.crs is None:
            aree_verdi.set_crs("EPSG:4326", inplace=True)
        edifici_proj = edifici.to_crs("EPSG:32632")
        aree_verdi_proj = aree_verdi.to_crs("EPSG:32632")

        # calcolo l'area (in metri quadri) di ogni poligono
        aree_verdi_proj['area_mq'] = aree_verdi_proj.geometry.area
        
        # filtro per area
        """
            Attenzione: questa parte normalmente genererebbe un warning da parte di Pandas senza la copia esplicita (.copy()),
            in quanto si sta tentando di modificare un DataFrame filtrato. L'uso di .copy() previene questo warning creando una copia indipendente.
        """
        aree_verdi_filtrate = aree_verdi_proj[aree_verdi_proj['area_mq'] >= SOGLIA_MINIMA].copy()

        # ricontrollo caso dataset nullo
        if aree_verdi_filtrate.empty:
            logger.warning(f"Nessuna area verde significativa (>= {SOGLIA_MINIMA}mq) trovata. Restituisco score 0.")
            return edifici.assign(score_300=0)

        """
            Creo un buffer di 300 metri intorno ad ogni edificio:
                - creo una copia del GeoDataFrame degli edifici per non modificare l'originale;
                - aggiungo una colonna 'original_index' per tenere traccia dell'indice originale degli edifici;
                - creo il buffer di 300 metri sulla colonna 'geometry' ---> sostituisce il campo geometria con geometry + buffer
        """
        edifici_buffer = edifici_proj.copy()
        edifici_buffer['geometry'] = edifici_buffer.geometry.buffer(300)
        edifici_buffer['original_index'] = edifici_buffer.index

        # unione spaziale tra i buffer degli edifici e le aree verdi (inner è join base, predicate 'intersects' controlla l'intersezione)
        join_result = gpd.sjoin(edifici_buffer, aree_verdi_proj, how="inner", predicate='intersects')

        # crea copia per il risultato finale e inizializza colonna punteggio a 0
        risultato_finale = edifici.copy()
        risultato_finale['score_300'] = 0

        # se ci sono intersezioni, si assegna loro il punteggio senza ripetere gli indici originali
        if not join_result.empty:
            soddisfatti_index = join_result['original_index'].unique()
            risultato_finale.loc[soddisfatti_index, 'score_300'] = 1
    except Exception as e:
        logger.error(f"Errore nel calcolo della regola 300: {e}")
        return edifici.assign(score_300=0)

    return risultato_finale

#Esempio di utilizzo singolo dell'algoritmo
"""edifici = gpd.read_file("./INPUT/Edifici.geojson")
areeverdi = gpd.read_file("./INPUT/Areeverdi.geojson")
print(run_rule_300(edifici, areeverdi))"""