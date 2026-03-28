from typing import Tuple


def get_fog_color(dimension: str) -> Tuple[int, int, int, int]:

    return {
        "the_nether": (120, 30, 30, 255),
        "the_end": (40, 0, 60, 255)
    }.get(dimension, (135, 206, 235, 255))


def apply_fog(
    color: Tuple[int, int, int, int],
    distance: int | None,
    max_distance: int,
    fog_color: Tuple[int, int, int, int]
) -> Tuple[int, int, int, int]:

    if distance is None:
        return fog_color

    t = min(distance / max_distance, 1.0)
    r, g, b, a = color

    r = int(r * (1 - t) + r * t)
    g = int(g * (1 - t) + g * t)
    b = int(b * (1 - t) + b * t)
    
    return r, g, b, 255