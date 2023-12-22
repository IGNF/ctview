import os
import shutil

import laspy
import numpy as np

from ctview.utils_tools import get_pointcloud_origin

TEST_DIR = os.path.join("data", "labo")
dir_filename = os.path.join(TEST_DIR, "table.txt")
table_interpolation = np.ones((2, 3))

path_json_config = os.path.join("ctview", "config.json")

maxX = 30
minX = 0
maxY = 60
minY = 0
res = 5
new_maxX_expected = 25
new_maxY_expected = 55

INPUT_LAS_50m = "./data/las/test_data_0000_0000_LA93_IGN69_ground.las"
LAS = laspy.read(INPUT_LAS_50m)
INPUT_POINTS = np.vstack((LAS.x, LAS.y, LAS.z)).transpose()
EXPECTED_ORIGIN = (770500, 6277550)


def setup_module(module):  # run before the first test
    try:  # Clean folder test if exists
        shutil.rmtree(TEST_DIR)
    except FileNotFoundError:
        pass
    # Create folder test if not exists
    os.makedirs(TEST_DIR)


def teardown_module(module):  # run after the last test
    try:  # Clean folder test if exists
        shutil.rmtree(TEST_DIR)
    except FileNotFoundError:
        pass


def test_get_pointcloud_origin():
    origin_x, origin_y = get_pointcloud_origin(points=INPUT_POINTS, tile_size=50)
    assert (origin_x, origin_y) == EXPECTED_ORIGIN
    origin_x_2, origin_y_2 = get_pointcloud_origin(points=INPUT_POINTS, tile_size=10, buffer_size=20)
    assert (origin_x_2, origin_y_2) == (EXPECTED_ORIGIN[0] + 20, EXPECTED_ORIGIN[1] - 20)
