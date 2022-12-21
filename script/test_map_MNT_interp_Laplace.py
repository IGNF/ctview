import os
import shutil
import numpy as np

from map_MNT_interp_Laplace import delete_folder, create_folder, filter_las_ground

# TEST FILE
FILE_MUTLI_1_TO_5 = "../data/filter_ground/multiclass_1to5.las"
FILE_MUTLI_1_TO_66 = "../data/filter_ground/multiclass_1to66.las"
OTHER   = "../../data/data_simple/solo/pont_route_OK.las"

# PATH TO FOLDER TEST
SRC = "../test"

if os.path.exists(FPATH) :
    # Clean folder test if exists
    shutil.rmtree(FPATH)
else :
    # Create folder test if not exists
    os.makedirs(FPATH)

def test_create_folder(fpath=FPATH):
    """Verify that folder are created"""
    # Create folders
    create_folder(fpath)

    assert os.path.exists(f"{fpath}/LAS") == True
    assert os.path.exists(f"{fpath}/DTM_brut") == True
    assert os.path.exists(f"{fpath}/DTM_shade") == True
    assert os.path.exists(f"{fpath}/DTM_color") == True

def test_delete_folder(fpath=FPATH):
    """Verify that folder are deleted"""
    # Delete folders
    delete_folder(fpath)

    assert os.path.exists(f"{fpath}/LAS") == False
    assert os.path.exists(f"{fpath}/DTM_brut") == False
    assert os.path.exists(f"{fpath}/DTM_shade") == False
    assert os.path.exists(f"{fpath}/DTm_color") == False

def test_filter_las_ground_class_2(fpath=FPATH, file=OTHER):
    """Verify :
        - output is an array
        - no points without classif 2"""
    OUT_FILTER_GROUND = filter_las_ground(fpath, file)

    assert isinstance(OUT_FILTER_GROUND, np.ndarray) # type is array
