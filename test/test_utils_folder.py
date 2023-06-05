import os
import shutil

from ctview.utils_folder import create_folder, dico_folder, add_folder_list_cycles, delete_empty_folder

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
    - folders are created
    """
    # Create folders
    create_folder(dest_dir)

    for dir_expected in list_dir_expected:
        assert os.path.exists(dir_expected)

def test_add_folder_list_cycles():
    """Verify :
    - keys and values are added to dictionnary
    """
    liste = [1,2,3]
    f = "FOLDER"
    k = "KEY"
    assert len(dico_folder) == 19
    add_folder_list_cycles(List=liste, folder_base=f, key_base=k)
    assert len(dico_folder) == 22

def test_delete_empty_folder():
    """Verify :
    - delete empty folder  
    """
    empty_folder = os.path.join(TEST_DIR, "empty_folder")
    os.mkdir(empty_folder)
    assert os.path.isdir(empty_folder)
    delete_empty_folder(dir=TEST_DIR)
    assert ~os.path.isdir(empty_folder)