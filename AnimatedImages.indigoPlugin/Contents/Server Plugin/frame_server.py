####################
# C GlennNZ 2023
#
from PIL import Image, ImageSequence
import io
import os
import indigo
# from pympler import asizeof  ## works well - rather avoid dependncy
from collections import OrderedDict

class ImageFrameServer:
    def __init__(self, logger, plugin):
        # Initialize a dictionary to hold counters for each image
        self.counters = {}
        self.logger = logger
        self.plugin = plugin
        self.logger.debug("Init Image Frame Server")
        self.saveDirectory =  os.path.expanduser("~") + "/" + "Pictures/Indigo-AnimatedImages/"
        self.frame_cache = OrderedDict()  # Initialize cache for frames
        self.not_found_image_data = None  # Placeholder for the cached not found image
        self.MAX_CACHE_SIZE = 5
        self.cache_not_found_image()
    ## Add Cache for frames

    # def log_cache_memory_usage(self):
    #     total_size = asizeof.asizeof(self.frame_cache)  ## avoid pympler dependency
    #     self.logger.debug(f"Current deep cache size: {total_size} bytes")
    def cache_not_found_image(self):
        """
        Load the 'not found' image into memory once to avoid repeated disk access.
        """
        not_found_path = os.path.join(os.path.dirname(__file__), 'not_found.jpg')
        try:
            with open(not_found_path, 'rb') as file:
                self.not_found_image_data = file.read()
        except FileNotFoundError:
            self.logger.error(f"'not_found.jpg' not found at {not_found_path}.")
            self.not_found_image_data = None

    def add_to_cache(self, key, value):
        try:
            if len(self.frame_cache) >= self.MAX_CACHE_SIZE:
                # Remove the first added item (FIFO) to make space
                removed_key, _ = self.frame_cache.popitem(last=False)
                self.logger.debug(f"Evicted {removed_key} from cache to maintain cache size.")
            self.frame_cache[key] = value
            self.logger.debug(f"Added {key} to cache. Current cache size: {len(self.frame_cache)} items.")
        except:
            self.logger.exception("add_to_cached error")
    async def get_next_frame(self, request, gif_name):
        try:
            gif_path = os.path.join(self.saveDirectory, gif_name)
            # get args first
            # show
            show_image = request.args.get("show", "true")
            show_image = self.plugin.substitute(show_image)
            show_image = show_image.lower() in ("yes", "true","1", "yeah", "yep", "ok", "on","active","activated", "home", "100")
            if self.plugin.debug1:
                self.logger.debug(f"{show_image=}")
            if not show_image:
                # If show_image is False, just return blank data instead of an image.
                return b'', 'image/jpeg'
            ## 2nd args

            # Check if GIF frames are already cached
            if gif_name in self.frame_cache:
                if self.plugin.debug1:
                    self.logger.debug(f"Serving {gif_name} frame {self.counters[gif_name] % len(self.frame_cache[gif_name])} from cache")
                frames = self.frame_cache[gif_name]
            else:
                if not os.path.exists(gif_path):
                    if self.plugin.debug1:
                        self.logger.debug("Serving cached 'not found' image.")
                    return self.not_found_image_data, 'image/jpeg'

                with Image.open(gif_path) as img:
                    if img.format in ['GIF', 'WEBP'] and img.is_animated:
                        frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
                    else:
                        frames = [img.copy()]  # Treat as single frame
                    # Convert and cache frames
                    cached_frames = []
                    for frame in frames:
                        byte_io = io.BytesIO()
                        # If the image is in a mode that doesn't support transparency (e.g., 'P' mode for GIFs),
                        # convert it to 'RGBA' to ensure transparency is retained in the PNG output.
                        # However, be aware that 'convert' doesn't apply to 'WEBP' as they should already support transparency.
                        if frame.mode == 'P':
                            frame = frame.convert('RGBA')
                        frame.save(byte_io, 'PNG')
                        cached_frames.append(byte_io.getvalue())
                    self.add_to_cache(gif_name, cached_frames)

            # Serving frames from cache or newly cached
            if gif_name not in self.counters:
                self.counters[gif_name] = 0
            frame_data = self.frame_cache[gif_name][self.counters[gif_name] % len(self.frame_cache[gif_name])]
            self.counters[gif_name] += 1

            return frame_data, 'image/png'
        except:
            self.logger.exception("Caught Exception get_next_frame Sanic App")
