import logging as log
import os

import numpy as np


def repare_files(las_liste: str, input_dir):
    for filename in las_liste:
        f = open(os.path.join(input_dir, filename), "rb+")
        f.seek(6)
        f.write(bytes([17, 0, 0, 0]))
        f.close()
        log.info(f"fichier {filename} repare")


def get_pointcloud_origin(points: np.array, tile_width: int = 1000, buffer_size: float = 0):
    # Extract coordinates xmin, xmax, ymin and ymax of the original tile without buffer
    x_min, y_min = np.min(points[:, :2], axis=0) + buffer_size
    x_max, y_max = np.max(points[:, :2], axis=0) - buffer_size

    # Calculate the difference Xmin and Xmax, then Ymin and Ymax
    diff_x = x_max - x_min
    diff_y = y_max - y_min
    # Check [x_min - x_max] == amplitude and [y_min - y_max] == amplitude
    if abs(diff_x) <= tile_width and abs(diff_y) <= tile_width:
        origin_x = np.floor(x_min / tile_width) * tile_width  # round low
        origin_y = np.ceil(y_max / tile_width) * tile_width  # round top
        return origin_x, origin_y
    else:
        raise ValueError(f"Extents (diff_x={diff_x} and diff_y={diff_y}) is bigger than tile_width ({tile_width}).")
