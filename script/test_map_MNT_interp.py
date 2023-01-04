import os
import shutil
import numpy as np

from map_MNT_interp import delete_folder, create_folder, filter_las_ground, write_las, las_prepare_1_file, execute_startin

from utils_pdal import get_class_min_max_from_las,get_info_from_las, read_las_file
# from utils_pdal import get_stats_from_las

# TEST FILE
DATA_DIR = "../data/filter_ground/"
FILE_MUTLI_1_TO_5 = "multiclass_1to5.las"
FILE_MUTLI_65_TO_66 = "multiclass_65to66.las"
PTS_TO_INTERPOL = read_las_file(input_las=DATA_DIR+FILE_MUTLI_65_TO_66)
PTS_OTHER = "oneclass_2.las"


# PATH TO FOLDER TEST
TEST_DIR = "../test/"

if os.path.exists(TEST_DIR) :
    # Clean folder test if exists
    shutil.rmtree(TEST_DIR)
else :
    # Create folder test if not exists
    os.makedirs(TEST_DIR)

def test_create_folder(dest_dir=TEST_DIR):
    """Verify :
        - folders are created"""
    # Create folders
    create_folder(dest_dir)

    assert os.path.exists(f"{dest_dir}/LAS") == True
    assert os.path.exists(f"{dest_dir}/DTM_brut") == True
    assert os.path.exists(f"{dest_dir}/DTM_shade") == True
    assert os.path.exists(f"{dest_dir}/DTM_color") == True


def test_delete_folder(dest_dir=TEST_DIR):
    """Verify :
        - folders are deleted"""
    # Delete folders
    delete_folder(dest_dir)

    assert os.path.exists(f"{dest_dir}/LAS") == False
    assert os.path.exists(f"{dest_dir}/DTM_brut") == False
    assert os.path.exists(f"{dest_dir}/DTM_shade") == False
    assert os.path.exists(f"{dest_dir}/DTm_color") == False


def test_1_filter_las_ground(INPUT_DIR=DATA_DIR, filename=FILE_MUTLI_1_TO_5):
    """
    Input :
        las_file with points where classif in [1:5]
    Verify :
        - output is an array
        - no remaining points with classif != 2
    """
    # Application of the filter
    out_filter_ground = filter_las_ground(input_dir=DATA_DIR, filename=filename)
    # Check Classif of each point
    for p in out_filter_ground :
        assert p[8] == 2 # Classification==2

    assert isinstance(out_filter_ground, np.ndarray) # type is array

def test_2_filter_las_ground(INPUT_DIR=DATA_DIR, filename=FILE_MUTLI_65_TO_66):
    """
    Input :
        las_file with points where classif in [65:66]
    Verify :
        - output is an array
        - no remaining points with classif != 66
    """
    # Application of the filter
    out_filter_ground = filter_las_ground(input_dir=DATA_DIR, filename=filename)
    # Check Classif of each point
    for p in out_filter_ground :
        assert p[8] == 66 # Classification==66

    assert isinstance(out_filter_ground, np.ndarray) # type is array

def test_write_las():
    """
    Verify :
        - file is created
        - extension is las
    """
    input_file = DATA_DIR + FILE_MUTLI_1_TO_5
    input_points = read_las_file(input_las=input_file) # fct tested in test_utils_pdal.py

    filename = "Stand_ardd_Name_File_Test_IGN69.laz"
    output_filename = write_las(input_points=input_points, filename=filename, output_dir=TEST_DIR, name="")
    output_file = TEST_DIR + "LAS/" + output_filename

    assert os.path.exists(output_file) # file created
    assert output_file[-4:] == ".las"  # extension is las

    shutil.rmtree(TEST_DIR + "LAS/")  # suppr folder /test/LAS/



def test_las_prepare_1_file():
    """
    Verify :
        - type and size
    """
    input_file  = DATA_DIR + FILE_MUTLI_1_TO_5
    size        = 1.0

    extends, resolution, origin = las_prepare_1_file(input_file=input_file, size=size)

    assert isinstance(extends, np.ndarray) # type is array
    assert isinstance(resolution, list) and len(resolution)==2 # type is list and len==2
    assert isinstance(origin, list) and len(resolution)==2 # type is list and len==2



def test_execute_startin():
    """
    Verify :
        - return an array
    """
    #input_file  = DATA_DIR + FILE_MUTLI_65_TO_66
    input_file  = DATA_DIR + PTS_OTHER
    size=1.0

    pts_to_interpol, resolution, origin = las_prepare_1_file(input_file=input_file, size=size)

    
    resolution = [21,21]
    print("\n\n\n\nresolution", resolution)

    print("\nPTS_TO_INTERPOL", PTS_TO_INTERPOL)
    ras = execute_startin(
        pts=pts_to_interpol,
        res=resolution,
        origin=origin,
        size=1.0,
        method="Laplace"
    )
    print("\nras", ras)
    assert isinstance(ras, np.ndarray) # type is array

# def test_execute_startin_2():
#     """
#     Verify :
#         - return an array
#     """
#     input_file  = DATA_DIR + FILE_MUTLI_65_TO_66
#     size=1.0

#     pts_to_interpol, resolution, origin = las_prepare_1_file(input_file=input_file, size=size)

#     print("\nPTS_TO_INTERPOL", PTS_TO_INTERPOL)
#     ras = execute_startin(
#         pts=pts_to_interpol,
#         res=resolution,
#         origin=origin,
#         size=1.0,
#         method="TINlinear"
#     )
#     print("\nras", ras)
#     assert isinstance(ras, np.ndarray) # type is array

