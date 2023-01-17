import os
import shutil

from check_folder import delete_folder, create_folder

# PATH TO FOLDER "TEST"
TEST_DIR = os.path.join("..","test")

if os.path.exists(TEST_DIR) :
    # Clean folder test if exists
    shutil.rmtree(TEST_DIR)
else :
    # Create folder test if not exists
    os.makedirs(TEST_DIR)


# FOLDER TO TEST
folder1 = "LAS_ground"
folder2 = "DTM_brut"
folder3 = "DTM_shade"
folder4 = "DTM_color"

dir_folder1 = os.path.join(TEST_DIR, folder1)
dir_folder2 = os.path.join(TEST_DIR, folder2)
dir_folder3 = os.path.join(TEST_DIR, folder3)
dir_folder4 = os.path.join(TEST_DIR, folder4)


def test_create_folder(dest_dir=TEST_DIR):
    """Verify :
        - folders are created"""
    # Create folders
    create_folder(dest_dir)

    assert os.path.exists(dir_folder1) == True
    assert os.path.exists(dir_folder2) == True
    assert os.path.exists(dir_folder3) == True
    assert os.path.exists(dir_folder4) == True


def test_delete_folder(dest_dir=TEST_DIR):
    """Verify :
        - folders are deleted"""
    # Delete folders
    delete_folder(dest_dir)

    assert os.path.exists(dir_folder1) == False
    assert os.path.exists(dir_folder2) == False
    assert os.path.exists(dir_folder3) == False
    assert os.path.exists(dir_folder4) == False