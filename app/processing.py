import pandas as pd
import io
import os
from pathlib import Path
import re
from typing import List, Dict, Any, Optional
import logging

from utils import emotion_primary_patterns

def sanitize_dataset(file_path: str, output_dir: str, logger: logging.Logger) -> str:
    """
    Sanitizza un file CSV:
    - Rimuove le righe con espressione "Invalid"
    - Gestisce i problemi di formattazione dei numeri decimali
    
    Args:
        file_path: Path del file da sanitizzare
        output_dir: Directory di output
        logger: Logger per il logging
        
    Returns:
        Path del file sanitizzato
    """
    logger.info(f"Sanitizzazione del file: {file_path}")
    
    # Leggi il file come testo per pre-processarlo
    with open(file_path, "r") as file:
        content = file.read()
    
    # Dividi in righe
    lines = content.strip().split("\n")
    header = lines[0]
    processed_lines = [header]

    for line in lines[1:]:
        # Salta le righe con espressione "Invalid"
        if ",Invalid," in line:
            logger.debug(f"Riga con 'Invalid' ignorata: {line}")
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
    
    # Crea il nome del file di output
    base_name = os.path.basename(file_path)
    output_file = os.path.join(output_dir, f"sanitized_{base_name}")
    
    # Usa pandas per leggere e salvare i dati
    df = pd.read_csv(io.StringIO(processed_content))
    df.to_csv(output_file, index=False)
    
    logger.info(f"File sanitizzato salvato come: {output_file}")
    return output_file

def split_tasks(file_path: str, output_dir: str, logger: logging.Logger) -> List[str]:
    """
    Divide un file CSV in più file quando si incontrano righe di divisione di task.
    Il primo task va dall'inizio del file fino al primo delimitatore,
    il secondo task va dal primo al secondo delimitatore, e così via.
    
    Args:
        file_path: Path del file da dividere
        output_dir: Directory di output
        logger: Logger per il logging
        
    Returns:
        Lista dei path dei file creati
    """
    logger.info(f"Splitting del file per task: {file_path}")
    
    # Pattern regex per identificare le righe di divisione dei task
    task_pattern = re.compile(r'#+\s*New level - TASK (\d+)\s*#+')
    
    # Leggi il file
    with open(file_path, "r") as file:
        content = file.read()
    
    # Dividi in righe
    lines = content.strip().split("\n")
    
    # Lista per tenere traccia degli indici di inizio dei task e dei numeri dei task
    task_boundaries = []
    task_numbers = []
    
    # Trova tutte le righe di divisione dei task
    for i, line in enumerate(lines):
        match = task_pattern.match(line)
        if match:
            task_number = match.group(1)
            task_boundaries.append(i)
            task_numbers.append(task_number)
            logger.debug(f"Trovato delimitatore per TASK {task_number} alla riga {i}")
    
    # Se non ci sono divisioni di task, restituisci il file originale
    if not task_boundaries:
        logger.info(f"Nessun delimitatore di task trovato nel file {file_path}")
        return [file_path]
    
    # Nome base per i file di output
    base_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(base_name)[0]
    
    # Lista dei file creati
    created_files = []
    
    # Estrai l'intestazione (prima riga)
    header = lines[0]
    
    # Gestisci il primo task (dall'inizio fino al primo delimitatore)
    first_task_end = task_boundaries[0]
    if first_task_end > 1:  # Se ci sono dati prima del primo delimitatore
        first_task_content = lines[:first_task_end]
        first_task_file = os.path.join(output_dir, f"{name_without_ext}_processed_task_1.csv")
        with open(first_task_file, "w") as out_file:
            out_file.write("\n".join(first_task_content))
        created_files.append(first_task_file)
        logger.info(f"File per TASK 1 creato: {first_task_file}")
    
    # Crea un file per ogni task successivo
    for i in range(len(task_boundaries)):
        start_idx = task_boundaries[i] + 1  # Salta la riga di divisione
        
        if i < len(task_boundaries) - 1:
            end_idx = task_boundaries[i + 1]
        else:
            end_idx = len(lines)
        
        # Assicurati che ci siano dati da estrarre
        if start_idx >= end_idx:
            logger.warning(f"Task {task_numbers[i]} vuoto, ignorato")
            continue
        
        # Crea un nuovo file con i dati del task (assicurandoci di includere l'intestazione)
        task_content = [header] + lines[start_idx:end_idx]
        while len(task_content) > 1 and task_pattern.match(task_content[1]):
            task_content.pop(1)  # Rimuovi eventuali delimitatori aggiuntivi
        
        task_content_str = "\n".join(task_content)
        
        # Nome del file di output (utilizza il numero di task dal delimitatore)
        task_num = int(task_numbers[i])
        output_file = os.path.join(output_dir, f"{name_without_ext}_processed_task_{task_num+1}.csv")
        
        # Scrivi il file
        with open(output_file, "w") as out_file:
            out_file.write(task_content_str)
        
        created_files.append(output_file)
        logger.info(f"File per TASK {task_num+1} creato: {output_file}")
    
    return created_files

def aggregate_by_second(df: pd.DataFrame, output_file: Optional[str] = None) -> pd.DataFrame:
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

    if output_file:
        aggregated_df.to_csv(output_file, index=False)

    return aggregated_df

def detect_emotions(df: pd.DataFrame, output_file: Optional[str] = None) -> pd.DataFrame:
    """
    Rileva le emozioni primarie basate sui pattern di espressioni facciali.
    Per ogni gruppo di AU, è sufficiente che sia presente almeno una delle varianti (L o R).
    
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
        
        for emotion, pattern_groups in emotion_primary_patterns.items():
            # Verifico se ogni gruppo di AU è attivato (almeno una variante L o R)
            all_groups_active = True
            group_weights = []
            
            for au_group in pattern_groups:
                # Controllo se almeno una variante nel gruppo è presente
                group_active = False
                max_weight_in_group = 0
                
                for au in au_group:
                    if au in expression_to_weight and expression_to_weight[au] > 0:
                        group_active = True
                        if expression_to_weight[au] > max_weight_in_group:
                            max_weight_in_group = expression_to_weight[au]
                
                # Se nessuna variante del gruppo è attiva, l'emozione non è attivata
                if not group_active:
                    all_groups_active = False
                    break
                
                # Aggiungo il peso massimo per questo gruppo
                group_weights.append(max_weight_in_group)
            
            # Calcolo l'intensità media solo se tutti i gruppi sono attivi
            if all_groups_active:
                emotion_intensities[emotion] = sum(group_weights) / len(group_weights)
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
    
    if output_file:
        results_df.to_csv(output_file, index=False)
    
    return results_df


def create_final_dataset(emotions_df: pd.DataFrame, threshold: float = 0.25, 
                         output_file: Optional[str] = None) -> pd.DataFrame:
    """
    Crea un dataset finale con un'unica riga per timestamp, contenente 
    l'intensità di tutte le 6 emozioni e l'emozione dominante.
    
    Args:
        emotions_df: DataFrame con i dati di emozioni (output di detect_emotions)
        threshold: Soglia minima di intensità per considerare un'emozione (default: 0.25)
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
    
    if output_file:
        final_df.to_csv(output_file, index=False)
    
    return final_df

def process_file(file_path: str, threshold: float, logger: logging.Logger) -> str:
    """
    Elabora un singolo file CSV attraverso tutte le fasi di processing.
    
    Args:
        file_path: Path del file da elaborare
        threshold: Soglia per considerare un'emozione valida
        logger: Logger per il logging
        
    Returns:
        Path del file finale con i risultati
    """
    logger.info(f"Inizio elaborazione del file: {file_path}")
    
    # Nome base per i file di output
    base_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(base_name)[0]
    
    # Leggi il file
    try:
        df = pd.read_csv(file_path)
        logger.info(f"File letto correttamente: {file_path}")
    except Exception as e:
        logger.error(f"Errore nella lettura del file {file_path}: {str(e)}")
        raise
    
    # Aggregazione per secondo
    aggregated_file = os.path.join("results/aggregated", f"{name_without_ext}_aggregated.csv")
    aggregated_df = aggregate_by_second(df, aggregated_file)
    logger.info(f"Aggregazione completata: {aggregated_file}")
    
    # Rilevamento delle emozioni
    emotions_file = os.path.join("results/emotions", f"{name_without_ext}_emotions.csv")
    emotions_df = detect_emotions(aggregated_df, emotions_file)
    logger.info(f"Rilevamento emozioni completato: {emotions_file}")
    
    # Dataset finale
    final_file = os.path.join("results/final", f"{name_without_ext}_final.csv")
    final_df = create_final_dataset(emotions_df, threshold, final_file)
    logger.info(f"Dataset finale creato: {final_file}")
    
    return final_file

def process_files(file_paths: List[str], threshold: float, logger: logging.Logger) -> List[str]:
    """
    Elabora una lista di file CSV.
    
    Args:
        file_paths: Lista dei path dei file da elaborare
        threshold: Soglia per considerare un'emozione valida
        logger: Logger per il logging
        
    Returns:
        Lista dei path dei file finali con i risultati
    """
    logger.info(f"Inizio elaborazione di {len(file_paths)} file")
    
    # Crea le directory per organizzare i diversi tipi di file
    for dir_path in ["results", "results/sanitized", "results/aggregated", "results/emotions", "results/final", "temp"]:
        Path(dir_path).mkdir(exist_ok=True, parents=True)
    
    result_files = []
    
    for file_path in file_paths:
        try:
            # Sanitizza il file
            sanitized_file = sanitize_dataset(file_path, "results/sanitized", logger)
            logger.info(f"File sanitizzato: {sanitized_file}")
            
            # Dividi il file in task se necessario
            task_files = split_tasks(sanitized_file, "results/sanitized", logger)
            logger.info(f"File divisi in {len(task_files)} task")
            
            # Elabora ogni file di task
            for task_file in task_files:
                try:
                    result_file = process_file(task_file, threshold, logger)
                    result_files.append(result_file)
                    logger.info(f"Elaborazione completata per {task_file}")
                except Exception as e:
                    logger.error(f"Errore nell'elaborazione del file {task_file}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Errore nella preparazione del file {file_path}: {str(e)}")
    
    return result_files