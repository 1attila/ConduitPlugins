import moderngl
from pathlib import Path
from PIL import Image

from mconduit import Vec3d, Rot, Dimension, Server
from mconduit.world import CachedWorldReader

from .camera import Camera
from .texture_manager import TextureManager
from .atlas import TextureAtlas
from .mesher import generate_mesh
from .fog import get_fog_color


class Renderer:

    def __init__(
        self,
        server: Server,
        base_path: Path
    ) -> "Renderer":
        
        self.server = server
        self.world_reader = CachedWorldReader(server)
        self.texture_manager = TextureManager(base_path)
        
        self.vertex_shader = """
            #version 330
            uniform mat4 proj;
            uniform mat4 view;
            
            in vec3 in_position;
            in vec2 in_uv;
            in float in_light;
            in vec3 in_tint;
            
            out vec2 v_uv;
            out float v_light;
            out float v_distance;
            out vec3 v_tint;

            void main() {
                vec4 pos = view * vec4(in_position, 1.0);
                v_distance = length(pos.xyz);
                gl_Position = proj * pos;
                v_uv = in_uv;
                v_light = in_light;
                v_tint = in_tint;
            }
        """

        self.fragment_shader = """
            #version 330
            uniform sampler2D Texture;
            uniform vec3 fogColor;
            uniform float maxDist;

            in vec2 v_uv;
            in float v_light;
            in float v_distance;
            in vec3 v_tint;

            out vec4 f_color;

            void main() {
                vec4 tex_color = texture(Texture, v_uv);
                if (tex_color.a < 0.1) discard;
                
                // MULTIPLY BY v_tint HERE:
                vec3 color = tex_color.rgb * v_light * v_tint;
                
                float fogFactor = clamp(v_distance / maxDist, 0.0, 1.0);
                color = mix(color, fogColor, fogFactor);
                
                f_color = vec4(color, tex_color.a);
            }
        """

    def generate_picture(
        self,
        pos: Vec3d,
        rot: Rot,
        dim: Dimension,
        fov: float,
        max_distance: int,
        texture: str,
        width: int,
        height: int
    ) -> Image:
        
        width, height = int(width), int(height)
        fov, max_distance = float(fov), int(max_distance)

        self.texture_manager.load_texture_pack(texture)
        atlas = TextureAtlas(self.texture_manager)
        mesh_data = generate_mesh(self.world_reader, pos, rot, dim, atlas, render_distance=max_distance)

        ctx = moderngl.create_standalone_context()
        prog = ctx.program(vertex_shader=self.vertex_shader, fragment_shader=self.fragment_shader)

        color_tex = ctx.texture((width, height), 4)
        depth_tex = ctx.depth_texture((width, height))

        fbo = ctx.framebuffer(
            color_attachments=[color_tex],
            depth_attachment=depth_tex
        )
        
        fbo.use()
        ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE) 
        
        fog_c = get_fog_color(dim)
        bg_color = (fog_c[0]/255, fog_c[1]/255, fog_c[2]/255, 1.0)
        fbo.clear(*bg_color)
        
        if len(mesh_data) > 0:

            camera = Camera(pos.x, pos.y, pos.z, rot.yaw, rot.pitch, fov)
            
            prog['proj'].write(camera.get_projection_matrix(width, height).tobytes())
            prog['view'].write(camera.get_view_matrix().tobytes())
            prog['fogColor'].value = (bg_color[0], bg_color[1], bg_color[2])
            prog['maxDist'].value = max_distance
            
            tex = ctx.texture((atlas.size, atlas.size), 4, atlas.image.tobytes())
            tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
            tex.use()

            vbo = ctx.buffer(mesh_data.tobytes())
            vao = ctx.vertex_array(prog,[(vbo, '3f 2f 1f 3f', 'in_position', 'in_uv', 'in_light', 'in_tint')])
            
            vao.render(moderngl.TRIANGLES)

            vao.release()
            vbo.release()
            tex.release()

        img_data = fbo.read(components=4)
        img = Image.frombytes('RGBA', (width, height), img_data)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

        fbo.release()
        color_tex.release()
        depth_tex.release()
        prog.release()
        ctx.release()
        
        return img