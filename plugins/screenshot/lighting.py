from typing import Tuple


FACE_LIGHT = {
    "top": 1.0,
    "bottom": 0.5,
    "north": 0.8,
    "south": 0.8,
    "east": 0.7,
    "west": 0.7
}


def apply_lighting(
    color: Tuple[int, int, int, int],
    face: str
) -> Tuple[int, int, int, int]:

    factor = FACE_LIGHT.get(face, 1.0)

    r, g, b, a = color

    return (
        int(r * factor),
        int(g * factor),
        int(b * factor),
        a
    )