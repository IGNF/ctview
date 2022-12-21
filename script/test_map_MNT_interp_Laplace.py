import os
import shutil
import numpy as np

from map_MNT_interp_Laplace import delete_folder, create_folder, filter_las_ground

from utils_pdal import get_class_min_max_from_las,get_info_from_las 
# from utils_pdal import get_stats_from_las

# TEST FILE
INPUT_DIR = "../data/filter_ground/"
FILE_MUTLI_1_TO_5 = "multiclass_1to5.las"
FILE_MUTLI_65_TO_66 = "multiclass_65to66.las"

INPUT_DIR_2   = "../../data/data_simple/solo/"
FILE_DIR_2 = "pont_route_OK.las"

# PATH TO FOLDER TEST
OUTPUT_DIR = "../test"

if os.path.exists(OUTPUT_DIR) :
    # Clean folder test if exists
    shutil.rmtree(OUTPUT_DIR)
else :
    # Create folder test if not exists
    os.makedirs(OUTPUT_DIR)

def test_create_folder(dest_dir=OUTPUT_DIR):
    """Verify that folder are created"""
    # Create folders
    create_folder(dest_dir)

    assert os.path.exists(f"{dest_dir}/LAS") == True
    assert os.path.exists(f"{dest_dir}/DTM_brut") == True
    assert os.path.exists(f"{dest_dir}/DTM_shade") == True
    assert os.path.exists(f"{dest_dir}/DTM_color") == True

def test_delete_folder(dest_dir=OUTPUT_DIR):
    """Verify that folder are deleted"""
    # Delete folders
    delete_folder(dest_dir)

    assert os.path.exists(f"{dest_dir}/LAS") == False
    assert os.path.exists(f"{dest_dir}/DTM_brut") == False
    assert os.path.exists(f"{dest_dir}/DTM_shade") == False
    assert os.path.exists(f"{dest_dir}/DTm_color") == False

def test_1_filter_las_ground(input_dir=INPUT_DIR, filename=FILE_MUTLI_1_TO_5):
    """
    Input :
        las_file with points with classif in [1:5]
    Verify :
        - output is an array
        - no points with classif != 2
    """
    # Application of the filter
    OUT_FILTER_GROUND = filter_las_ground(input_dir=input_dir, filename=filename)

    # Get minimim and maximum classification
    minClass, maxClass = get_class_min_max_from_las(points=OUT_FILTER_GROUND)

    assert isinstance(OUT_FILTER_GROUND, np.ndarray) # type is array
    assert minClass == 2 # 2 is the minimum classification of all points
    assert maxClass == 2 # 2 is the maximum classification of all points



def test_2_filter_las_ground(input_dir=INPUT_DIR, filename=FILE_MUTLI_65_TO_66):
    """
    Input :
        las_file with points with classif in [65:66]
    Verify :
        - output is an array
        - no points with classif != 66
    """
    # Application of the filter
    OUT_FILTER_GROUND = filter_las_ground(input_dir=input_dir, filename=filename)

    # Get minimim and maximum classification
    minClass, maxClass = get_class_min_max_from_las(points=OUT_FILTER_GROUND)
    
    assert isinstance(OUT_FILTER_GROUND, np.ndarray) # test if type is array
    assert minClass == 66 # test if 66 is the minimum classification of all points
    assert maxClass == 66 # test if 66 is the maximum classification of all points