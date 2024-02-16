import os
import shutil

from ctview.utils_folder import create_folder, dico_folder_template

OUTPUT_DIR = os.path.join("tmp", "utils_folder")

# FOLDER TO TEST
EXPECTED_DIR_LIST = []

for f_name in dico_folder_template:
    EXPECTED_DIR_LIST.append(os.path.join(OUTPUT_DIR, dico_folder_template[f_name]))


def setup_module():
    try:
        shutil.rmtree(OUTPUT_DIR)

    except FileNotFoundError:
        pass
    os.mkdir(OUTPUT_DIR)


def test_create_folder(dest_dir=OUTPUT_DIR):
    """Verify :
    - folders are created
    """
    setup_module()
    # Create folders
    create_folder(dest_dir, dico_fld=dico_folder_template)

    for dir_expected in EXPECTED_DIR_LIST:
        assert os.path.exists(dir_expected)
