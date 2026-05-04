"""Shim imported before ``mp.solutions.*`` in pose detectors.

MediaPipe 0.10.x wheels usually still expose ``mediapipe.solutions``; some newer
builds removed it. This module validates the legacy API is present so failures
are explicit.
"""

import mediapipe as mp

if not hasattr(mp, "solutions"):
    raise ImportError(
        "mediapipe.solutions is missing from your MediaPipe install. This app "
        "uses the legacy pose API (mp.solutions.pose). Pin a compatible wheel, "
        "for example: pip install 'mediapipe>=0.10.11,<0.10.31'"
    ) from None
