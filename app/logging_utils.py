import logging
import os
from pathlib import Path
from datetime import datetime

def setup_logger(name, log_file, level=logging.INFO):
    """
    Configura un logger con un determinato nome e file di output.
    
    Args:
        name: Nome del logger
        log_file: Path del file di log
        level: Livello di logging (default: INFO)
        
    Returns:
        Logger configurato
    """
    # Crea la directory dei log se non esiste
    log_dir = os.path.dirname(log_file)
    Path(log_dir).mkdir(exist_ok=True)
    
    # Configura il logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evita di aggiungere handler duplicati
    if not logger.handlers:
        # Crea un handler per il file
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        # Crea un handler per la console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Crea un formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Aggiungi gli handler al logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger