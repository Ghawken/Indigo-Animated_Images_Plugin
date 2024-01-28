####################
# C GlennNZ 2023
#
from PIL import Image, ImageSequence
import io
import os
# from pympler import asizeof  ## works well - rather avoid dependncy
from collections import OrderedDict

class ImageFrameServer:
    def __init__(self, logger):
        # Initialize a dictionary to hold counters for each image
        self.counters = {}
        self.logger = logger
        self.logger.debug("Init Image Frame Server")
        self.saveDirectory =  os.path.expanduser("~") + "/" + "Pictures/Indigo-AnimatedImages/"
        self.frame_cache = OrderedDict()  # Initialize cache for frames
        self.MAX_CACHE_SIZE = 5

    ## Add Cache for frames

    # def log_cache_memory_usage(self):
    #     total_size = asizeof.asizeof(self.frame_cache)  ## avoid pympler dependency
    #     self.logger.debug(f"Current deep cache size: {total_size} bytes")
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
    async def get_next_frame(self, gif_name):
        gif_path = os.path.join(self.saveDirectory, gif_name)
        # Check if GIF frames are already cached
        if gif_name in self.frame_cache:
            self.logger.debug(f"Serving {gif_name} from cache")
            frames = self.frame_cache[gif_name]
        else:
            if not os.path.exists(gif_path):
                not_found_path = os.path.join(os.path.dirname(__file__), 'not_found.jpg')
                self.logger.debug(f"No path {not_found_path}")
                with open(not_found_path, 'rb') as file:
                    return file.read(), 'image/jpeg'

            with Image.open(gif_path) as img:
                frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
                # Convert and cache frames
                cached_frames = []
                for frame in frames:
                    byte_io = io.BytesIO()
                    frame.convert('RGB').save(byte_io, 'JPEG')
                    cached_frames.append(byte_io.getvalue())
                self.add_to_cache(gif_name, cached_frames)

        # Serving frames from cache or newly cached
        if gif_name not in self.counters:
            self.counters[gif_name] = 0
        frame_data = self.frame_cache[gif_name][self.counters[gif_name] % len(self.frame_cache[gif_name])]
        self.counters[gif_name] += 1

        return frame_data, 'image/jpeg'

    # async def get_next_frame(self, gif_name):  # Include 'self' here
    #
    #     gif_path = os.path.join(self.saveDirectory, gif_name)
    #
    #     if not os.path.exists(gif_path):
    #         not_found_path = os.path.join(os.path.dirname(__file__), 'not_found.jpg')
    #         self.logger.debug(f"No path {not_found_path}")
    #         with open(not_found_path, 'rb') as file:
    #             return file.read(), 'image/jpeg'
    #
    #     with Image.open(gif_path) as img:
    #         frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
    #         if gif_name not in self.counters:  # Use 'self.counters' here
    #             self.counters[gif_name] = 0
    #         current_frame = frames[self.counters[gif_name] % len(frames)]  # And here
    #         self.counters[gif_name] += 1  # And here
    #         byte_io = io.BytesIO()
    #         current_frame.convert('RGB').save(byte_io, 'JPEG')
    #         byte_io.seek(0)
    #         return byte_io.getvalue(), 'image/jpeg'