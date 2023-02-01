import os
import shutil

<<<<<<<< HEAD:test/test_utils_folder.py
from ctview.utils_folder import create_folder, dico_folder
========
from ctview.check_folder import create_folder, dico_folder
>>>>>>>> af18971c5ad9f6217f1619175b98c75e030488e7:test/test_check_folder.py

# PATH TO FOLDER "TEST"
TEST_DIR = os.path.join("data", "labo")

if os.path.exists(TEST_DIR):
    # Clean folder test if exists
    shutil.rmtree(TEST_DIR)
else:
    # Create folder test if not exists
    os.makedirs(TEST_DIR)


# FOLDER TO TEST
list_dir_expected = []

for f_name in dico_folder:
    list_dir_expected.append(os.path.join(TEST_DIR, dico_folder[f_name]))


def test_create_folder(dest_dir=TEST_DIR):
    """Verify :
    - folders are created"""
    # Create folders
    create_folder(dest_dir)

    for dir_expected in list_dir_expected:
        assert os.path.exists(dir_expected)