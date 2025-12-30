from typing import Optional, Union, Tuple
from PIL import Image
from io import BytesIO
import numpy as np
import requests
import enum
import time
import math

from mconduit import plugins, text, Context, Vec3d
from mconduit.utils.color import rgb_to_argb


SPACING = 0.02


class Persistent(plugins.Persistent):
    downloaded_pictures: dict[str, Union[list, np.array]] = {} # img_name -> processed array
    loaded_pictures: list[str] = []


class Rotation(enum.Enum):
    NONE =   enum.auto()
    CW_90 =  enum.auto()
    CW_180 = enum.auto()
    CCW_90 = enum.auto()


class Mirror(enum.Enum):
    NONE =      enum.auto()
    LeftRight = enum.auto()
    FrontBack = enum.auto()


class ImageRotation:
    """
    Rotation angle (0, 90, 180, 270, none, cw_90, cw_180, ccw_90)
    """

    value: Rotation

    
    def __init__(self, value: str) -> "ImageRotation":
        
        value = value.strip().lower()

        try:
            self.value = {
                "0": Rotation.NONE,
                "none": Rotation.NONE,
                "90": Rotation.CW_90,
                "cw-90": Rotation.CW_90,
                "cw_90": Rotation.CW_90,
                "180": Rotation.CW_180,
                "cw-180": Rotation.CW_180,
                "cw_180": Rotation.CW_180,
                "270": Rotation.CCW_90,
                "-90": Rotation.CCW_90,
                "ccw-90": Rotation.CCW_90,
                "ccw_90": Rotation.CCW_90
                }[value]
        except:
            raise ValueError("Valid values: integers or none/cw_90/cw_180/ccw_90")


class ImageMirroring:
    """
    Mirror options (none, left_rigth, front_back)
    """

    value: str


    def __init__(self, value: str) -> "ImageMirroring":

        value = value.strip().lower()

        try:
            self.value = {
                "none": Mirror.NONE,
                "left-right": Mirror.LeftRight,
                "left_right": Mirror.LeftRight,
                "front-back": Mirror.FrontBack,
                "front_back": Mirror.FrontBack
            }[value]

        except:
            raise ValueError()


class PictureLoader(plugins.Plugin[None, Persistent]):
    """
    Displays realistic pictures in-game
    """


    pic = plugins.Command.group(
        name="pil",
        aliases=["pl"],
        checks=[plugins.check_perms(plugins.Permission.User)]
    )


    def _create_tag(self, name: str) -> str:
        """
        Creates the tag for all the text_displays of that image
        """
        
        id = 0

        for picture in self.persistent.loaded_pictures:

            if picture.startswith(name):
                
                if len(name) < len(picture):
                    suffix = picture[len(name):]

                    if suffix.isdigit():
                        id = max(id, int(suffix))

        return f"{name}{id + 1}"
    

    @pic.command
    def load(self, ctx: Context, url_or_file: str, name: str):
        """
        Downloads an image from the given url or filename and saves it as with the given name
        """
        
        image_arr = self._fetch_image(url_or_file)
        self.persistent.downloaded_pictures[name] = image_arr.tolist()
        self.persistent._save()

        ctx.success(f"Succesfully saved the image as `{name}`")


    def _download_image(self, url: str, name: Optional[str]=None) -> np.ndarray:
        """
        Downloads an image from the given url
        """
        
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))

        if image.mode != "RGBA":
            image = image.convert("RGBA")

        image_arr = np.array(image)
        image_arr = np.rot90(image_arr, k=-1)

        if name is not None:
            self.persistent.downloaded_pictures[name] = image_arr.tolist()
            self.persistent._save()

        return image_arr


    def _fetch_image(self, image: Union[str, list, np.ndarray, Image.Image]) -> np.ndarray:
        """
        Fetches and casts the image from a name/url/array/PIL.Image
        """

        if isinstance(image, np.ndarray):
            return image
        
        if isinstance(image, list):
            return np.asarray(image, np.int16)

        if isinstance(image, Image.Image):
            return np.array(image)

        if isinstance(image, str):

            if image in self.persistent.downloaded_pictures:
                return np.array(self.persistent.downloaded_pictures[image])

            if image.endswith(".png") or image.endswith(".jpg"):
                try:
                    return np.array(Image.open(image))
                except:
                    pass

            if image.startswith("http"):
                return self._download_image(image)

        raise ValueError()

    
    def _rotate_and_mirror_image(self,
                                 image_arr: np.ndarray,
                                 rotation: Rotation,
                                 mirror: Mirror
                                ) -> np.ndarray:
        """
        Rotates and mirrors the image with the given parameters
        """

        if rotation == Rotation.NONE:
            image_arr = np.rot90(image_arr, k=-1)

        elif rotation == Rotation.CW_90:
            image_arr = np.rot90(image_arr, k=-2)

        elif rotation == Rotation.CW_180:
            image_arr = np.rot90(image_arr, k=3)

        elif rotation == Rotation.CCW_90:
            image_arr = np.rot90(image_arr, k=0)

        if mirror == Mirror.LeftRight:
            image_arr = np.fliplr(image_arr)

        if mirror == Mirror.FrontBack:
            image_arr = np.flipud(image_arr)

        return image_arr
    

    def _resize_image(self,
                      image_arr: np.ndarray,
                      size_x: Optional[int]=None,
                      size_y: Optional[int]=None
                     ) -> np.ndarray:
        """
        Resizes the image with the given sizes
        """

        if size_x is not None or size_y is not None:

            img = Image.fromarray(image_arr)

            target_sizes = (
                img.width  if size_x is None else size_x,
                img.height if size_y is None else size_y
            )

            img = img.resize(target_sizes, Image.Resampling.LANCZOS)
            image_arr = np.array(img)
    
        return image_arr
    

    def _get_orientation_vectors(self,
                                 yaw: float=0.0,
                                 pitch: float=0.0
                                ) -> Tuple[Vec3d, Vec3d, Vec3d]:
        """
        Returns the forward, rigth and up vector for the given yaw and pitch
        """

        yaw = math.radians(yaw)
        pitch = math.radians(pitch)

        fx = -math.cos(pitch) * math.sin(yaw)
        fy = -math.sin(pitch)
        fz = math.cos(pitch) * math.cos(yaw)

        forward = Vec3d(fx, fy, fz).normalize()
        world_up = Vec3d(0, 1, 0)

        right = forward.cross(world_up).normalize()

        if right.len < 1e-6:

            alt_up = Vec3d(0, 0, 1)
            right = forward.cross(alt_up).normalize()
        
        up = right.cross(forward).normalize()

        return forward, right, up


    def draw_picture(self,
                     picture: Union[str, np.ndarray, Image.Image],
                     x: float,
                     y: float,
                     z: float,
                     *,
                     yaw: float=0.0,
                     pitch: float=0.0,
                     size_x: Optional[int]=None,
                     size_y: Optional[int]=None,
                     rotation: Rotation=Rotation.NONE,
                     mirror: Mirror=Mirror.NONE,
                     name: str="unknown"
                    ) -> str:
        """
        Draws the given picture in-game and returns it's tag-name

        The picture could be a downloaded image, image-url or PIL.Image.

        If size is set to None, image is not resized
        """

        image_arr = self._fetch_image(picture)
        
        image_arr = self._rotate_and_mirror_image(image_arr, rotation, mirror)
        image_arr = self._resize_image(image_arr, size_x, size_y)

        sy, sx = image_arr.shape[:2]
        corner_pos = Vec3d(x, y, z)
        tag_name = self._create_tag(name)
        
        _forward, right, up = self._get_orientation_vectors(yaw, pitch)
        
        with self.server.all_at_once():

            for py in range(sy):
                for px in range(sx):

                    pos = corner_pos + right * (px * SPACING) + up * (py * SPACING)
                    color = rgb_to_argb(*map(int, image_arr[px, py]))

                    if image_arr[px, py][-1] == 0:
                        continue

                    nbt = "{" + f"""Rotation:[{yaw}F, {pitch}F], background: {color}, Tags:[{tag_name}]""" + "}"

                    self.server.execute(
                        f"""/summon text_display {pos.x} {pos.y} {pos.z} {nbt}"""
                    )
        
        self.persistent.loaded_pictures.append(tag_name)
        self.persistent._save()

        return tag_name

    
    @pic.command
    def display(self,
                ctx: Context,
                name: str,
                x: Optional[float]=None,
                y: Optional[float]=None,
                z: Optional[float]=None,
                yaw: Optional[float]=None,
                pitch: Optional[float]=None,
                size_x: Optional[int]=None,
                size_y: Optional[int]=None,
                rotation: ImageRotation=ImageRotation("none"),
                mirror: ImageMirroring=ImageMirroring("none")
                ):

        if name not in self.persistent.downloaded_pictures.keys():
            ctx.error(f"There is not picture named `{name}`")

        image_arr = np.asarray(self.persistent.downloaded_pictures[name], np.int16)

        rot = ctx.player.rotation

        if yaw is None:
            yaw = rot.yaw + 180

        if pitch is None:
            pitch = -rot.pitch

        if x is None or y is None or z is None:
            corner = (ctx.player.pos + ctx.player.forward_vec * 2)

            temp_size_x = image_arr.shape[1] if size_x is None else size_x
            temp_size_y = image_arr.shape[0] if size_y is None else size_y

            _f, right, up = self._get_orientation_vectors(yaw, pitch)
            x, y, z = (corner + (right * -temp_size_x + up * temp_size_y) * (SPACING / 2)).as_tuple()

            y -= math.sin(pitch)


        ctx.reply(text.aqua("Start displaying..."))

        t0 = time.perf_counter()
        
        tag_name = self.draw_picture(
            image_arr,
            x,
            y,
            z,
            yaw=yaw,
            pitch=pitch,
            size_x=size_x,
            size_y=size_y,
            rotation=rotation.value,
            mirror=mirror.value,
            name=name
        )

        ctx.success(f"Drawing task finished! Saved as `{tag_name}`. Took {time.perf_counter() - t0:.2f} seconds")


    @pic.command(name="list")
    def _list(self, ctx: Context, downloaded: plugins.Flag):
        """
        Lists the loaded pics
        """

        if len(self.persistent.loaded_pictures) == 0 and not downloaded:
            ctx.warn("There is no loaded picture yet!")
            return

        ctx.reply(text.aqua(f"""Loaded pictures: {", ".join(self.persistent.loaded_pictures)}"""))

        if downloaded is True:

            if len(self.persistent.downloaded_pictures) == 0:
                ctx.warn("There is no downloaded picture yet!")
                return

            ctx.reply(text.yellow(f"""Downloaded pictures: {", ".join(self.persistent.downloaded_pictures.keys())}"""))


    @pic.command
    def sizes(self, ctx: Context, picture: str):
        """
        Displays the sizes of the given image
        """

        if picture not in self.persistent.downloaded_pictures.keys():
            ctx.error(f"There is no downloaded image called `{picture}`")
            return

        img_arr = self._fetch_image(picture)

        y, x = img_arr.shape[:2]

        ctx.info(f"`{picture}`: {x}x{y}")

    
    @pic.command
    def clear(self, ctx: Context, name: str):
        """
        Eliminates an image that has been drawn
        """

        if name not in self.persistent.loaded_pictures:
            ctx.error(f"There is not picture named `{name}`")
            return

        self.persistent.loaded_pictures.remove(name)

        self.server.execute(f"/kill @e[tag={name}]")
        ctx.success(f"Picture `{name}` cleared sucesfully")