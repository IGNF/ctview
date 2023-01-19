import numpy as np

from utils_pdal import stem, parent, read_las_file


path = "/test/blue/jones.tif"
dir = "/test/blue"
filename = "jones"

# TEST FILE
DATA_DIR = "../data/utils_pdal/"
FILE_MUTLI_1_TO_5 = "multiclass_1to5.las"
FILE_MUTLI_65_TO_66 = "multiclass_65to66.las"


def test_stem():
    assert stem(path) == filename  # get filename without extension


def test_parent():
    assert parent(path) == dir  # get directory


def test_read_las_file():
    pts = read_las_file(input_las=DATA_DIR + FILE_MUTLI_65_TO_66)
    print("\n", pts)
    assert isinstance(pts, np.ndarray)  # type is array
