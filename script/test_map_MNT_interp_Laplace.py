import os
import shutil
import numpy as np

from map_MNT_interp_Laplace import delete_folder, create_folder, filter_las_ground

# TEST FILE
INPUT_DIR = "../data/filter_ground/"
FILE_MUTLI_1_TO_5 = "multiclass_1to5.las"
FILE_MUTLI_1_TO_66 = "multiclass_1to66.las"

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

def test_filter_las_ground_class_2(input_dir=INPUT_DIR_2, filename=FILE_DIR_2):
    """Verify :
        - output is an array
        - no points without classif 2"""
    OUT_FILTER_GROUND = filter_las_ground(input_dir=input_dir, filename=filename)

    assert isinstance(OUT_FILTER_GROUND, np.ndarray) # type is array
