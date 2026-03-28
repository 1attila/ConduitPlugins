import numpy as np

class Camera:

    def __init__(
        self,
        x: float,
        y: float,
        z: float,
        yaw: float,
        pitch: float,
        fov: float = 70.0
    ) -> "Camera":
        
        self.pos = np.array([x, y, z], dtype=np.float32)
        self.yaw = np.radians(yaw)
        self.pitch = np.radians(pitch)
        self.fov = fov


    def get_view_matrix(self) -> np.ndarray:
        
        cos_p = np.cos(self.pitch)
        sin_p = np.sin(self.pitch)
        cos_y = np.cos(self.yaw)
        sin_y = np.sin(self.yaw)

        forward = np.array([-sin_y * cos_p, -sin_p, cos_y * cos_p])
        forward = forward / np.linalg.norm(forward)

        world_up = np.array([0.0, 1.0, 0.0])
        right = np.cross(forward, world_up)
        right = right / np.linalg.norm(right)
        up = np.cross(right, forward)

        view = np.identity(4, dtype=np.float32)
        view[0, :3] = right
        view[1, :3] = up
        view[2, :3] = -forward
        view[0:3, 3] = -np.dot(view[:3, :3], self.pos)
        
        return view.T
    

    def get_projection_matrix(
        self, width: int,
        height: int,
        near: float = 0.1,
        far: float = 1000.0
    ) -> np.ndarray:
        
        aspect_ratio = width / height
        f = 1.0 / np.tan(np.radians(self.fov) / 2.0)
        
        proj = np.zeros((4, 4), dtype=np.float32)
        proj[0, 0] = f / aspect_ratio
        proj[1, 1] = f
        proj[2, 2] = (far + near) / (near - far)
        proj[2, 3] = (2 * far * near) / (near - far)
        proj[3, 2] = -1.0
        
        return proj.T