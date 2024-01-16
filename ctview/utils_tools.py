# Autor : ELucon

import logging as log
import os

import numpy as np


def give_name_resolution_raster(size):
    """
    Give a resolution from raster

    Args:
        size (int): raster cell size

    Return:
        _size(str): resolution from raster for output's name
    """
    if float(size) == 1.0:
        _size = str("_1M")
    elif float(size) == 0.5:
        _size = str("_50CM")
    elif float(size) == 5.0:
        _size = str("_5M")
    else:
        _size = str(size)
    return _size


def repare_files(las_liste: str, input_dir):
    for filename in las_liste:
        f = open(os.path.join(input_dir, filename), "rb+")
        f.seek(6)
        f.write(bytes([17, 0, 0, 0]))
        f.close()
        log.info(f"fichier {filename} repare")


def get_pointcloud_origin(points: np.array, tile_size: int = 1000, buffer_size: float = 0):
    # Extract coordinates xmin, xmax, ymin and ymax of the original tile without buffer
    x_min, y_min = np.min(points[:, :2], axis=0) + buffer_size
    x_max, y_max = np.max(points[:, :2], axis=0) - buffer_size

    # Calculate the difference Xmin and Xmax, then Ymin and Ymax
    diff_x = x_min - x_max
    diff_y = y_min - y_max
    # Check [x_min - x_max] == amplitude and [y_min - y_max] == amplitude
    if abs(diff_x) <= tile_size and abs(diff_y) <= tile_size:
        origin_x = np.floor(x_min / tile_size) * tile_size  # round low
        origin_y = np.ceil(y_max / tile_size) * tile_size  # round top
        return origin_x, origin_y
    else:
        raise ValueError(f"Extents (diff_x={diff_x} and diff_y={diff_y}) is bigger than tile_size ({tile_size}).")
