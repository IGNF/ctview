import numpy as np
import os

from ctview.utils_pdal import stem, parent, read_las_file, get_bounds_from_las

path = os.path.join("test","blue","jones.tif")
dir = os.path.join("test","blue")
filename = "jones"

# TEST FILE
DATA_DIR = os.path.join("data","las")
FILE_MUTLI_1_TO_5 = "multiclass_1to5.las"
FILE_MUTLI_65_TO_66 = "multiclass_65to66.las"

# Expected
# ([minx,maxx],[miny,maxy])
BoundsExpected_FILE_MUTLI_65_TO_66 = ([940967,940973,],[6538270,6538298])

def test_stem():
    assert stem(path) == filename  # get filename without extension


def test_parent():
    assert parent(path) == dir  # get directory


def test_read_las_file():
    pts = read_las_file(input_las=os.path.join(DATA_DIR, FILE_MUTLI_65_TO_66))
    assert isinstance(pts, np.ndarray)  # type is array

def test_get_bounds_from_las():
    bounds = get_bounds_from_las(in_las=os.path.join(DATA_DIR, FILE_MUTLI_65_TO_66))
    assert type(bounds) == tuple
    assert bounds == BoundsExpected_FILE_MUTLI_65_TO_66
