import pandas as pd
import io
import os
from pathlib import Path
import re
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

from utils import emotion_primary_patterns

def sanitize_dataset(file_path: str, output_dir: str, logger: logging.Logger) -> str:
    """
    Sanitizes a CSV file:
    - Removes rows with "Invalid" expression
    - Handles decimal number formatting issues
    
    Args:
        file_path: Path of the file to sanitize
        output_dir: Output directory
        logger: Logger for logging
        
    Returns:
        Path of the sanitized file
    """
    logger.info(f"Sanitizing file: {file_path}")
    
    # Read the file as text for pre-processing
    with open(file_path, "r") as file:
        content = file.read()
    
    # Split into lines
    lines = content.strip().split("\n")
    header = lines[0]
    processed_lines = [header]

    for line in lines[1:]:
        # Skip lines with "Invalid" expression
        if ",Invalid," in line:
            logger.debug(f"Line with 'Invalid' ignored: {line}")
            continue

        # Split by comma
        parts = line.split(",")

        # If there are 4 parts, it means the decimal number uses a comma
        # and we need to replace it with a period
        if len(parts) == 4:
            fixed_line = f"{parts[0]},{parts[1]},{parts[2]}.{parts[3]}"
            processed_lines.append(fixed_line)
        else:
            processed_lines.append(line)

    # Join the processed lines
    processed_content = "\n".join(processed_lines)
    
    # Create the output file name
    base_name = os.path.basename(file_path)
    output_file = os.path.join(output_dir, f"sanitized_{base_name}")
    
    # Use pandas to read and save the data
    df = pd.read_csv(io.StringIO(processed_content))
    df.to_csv(output_file, index=False)
    
    logger.info(f"Sanitized file saved as: {output_file}")
    return output_file

def split_tasks_data(file_path: str, logger: logging.Logger) -> List[Tuple[pd.DataFrame, str]]:
    """
    Splits a CSV file into multiple DataFrames when task division rows are encountered.
    Returns a list of tuples (DataFrame, task_name).
    
    Args:
        file_path: Path of the file to split
        logger: Logger for logging
        
    Returns:
        List of tuples (DataFrame, task_name)
    """
    logger.info(f"Splitting the file by task: {file_path}")
    
    # Regex pattern to identify task division rows
    task_pattern = re.compile(r'#+\s*New level - TASK (\d+)\s*#+')
    
    # Read the file
    with open(file_path, "r") as file:
        content = file.read()
    
    # Split into lines
    lines = content.strip().split("\n")
    header = lines[0]
    
    # List to keep track of task start indices and task numbers
    task_boundaries = []
    task_numbers = []
    
    # Find all task division rows
    for i, line in enumerate(lines):
        match = task_pattern.match(line)
        if match:
            task_number = match.group(1)
            task_boundaries.append(i)
            task_numbers.append(task_number)
            logger.debug(f"Found delimiter for TASK {task_number} at line {i}")
    
    # If there are no task divisions, return the complete DataFrame
    if not task_boundaries:
        logger.info(f"No task delimiters found in file {file_path}")
        df = pd.read_csv(file_path)
        return [(df, "task_1")]
    
    # List of created DataFrames
    task_dataframes = []
    
    # Handle the first task (from the beginning to the first delimiter)
    first_task_end = task_boundaries[0]
    if first_task_end > 1:  # If there's data before the first delimiter
        first_task_content = "\n".join(lines[:first_task_end])
        first_task_df = pd.read_csv(io.StringIO(first_task_content))
        task_dataframes.append((first_task_df, "task_1"))
        logger.info(f"DataFrame for TASK 1 created with {len(first_task_df)} rows")
    
    # Create a DataFrame for each subsequent task
    for i in range(len(task_boundaries)):
        start_idx = task_boundaries[i] + 1  # Skip the division row
        
        if i < len(task_boundaries) - 1:
            end_idx = task_boundaries[i + 1]
        else:
            end_idx = len(lines)
        
        # Make sure there's data to extract
        if start_idx >= end_idx:
            logger.warning(f"Task {task_numbers[i]} empty, ignored")
            continue
        
        # Create a new DataFrame with the task data
        task_content = [header] + lines[start_idx:end_idx]
        # Remove any additional delimiters
        task_content = [line for line in task_content if not task_pattern.match(line)]
        
        task_content_str = "\n".join(task_content)
        task_df = pd.read_csv(io.StringIO(task_content_str))
        
        # Use the task number from the delimiter
        task_num = int(task_numbers[i])
        task_name = f"task_{task_num+1}"
        
        # Skip task 14
        if task_num+1 == 14:
            logger.info(f"Task 14 skipped as requested")
            continue
        
        task_dataframes.append((task_df, task_name))
        logger.info(f"DataFrame for TASK {task_num+1} created with {len(task_df)} rows")
    
    return task_dataframes

def aggregate_by_second(df: pd.DataFrame, output_file: Optional[str] = None) -> pd.DataFrame:
    """
    Groups data by second (ignoring milliseconds) and calculates the average Weight
    for each Expression in that time interval.

    Args:
        df: DataFrame with the data
        output_file: Output file name (optional)

    Returns:
        DataFrame with aggregated data
    """
    # DEBUG: Analyze the Weight column
    print(f"DEBUG - Available columns: {df.columns.tolist()}")
    print(f"DEBUG - Weight column type: {df['Weight'].dtype}")
    print(f"DEBUG - First 10 Weight values: {df['Weight'].head(10).tolist()}")
    print(f"DEBUG - Unique Weight values (first 20): {df['Weight'].unique()[:20]}")
    print(f"DEBUG - Null values in Weight: {df['Weight'].isnull().sum()}")
    print(f"DEBUG - DataFrame shape: {df.shape}")
    
    # Check for non-numeric values
    non_numeric = df[pd.to_numeric(df['Weight'], errors='coerce').isnull() & df['Weight'].notna()]
    if len(non_numeric) > 0:
        print(f"DEBUG - Non-numeric values found: {non_numeric['Weight'].unique()}")
        print(f"DEBUG - Number of non-numeric values: {len(non_numeric)}")
    
    # Extract only the time without milliseconds (taking everything up to the period and keeping AM/PM)
    df["TimeSecond"] = df["Time"].apply(
        lambda x: x.split(".")[0] + " " + x.split(" ")[1]
    )

    # Convert Weight to numeric, replacing non-numeric values with NaN
    df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce')
    
    # Remove rows with NaN Weight
    original_len = len(df)
    df = df.dropna(subset=['Weight'])
    if len(df) < original_len:
        print(f"DEBUG - Removed {original_len - len(df)} rows with invalid Weight")

    # Group by TimeSecond and Expression, and calculate the average Weight
    aggregated_df = (
        df.groupby(["TimeSecond", "Expression"])["Weight"].mean().reset_index()
    )

    # Rename TimeSecond to Time
    aggregated_df.rename(columns={"TimeSecond": "Time"}, inplace=True)

    if output_file:
        aggregated_df.to_csv(output_file, index=False)

    return aggregated_df

def detect_emotions(df: pd.DataFrame, output_file: Optional[str] = None) -> pd.DataFrame:
    """
    Detects primary emotions based on facial expression patterns.
    For each AU group, at least one of the variants (L or R) must be present.
    
    Args:
        df: DataFrame with data aggregated by second
        output_file: Output file name (optional)
        
    Returns:
        DataFrame with timestamps and detected emotions ordered by intensity
    """
    # Emotion results
    all_results = []
    
    # Process each timestamp separately
    for time, group in df.groupby('Time'):
        # Create a dictionary to map expression to weight
        expression_to_weight = dict(zip(group['Expression'], group['Weight']))
        
        # Calculate the intensity of each primary emotion
        emotion_intensities = {}
        
        for emotion, pattern_groups in emotion_primary_patterns.items():
            # Check if each AU group is activated (at least one L or R variant)
            all_groups_active = True
            group_weights = []
            
            for au_group in pattern_groups:
                # Check if at least one variant in the group is present
                group_active = False
                max_weight_in_group = 0
                
                for au in au_group:
                    if au in expression_to_weight and expression_to_weight[au] > 0:
                        group_active = True
                        if expression_to_weight[au] > max_weight_in_group:
                            max_weight_in_group = expression_to_weight[au]
                
                # If no variant of the group is active, the emotion is not activated
                if not group_active:
                    all_groups_active = False
                    break
                
                # Add the maximum weight for this group
                group_weights.append(max_weight_in_group)
            
            # Calculate the average intensity only if all groups are active
            if all_groups_active:
                emotion_intensities[emotion] = sum(group_weights) / len(group_weights)
            else:
                emotion_intensities[emotion] = 0
        
        # Normalize emotion intensities for this timestamp
        total_intensity = sum(emotion_intensities.values())
        if total_intensity > 0:  # Avoid division by zero
            for emotion in emotion_intensities:
                emotion_intensities[emotion] /= total_intensity
        
        # Sort emotions by intensity (from most intense to least intense)
        sorted_emotions = sorted(
            emotion_intensities.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Add results for this timestamp
        time_results = []
        for emotion, intensity in sorted_emotions:
            time_results.append({
                'Time': time,
                'Emotion': emotion,
                'Intensity': intensity
            })
        
        all_results.extend(time_results)
    
    # Create a DataFrame from results
    results_df = pd.DataFrame(all_results)
    
    if output_file:
        results_df.to_csv(output_file, index=False)
    
    return results_df

def create_final_dataset(emotions_df: pd.DataFrame, threshold: float = 0.25, 
                         output_file: Optional[str] = None) -> pd.DataFrame:
    """
    Creates a final dataset with a single row per timestamp, containing
    the intensity of all 6 emotions and the dominant emotion.
    
    Args:
        emotions_df: DataFrame with emotion data (output from detect_emotions)
        threshold: Minimum intensity threshold to consider an emotion (default: 0.25)
        output_file: Output file name (optional)
        
    Returns:
        DataFrame with the final dataset
    """
    # List of all emotions
    all_emotions = ["happiness", "sadness", "surprise", "fear", "anger", "disgust"]
    
    # Prepare a dictionary to contain results
    final_results = []
    
    # For each timestamp, find the dominant emotion
    for time, group in emotions_df.groupby('Time'):
        # Create a dictionary to map emotion to intensity
        emotion_to_intensity = dict(zip(group['Emotion'], group['Intensity']))
        
        # Find the emotion with maximum intensity
        max_emotion = max(emotion_to_intensity.items(), key=lambda x: x[1])
        dominant_emotion = max_emotion[0]
        dominant_intensity = max_emotion[1]
        
        # If intensity is below threshold, label as "neutral"
        if dominant_intensity < threshold:
            dominant_emotion = "neutral"
        
        # Prepare a row for this timestamp
        row = {'Time': time, 'DominantEmotion': dominant_emotion}
        
        # Add the intensity of each emotion
        for emotion in all_emotions:
            row[emotion] = emotion_to_intensity.get(emotion, 0)
        
        final_results.append(row)
    
    # Create a DataFrame from results
    final_df = pd.DataFrame(final_results)
    
    # Reorder columns
    columns = ['Time'] + all_emotions + ['DominantEmotion']
    final_df = final_df[columns]
    
    if output_file:
        final_df.to_csv(output_file, index=False)
    
    return final_df

def generate_statistics(df: pd.DataFrame, output_base_path: str, task_name: Optional[str] = None, logger: logging.Logger = None) -> Dict:
    """
    Generates and saves statistics based on the processed emotion data.
    
    Args:
        df: DataFrame with emotion data
        output_base_path: Base path for output files (without extension)
        task_name: Name of the task (optional)
        logger: Logger for logging
    
    Returns:
        Dictionary with statistics data
    """
    stats = {}
    
    if logger:
        logger.info(f"Generating statistics for {os.path.basename(output_base_path)}")
    
    # Basic record counts
    stats["total_records"] = len(df)
    stats["timestamps"] = df["Time"].nunique()
    
    # Emotion statistics
    if 'DominantEmotion' in df.columns:
        emotion_counts = df['DominantEmotion'].value_counts().to_dict()
        emotion_percentages = (df['DominantEmotion'].value_counts(normalize=True) * 100).to_dict()
        
        stats["emotion_counts"] = emotion_counts
        stats["emotion_percentages"] = {k: f"{v:.2f}%" for k, v in emotion_percentages.items()}
        
        # Find the most common emotion
        most_common_emotion = max(emotion_counts.items(), key=lambda x: x[1])
        stats["most_common_emotion"] = {
            "emotion": most_common_emotion[0],
            "count": most_common_emotion[1],
            "percentage": stats["emotion_percentages"][most_common_emotion[0]]
        }
    
    # Average intensity of each emotion
    all_emotions = ["happiness", "sadness", "surprise", "fear", "anger", "disgust"]
    avg_intensities = {}
    for emotion in all_emotions:
        if emotion in df.columns:
            avg_intensities[emotion] = df[emotion].mean()
    
    stats["average_intensities"] = avg_intensities
    
    # If task name is provided, add it to the statistics
    if task_name:
        stats["task_name"] = task_name
    
    # Add timestamp for when the statistics were generated
    stats["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save statistics to JSON file
    stats_file = f"{output_base_path}_statistics.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)
    
    if logger:
        logger.info(f"Statistics saved to {stats_file}")
    
    # Generate a pie chart of emotion distribution
    if 'DominantEmotion' in df.columns:
        try:
            plt.figure(figsize=(10, 7))
            emotion_counts = df['DominantEmotion'].value_counts()
            
            # Use a nice color palette
            colors = plt.cm.tab10(np.arange(len(emotion_counts)))
            
            # Create pie chart
            plt.pie(emotion_counts, labels=emotion_counts.index, autopct='%1.1f%%', startangle=140, colors=colors)
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.title('Distribution of Emotions')
            
            # Save the chart
            chart_file = f"{output_base_path}_emotion_chart.png"
            plt.savefig(chart_file)
            plt.close()
            
            if logger:
                logger.info(f"Emotion distribution chart saved to {chart_file}")
        except Exception as e:
            if logger:
                logger.warning(f"Could not generate emotion chart: {str(e)}")
    
    return stats

def process_task_data(task_df: pd.DataFrame, task_name: str, threshold: float, 
                      logger: logging.Logger, split_output_files: bool = False) -> pd.DataFrame:
    """
    Processes data from a single task.
    
    Args:
        task_df: DataFrame with task data
        task_name: Task name (e.g., "task_1")
        threshold: Threshold to consider an emotion valid
        logger: Logger for logging
        split_output_files: If True, save intermediate files for this task
        
    Returns:
        DataFrame with the final dataset for this task
    """
    logger.info(f"Processing task: {task_name}")
    
    # Aggregation by second
    aggregated_df = aggregate_by_second(task_df)
    if split_output_files:
        aggregated_file = os.path.join("results/aggregated", f"{task_name}_aggregated.csv")
        aggregated_df.to_csv(aggregated_file, index=False)
        logger.info(f"Aggregation saved: {aggregated_file}")
    
    # Emotion detection
    emotions_df = detect_emotions(aggregated_df)
    if split_output_files:
        emotions_file = os.path.join("results/emotions", f"{task_name}_emotions.csv")
        emotions_df.to_csv(emotions_file, index=False)
        logger.info(f"Emotions saved: {emotions_file}")
    
    # Final dataset
    final_df = create_final_dataset(emotions_df, threshold)
    if split_output_files:
        final_file = os.path.join("results/final", f"{task_name}_final.csv")
        final_df.to_csv(final_file, index=False)
        logger.info(f"Final dataset saved: {final_file}")
    
    # Add a column with the task name (will be removed in the final output)
    final_df['Task'] = task_name
    
    return final_df

def process_file(file_path: str, threshold: float, logger: logging.Logger, 
                 split_output_files: bool = False) -> str:
    """
    Processes a single CSV file through all processing phases.
    
    Args:
        file_path: Path of the file to process
        threshold: Threshold to consider an emotion valid
        logger: Logger for logging
        split_output_files: If True, create separate files for each task
        
    Returns:
        Path of the final results file
    """
    logger.info(f"Starting to process file: {file_path}")
    
    # Base name for output files
    base_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(base_name)[0]
    
    # Split the file into tasks
    task_data_list = split_tasks_data(file_path, logger)
    logger.info(f"File split into {len(task_data_list)} tasks")
    
    # List to contain all final results
    all_final_results = []
    
    # Process each task
    for task_df, task_name in task_data_list:
        final_df = process_task_data(task_df, task_name, threshold, logger, split_output_files)
        all_final_results.append(final_df)
    
    # Create directories for statistics files if they don't exist
    Path("results/statistics").mkdir(exist_ok=True, parents=True)
    
    if split_output_files:
        # Original mode: one file per task
        result_files = []
        for i, final_df in enumerate(all_final_results):
            task_name = task_data_list[i][1]
            if len(all_final_results) == 1:
                # If there's only one task, use the base name of the input file
                final_name = f"{name_without_ext}_final.csv"
            else:
                # If there are multiple tasks, use the task name
                final_name = f"{name_without_ext}_{task_name}_final.csv"
            
            # Remove the Task column before saving
            if 'Task' in final_df.columns:
                final_df = final_df.drop(columns=['Task'])
            
            final_file = os.path.join("results/final", final_name)
            final_df.to_csv(final_file, index=False)
            
            # Generate statistics for this task
            stats_base_path = os.path.join("results/statistics", f"{name_without_ext}_{task_name}")
            generate_statistics(final_df, stats_base_path, task_name, logger)
            
            result_files.append(final_file)
            logger.info(f"Final file saved: {final_file}")
        
        return result_files[0] if len(result_files) == 1 else result_files
    else:
        # Aggregated mode: a single file with all tasks
        combined_df = pd.concat(all_final_results, ignore_index=True)
        
        # Remove the Task column before saving
        if 'Task' in combined_df.columns:
            combined_df = combined_df.drop(columns=['Task'])
        
        final_file = os.path.join("results/final", f"{name_without_ext}_final.csv")
        combined_df.to_csv(final_file, index=False)
        
        # Generate statistics for the combined file
        stats_base_path = os.path.join("results/statistics", f"{name_without_ext}")
        generate_statistics(combined_df, stats_base_path, None, logger)
        
        logger.info(f"Final aggregated file saved: {final_file}")
        
        return final_file

def process_files(file_paths: List[str], threshold: float, logger: logging.Logger, 
                  split_output_files: bool = False) -> List[str]:
    """
    Processes a list of CSV files.
    
    Args:
        file_paths: List of file paths to process
        threshold: Threshold to consider an emotion valid
        logger: Logger for logging
        split_output_files: If True, create separate files for each task
        
    Returns:
        List of paths of the final results files
    """
    logger.info(f"Starting to process {len(file_paths)} files")
    logger.info(f"Split output files: {split_output_files}")
    
    # Create directories to organize different types of files
    dirs_to_create = ["results", "results/sanitized", "results/final", "results/statistics"]
    if split_output_files:
        dirs_to_create.extend(["results/aggregated", "results/emotions"])
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(exist_ok=True, parents=True)
    
    result_files = []
    
    for file_path in file_paths:
        try:
            # Sanitize the file
            sanitized_file = sanitize_dataset(file_path, "results/sanitized", logger)
            logger.info(f"Sanitized file: {sanitized_file}")
            
            # Process the file
            result_file = process_file(sanitized_file, threshold, logger, split_output_files)
            
            # Handle the case where process_file returns a list or a single file
            if isinstance(result_file, list):
                result_files.extend(result_file)
            else:
                result_files.append(result_file)
            
            logger.info(f"Processing completed for {file_path}")
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
    
    return result_files