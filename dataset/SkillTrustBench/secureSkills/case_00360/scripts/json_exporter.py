# -*- coding: utf-8 -*-
# JSON Exporter for NMEA parsed lap data
# US-005: Output structured JSON metrics for LLM consumption

import json
import logging
from skill.nmea_parser import LapData, GPSPoint
from skill.racing_metrics import RacingMetricsCalculator

logger = logging.getLogger(__name__)


class LapJsonExporter:
    """
    Export lap comparison data to structured JSON format for LLM analysis.
    Provides comprehensive metrics comparing a target lap against a reference lap.
    """

    @staticmethod
    def export_lap_comparison(target_lap, reference_lap, 
                              include_points=False,
                              calculate_racing_metrics=False,
                              sector_splits=None,
                              corners=None,
                              braking_threshold=3.0):
        """
        Export a comparison between target lap and reference lap as JSON.

        Args:
            target_lap: LapData object of the target lap to analyze
            reference_lap: LapData object of the reference lap for comparison
            include_points: whether to include all GPS points in output (default False)
            calculate_racing_metrics: enable braking/G-force/sector/corner deviation calculation (default False)
            sector_splits: list of sector split distances from start (optional)
            corners: list of (lat, lon, radius) for corner deviation analysis (optional)
            braking_threshold: deceleration threshold for braking detection (default 3.0 m/s²)
        
        Returns:
            dict structure ready for json.dumps
        """
        # Basic lap metrics
        target_duration = target_lap.duration
        ref_duration = reference_lap.duration
        delta_duration = target_duration - ref_duration
        delta_percent = (delta_duration / ref_duration) * 100 if ref_duration > 0 else 0

        # Speed statistics
        target_speed_stats = LapJsonExporter._calculate_speed_stats(target_lap)
        ref_speed_stats = LapJsonExporter._calculate_speed_stats(reference_lap)

        # Point counts and completeness
        target_info = {
            'duration_seconds': round(target_duration, 3),
            'point_count': target_lap.point_count,
            'average_speed_ms': round(target_speed_stats.get('avg', 0), 3),
            'max_speed_ms': round(target_speed_stats.get('max', 0), 3),
            'min_speed_ms': round(target_speed_stats.get('min', 0), 3)
        }

        reference_info = {
            'duration_seconds': round(ref_duration, 3),
            'point_count': reference_lap.point_count,
            'average_speed_ms': round(ref_speed_stats.get('avg', 0), 3),
            'max_speed_ms': round(ref_speed_stats.get('max', 0), 3),
            'min_speed_ms': round(ref_speed_stats.get('min', 0), 3)
        }

        comparison = {
            'delta_duration_seconds': round(delta_duration, 3),
            'delta_duration_percent': round(delta_percent, 2),
            'target_is_faster': delta_duration < 0,
            'delta_speed_avg_ms': round(target_speed_stats.get('avg', 0) - ref_speed_stats.get('avg', 0), 3),
            'delta_max_speed_ms': round(target_speed_stats.get('max', 0) - ref_speed_stats.get('max', 0), 3)
        }

        # Build complete output
        output = {
            'version': '1.1',  # Updated for US-006 racing metrics
            'target_lap': target_info,
            'reference_lap': reference_info,
            'comparison': comparison
        }

        # Add professional racing metrics if requested
        if calculate_racing_metrics:
            from skill.racing_metrics import RacingMetricsCalculator
            calculator = RacingMetricsCalculator()
            target_metrics = calculator.calculate_full_lap_metrics(
                target_lap, reference_lap, corners, sector_splits, braking_threshold
            )
            ref_metrics = calculator.calculate_full_lap_metrics(
                reference_lap, None, None, sector_splits, braking_threshold
            )
            output['racing_metrics'] = {
                'target': target_metrics,
                'reference': ref_metrics
            }

        # Optionally include GPS points for detailed analysis
        if include_points:
            output['target_lap']['points'] = LapJsonExporter._export_points(target_lap)
            output['reference_lap']['points'] = LapJsonExporter._export_points(reference_lap)

        return output

    @staticmethod
    def export_single_lap(lap, include_points=False):
        """
        Export a single lap metrics to JSON without comparison.

        Args:
            lap: LapData object
            include_points: whether to include all GPS points
        
        Returns:
            dict structure ready for json.dumps
        """
        speed_stats = LapJsonExporter._calculate_speed_stats(lap)

        output = {
            'version': '1.0',
            'lap': {
                'duration_seconds': round(lap.duration, 3),
                'point_count': lap.point_count,
                'average_speed_ms': round(speed_stats.get('avg', 0), 3),
                'max_speed_ms': round(speed_stats.get('max', 0), 3),
                'min_speed_ms': round(speed_stats.get('min', 0), 3),
                'start_timestamp_utc': round(lap.start_time, 3),
                'end_timestamp_utc': round(lap.end_time, 3)
            }
        }

        if include_points:
            output['lap']['points'] = LapJsonExporter._export_points(lap)

        return output

    @staticmethod
    def export_multiple_laps(laps):
        """
        Export multiple laps summary metrics to JSON.

        Args:
            laps: list of LapData objects
        
        Returns:
            dict structure ready for json.dumps
        """
        lap_summaries = []
        durations = []

        for i, lap in enumerate(laps):
            speed_stats = LapJsonExporter._calculate_speed_stats(lap)
            summary = {
                'lap_number': i + 1,
                'duration_seconds': round(lap.duration, 3),
                'average_speed_ms': round(speed_stats.get('avg', 0), 3),
                'max_speed_ms': round(speed_stats.get('max', 0), 3),
                'point_count': lap.point_count
            }
            lap_summaries.append(summary)
            durations.append(lap.duration)

        # Overall statistics
        overall = {}
        if len(durations) > 0:
            overall = {
                'lap_count': len(laps),
                'best_lap_seconds': round(min(durations), 3),
                'worst_lap_seconds': round(max(durations), 3),
                'average_lap_seconds': round(sum(durations) / len(durations), 3),
                'total_duration_seconds': round(sum(durations), 3)
            }

        return {
            'version': '1.0',
            'laps': lap_summaries,
            'overall_statistics': overall
        }

    @staticmethod
    def to_json_string(data, pretty_print=True):
        """
        Convert exported data to JSON string.

        Args:
            data: dict from export methods
            pretty_print: whether to format with indentation
        
        Returns:
            JSON string
        """
        try:
            if pretty_print:
                return json.dumps(data, indent=2, ensure_ascii=False)
            else:
                return json.dumps(data, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to serialize to JSON: {}".format(e))
            raise

    @staticmethod
    def _calculate_speed_stats(lap):
        """Calculate speed statistics for a lap."""
        speeds = []
        for point in lap.points:
            if point.speed is not None and point.speed > 0:
                speeds.append(point.speed)

        if not speeds:
            return {'avg': 0, 'max': 0, 'min': 0}

        avg = sum(speeds) / len(speeds)
        max_speed = max(speeds)
        min_speed = min(speeds)

        return {'avg': avg, 'max': max_speed, 'min': min_speed}

    @staticmethod
    def _export_points(lap):
        """Export all GPS points from a lap to list of dicts."""
        points = []
        for point in lap.points:
            p = {
                'latitude': point.latitude,
                'longitude': point.longitude,
                'timestamp_utc': point.timestamp
            }
            if point.speed is not None:
                p['speed_ms'] = point.speed
            if point.altitude is not None:
                p['altitude'] = point.altitude
            if point.track is not None:
                p['track_degrees'] = point.track
            points.append(p)
        return points
