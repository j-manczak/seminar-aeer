"""Assign an observation to the nearest study reactor, if it is close enough."""

from typing import Optional, Tuple

from pipeline.config import SITE_RADIUS_KM
from pipeline.geo import nearest
from pipeline.reactors import Reactor, STUDY_REACTORS


def match(lat: float, lon: float, radius_km: float = SITE_RADIUS_KM) -> Optional[Tuple[Reactor, float]]:
    """Return (reactor, distance_km) for the nearest study reactor within
    ``radius_km``, or None if the point is too far from every study site.

    The radius defaults to the study radius but can be widened, e.g. for weather,
    which is a regional covariate rather than a local treatment.
    """
    reactor, distance = nearest(lat, lon, STUDY_REACTORS)
    if reactor is None or distance > radius_km:
        return None
    return reactor, distance
