"""AR overlay: draws game objects on top of a car's camera image.

Phase 1 (2D): highlight the next gate's markers, show item boxes as sprites
on their markers' corners. Phase 2 (3D): use CameraIntrinsics + solvePnP to
place 3D models on markers.
"""
