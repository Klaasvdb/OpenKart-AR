"""Generate printable ArUco markers for the track gates.

    python tools/generate_markers.py --count 8 --out markers/

Print them as large as practical (10–15 cm) with a white border, and glue them
flat on cardboard: bent markers are detected poorly.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from openkart.vision.markers import DICTIONARY


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--size", type=int, default=800, help="pixels per marker")
    parser.add_argument("--out", type=Path, default=Path("markers"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DICTIONARY))
    border = args.size // 8
    for marker_id in range(args.count):
        img = cv2.aruco.generateImageMarker(dictionary, marker_id, args.size)
        img = cv2.copyMakeBorder(img, border, border, border, border, cv2.BORDER_CONSTANT, value=255)
        cv2.putText(img, f"id {marker_id}", (border, border // 2 + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, 0, 2)
        cv2.imwrite(str(args.out / f"marker_{marker_id:02d}.png"), img)
    print(f"{args.count} markers geschreven naar {args.out}/")


if __name__ == "__main__":
    main()
