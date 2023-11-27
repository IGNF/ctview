import os

import numpy as np

from ctview.utils_pdal import get_bounds_from_las, read_las_file

path = os.path.join("test", "blue", "jones.tif")
dir = os.path.join("test", "blue")
filename = "jones"

# Test files
DATA_DIR = os.path.join("data", "las")
FILE_MUTLI_1_TO_5 = "multiclass_1to5.las"
FILE_MUTLI_65_TO_66 = "test_data_multiclass_65to66.las"

# Expected : ([minx,maxx],[miny,maxy])
BoundsExpected_FILE_MUTLI_65_TO_66 = (
    [
        940967,
        940973,
    ],
    [6538270, 6538298],
)


def test_read_las_file():
    pts = read_las_file(input_las=os.path.join(DATA_DIR, FILE_MUTLI_65_TO_66))
    assert isinstance(pts, np.ndarray)  # type is array


def test_get_bounds_from_las():
    bounds = get_bounds_from_las(in_las=os.path.join(DATA_DIR, FILE_MUTLI_65_TO_66))
    assert isinstance(bounds, tuple)
    assert bounds == BoundsExpected_FILE_MUTLI_65_TO_66
