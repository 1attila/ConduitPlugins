from typing import Tuple
from math import floor
import numpy as np
import nbtlib

from mconduit import Vec3d


def is_renderable(
    block_name: str
) -> bool:
    
    if block_name == "air":
        return False

    if block_name == "sunflower":
        return False

    if block_name.__contains__("sign"):
        return False

    if block_name.__contains__("glass"):
        return False

    return True


def raycast(
    world_reader: object,
    origin: Vec3d,
    direction: np.ndarray,
    max_distance: int = 200
) -> Tuple[Vec3d, nbtlib.tag.Base, str, float] | None:

    pos = np.array(
        [floor(i) for i in origin.as_tuple()],
        dtype=int
    )

    step = np.sign(direction).astype(int)
    t_max = np.zeros(3)
    t_delta = np.zeros(3)

    for i in range(3):

        if direction[i] != 0:

            next_boundary = pos[i] + (step[i] > 0)
            t_max[i] = (next_boundary - pos[i]) / direction[i]
            t_delta[i] = abs(1 / direction[i])
        else:
            t_max[i] = float("inf")
            t_delta[i] = float("inf")

    distance = 0
    face = None 

    while distance < max_distance:

        p = Vec3d(*pos)
        block = world_reader.get_block(p)


        if block and is_renderable(block["Name"].replace("minecraft:", "")):
            return Vec3d(*(pos + direction * distance)), block, face, distance

        axis = np.argmin(t_max)
        distance = t_max[axis]
        t_max[axis] += t_delta[axis]
        pos[axis] += step[axis]

        if axis == 0:
            face = "west" if step[axis] > 0 else "east"

        elif axis == 1:
            face = "bottom" if step[axis] > 0 else "top"

        else:
            face = "north" if step[axis] > 0 else "south"