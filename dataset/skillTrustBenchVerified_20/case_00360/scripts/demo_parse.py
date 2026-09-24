#!/usr/bin/env python3
"""Demo: Parse NMEA file and extract laps."""

import sys
import logging
logging.basicConfig(level=logging.INFO)

from skill.nmea_parser import NMEAParser


def main():
    if len(sys.argv) < 2:
        print("Usage: {} <nmea-file> [start-finish-lat start-finish-lon]".format(sys.argv[0]))
        sys.exit(1)

    file_path = sys.argv[1]
    parser = NMEAParser()

    print("Parsing {}...".format(file_path))
    points = parser.parse_file(file_path)
    print("Total points: {}".format(len(points)))

    if len(points) == 0:
        print("No valid points parsed")
        sys.exit(0)

    # Print some stats
    valid_points = [p for p in points if p.speed is not None and p.speed > 0]
    if valid_points:
        avg_speed = sum(p.speed for p in valid_points) / len(valid_points)
        max_speed = max(p.speed for p in valid_points)
        print("Average speed: {:.1f} m/s ({:.1f} km/h)".format(avg_speed, avg_speed * 3.6))
        print("Max speed: {:.1f} m/s ({:.1f} km/h)".format(max_speed, max_speed * 3.6))

    # Extract laps if coordinates provided
    if len(sys.argv) == 4:
        sf_lat = float(sys.argv[2])
        sf_lon = float(sys.argv[3])
        laps = parser.extract_laps(points, sf_lat, sf_lon, 20.0)
        print("\nExtracted {} laps:".format(len(laps)))
        for i, lap in enumerate(laps):
            minutes = int(lap.duration) // 60
            seconds = int(lap.duration) % 60
            print("  Lap {}: {}:{:02d} ({:.2f}s), {} points".format(i+1, minutes, seconds, lap.duration, lap.point_count))


if __name__ == "__main__":
    main()
