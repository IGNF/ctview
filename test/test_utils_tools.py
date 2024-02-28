import laspy
import numpy as np

from ctview.utils_tools import get_pointcloud_origin

INPUT_LAS_50m = "./data/las/test_data_0000_0000_LA93_IGN69_ground.las"
LAS = laspy.read(INPUT_LAS_50m)
INPUT_POINTS = np.vstack((LAS.x, LAS.y, LAS.z)).transpose()
EXPECTED_ORIGIN = (770500, 6277550)


def test_get_pointcloud_origin():
    origin_x, origin_y = get_pointcloud_origin(points=INPUT_POINTS, tile_size=50)
    assert (origin_x, origin_y) == EXPECTED_ORIGIN
    origin_x_2, origin_y_2 = get_pointcloud_origin(points=INPUT_POINTS, tile_size=10, buffer_size=20)
    assert (origin_x_2, origin_y_2) == (EXPECTED_ORIGIN[0] + 20, EXPECTED_ORIGIN[1] - 20)
