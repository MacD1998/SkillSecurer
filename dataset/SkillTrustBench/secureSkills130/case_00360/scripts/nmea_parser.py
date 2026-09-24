# -*- coding: utf-8 -*-
# NMEA 0183 Parser Skill
# US-003: 能够解析NMEA 0183格式文件并提取圈速、GPS位置等核心数据

import logging
from datetime import datetime
import time
import pynmea2

logger = logging.getLogger(__name__)


class GPSPoint:
    """Represents a single GPS data point extracted from NMEA."""
    def __init__(self, latitude=None, longitude=None, altitude=None,
                 speed=None, track=None, timestamp=None,
                 has_3d_fix=False, satellites_used=0):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.speed = speed  # m/s
        self.track = track  # degrees true
        self.timestamp = timestamp  # unix timestamp UTC
        self.has_3d_fix = has_3d_fix
        self.satellites_used = satellites_used


class LapData:
    """Represents extracted lap data from NMEA file."""
    def __init__(self, start_time, end_time, points):
        self.start_time = start_time
        self.end_time = end_time
        self.points = points
        self.duration = end_time - start_time

    @property
    def point_count(self):
        return len(self.points)


class NMEAParser:
    """Parser for NMEA 0183 format files, extracts GPS and timing data."""

    def __init__(self):
        self._points = []
        self._current_point = GPSPoint()

    def parse_file(self, file_path):
        """Parse entire NMEA file and extract all GPS points."""
        self._points.clear()
        self._current_point = GPSPoint()

        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or not (line.startswith('$') or line.startswith('!')):
                        continue

                    self._parse_sentence(line, line_num)

            logger.info("NMEAParser: Parsed {} valid GPS points from {}".format(len(self._points), file_path))
            return self._points

        except Exception as e:
            logger.error("NMEAParser: Failed to parse file {}: {}".format(file_path, e), exc_info=True)
            raise

    def parse_file_stream(self, file_path):
        """Stream parse NMEA file, yielding one point at a time."""
        self._current_point = GPSPoint()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or not (line.startswith('$') or line.startswith('!')):
                        continue

                    point = self._parse_sentence(line, line_num)
                    if point is not None:
                        yield point

        except Exception as e:
            logger.error("NMEAParser: Failed to stream parse file {}: {}".format(file_path, e), exc_info=True)
            raise

    def _parse_time(self, time_str, date_str=""):
        """Parse NMEA time/date fields to unix timestamp."""
        try:
            time_parts = time_str.split('.')
            hms = time_parts[0]

            hour = int(hms[:2])
            minute = int(hms[2:4])
            second = int(hms[4:6])
            microsecond = 0
            if len(time_parts) > 1:
                microsecond = int(time_parts[1] + '0' * (6 - len(time_parts[1])))

            if date_str:
                day = int(date_str[:2])
                month = int(date_str[2:4])
                year = 2000 + int(date_str[4:6])
            else:
                now = datetime.now()
                day, month, year = now.day, now.month, now.year

            dt = datetime(year, month, day, hour, minute, second, microsecond)
            # Convert to Unix timestamp (UTC)
            timestamp = time.mktime(dt.timetuple()) + microsecond / 1e6
            # mktime assumes local time, we need to adjust to UTC
            local_offset = time.timezone - (time.daylight and 3600 or 0)
            timestamp -= local_offset
            return timestamp

        except Exception as e:
            logger.warning("NMEAParser: Failed to parse time {} {}: {}".format(time_str, date_str, e))
            return 0.0

    def _parse_sentence(self, sentence, line_num):
        """Parse a single NMEA sentence, update current point."""
        try:
            msg = pynmea2.parse(sentence)

            if isinstance(msg, pynmea2.types.talker.GGA):
                return self._parse_gga(msg)
            elif isinstance(msg, pynmea2.types.talker.RMC):
                return self._parse_rmc(msg)
            elif isinstance(msg, pynmea2.types.talker.GSA):
                self._parse_gsa(msg)
            elif isinstance(msg, pynmea2.types.talker.GSV):
                self._parse_gsv(msg)
            else:
                # Unsupported sentence type, keep accumulating
                pass

            return None

        except Exception as e:
            logger.warning("NMEAParser: Failed to parse line {}: {}: {}".format(line_num, sentence, e))
            return None

    def _parse_gga(self, msg):
        """Parse GGA (Global Positioning System Fix Data) sentence."""
        try:
            if msg.timestamp:
                ts = self._parse_time(msg.timestamp.strftime('%H%M%S.%f'))
                self._current_point.timestamp = ts if ts > 0 else None
        except Exception as e:
            logger.warning("NMEAParser: Failed to parse GGA timestamp: {}".format(e))

        try:
            if msg.latitude is not None and msg.longitude is not None:
                self._current_point.latitude = float(msg.latitude)
                self._current_point.longitude = float(msg.longitude)
        except Exception as e:
            logger.warning("NMEAParser: Failed to parse GGA coordinates: {}".format(e))

        try:
            if msg.altitude is not None:
                self._current_point.altitude = float(msg.altitude)
        except Exception as e:
            logger.warning("NMEAParser: Failed to parse GGA altitude: {}".format(e))

        try:
            if msg.num_sats is not None:
                self._current_point.satellites_used = int(msg.num_sats)
        except Exception as e:
            logger.warning("NMEAParser: Failed to parse GGA satellite count: {}".format(e))

        try:
            # GGA fix quality: 0 = invalid, 1 = GPS fix, 2 = DGPS fix
            fix_quality = int(msg.gps_qual) if msg.gps_qual is not None else 0
            # We have 3D fix if altitude is also available
            self._current_point.has_3d_fix = fix_quality > 0 and self._current_point.altitude is not None
        except Exception as e:
            logger.warning("NMEAParser: Failed to parse GGA fix quality: {}".format(e))

        return self._try_emit_point()

    def _parse_rmc(self, msg):
        """Parse RMC (Recommended Minimum Navigation Information) sentence."""
        try:
            if msg.status != 'A':
                # Warning, don't emit point but keep current for other sentences
                return None
        except Exception as e:
            logger.warning("NMEAParser: Failed to parse RMC status: {}".format(e))
            return None

        try:
            if msg.timestamp and hasattr(msg, 'datestamp') and msg.datestamp:
                t_str = msg.timestamp.strftime('%H%M%S.%f')
                d_str = msg.datestamp.strftime('%d%m%y')
                ts = self._parse_time(t_str, d_str)
                self._current_point.timestamp = ts if ts > 0 else None
            elif msg.timestamp:
                ts = self._parse_time(msg.timestamp.strftime('%H%M%S.%f'))
                self._current_point.timestamp = ts if ts > 0 else None
        except Exception as e:
            logger.warning("NMEAParser: Failed to parse RMC timestamp/date: {}".format(e))

        try:
            if msg.latitude is not None and msg.longitude is not None:
                self._current_point.latitude = float(msg.latitude)
                self._current_point.longitude = float(msg.longitude)
        except Exception as e:
            logger.warning("NMEAParser: Failed to parse RMC coordinates: {}".format(e))

        try:
            if msg.spd_over_grnd is not None:
                # Convert knots to m/s
                self._current_point.speed = float(msg.spd_over_grnd) * 0.514444
        except Exception as e:
            logger.warning("NMEAParser: Failed to parse RMC speed: {}".format(e))

        try:
            if msg.true_course is not None:
                self._current_point.track = float(msg.true_course)
        except Exception as e:
            logger.warning("NMEAParser: Failed to parse RMC course: {}".format(e))

        try:
            # RMC with status A already means valid fix
            if self._current_point.latitude is not None and self._current_point.longitude is not None:
                self._current_point.has_3d_fix = self._current_point.has_3d_fix or True
        except Exception as e:
            logger.warning("NMEAParser: Failed to update RMC fix status: {}".format(e))

        return self._try_emit_point()

    def _parse_gsa(self, msg):
        """Parse GSA (GPS DOP and Active Satellites) sentence."""
        try:
            # Fix type: 1 = no fix, 2 = 2D, 3 = 3D
            if msg.fix_type is not None:
                fix_type = int(msg.fix_type)
                self._current_point.has_3d_fix = fix_type >= 3
        except Exception as e:
            logger.warning("NMEAParser: Failed to parse GSA fix type: {}".format(e))

    def _parse_gsv(self, msg):
        """Parse GSV (GPS Satellites in View) sentence."""
        # GSV only provides satellites in view, we already get used count from GGA
        # Don't fail even if parsing fails, it's not critical
        try:
            pass
        except Exception as e:
            logger.warning("NMEAParser: Failed to parse GSV: {}".format(e))

    def _try_emit_point(self):
        """Try to emit the current point if it has minimum required data."""
        if (self._current_point.latitude is not None and
            self._current_point.longitude is not None and
            self._current_point.timestamp is not None):

            # We have enough data for a valid point
            point = self._current_point
            self._points.append(point)
            self._current_point = GPSPoint(
                has_3d_fix=point.has_3d_fix,
                satellites_used=point.satellites_used
            )
            return point

        return None

    def extract_laps(self, points, start_finish_lat, start_finish_lon,
                     threshold_meters=10.0):
        """Extract lap data from GPS points by detecting start/finish line crossings."""
        if len(points) < 2:
            return []

        laps = []
        current_lap_start = None
        lap_points = []

        # Simple crossing detection: when point enters threshold and then exits
        # We count a lap when we cross from outside to inside after having a complete lap
        in_threshold = False

        for point in points:
            if point.latitude is None or point.longitude is None:
                continue

            distance = self._haversine_distance(
                point.latitude, point.longitude,
                start_finish_lat, start_finish_lon
            )

            crossing_detected = distance <= threshold_meters and not in_threshold
            in_threshold = distance <= threshold_meters

            if crossing_detected:
                if current_lap_start is not None and len(lap_points) > 10:  # Minimum points for valid lap
                    # Complete current lap
                    lap = LapData(
                        start_time=current_lap_start,
                        end_time=point.timestamp,
                        points=lap_points.copy()
                    )
                    laps.append(lap)
                    lap_points = []

                if current_lap_start is None:
                    # First crossing, start first lap
                    current_lap_start = point.timestamp

            if current_lap_start is not None:
                lap_points.append(point)

        logger.info("NMEAParser: Extracted {} laps from {} points".format(len(laps), len(points)))
        return laps

    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate great circle distance between two points in meters."""
        import math
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2)**2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
