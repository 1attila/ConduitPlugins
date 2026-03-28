import numpy as np


class Camera:

    def __init__(
        self,
        x: float,
        y: float,
        z: float,
        yaw: float,
        pitch: float,
        fov: int = 70
    ) -> "Camera":

        self.pos = np.array([x, y, z], dtype=float)
        self.yaw = np.radians(yaw)
        self.pitch = np.radians(pitch)
        self.fov = np.radians(fov)

    
    def get_ray_direction(
        self,
        px: int,
        py: int,
        width: int,
        height: int
    ) -> np.ndarray:

        aspect = width / height

        screen_x = (2 * (px + 0.5) / width - 1) * np.tan(self.fov / 2) * aspect
        screen_y = (1 - 2 * (py + 0.5) / height) * np.tan(self.fov / 2)

        direction = np.array([screen_x, screen_y, -1.0])

        cos_y = np.cos(self.yaw)
        sin_y = np.sin(self.yaw)

        dx = direction[0] * cos_y - direction[2] * sin_y
        dy = direction[0] * sin_y + direction[2] * cos_y
        direction[0] = dx
        direction[2] = dy

        cos_p = np.cos(self.pitch)
        sin_p = np.sin(self.pitch)

        dy = direction[1] * cos_p - direction[2] * sin_p
        dz = direction[1] * sin_p - direction[2] * cos_p
        direction[1] = dy
        direction[2] = dz

        return direction / np.linalg.norm(direction)