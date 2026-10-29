"""ArUco marker detection on car camera frames."""

from __future__ import annotations

import math

from openkart.core.types import MarkerSighting, VideoFrame

# 4x4 markers are the most robust at low resolution and with motion blur.
DICTIONARY = "DICT_4X4_50"


class MarkerDetector:
    def __init__(self, downscale: float = 0.5) -> None:
        import cv2

        self._cv2 = cv2
        self.downscale = downscale
        dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DICTIONARY))
        self._detector = cv2.aruco.ArucoDetector(dictionary, cv2.aruco.DetectorParameters())

    def detect(self, frame: VideoFrame) -> list[MarkerSighting]:
        cv2 = self._cv2
        image = frame.image
        if self.downscale != 1.0:
            image = cv2.resize(image, None, fx=self.downscale, fy=self.downscale)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self._detector.detectMarkers(gray)
        if ids is None:
            return []

        sightings = []
        for quad, marker_id in zip(corners, ids.flatten()):
            pts = tuple((x / self.downscale, y / self.downscale) for x, y in quad.reshape(4, 2))
            sightings.append(MarkerSighting(
                car_id=frame.car_id,
                marker_id=int(marker_id),
                timestamp=frame.timestamp,
                width_px=_mean_edge(pts),
                corners=pts,
            ))
        return sightings


def _mean_edge(pts: tuple[tuple[float, float], ...]) -> float:
    return sum(math.dist(pts[i], pts[(i + 1) % 4]) for i in range(4)) / 4
