# -*- coding: utf-8 -*-
# Complete Lap Comparison Workflow - US-013
# Parse target and reference files → calculate metrics → output comparison JSON

import logging
from skill.nmea_parser import NMEAParser, LapData
from skill.racing_metrics import RacingMetricsCalculator
from skill.json_exporter import LapJsonExporter

logger = logging.getLogger(__name__)


class LapComparisonWorkflow:
    """
    Complete end-to-end lap comparison workflow:
    1. Parse NMEA files for target and reference
    2. Extract laps based on start/finish coordinates
    3. Calculate all racing metrics
    4. Output structured JSON comparison for LLM
    """

    def __init__(self, start_finish_lat, start_finish_lon, detection_threshold_m=15.0):
        """
        Initialize workflow.
        
        Args:
            start_finish_lat: Start/Finish line latitude
            start_finish_lon: Start/Finish line longitude
            detection_threshold_m: Detection threshold for start/finish crossing
        """
        self.start_finish_lat = start_finish_lat
        self.start_finish_lon = start_finish_lon
        self.detection_threshold_m = detection_threshold_m

    def compare_from_files(self, target_file, reference_file,
                           sector_splits=None, corners=None,
                           braking_threshold=3.0,
                           include_points=False,
                           include_racing_metrics=True):
        """
        Complete comparison from two NMEA files.
        
        Args:
            target_file: Path to target lap NMEA file
            reference_file: Path to reference lap NMEA file
            sector_splits: Optional list of sector split distances (meters from start)
            corners: Optional list of (lat, lon, radius) for corner deviation analysis
            braking_threshold: Deceleration threshold for braking detection (m/s²)
            include_points: Include all GPS points in JSON output
            include_racing_metrics: Calculate and include racing metrics
        
        Returns:
            JSON-ready dict with complete comparison
        """
        # Parse both files
        parser = NMEAParser()
        logger.info("Parsing target file: {}".format(target_file))
        target_points = parser.parse_file(target_file)
        logger.info("Parsing reference file: {}".format(reference_file))
        ref_points = parser.parse_file(reference_file)

        # Extract laps based on start/finish detection
        logger.info("Extracting laps from target...")
        target_laps = parser.extract_laps(
            target_points, 
            self.start_finish_lat, 
            self.start_finish_lon, 
            self.detection_threshold_m
        )
        logger.info("Extracting laps from reference...")
        ref_laps = parser.extract_laps(
            ref_points,
            self.start_finish_lat,
            self.start_finish_lon,
            self.detection_threshold_m
        )

        if len(target_laps) == 0:
            logger.error("No valid laps detected in target file")
            raise ValueError("No valid laps detected in target file. Check start/finish coordinates.")
        if len(ref_laps) == 0:
            logger.error("No valid laps detected in reference file")
            raise ValueError("No valid laps detected in reference file. Check start/finish coordinates.")

        # Use the last complete lap from each file
        # Typically the fastest/most recent is last
        target_lap = target_laps[-1]
        reference_lap = ref_laps[-1]

        logger.info("Target: {} points, {:.2f}s".format(target_lap.point_count, target_lap.duration))
        logger.info("Reference: {} points, {:.2f}s".format(reference_lap.point_count, reference_lap.duration))

        # Export to JSON with metrics
        exporter = LapJsonExporter()
        result = exporter.export_lap_comparison(
            target_lap,
            reference_lap,
            include_points=include_points,
            calculate_racing_metrics=include_racing_metrics,
            sector_splits=sector_splits,
            corners=corners,
            braking_threshold=braking_threshold
        )

        # Add extra metadata
        result['metadata'] = {
            'target_file': target_file,
            'reference_file': reference_file,
            'target_lap_index': len(target_laps) - 1,
            'reference_lap_index': len(ref_laps) - 1,
            'total_laps_target': len(target_laps),
            'total_laps_reference': len(ref_laps),
            'start_finish_lat': self.start_finish_lat,
            'start_finish_lon': self.start_finish_lon
        }

        return result

    def compare_single_lap_file(self, nmea_file, reference_lap,
                                 sector_splits=None, corners=None,
                                 braking_threshold=3.0,
                                 include_points=False,
                                 include_racing_metrics=True):
        """
        Compare a new NMEA file against an already extracted reference lap.
        
        Args:
            nmea_file: Path to target NMEA file
            reference_lap: Already extracted LapData reference object
            Other args same as compare_from_files
        
        Returns:
            JSON-ready dict with complete comparison
        """
        parser = NMEAParser()
        target_points = parser.parse_file(nmea_file)
        target_laps = parser.extract_laps(
            target_points,
            self.start_finish_lat,
            self.start_finish_lon,
            self.detection_threshold_m
        )

        if len(target_laps) == 0:
            logger.error("No valid laps detected in target file")
            raise ValueError("No valid laps detected in target file. Check start/finish coordinates.")

        target_lap = target_laps[-1]

        exporter = LapJsonExporter()
        result = exporter.export_lap_comparison(
            target_lap,
            reference_lap,
            include_points=include_points,
            calculate_racing_metrics=include_racing_metrics,
            sector_splits=sector_splits,
            corners=corners,
            braking_threshold=braking_threshold
        )

        result['metadata'] = {
            'target_file': nmea_file,
            'target_lap_index': len(target_laps) - 1,
            'total_laps_target': len(target_laps),
            'start_finish_lat': self.start_finish_lat,
            'start_finish_lon': self.start_finish_lon
        }

        return result

    @staticmethod
    def to_json(data, pretty_print=True):
        """Convert comparison result to JSON string."""
        return LapJsonExporter.to_json_string(data, pretty_print=pretty_print)
