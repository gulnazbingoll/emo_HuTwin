#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test.py - Utility per elaborare direttamente file CSV di espressioni facciali.

Utilizzo:
    python test.py input.csv [--output-dir output_directory] [--threshold 0.2]

Argomenti:
    input.csv         File CSV di input con dati di espressioni facciali
    --output-dir      Directory di output (default: output)
    --threshold       Soglia per considerare un'emozione valida (default: 0.2)
"""

import os
import sys
import argparse
import logging
import shutil
from pathlib import Path
import pandas as pd

# Assicuriamoci che tutte le directory necessarie esistano
for dir_path in ["logs", "results", "results/sanitized", "results/aggregated", 
                "results/emotions", "results/final", "temp"]:
    Path(dir_path).mkdir(exist_ok=True, parents=True)

# Importiamo le funzioni di elaborazione dal modulo processing
try:
    from processing import sanitize_dataset, split_tasks, process_file
    from logging_utils import setup_logger
except ImportError:
    print("Errore: impossibile importare i moduli necessari.")
    print("Assicurati che i file processing.py e logging_utils.py siano nella directory corrente.")
    sys.exit(1)

def print_emotion_stats(file_path):
    """Stampa le statistiche delle emozioni per un file CSV."""
    try:
        result_df = pd.read_csv(file_path)
        if 'DominantEmotion' in result_df.columns:
            emotion_counts = result_df['DominantEmotion'].value_counts()
            print(f"\nStatistiche emozioni per {os.path.basename(file_path)}:")
            print("-" * 40)
            for emotion, count in emotion_counts.items():
                percentage = (count / len(result_df)) * 100
                print(f"{emotion}: {count} ({percentage:.1f}%)")
            print("-" * 40)
            print(f"Totale timestamps: {len(result_df)}")
    except Exception as e:
        print(f"Errore nell'analisi dei risultati per {file_path}: {str(e)}")

def main():
    # Configurazione del parser dei comandi
    parser = argparse.ArgumentParser(description='Elabora un file CSV per rilevare emozioni.')
    parser.add_argument('input_file', help='File CSV di input con dati di espressioni facciali')
    parser.add_argument('--output-dir', '-o', default='output',
                      help='Directory di output (default: output)')
    parser.add_argument('--threshold', '-t', type=float, default=0.2,
                      help='Soglia per considerare un\'emozione valida (default: 0.2)')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Abilita output dettagliato')
    
    args = parser.parse_args()
    
    # Verifica che il file di input esista
    if not os.path.isfile(args.input_file):
        print(f"Errore: il file {args.input_file} non esiste.")
        sys.exit(1)
    
    # Crea la directory di output se non esiste
    output_dir = args.output_dir
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    
    # Configura il logger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger('test_emotion', 'logs/test_emotion.log', level=log_level)
    
    logger.info(f"Avvio elaborazione del file: {args.input_file}")
    logger.info(f"Threshold impostata a: {args.threshold}")
    logger.info(f"Directory di output: {output_dir}")
    
    try:
        # Sanitizza il file
        logger.info("Fase 1: Sanitizzazione del file")
        sanitized_file = sanitize_dataset(args.input_file, "results/sanitized", logger)
        
        # Dividi il file in task se necessario
        logger.info("Fase 2: Divisione in task")
        task_files = split_tasks(sanitized_file, "results/sanitized", logger)
        
        final_output_files = []
        
        # Elabora ogni file di task
        for i, task_file in enumerate(task_files):
            logger.info(f"Elaborazione task {i+1}/{len(task_files)}: {task_file}")
            try:
                # Process_file restituisce il path del file di output finale
                result_file = process_file(task_file, args.threshold, logger)
                
                # Ottieni il nome base del file di task
                base_name = os.path.splitext(os.path.basename(task_file))[0]
                
                # Crea il nome del file finale nella directory di output
                if len(task_files) == 1:
                    # Se c'è un solo task, usa il nome base del file di input
                    input_base = os.path.splitext(os.path.basename(args.input_file))[0]
                    final_name = f"{input_base}_emotions.csv"
                else:
                    # Se ci sono più task, mantieni il nome del task
                    final_name = f"{base_name}_emotions.csv"
                
                final_output = os.path.join(output_dir, final_name)
                
                # Copia il file di risultato nella destinazione finale
                shutil.copy2(result_file, final_output)
                logger.info(f"File di output per task {i+1} salvato come: {final_output}")
                
                final_output_files.append(final_output)
                
            except Exception as e:
                logger.error(f"Errore nell'elaborazione del task {task_file}: {str(e)}")
                continue
        
        # Stampa un riepilogo dei file generati
        if final_output_files:
            print("\nElaborazione completata con successo!")
            print(f"Sono stati generati {len(final_output_files)} file di output:")
            
            for file_path in final_output_files:
                print(f"\n- {file_path}")
                print_emotion_stats(file_path)
                
            print(f"\nTutti i file sono stati salvati nella directory: {output_dir}")
        else:
            logger.error("Nessun task è stato elaborato correttamente.")
            print("Errore: nessun file di output è stato generato.")
            sys.exit(1)
        
        logger.info("Elaborazione completata con successo")
        
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione: {str(e)}")
        print(f"Errore: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()