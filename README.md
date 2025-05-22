# Emotion Recognition System

## Overview

This system analyzes facial expressions to detect emotions in real-time. It uses facial expression tracking data (Action Units) to identify six primary emotions: happiness, sadness, surprise, fear, anger, and disgust. The system processes CSV files containing facial expression data from sensors or computer vision systems.

## Project Structure

- `main.py`: FastAPI web server for the user interface
- `processing.py`: Main functions for data processing
- `utils.py`: Utilities, including the definition of emotion patterns
- `logging_utils.py`: Utilities for logging

## Processing Pipeline

The data processing pipeline proceeds through the following phases:

1. **Data loading and sanitization**
   - Removal of rows with invalid expressions
   - Correction of numerical formats
   - Splitting files into separate tasks (if present)

2. **Aggregation by second**
   - Grouping data by second, ignoring milliseconds
   - Calculating the average weight for each expression in each time interval

3. **Emotion detection** (detailed in the next section)
   - Identification of emotions present in each timestamp
   - Calculation of the intensity of each emotion

4. **Creation of the final dataset**
   - Generation of a dataset with a single row per timestamp
   - Inclusion of the intensity of all 6 emotions
   - Identification of the dominant emotion by applying a threshold

## Emotion Recognition Pipeline (Step-by-Step)

Emotion recognition is based on specific patterns of Action Units (AU). The key is in the structure of the `emotion_primary_patterns` dictionary and the detection algorithm.

### 1. Emotion Pattern Structure

Each emotion is defined by a set of AU groups. For each group, it is sufficient that at least one of the variants (L or R) is present to consider that group activated:

```python
# Example for happiness
"happiness": [
    ["CheekRaiserL", "CheekRaiserR"],        # AU6 (L or R)
    ["LipCornerPullerL", "LipCornerPullerR"]  # AU12 (L or R)
]
```

This means that to recognize happiness, it is necessary that:
- AU6 left OR AU6 right (cheek raising) is present
- AND AU12 left OR AU12 right (lip corner pulling) is present

### 2. Detection Algorithm (Detailed)

For each timestamp, the process is as follows:

1. **Collection of present expressions**:
   - Creation of a dictionary that maps each expression to its weight

2. **Emotion analysis**:
   - For each emotion defined in the patterns:
     - For each AU group in this emotion:
       - Check if at least one AU of the group is present (with weight > 0)
       - If a group is completely absent, the emotion is not recognized
       - If all groups are present, calculate the emotion's intensity

3. **Intensity calculation**:
   - For each activated AU group, the maximum weight among the variants is considered
   - The emotion's intensity is the average of the maximum weights of all groups
   - Intensities are normalized (divided by the total sum)

4. **Sorting**:
   - Emotions are sorted by intensity (from strongest to weakest)

### Complete Calculation Example

Let's take as an example a timestamp with these active expressions:
- CheekRaiserL: 0.8
- LipCornerPullerR: 0.6
- BrowLowererL: 0.3

For happiness:
- Group 1 (AU6): CheekRaiserL present with weight 0.8 → Group activated
- Group 2 (AU12): LipCornerPullerR present with weight 0.6 → Group activated
- All groups are activated → Intensity = (0.8 + 0.6) / 2 = 0.7

For anger:
- Group 1 (AU4): BrowLowererL present with weight 0.3 → Group activated
- Group 2 (AU5): no variant present → Group not activated
- At least one group is not activated → Intensity = 0

For sadness and other emotions: same logic, but in this case no other emotion is recognized because essential AU groups are missing.

### Normalization:
- Total intensity: 0.7 (happiness) + 0 (other emotions) = 0.7
- Normalized intensity for happiness: 0.7 / 0.7 = 1.0
- Result: 100% happiness

## Configuration and Usage

### Prerequisites
- Python 3.8+
- FastAPI
- Pandas
- Other requirements in `requirements.txt`

### Installation
```bash
pip install -r requirements.txt
```

### Execution
```bash
python main.py
```

The application will be available at `http://localhost:8000`

### File Upload
1. Access the web interface
2. Upload one or more CSV files with facial expression data
3. Set the threshold for emotion detection (default: 0.2)
4. Start processing

### Input File Format
The CSV file must contain the following columns:
- Time: timestamp in the format "HH:MM:SS.sss AM/PM"
- Expression: name of the facial expression (e.g., "CheekRaiserL")
- Weight: weight/intensity of the expression (numerical value)

## Notes on Threshold and Sensitivity

The threshold defined by the user determines when an emotion is considered dominant:
- If the normalized intensity of the strongest emotion is below the threshold, the emotional state is labeled as "neutral"
- Lower threshold values increase the system's sensitivity
- Higher values reduce false positives but might not detect more subtle emotions

## Troubleshooting

If the system does not correctly detect emotions:
- Verify that the CSV files contain all the necessary Action Units
- Check that the data format is correct
- Lower the threshold to increase sensitivity
- Examine the logs to identify any errors

---

## Additional Technical Documentation

### Action Units → Emotions Mapping

Emotions are defined by the following Action Unit patterns:

| Emotion | AU Pattern |
|----------|---------------|
| Happiness | AU6 (L/R) + AU12 (L/R) |
| Sadness | AU1 (L/R) + AU4 (L/R) + AU15 (L/R) |
| Surprise | AU1 (L/R) + AU2 (L/R) + AU5 (L/R) + AU26 |
| Fear | AU1 (L/R) + AU2 (L/R) + AU4 (L/R) + AU5 (L/R) + AU20 (L/R) + AU26 |
| Anger | AU4 (L/R) + AU5 (L/R) + AU7 (L/R) + AU23 (L/R) + AU24 (L/R) |
| Disgust | AU9 (L/R) + AU10 (L/R) + AU15 (L/R) + AU16 (L/R) + AU17 |

Where:
- (L/R) indicates that the presence of the left OR right version of the AU is sufficient
- For each emotion, all listed AUs must be present (in at least one L or R variant)