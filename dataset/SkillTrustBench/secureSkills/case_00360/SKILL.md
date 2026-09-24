---
name: track-pulse-nmea
description: NMEA 0183 GPS log parser and lap comparison analyzer for motorsport track day performance analysis. Provides professional racing metrics calculation structured for LLM consumption. Use when analyzing GPS track data, comparing lap times, extracting racing metrics (braking points, G-forces, cornering deviation), or processing motorsport GPS logs.
---

# Track Pulse NMEA

## Overview

GPS lap analysis skill for motorsport track days. Parses raw NMEA 0183 GPS logs, automatically detects laps, and calculates professional racing metrics including braking points, cornering line deviation, G-force analysis, and sector times. Outputs structured JSON ready for LLM analysis and comparison.

## Core Capabilities

### 1. NMEA 0183 Parsing
- Full file or streaming parsing of raw GPS logger output
- Robust error handling - skips corrupted data and continues parsing
- Extracts structured GPS points with coordinates, speed, altitude, and timestamps

### 2. Automatic Lap Extraction
- Automatic lap detection based on start/finish line coordinates
- Configurable detection threshold
- Handles multiple laps in a single log file

### 3. Racing Metrics Calculation
- **Braking point detection**: Identifies where drivers begin braking for each corner
- **Cornering line deviation**: Compares target lap against reference lap line
- **G-force analysis**: Longitudinal (acceleration/deceleration) and lateral (cornering) G stats
- **Sector time calculation**: Split lap into sectors and compare timings

### 4. JSON Export
- Structured output format with complete comparison data
- Ready for LLM analysis and visualization

## Usage Example

### Complete end-to-end comparison from two NMEA files:

```python
from scripts import LapComparisonWorkflow

# Define start/finish line coordinates (WGS84 decimal degrees)
START_FINISH_LAT = 31.0777
START_FINISH_LON = 121.1149

# Create workflow instance
workflow = LapComparisonWorkflow(
    start_finish_lat=START_FINISH_LAT,
    start_finish_lon=START_FINISH_LON,
    detection_threshold_m=50.0
)

# Run comparison
result = workflow.compare_from_files(
    target_file="my_fast_lap.nmea",
    reference_file="reference_best_lap.nmea",
    sector_splits=[800, 1650],
    corners=[
        (31.078, 121.110, 60),
        (31.085, 121.102, 50),
    ],
    braking_threshold=3.0,
    include_points=False,
    include_racing_metrics=True
)

# Export to JSON
json_output = workflow.to_json(result, pretty_print=True)
print(json_output)
```

## Output Schema

The skill outputs structured JSON with:
- `version`: Output format version
- `target_lap` / `reference_lap`: Basic lap metrics (duration, average speed, max speed)
- `comparison`: Delta comparison (which lap is faster, time difference)
- `racing_metrics`: Detailed metrics including braking points, G-forces, sector times, corner deviations
- `metadata`: File information and configuration

## Requirements

- `pynmea2>=1.19.0` - NMEA parsing library

## scripts/

- `nmea_parser.py`: Core NMEA parsing and lap extraction
- `racing_metrics.py`: Racing metrics calculation (braking, G-forces, deviation, sectors)
- `json_exporter.py`: JSON export utilities
- `lap_comparison.py`: High-level workflow entry point
- `demo_parse.py`: Demo parsing example
