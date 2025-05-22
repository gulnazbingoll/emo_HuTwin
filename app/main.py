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
from typing import List, Optional

from processing import process_files
from logging_utils import setup_logger

# Create necessary directories if they don't exist
for dir_path in ["logs", "results", "uploads"]:
    Path(dir_path).mkdir(exist_ok=True)

app = FastAPI(title="Emotion Analysis API")

# Configure templates and static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Setup logger for the application
logger = setup_logger("app", "logs/app.log")

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    """Display the form for uploading CSV files."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process/")
async def process_csv_files(
    request: Request,
    files: List[UploadFile] = File(...),
    threshold: float = Form(0.2),
    split_output_files: Optional[bool] = Form(False)
):
    """
    Process the uploaded CSV files.
    
    Args:
        files: List of uploaded CSV files
        threshold: Threshold to consider an emotion valid
        split_output_files: If True, create separate files for each task
    """
    # Create a new logger specific to this execution
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/processing_{timestamp}.log"
    process_logger = setup_logger(f"process_{timestamp}", log_file)
    
    process_logger.info(f"Starting processing with threshold={threshold}")
    process_logger.info(f"Split output files: {split_output_files}")
    process_logger.info(f"Number of uploaded files: {len(files)}")
    
    # Temporarily save the uploaded files
    saved_files = []
    for file in files:
        if not file.filename.endswith('.csv'):
            process_logger.warning(f"File {file.filename} ignored: not a CSV file")
            continue
            
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file_path)
        process_logger.info(f"File saved: {file_path}")
    
    # Process the files
    if saved_files:
        try:
            result_files = process_files(saved_files, threshold, process_logger, split_output_files)
            process_logger.info(f"Processing completed. Result files: {result_files}")
            
            # Get statistics file paths
            stat_files = []
            for file_path in result_files:
                base_path = os.path.splitext(file_path)[0]
                base_name = os.path.basename(base_path)
                stat_file = f"results/statistics/{base_name}_statistics.json"
                if os.path.exists(stat_file):
                    stat_files.append(stat_file)
            
            # Custom success message
            if split_output_files:
                success_msg = f"Processing completed successfully! Generated {len(result_files)} files (separated by task) with corresponding statistics and charts."
            else:
                success_msg = f"Processing completed successfully! Generated {len(result_files)} aggregated files with corresponding statistics and charts."
            
            return templates.TemplateResponse(
                "index.html", 
                {
                    "request": request, 
                    "message": success_msg,
                    "result_files": result_files,
                    "split_mode": split_output_files
                }
            )
        except Exception as e:
            process_logger.error(f"Error during processing: {str(e)}")
            return templates.TemplateResponse(
                "index.html", 
                {
                    "request": request, 
                    "error": f"Error: {str(e)}"
                }
            )
    else:
        process_logger.warning("No valid CSV files uploaded")
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request, 
                "error": "No valid CSV files uploaded"
            }
        )

if __name__ == "__main__":
    logger.info("Starting the application")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)