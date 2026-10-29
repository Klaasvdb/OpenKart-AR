"""Camera calibration, needed later for AR (placing 3D items on markers).

Plan: film a printed ChArUco board with each car, solve with
cv2.aruco.calibrateCameraCharuco, store per car in config/calibration/<car>.json.
Cars of the same model can probably share one calibration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CameraIntrinsics:
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    distortion: tuple[float, ...] = ()
