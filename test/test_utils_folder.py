import os
import shutil
import ctview
from ctview.utils_folder import create_folder, dico_folder_template, add_folder_list_cycles, delete_empty_folder

# PATH TO FOLDER "TEST"
tmp_path = os.path.join("data", "labo")

# FOLDER TO TEST
list_dir_expected = []

for f_name in dico_folder_template:
    list_dir_expected.append(os.path.join(tmp_path, dico_folder_template[f_name]))


def setup_module():
    try:
        shutil.rmtree(tmp_path)

    except (FileNotFoundError):
        pass
    os.mkdir(tmp_path)


def test_create_folder(dest_dir=tmp_path):
    """Verify :
    - folders are created
    """
    setup_module()
    # Create folders
    create_folder(dest_dir, dico_fld=dico_folder_template)

    for dir_expected in list_dir_expected:
        assert os.path.exists(dir_expected)

def test_add_folder_list_cycles():
    """Verify :
    - keys and values are added to dictionnary
    """
    liste = [1,2,3]
    f = "FOLDER"
    k = "KEY"

    assert len(dico_folder_template) == 19

    new_dico = add_folder_list_cycles(List=liste, folder_base=f, key_base=k, dico_fld=dico_folder_template)

    assert len(dico_folder_template) == 19 # verif static dico has not changed

    assert len(new_dico) == 22

def test_delete_empty_folder():
    """Verify :
    - delete empty folder  
    """
    setup_module()
    empty_folder = os.path.join(tmp_path, "empty_folder")
    os.mkdir(empty_folder)
    assert os.path.isdir(empty_folder)
    delete_empty_folder(dir=tmp_path)
    assert ~os.path.isdir(empty_folder)