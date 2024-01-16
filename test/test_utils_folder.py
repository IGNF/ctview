import os
import shutil

from ctview.utils_folder import create_folder, dico_folder_template

tmp_path = os.path.join("tmp")

# FOLDER TO TEST
EXPECTED_DIR_LIST = []

for f_name in dico_folder_template:
    EXPECTED_DIR_LIST.append(os.path.join(tmp_path, dico_folder_template[f_name]))


def setup_module():
    try:
        shutil.rmtree(tmp_path)

    except FileNotFoundError:
        pass
    os.mkdir(tmp_path)


def test_create_folder(dest_dir=tmp_path):
    """Verify :
    - folders are created
    """
    setup_module()
    # Create folders
    create_folder(dest_dir, dico_fld=dico_folder_template)

    for dir_expected in EXPECTED_DIR_LIST:
        assert os.path.exists(dir_expected)
