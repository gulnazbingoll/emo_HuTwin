import pandas as pd
import io
from utils import emotion_primary_patterns


def aggregate_by_second(df, output_file=None):
    """
    Raggruppa i dati per secondo (ignorando i millisecondi) e calcola la media del Weight
    per ogni Expression in quell'intervallo di tempo.

    Args:
        df: DataFrame con i dati
        output_file: Nome del file di output (opzionale)

    Returns:
        DataFrame con i dati aggregati
    """
    # Estrai solo l'ora senza millisecondi (prendendo tutto fino al punto e mantenendo AM/PM)
    df["TimeSecond"] = df["Time"].apply(
        lambda x: x.split(".")[0] + " " + x.split(" ")[1]
    )

    # Raggruppa per TimeSecond ed Expression, e calcola la media del Weight
    aggregated_df = (
        df.groupby(["TimeSecond", "Expression"])["Weight"].mean().reset_index()
    )

    # Rinomina TimeSecond a Time
    aggregated_df.rename(columns={"TimeSecond": "Time"}, inplace=True)

    print(f"Dataset aggregato per secondo e salvato")
    if output_file:
        aggregated_df.to_csv(output_file, index=False)

    return aggregated_df


def sanitize_dataset(filename, output_file=None):
    # Leggi il file come testo per pre-processarlo
    with open(filename, "r") as file:
        content = file.read()
    # Dividi in righe
    lines = content.strip().split("\n")
    header = lines[0]
    processed_lines = [header]

    for line in lines[1:]:
        # Salta le righe con espressione "Invalid"
        if ",Invalid," in line:
            continue

        # Dividi per virgola
        parts = line.split(",")

        # Se ci sono 4 parti, significa che il numero decimale usa la virgola
        # e dobbiamo sostituirla con un punto
        if len(parts) == 4:
            fixed_line = f"{parts[0]},{parts[1]},{parts[2]}.{parts[3]}"
            processed_lines.append(fixed_line)
        else:
            processed_lines.append(line)

    # Unisci le righe processate
    processed_content = "\n".join(processed_lines)

    print("Dataset sanitizzato e salvato come 'dataset_sanitized.csv'")
    if output_file:
        # Usa pandas per leggere e salvare i dati
        df = pd.read_csv(io.StringIO(processed_content))
        df.to_csv(output_file, index=False)
    return df


def detect_emotions(df, output_file=None):
    """
    Rileva le emozioni primarie basate sui pattern di espressioni facciali.
    
    Args:
        df: DataFrame con i dati aggregati per secondo
        output_file: Nome del file di output (opzionale)
        
    Returns:
        DataFrame con i timestamp e le emozioni rilevate ordinate per intensità
    """
    # Risultati delle emozioni
    all_results = []
    
    # Elaboro ogni timestamp separatamente
    for time, group in df.groupby('Time'):
        # Creo un dizionario per mappare expression a weight
        expression_to_weight = dict(zip(group['Expression'], group['Weight']))
        
        # Calcolo l'intensità di ogni emozione primaria
        emotion_intensities = {}
        
        for emotion, pattern in emotion_primary_patterns.items():
            # Raccolgo i pesi delle AU presenti nel pattern
            pattern_weights = []
            
            for au in pattern:
                if au in expression_to_weight:
                    pattern_weights.append(expression_to_weight[au])
            
            # Calcolo l'intensità media, solo se ci sono pesi disponibili
            if pattern_weights:
                emotion_intensities[emotion] = sum(pattern_weights) / len(pattern_weights)
            else:
                emotion_intensities[emotion] = 0
        
        # Normalizzazione delle intensità delle emozioni per questo timestamp
        total_intensity = sum(emotion_intensities.values())
        if total_intensity > 0:  # Evito divisione per zero
            for emotion in emotion_intensities:
                emotion_intensities[emotion] /= total_intensity
        
        # Ordino le emozioni per intensità (dalla più intensa alla meno intensa)
        sorted_emotions = sorted(
            emotion_intensities.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Aggiungo i risultati per questo timestamp
        time_results = []
        for emotion, intensity in sorted_emotions:
            time_results.append({
                'Time': time,
                'Emotion': emotion,
                'Intensity': intensity
            })
        
        all_results.extend(time_results)
    
    # Creo un DataFrame dai risultati
    results_df = pd.DataFrame(all_results)
    
    print(f"Emozioni rilevate e analizzate")
    if output_file:
        results_df.to_csv(output_file, index=False)
    
    return results_df

def create_final_dataset(emotions_df, threshold=0.25, output_file=None):
    """
    Crea un dataset finale con un'unica riga per timestamp, contenente 
    l'intensità di tutte le 6 emozioni e l'emozione dominante.
    
    Args:
        emotions_df: DataFrame con i dati di emozioni (output di detect_emotions)
        threshold: Soglia minima di intensità per considerare un'emozione (default: 0.2)
        output_file: Nome del file di output (opzionale)
        
    Returns:
        DataFrame con il dataset finale
    """
    # Lista di tutte le emozioni
    all_emotions = ["happiness", "sadness", "surprise", "fear", "anger", "disgust"]
    
    # Preparo un dizionario per contenere i risultati
    final_results = []
    
    # Per ogni timestamp, trovo l'emozione dominante
    for time, group in emotions_df.groupby('Time'):
        # Creo un dizionario per mappare emozione a intensità
        emotion_to_intensity = dict(zip(group['Emotion'], group['Intensity']))
        
        # Trovo l'emozione con la massima intensità
        max_emotion = max(emotion_to_intensity.items(), key=lambda x: x[1])
        dominant_emotion = max_emotion[0]
        dominant_intensity = max_emotion[1]
        
        # Se l'intensità è sotto la soglia, etichetta come "neutral"
        if dominant_intensity < threshold:
            dominant_emotion = "neutral"
        
        # Preparo una riga per questo timestamp
        row = {'Time': time, 'DominantEmotion': dominant_emotion}
        
        # Aggiungo l'intensità di ogni emozione
        for emotion in all_emotions:
            row[emotion] = emotion_to_intensity.get(emotion, 0)
        
        final_results.append(row)
    
    # Creo un DataFrame dai risultati
    final_df = pd.DataFrame(final_results)
    
    # Riordino le colonne
    columns = ['Time'] + all_emotions + ['DominantEmotion']
    final_df = final_df[columns]
    
    print(f"Dataset finale creato")
    if output_file:
        final_df.to_csv(output_file, index=False)
    
    return final_df


if __name__ == "__main__":
    filename = "dataset/expression_log_2025_03_26_12-13-05.csv"
    
    # Passo 1: Sanitizzazione del dataset
    sanitized_df = sanitize_dataset(filename, "data_set.csv")
    
    # Passo 2: Aggregazione per secondo
    aggregated_df = aggregate_by_second(sanitized_df, "data_set_aggregated.csv")
    
    # Passo 3: Rilevamento delle emozioni
    emotions_df = detect_emotions(aggregated_df, "emotions_results.csv")
    
    # Passo 4: Creazione del dataset finale
    threshold = 0.25  # Soglia per considerare un'emozione valida
    final_df = create_final_dataset(emotions_df, threshold, "final_emotions.csv")
    
    # Stampa le prime 5 righe del dataset finale
    print("\nPrime 5 righe del dataset finale:")
    print(final_df.head(5))