#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test.py - Utility for directly processing facial expression CSV files.

Usage:
    python test.py input.csv [--output-dir output_directory] [--threshold 0.2] [--split-tasks]

Arguments:
    input.csv         Input CSV file with facial expression data
    --output-dir      Output directory (default: output)
    --threshold       Threshold to consider an emotion valid (default: 0.2)
    --split-tasks     Create separate files for each task instead of an aggregated file
"""

import os
import sys
import argparse
import logging
import shutil
from pathlib import Path
import pandas as pd
import json

# Ensure all necessary directories exist
for dir_path in ["logs", "results", "results/sanitized", "results/final", "results/statistics"]:
    Path(dir_path).mkdir(exist_ok=True, parents=True)

# Import processing functions from the processing module
try:
    from processing import sanitize_dataset, process_file
    from logging_utils import setup_logger
except ImportError:
    print("Error: could not import required modules.")
    print("Make sure that processing.py and logging_utils.py are in the current directory.")
    sys.exit(1)

def print_emotion_stats(file_path):
    """Print emotion statistics for a CSV file."""
    try:
        result_df = pd.read_csv(file_path)
        if 'DominantEmotion' in result_df.columns:
            emotion_counts = result_df['DominantEmotion'].value_counts()
            print(f"\nEmotion statistics for {os.path.basename(file_path)}:")
            print("-" * 40)
            for emotion, count in emotion_counts.items():
                percentage = (count / len(result_df)) * 100
                print(f"{emotion}: {count} ({percentage:.1f}%)")
            print("-" * 40)
            print(f"Total timestamps: {len(result_df)}")
            
            # If there's a Task column, also show statistics by task
            if 'Task' in result_df.columns:
                task_counts = result_df['Task'].value_counts().sort_index()
                print(f"\nStatistics by task:")
                for task, count in task_counts.items():
                    print(f"{task}: {count} timestamps")
            
            # Check if a statistics file exists for this file
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            stats_file = os.path.join("results/statistics", f"{base_name}_statistics.json")
            chart_file = os.path.join("results/statistics", f"{base_name}_emotion_chart.png")
            
            if os.path.exists(stats_file):
                print(f"\nDetailed statistics available in: {stats_file}")
            
            if os.path.exists(chart_file):
                print(f"Emotion distribution chart available in: {chart_file}")
                    
    except Exception as e:
        print(f"Error analyzing results for {file_path}: {str(e)}")

def main():
    # Command parser configuration
    parser = argparse.ArgumentParser(description='Process a CSV file to detect emotions.')
    parser.add_argument('input_file', help='Input CSV file with facial expression data')
    parser.add_argument('--output-dir', '-o', default='output',
                      help='Output directory (default: output)')
    parser.add_argument('--threshold', '-t', type=float, default=0.2,
                      help='Threshold to consider an emotion valid (default: 0.2)')
    parser.add_argument('--split-tasks', '-s', action='store_true',
                      help='Create separate files for each task instead of an aggregated file')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable detailed output')
    
    args = parser.parse_args()
    
    # Verify that the input file exists
    if not os.path.isfile(args.input_file):
        print(f"Error: the file {args.input_file} does not exist.")
        sys.exit(1)
    
    # Create the output directory if it doesn't exist
    output_dir = args.output_dir
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    
    # Configure the logger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger('test_emotion', 'logs/test_emotion.log', level=log_level)
    
    logger.info(f"Starting processing of file: {args.input_file}")
    logger.info(f"Threshold set to: {args.threshold}")
    logger.info(f"Split tasks: {args.split_tasks}")
    logger.info(f"Output directory: {output_dir}")
    
    try:
        # Sanitize the file
        logger.info("Phase 1: File sanitization")
        sanitized_file = sanitize_dataset(args.input_file, "results/sanitized", logger)
        
        # Process the file
        logger.info("Phase 2: Complete processing")
        result_file = process_file(sanitized_file, args.threshold, logger, args.split_tasks)
        
        # Handle the result (can be a single file or a list)
        if isinstance(result_file, list):
            final_output_files = []
            for i, file_path in enumerate(result_file):
                # Get the base name of the file
                base_name = os.path.basename(file_path)
                final_output = os.path.join(output_dir, base_name)
                
                # Copy the result file to the final destination
                shutil.copy2(file_path, final_output)
                logger.info(f"Output file {i+1} saved as: {final_output}")
                final_output_files.append(final_output)
                
                # Copy any statistics files
                stat_base = os.path.splitext(base_name)[0]
                stat_file = os.path.join("results/statistics", f"{stat_base}_statistics.json")
                chart_file = os.path.join("results/statistics", f"{stat_base}_emotion_chart.png")
                
                if os.path.exists(stat_file):
                    stat_output = os.path.join(output_dir, f"{stat_base}_statistics.json")
                    shutil.copy2(stat_file, stat_output)
                    logger.info(f"Statistics file copied to: {stat_output}")
                
                if os.path.exists(chart_file):
                    chart_output = os.path.join(output_dir, f"{stat_base}_emotion_chart.png")
                    shutil.copy2(chart_file, chart_output)
                    logger.info(f"Chart file copied to: {chart_output}")
        else:
            # Single output file
            input_base = os.path.splitext(os.path.basename(args.input_file))[0]
            final_name = f"{input_base}_emotions.csv"
            final_output = os.path.join(output_dir, final_name)
            
            # Copy the result file to the final destination
            shutil.copy2(result_file, final_output)
            logger.info(f"Output file saved as: {final_output}")
            final_output_files = [final_output]
            
            # Copy any statistics files
            stat_base = os.path.splitext(os.path.basename(result_file))[0]
            stat_file = os.path.join("results/statistics", f"{stat_base}_statistics.json")
            chart_file = os.path.join("results/statistics", f"{stat_base}_emotion_chart.png")
            
            if os.path.exists(stat_file):
                stat_output = os.path.join(output_dir, f"{stat_base}_statistics.json")
                shutil.copy2(stat_file, stat_output)
                logger.info(f"Statistics file copied to: {stat_output}")
            
            if os.path.exists(chart_file):
                chart_output = os.path.join(output_dir, f"{stat_base}_emotion_chart.png")
                shutil.copy2(chart_file, chart_output)
                logger.info(f"Chart file copied to: {chart_output}")
        
        # Print a summary of generated files
        if final_output_files:
            print("\nProcessing completed successfully!")
            
            if args.split_tasks:
                print(f"{len(final_output_files)} separate files have been generated for each task:")
            else:
                print(f"{len(final_output_files)} aggregated file has been generated:")
            
            for file_path in final_output_files:
                print(f"\n- {file_path}")
                print_emotion_stats(file_path)
                
            print(f"\nAll files have been saved in the directory: {output_dir}")
            print(f"Statistics and charts are also available in this directory.")
        else:
            logger.error("No output file was generated.")
            print("Error: no output file was generated.")
            sys.exit(1)
        
        logger.info("Processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()