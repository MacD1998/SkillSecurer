# -*- coding: utf-8 -*-
# Racing Metrics Calculator - US-006
# Calculate braking points, corner line deviation, G values, sector lap times

import math
import logging
from skill.nmea_parser import GPSPoint, LapData

logger = logging.getLogger(__name__)


class RacingMetricsCalculator:
    """
    Calculate professional racing metrics from parsed GPS lap data:
    - Braking point detection
    - Corner line deviation from reference
    - Longitudinal and lateral G-force analysis
    - Sector lap time calculation
    """

    def __init__(self, sampling_tolerance=0.1):
        """
        Initialize calculator.
        
        Args:
            sampling_tolerance: time gap tolerance between consecutive points (seconds)
        """
        self.sampling_tolerance = sampling_tolerance

    def detect_braking_points(self, lap, deceleration_threshold=3.0):
        """
        Detect braking points based on longitudinal deceleration.
        
        Args:
            lap: LapData object
            deceleration_threshold: minimum deceleration to count as braking (m/s²)
                                     ~3m/s² = 0.3G is typical aggressive braking
        
        Returns:
            List of braking point dictionaries with position, speed, deceleration
        """
        braking_points = []
        
        if len(lap.points) < 3:
            return braking_points

        for i in range(1, len(lap.points) - 1):
            prev = lap.points[i-1]
            curr = lap.points[i]
            next_p = lap.points[i+1]

            if prev.speed is None or curr.speed is None or next_p.speed is None:
                continue
            if prev.timestamp is None or curr.timestamp is None or next_p.timestamp is None:
                continue

            # Calculate deceleration between prev and next
            dt = next_p.timestamp - prev.timestamp
            if dt <= 0:
                continue

            deceleration = (prev.speed - next_p.speed) / dt
            # Only count significant deceleration
            if deceleration >= deceleration_threshold:
                distance = self._haversine_distance(
                    curr.latitude, curr.longitude,
                    lap.points[0].latitude, lap.points[0].longitude
                )
                braking_points.append({
                    'index': i,
                    'latitude': curr.latitude,
                    'longitude': curr.longitude,
                    'distance_from_start': round(distance, 1),
                    'speed_kmh': round(curr.speed * 3.6, 1) if curr.speed else None,
                    'speed_ms': round(curr.speed, 3) if curr.speed else None,
                    'deceleration_ms2': round(deceleration, 2),
                    'g_force': round(deceleration / 9.81, 2)
                })

        logger.info("RacingMetrics: Detected {} braking points".format(len(braking_points)))
        return braking_points

    def calculate_corner_deviation(self, target_lap, reference_lap, corner_lat, corner_lon, radius=50):
        """
        Calculate average and maximum line deviation at a corner compared to reference.
        
        Args:
            target_lap: target LapData
            reference_lap: reference LapData
            corner_lat: corner center latitude (usually apex)
            corner_lon: corner center longitude
            radius: search radius around corner center (meters)
        
        Returns:
            Dictionary with deviation statistics
        """
        target_points = self._get_points_in_radius(target_lap, corner_lat, corner_lon, radius)
        ref_points = self._get_points_in_radius(reference_lap, corner_lat, corner_lon, radius)

        if len(target_points) == 0 or len(ref_points) == 0:
            return {
                'corner_latitude': corner_lat,
                'corner_longitude': corner_lon,
                'deviation_avg_m': None,
                'deviation_max_m': None,
                'point_count_target': 0,
                'point_count_reference': 0
            }

        # For each target point, find closest distance to reference line
        deviations = []
        for tp in target_points:
            min_dist = float('inf')
            for rp in ref_points:
                dist = self._haversine_distance(
                    tp.latitude, tp.longitude, rp.latitude, rp.longitude
                )
                if dist < min_dist:
                    min_dist = dist
            deviations.append(min_dist)

        avg_dev = sum(deviations) / len(deviations)
        max_dev = max(deviations)

        return {
            'corner_latitude': round(corner_lat, 6),
            'corner_longitude': round(corner_lon, 6),
            'search_radius_m': radius,
            'deviation_avg_m': round(avg_dev, 2),
            'deviation_max_m': round(max_dev, 2),
            'point_count_target': len(target_points),
            'point_count_reference': len(ref_points)
        }

    def analyze_g_forces(self, lap):
        """
        Calculate longitudinal (acceleration/deceleration) and lateral (cornering) G forces.
        
        Uses finite differences on speed and heading changes.
        
        Args:
            lap: LapData object
        
        Returns:
            Dictionary with G-force statistics
        """
        longitudinal_g = []
        lateral_g = []
        samples = []

        if len(lap.points) < 3:
            return {
                'max_longitudinal_g': 0,
                'max_deceleration_g': 0,
                'max_lateral_g': 0,
                'sample_count': 0
            }

        for i in range(1, len(lap.points) - 1):
            prev = lap.points[i-1]
            curr = lap.points[i]
            next_p = lap.points[i+1]

            if prev.timestamp is None or curr.timestamp is None or next_p.timestamp is None:
                continue

            dt = next_p.timestamp - prev.timestamp
            if dt <= 0 or dt > 1.0:
                continue  # Skip too large gaps

            # Longitudinal acceleration: change in speed over time
            if prev.speed is not None and next_p.speed is not None:
                accel = (next_p.speed - prev.speed) / dt
                g = accel / 9.81
                longitudinal_g.append(g)

            # Lateral acceleration: v² / R = v * d(heading)/dt
            if curr.speed is not None and prev.track is not None and curr.track is not None:
                d_heading = math.radians(curr.track - prev.track)
                # Normalize to [-pi, pi]
                while d_heading > math.pi:
                    d_heading -= 2 * math.pi
                while d_heading < -math.pi:
                    d_heading += 2 * math.pi

                rate = d_heading / dt
                lateral_accel = curr.speed * abs(rate)
                g = lateral_accel / 9.81
                lateral_g.append(g)

            # Store sample for detailed output
            samples.append({
                'index': i,
                'latitude': curr.latitude,
                'longitude': curr.longitude,
                'distance': self._haversine_distance(
                    curr.latitude, curr.longitude,
                    lap.points[0].latitude, lap.points[0].longitude
                )
            })

        stats = {
            'sample_count': len(longitudinal_g),
            'max_lateral_g': round(max(lateral_g), 2) if lateral_g else 0,
            'avg_lateral_g': round(sum(lateral_g)/len(lateral_g), 2) if lateral_g else 0
        }

        if longitudinal_g:
            stats['max_positive_g'] = round(max(longitudinal_g), 2)
            stats['max_negative_g'] = round(min(longitudinal_g), 2)
            stats['max_deceleration_g'] = round(-min(longitudinal_g), 2)
        else:
            stats['max_positive_g'] = 0
            stats['max_negative_g'] = 0
            stats['max_deceleration_g'] = 0

        logger.info("RacingMetrics: G-force analysis done, {} samples".format(len(samples)))
        return stats

    def calculate_sector_times(self, lap, sector_split_distances):
        """
        Calculate lap time for each sector based on distance from start.
        
        Args:
            lap: LapData object
            sector_split_distances: list of cumulative distances for sector splits (meters)
                                   e.g. [1000, 2300] for 3 sectors: 0-1000, 1000-2300, 2300-end
        
        Returns:
            List of sector timing dictionaries
        """
        sectors = []
        prev_dist = 0.0
        prev_time = None

        # Sort splits to ensure correct order
        splits = sorted(sector_split_distances)

        for split in splits:
            sector = self._find_sector_time(lap, prev_dist, split)
            if sector:
                sectors.append({
                    'start_distance_m': round(prev_dist, 1),
                    'end_distance_m': round(split, 1),
                    'sector_length_m': round(split - prev_dist, 1),
                    'duration_seconds': round(sector['duration'], 3),
                    'start_timestamp': sector['start_time'],
                    'end_timestamp': sector['end_time']
                })
            prev_dist = split

        # Add final sector from last split to end
        total_dist = self._haversine_distance(
            lap.points[-1].latitude, lap.points[-1].longitude,
            lap.points[0].latitude, lap.points[0].longitude
        )
        final_sector = self._find_sector_time(lap, prev_dist, total_dist)
        if final_sector:
            sectors.append({
                'start_distance_m': round(prev_dist, 1),
                'end_distance_m': round(total_dist, 1),
                'sector_length_m': round(total_dist - prev_dist, 1),
                'duration_seconds': round(final_sector['duration'], 3),
                'start_timestamp': final_sector['start_time'],
                'end_timestamp': final_sector['end_time']
            })

        return sectors

    def calculate_full_lap_metrics(self, lap, reference_lap=None, 
                                   corners=None, sector_splits=None,
                                   braking_threshold=3.0):
        """
        Calculate all racing metrics for a lap in one pass.
        
        Args:
            lap: Target LapData
            reference_lap: Reference LapData for deviation calculation (optional)
            corners: List of (lat, lon, radius) for corners to analyze (optional)
            sector_splits: List of split distances for sectors (optional)
            braking_threshold: Deceleration threshold for braking detection
        
        Returns:
            Dictionary with all metrics
        """
        metrics = {
            'braking_points': self.detect_braking_points(lap, braking_threshold),
            'g_forces': self.analyze_g_forces(lap)
        }

        if sector_splits is not None and len(sector_splits) > 0:
            metrics['sectors'] = self.calculate_sector_times(lap, sector_splits)

        if reference_lap is not None and corners is not None and len(corners) > 0:
            corner_deviations = []
            for (lat, lon, radius) in corners:
                dev = self.calculate_corner_deviation(lap, reference_lap, lat, lon, radius)
                corner_deviations.append(dev)
            metrics['corner_deviations'] = corner_deviations
            metrics['reference_lap_point_count'] = reference_lap.point_count

        metrics['total_points'] = lap.point_count
        return metrics

    # Helper methods
    def _get_points_in_radius(self, lap, center_lat, center_lon, radius):
        """Get all points within given radius from center."""
        points = []
        for point in lap.points:
            if point.latitude is None or point.longitude is None:
                continue
            dist = self._haversine_distance(point.latitude, point.longitude, center_lat, center_lon)
            if dist <= radius:
                points.append(point)
        return points

    def _find_sector_time(self, lap, start_dist, end_dist):
        """Find the start and end time for a sector between two distances."""
        start_time = None
        end_time = None

        # Calculate cumulative distance from start
        if len(lap.points) == 0:
            return None

        prev_lat = lap.points[0].latitude
        prev_lon = lap.points[0].longitude
        cumulative = 0.0

        for point in lap.points:
            if point.latitude is None or point.longitude is None or point.timestamp is None:
                continue

            # Add distance from previous point to cumulative
            if prev_lat is not None and prev_lon is not None:
                segment_dist = self._haversine_distance(
                    point.latitude, point.longitude,
                    prev_lat, prev_lon
                )
                cumulative += segment_dist

            if start_time is None and cumulative >= start_dist:
                start_time = point.timestamp

            if start_time is not None and cumulative >= end_dist:
                end_time = point.timestamp
                break

            prev_lat = point.latitude
            prev_lon = point.longitude

        if start_time is None or end_time is None:
            return None

        return {
            'start_time': start_time,
            'end_time': end_time,
            'duration': end_time - start_time
        }

    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two GPS points in meters."""
        # Handle None inputs gracefully
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return 0.0

        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2)**2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
