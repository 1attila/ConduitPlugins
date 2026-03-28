from math import sqrt, sin, cos, pi
import numpy as np

from mconduit import Vec3d, Rot, Dimension
from mconduit.world import CachedWorldReader

from .atlas import TextureAtlas


FACES = {
    "top":    ([ (0,1,0), (0,1,1), (1,1,1), (1,1,0) ],[ (0,0), (0,1), (1,1), (1,0) ], 1.0, (0,1,0)),
    "bottom": ([ (0,0,1), (0,0,0), (1,0,0), (1,0,1) ],[ (0,0), (0,1), (1,1), (1,0) ], 0.5, (0,-1,0)),
    "north":  ([ (1,0,0), (0,0,0), (0,1,0), (1,1,0) ],[ (0,1), (1,1), (1,0), (0,0) ], 0.8, (0,0,-1)),
    "south":  ([ (0,0,1), (1,0,1), (1,1,1), (0,1,1) ],[ (0,1), (1,1), (1,0), (0,0) ], 0.8, (0,0,1)),
    "west":   ([ (0,0,0), (0,0,1), (0,1,1), (0,1,0) ],[ (0,1), (1,1), (1,0), (0,0) ], 0.6, (-1,0,0)),
    "east":   ([ (1,0,1), (1,0,0), (1,1,0), (1,1,1) ],[ (0,1), (1,1), (1,0), (0,0) ], 0.6, (1,0,0))
}


def is_transparent(block_name: str) -> bool:

    invalid_elements = [
        "air", "water", "lava",
        "glass", "sign", "torch", "chain", "rod",
        "flower", "tall_grass", "short_grass",
        "candle", "head", "sapling", "mushroom",
        "fungus", "fern", "bush", "sugar", "bamboo",
        "roots", "vines", "lilac", "coral",
        "dandelion", "poppy", "orchid", "allium",
        "bluet", "tulip", "daisy", "cornflower",
        "lily", "petals", "rose"
    ]

    for e in invalid_elements:
        if e in block_name:
            return True
    
    return False


def get_block_tint(
    block_name: str,
    face: str
) -> tuple[float, float, float]:
    
    r, g, b = 1.0, 1.0, 1.0
    
    if block_name == "grass_block" and face == "top":
        r, g, b = 121/255, 192/255, 90/255

    elif "leaves" in block_name:
        r, g, b = 72/255, 181/255, 76/255
    
    elif block_name in ["grass", "tall_grass", "fern", "large_fern", "vine"]:
        r, g, b = 121/255, 192/255, 90/255
        
    return r, g, b


def generate_mesh(
    world_reader: CachedWorldReader,
    pos: Vec3d,
    rot: Rot,
    dim: Dimension,
    atlas: TextureAtlas,
    render_distance: int = 132
) -> np.ndarray:

    vertices = []
    block_cache = {}

    px, py, pz = int(pos.x), int(pos.y), int(pos.z)
    max_dist_squared = render_distance * render_distance
    rot = rot * pi / 180
    yaw, pitch = rot.yaw, rot.pitch

    dir_x = -sin(yaw) * cos(pitch)
    dir_z = cos(yaw) * cos(pitch)

    scx = (px - render_distance) // 16
    ecx = (px + render_distance) // 16
    scz = (pz - render_distance) // 16
    ecz = (pz + render_distance) // 16

    def get_block(x, y, z):

        pos_tuple = (x, y, z)

        if pos_tuple in block_cache:
            return block_cache[pos_tuple]
        
        block = world_reader.get_block(Vec3d(x, y, z), dim)

        if block is not None:
            block = block["Name"].replace("minecraft:", "")
        
        block_cache[pos_tuple] = block

        return block
    
    world_reader.clean_cache()

    for cx in range(scx, ecx + 1):

        for cz in range(scz, ecz + 1):

            chunk_center_x = cx * 16 + 8
            chunk_center_z = cz * 16 + 8

            dx = chunk_center_x - px
            dz = chunk_center_z - pz
            dist_squared = dx*dx + dz*dz

            if dist_squared > max_dist_squared:
                continue

            dist = sqrt(dist_squared)
            dot = (dx / dist) * dir_x + (dz / dist) * dir_z

            if dot < -0.3:
                continue

            min_y = max(-54, py - render_distance)
            max_y = min(319, py + render_distance)

            for x in range(cx * 16, (cx + 1) * 16):

                for y in range(min_y, max_y):

                    for z in range(cz * 16, (cz + 1) * 16):
                
                        block = world_reader.get_block(Vec3d(x, y, z))
                        if not block: continue
                
                        name = block["Name"]
                        if is_transparent(name): continue
                
                        name_clean = name.replace("minecraft:", "")

                        for face_name, (verts, uv_corners, light, offset) in FACES.items():
                            
                            neighbor = get_block(x + offset[0], y + offset[1], z + offset[2])
                    
                            if not neighbor or is_transparent(neighbor):
                                
                                u0, v0, u1, v1 = atlas.get_uv(name_clean, face_name)
                                tr, tg, tb = get_block_tint(name_clean, face_name)

                                for idx in [0, 1, 2, 0, 2, 3]:
                                    
                                    vx, vy, vz = verts[idx]
                                    uc, vc = uv_corners[idx]
                                    
                                    final_u = u0 if uc == 0 else u1
                                    final_v = v0 if vc == 0 else v1
                            
                                    vertices.extend([
                                        x + vx, y + vy, z + vz,
                                        final_u, final_v,
                                        light,
                                        tr, tg, tb
                                    ])

    return np.array(vertices, dtype=np.float32)