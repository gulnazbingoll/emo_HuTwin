from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import shutil
import os
from pathlib import Path
from datetime import datetime
import logging
from typing import List

from processing import process_files
from logging_utils import setup_logger

# Creazione delle directory necessarie se non esistono
for dir_path in ["logs", "results", "uploads"]:
    Path(dir_path).mkdir(exist_ok=True)

app = FastAPI(title="Emotion Analysis API")

# Configurazione dei template e dei file statici
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Setup del logger per l'applicazione
logger = setup_logger("app", "logs/app.log")

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    """Mostra il form per il caricamento dei file CSV."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process/")
async def process_csv_files(
    request: Request,
    files: List[UploadFile] = File(...),
    threshold: float = Form(0.2)
):
    """
    Elabora i file CSV caricati.
    
    Args:
        files: Lista di file CSV caricati
        threshold: Soglia per considerare un'emozione valida
    """
    # Crea un nuovo logger specifico per questa esecuzione
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/processing_{timestamp}.log"
    process_logger = setup_logger(f"process_{timestamp}", log_file)
    
    process_logger.info(f"Inizio elaborazione con threshold={threshold}")
    process_logger.info(f"Numero di file caricati: {len(files)}")
    
    # Salva temporaneamente i file caricati
    saved_files = []
    for file in files:
        if not file.filename.endswith('.csv'):
            process_logger.warning(f"File {file.filename} ignorato: non è un file CSV")
            continue
            
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file_path)
        process_logger.info(f"File salvato: {file_path}")
    
    # Elabora i file
    if saved_files:
        try:
            result_files = process_files(saved_files, threshold, process_logger)
            process_logger.info(f"Elaborazione completata. File risultati: {result_files}")
            
            return templates.TemplateResponse(
                "index.html", 
                {
                    "request": request, 
                    "message": "Elaborazione completata con successo!",
                    "result_files": result_files
                }
            )
        except Exception as e:
            process_logger.error(f"Errore durante l'elaborazione: {str(e)}")
            return templates.TemplateResponse(
                "index.html", 
                {
                    "request": request, 
                    "error": f"Errore: {str(e)}"
                }
            )
    else:
        process_logger.warning("Nessun file CSV valido caricato")
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request, 
                "error": "Nessun file CSV valido caricato"
            }
        )

if __name__ == "__main__":
    logger.info("Avvio dell'applicazione")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)