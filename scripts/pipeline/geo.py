"""Small geographic helpers used across the pipeline."""

import math
from typing import Iterable, Optional, Tuple

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest(lat: float, lon: float, reactors: Iterable) -> Tuple[Optional[object], float]:
    """Return the reactor closest to (lat, lon) and the distance in km.

    ``reactors`` is any iterable of objects with ``latitude`` and ``longitude``
    attributes (our Reactor dataclass). Returns (None, inf) for an empty input.
    """
    best_reactor = None
    best_distance = float("inf")
    for reactor in reactors:
        distance = haversine_km(lat, lon, reactor.latitude, reactor.longitude)
        if distance < best_distance:
            best_reactor = reactor
            best_distance = distance
    return best_reactor, best_distance
