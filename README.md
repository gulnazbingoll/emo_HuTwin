# Emotion Recognition System

## Panoramica

Questo sistema analizza le espressioni facciali per rilevare emozioni in tempo reale. Utilizza dati di tracciamento delle espressioni facciali (Action Units) per identificare sei emozioni primarie: felicità, tristezza, sorpresa, paura, rabbia e disgusto. Il sistema elabora file CSV contenenti dati di espressioni facciali provenienti da sensori o sistemi di computer vision.

## Struttura del Progetto

- `main.py`: Server web FastAPI per l'interfaccia utente
- `processing.py`: Funzioni principali per l'elaborazione dei dati
- `utils.py`: Utilities, inclusa la definizione dei pattern di emozioni
- `logging_utils.py`: Utilities per il logging

## Pipeline di Elaborazione

La pipeline di elaborazione dei dati procede attraverso le seguenti fasi:

1. **Caricamento e sanitizzazione dei dati**
   - Rimozione delle righe con espressioni invalide
   - Correzione dei formati numerici
   - Divisione dei file in task separati (se presenti)

2. **Aggregazione per secondo**
   - Raggruppamento dei dati per secondo, ignorando i millisecondi
   - Calcolo della media del peso per ogni espressione in ciascun intervallo di tempo

3. **Rilevamento delle emozioni** (dettagliato nella sezione successiva)
   - Identificazione delle emozioni presenti in ogni timestamp
   - Calcolo dell'intensità di ciascuna emozione

4. **Creazione del dataset finale**
   - Generazione di un dataset con un'unica riga per timestamp
   - Inclusione dell'intensità di tutte le 6 emozioni
   - Identificazione dell'emozione dominante con applicazione di una soglia

## Pipeline di Riconoscimento delle Emozioni (Step-by-Step)

Il riconoscimento delle emozioni si basa su pattern specifici di Action Units (AU). La chiave sta nella struttura del dizionario `emotion_primary_patterns` e nell'algoritmo di rilevamento.

### 1. Struttura del Pattern di Emozioni

Ogni emozione è definita da un insieme di gruppi di AU. Per ciascun gruppo, è sufficiente che sia presente almeno una delle varianti (L o R) per considerare quel gruppo attivato:

```python
# Esempio per la felicità
"happiness": [
    ["CheekRaiserL", "CheekRaiserR"],        # AU6 (L o R)
    ["LipCornerPullerL", "LipCornerPullerR"]  # AU12 (L o R)
]
```

Questo significa che per riconoscere la felicità, è necessario che:
- Sia presente AU6 sinistra OPPURE AU6 destra (sollevamento guancia)
- E sia presente AU12 sinistra OPPURE AU12 destra (sollevamento angolo delle labbra)

### 2. Algoritmo di Rilevamento (Dettagliato)

Per ogni timestamp, il processo è il seguente:

1. **Raccolta delle espressioni presenti**:
   - Creazione di un dizionario che mappa ogni espressione al suo peso

2. **Analisi delle emozioni**:
   - Per ogni emozione definita nei pattern:
     - Per ogni gruppo di AU in questa emozione:
       - Verifica se almeno un'AU del gruppo è presente (con peso > 0)
       - Se un gruppo è completamente assente, l'emozione non è riconosciuta
       - Se tutti i gruppi sono presenti, calcola l'intensità dell'emozione

3. **Calcolo dell'intensità**:
   - Per ogni gruppo di AU attivato, viene considerato il peso massimo tra le varianti
   - L'intensità dell'emozione è la media dei pesi massimi di tutti i gruppi
   - Le intensità vengono normalizzate (divise per la somma totale)

4. **Ordinamento**:
   - Le emozioni vengono ordinate per intensità (dalla più forte alla più debole)

### Esempio Completo di Calcolo

Prendiamo come esempio un timestamp con queste espressioni attive:
- CheekRaiserL: 0.8
- LipCornerPullerR: 0.6
- BrowLowererL: 0.3

Per la felicità:
- Gruppo 1 (AU6): CheekRaiserL presente con peso 0.8 → Gruppo attivato
- Gruppo 2 (AU12): LipCornerPullerR presente con peso 0.6 → Gruppo attivato
- Tutti i gruppi sono attivati → Intensità = (0.8 + 0.6) / 2 = 0.7

Per la rabbia:
- Gruppo 1 (AU4): BrowLowererL presente con peso 0.3 → Gruppo attivato
- Gruppo 2 (AU5): nessuna variante presente → Gruppo non attivato
- Almeno un gruppo non è attivato → Intensità = 0

Per la tristezza e le altre emozioni: stessa logica, ma in questo caso nessun'altra emozione è riconosciuta perché mancano gruppi di AU essenziali.

### Normalizzazione:
- Totale intensità: 0.7 (felicità) + 0 (altre emozioni) = 0.7
- Intensità normalizzata per felicità: 0.7 / 0.7 = 1.0
- Risultato: 100% felicità

## Configurazione e Utilizzo

### Prerequisiti
- Python 3.8+
- FastAPI
- Pandas
- Altri requisiti in `requirements.txt`

### Installazione
```bash
pip install -r requirements.txt
```

### Esecuzione
```bash
python main.py
```

L'applicazione sarà disponibile all'indirizzo `http://localhost:8000`

### Caricamento dei File
1. Accedi all'interfaccia web
2. Carica uno o più file CSV con dati di espressioni facciali
3. Imposta la soglia per il rilevamento delle emozioni (default: 0.2)
4. Avvia l'elaborazione

### Formato del File di Input
Il file CSV deve contenere le seguenti colonne:
- Time: timestamp nel formato "HH:MM:SS.sss AM/PM"
- Expression: nome dell'espressione facciale (es. "CheekRaiserL")
- Weight: peso/intensità dell'espressione (valore numerico)

## Note sulla Soglia e Sensibilità

La soglia (threshold) definita dall'utente determina quando un'emozione è considerata dominante:
- Se l'intensità normalizzata dell'emozione più forte è inferiore alla soglia, lo stato emotivo è etichettato come "neutral"
- Valori più bassi di soglia aumentano la sensibilità del sistema
- Valori più alti riducono i falsi positivi ma potrebbero non rilevare emozioni più sottili

## Risoluzione dei Problemi

Se il sistema non rileva correttamente le emozioni:
- Verificare che i file CSV contengano tutte le Action Units necessarie
- Controllare che il formato dei dati sia corretto
- Abbassare la soglia per aumentare la sensibilità
- Esaminare i log per identificare eventuali errori

---

## Documentazione Tecnica Supplementare

### Mappatura Action Units → Emozioni

Le emozioni sono definite dai seguenti pattern di Action Units:

| Emozione | Pattern di AU |
|----------|---------------|
| Felicità | AU6 (L/R) + AU12 (L/R) |
| Tristezza | AU1 (L/R) + AU4 (L/R) + AU15 (L/R) |
| Sorpresa | AU1 (L/R) + AU2 (L/R) + AU5 (L/R) + AU26 |
| Paura | AU1 (L/R) + AU2 (L/R) + AU4 (L/R) + AU5 (L/R) + AU20 (L/R) + AU26 |
| Rabbia | AU4 (L/R) + AU5 (L/R) + AU7 (L/R) + AU23 (L/R) + AU24 (L/R) |
| Disgusto | AU9 (L/R) + AU10 (L/R) + AU15 (L/R) + AU16 (L/R) + AU17 |

Dove:
- (L/R) indica che è sufficiente la presenza della versione sinistra O destra dell'AU
- Per ogni emozione, tutte le AU elencate devono essere presenti (in almeno una variante L o R)