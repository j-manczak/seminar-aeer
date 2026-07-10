"""Assign an observation to the nearest study reactor, if it is close enough."""

from typing import Optional, Tuple

from pipeline.config import SITE_RADIUS_KM
from pipeline.geo import nearest
from pipeline.reactors import Reactor, STUDY_REACTORS


def match(lat: float, lon: float) -> Optional[Tuple[Reactor, float]]:
    """Return (reactor, distance_km) for the nearest study reactor within the
    site radius, or None if the point is too far from every study site."""
    reactor, distance = nearest(lat, lon, STUDY_REACTORS)
    if reactor is None or distance > SITE_RADIUS_KM:
        return None
    return reactor, distance
