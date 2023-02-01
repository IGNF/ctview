import os
import shutil
import numpy as np

from ctview.map_DTM_DSM import (
    filter_las_ground_virtual,
    write_las,
    las_prepare_1_file,
    execute_startin,
)

from ctview.utils_pdal import get_class_min_max_from_las, get_info_from_las, read_las_file

# from utils_pdal import get_stats_from_las

# TEST FILE
DATA_DIR = os.path.join("data","las")
FILE_MUTLI_1_TO_5 = "multiclass_1to5.las"
FILE_MUTLI_65_TO_66 = "multiclass_65to66.las"
PTS_TO_INTERPOL = "oneclass_2.las"


# PATH TO FOLDER TEST
TEST_DIR = os.path.join("data","labo")

def setUpModule(): # run before the first test
    try : # Clean folder test if exists
        shutil.rmtree(TEST_DIR)
    except (FileNotFoundError):
        pass
    # Create folder test if not exists
    os.makedirs(TEST_DIR)


def tearDownModule(): # run after the last test
    try : # Clean folder test if exists
        shutil.rmtree(TEST_DIR)
    except (FileNotFoundError):
        pass


def test_1_filter_las_ground_virtual(INPUT_DIR=DATA_DIR, filename=FILE_MUTLI_1_TO_5):
    """
    Input :
        las_file with points where classif in [1:5]
    Verify :
        - output is an array
        - no remaining points with classif != 2
    """
    # Application of the filter
    out_filter_ground = filter_las_ground_virtual(input_dir=DATA_DIR, filename=filename)
    # Check Classif of each point
    for p in out_filter_ground:
        assert p[8] == 2  # Classification==2

    assert isinstance(out_filter_ground, np.ndarray)  # type is array


def test_2_filter_las_ground_virtual(INPUT_DIR=DATA_DIR, filename=FILE_MUTLI_65_TO_66):
    """
    Input :
        las_file with points where classif in [65:66]
    Verify :
        - output is an array
        - no remaining points with classif != 66
    """
    # Application of the filter
    out_filter_ground = filter_las_ground_virtual(input_dir=DATA_DIR, filename=filename)
    # Check Classif of each point
    for p in out_filter_ground:
        assert p[8] == 66  # Classification==66

    assert isinstance(out_filter_ground, np.ndarray)  # type is array


def test_write_las():
    """
    Test function write_las
    Verify :
        - file is created
        - extension is las
    """
    input_file = os.path.join(DATA_DIR , FILE_MUTLI_1_TO_5)
    input_points = read_las_file(
        input_las=input_file
    )  # fct tested in test_utils_pdal.py

    filename = "Stand_ardd_Name_File_Test_IGN69.laz"
    output_filename = write_las(
        input_points=input_points, filename=filename, output_dir=TEST_DIR, name=""
    )
    print("filename", output_filename)

    assert os.path.exists(output_filename)  # file created
    assert os.path.splitext(output_filename)[1] == ".las"  # extension is las


def test_las_prepare_1_file():
    """
    Verify :
        - type and size
    """
    input_file = os.path.join(DATA_DIR , FILE_MUTLI_1_TO_5)
    size = 1.0

    extends, resolution, origin = las_prepare_1_file(input_file=input_file, size=size)

    assert isinstance(extends, np.ndarray)  # type is array
    assert (
        isinstance(resolution, list) and len(resolution) == 2
    )  # type is list and len==2
    assert isinstance(origin, list) and len(resolution) == 2  # type is list and len==2


def execute_test_mnt(method: str):
    """
    Verify :
        - return an array
    """
    input_file = os.path.join(DATA_DIR , PTS_TO_INTERPOL)
    size = 1.0

    pts_to_interpol, resolution, origin = las_prepare_1_file(
        input_file=input_file, size=size
    )

    ras = execute_startin(
        pts=pts_to_interpol, res=resolution, origin=origin, size=1.0, method=method
    )
    assert isinstance(ras, np.ndarray)  # type is array


def test_execute_startin():
    execute_test_mnt("Laplace")


def test_execute_startin_2():
    execute_test_mnt("TINlinear")
